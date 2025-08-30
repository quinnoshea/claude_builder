"""Async template download and network operations.

This module provides async implementations of template download operations,
optimized for performance and memory efficiency in Phase 3.4.
"""

import asyncio
import json
import logging
import tempfile

from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiofiles  # type: ignore[import-untyped]
import aiohttp

from claude_builder.utils.async_performance import (
    AsyncConnectionPool,
    AsyncFileProcessor,
    async_rate_limit,
    async_retry,
    cache,
    performance_monitor,
)
from claude_builder.utils.exceptions import PerformanceError, SecurityError
from claude_builder.utils.security import security_validator


class AsyncTemplateDownloader:
    """Async template downloader with performance optimization."""

    def __init__(
        self,
        *,
        timeout: int = 30,
        max_download_size: int = 50 * 1024 * 1024,
        max_concurrent_downloads: int = 5,
        enable_caching: bool = True,
    ):
        """Initialize async downloader with performance settings.

        Args:
            timeout: Network request timeout in seconds
            max_download_size: Maximum download size in bytes
            max_concurrent_downloads: Maximum concurrent downloads
            enable_caching: Whether to enable response caching
        """
        self.timeout = timeout
        self.max_download_size = max_download_size
        self.max_concurrent_downloads = max_concurrent_downloads
        self.enable_caching = enable_caching
        self.logger = logging.getLogger(__name__)

        # Performance components
        self._semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self._file_processor = AsyncFileProcessor(
            max_concurrent_files=max_concurrent_downloads
        )

    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError,))
    @async_rate_limit(calls_per_second=10.0, burst_size=20)
    async def download_file_async(self, url: str, destination: Path) -> None:
        """Download file asynchronously with comprehensive optimization.

        Args:
            url: URL to download from
            destination: Local path to save file

        Raises:
            SecurityError: If URL validation fails or download exceeds limits
            PerformanceError: If download performance issues occur
        """
        async with performance_monitor.track_operation("async_file_download") as op:
            op["url"] = url
            op["destination"] = str(destination)

            async with self._semaphore:
                await self._download_file_internal(url, destination)

    async def _download_file_internal(self, url: str, destination: Path) -> None:
        """Internal download implementation with security validation."""
        try:
            # Security validation
            security_validator.validate_url(url)
            security_validator.validate_file_path(str(destination.name))

            async with AsyncConnectionPool(
                max_connections=self.max_concurrent_downloads,
                timeout=self.timeout,
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise PerformanceError(
                            f"HTTP error {response.status} for URL: {url}"
                        )

                    # Check content length
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        size = int(content_length)
                        if size > self.max_download_size:
                            raise SecurityError(
                                f"File too large: {size} bytes > {self.max_download_size} bytes"
                            )

                    # Stream download with size monitoring
                    await self._stream_download(response, destination)

        except (SecurityError, PerformanceError):
            raise
        except Exception as e:
            self.logger.error(f"Download failed for {url}: {e}")
            raise PerformanceError(f"Download error: {e}") from e

    async def _stream_download(
        self, response: aiohttp.ClientResponse, destination: Path
    ) -> None:
        """Stream download with memory optimization."""
        downloaded = 0
        chunk_size = 8192

        async with aiofiles.open(destination, "wb") as f:
            async for chunk in response.content.iter_chunked(chunk_size):
                downloaded += len(chunk)
                if downloaded > self.max_download_size:
                    raise SecurityError(
                        f"Download exceeded size limit: {downloaded} bytes"
                    )

                await f.write(chunk)

                # Yield control periodically to prevent blocking
                if downloaded % (chunk_size * 10) == 0:
                    await asyncio.sleep(0)

        self.logger.info(f"Downloaded {downloaded} bytes to {destination}")

    @async_retry(max_attempts=2, delay=0.5)
    async def fetch_template_index_async(self, source_url: str) -> Dict[str, Any]:
        """Fetch template index asynchronously with caching.

        Args:
            source_url: Base URL of template repository

        Returns:
            Parsed JSON index data
        """
        async with performance_monitor.track_operation("fetch_template_index") as op:
            op["source_url"] = source_url

            # Check cache first if enabled
            cache_key = f"template_index:{source_url}"
            if self.enable_caching:
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    self.logger.debug(f"Cache hit for template index: {source_url}")
                    return cached_result  # type: ignore[no-any-return]

            try:
                security_validator.validate_url(source_url)
                index_url = f"{source_url.rstrip('/')}/index.json"

                async with AsyncConnectionPool(timeout=self.timeout) as session:
                    async with session.get(index_url) as response:
                        if response.status != 200:
                            raise PerformanceError(
                                f"Failed to fetch index: HTTP {response.status}"
                            )

                        content = await response.text()
                        result = json.loads(content)

                        # Cache successful result
                        if self.enable_caching:
                            await cache.set(cache_key, result)

                        return result  # type: ignore[no-any-return]

            except json.JSONDecodeError as e:
                raise PerformanceError(f"Invalid JSON in template index: {e}") from e
            except Exception as e:
                self.logger.error(
                    f"Failed to fetch template index from {source_url}: {e}"
                )
                raise PerformanceError(f"Template index fetch failed: {e}") from e

    async def download_template_bundle_async(
        self, bundle_url: str, extract_to: Path
    ) -> None:
        """Download and extract template bundle asynchronously.

        Args:
            bundle_url: URL of template bundle (zip file)
            extract_to: Directory to extract bundle to
        """
        async with performance_monitor.track_operation(
            "download_template_bundle"
        ) as op:
            op["bundle_url"] = bundle_url
            op["extract_to"] = str(extract_to)

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                # Download bundle
                await self.download_file_async(bundle_url, tmp_path)

                # Extract with security validation
                await self._extract_bundle_async(tmp_path, extract_to)

            finally:
                # Clean up temporary file
                if tmp_path.exists():
                    tmp_path.unlink()

    async def _extract_bundle_async(self, bundle_path: Path, extract_to: Path) -> None:
        """Extract bundle asynchronously with security validation."""
        try:
            # Use sync method for zip extraction (no async zip library available)
            # But run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: security_validator.safe_extract_zip(bundle_path, extract_to),
            )

            self.logger.info(f"Extracted template bundle to {extract_to}")

        except Exception as e:
            self.logger.error(f"Failed to extract bundle {bundle_path}: {e}")
            raise PerformanceError(f"Bundle extraction failed: {e}") from e

    async def batch_download_async(
        self, download_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Batch download multiple files asynchronously.

        Args:
            download_requests: List of {"url": str, "destination": Path} dicts

        Returns:
            List of download results with status and timing info
        """
        async with performance_monitor.track_operation("batch_download") as op:
            op["request_count"] = len(download_requests)

            # Create download tasks
            tasks = []
            for i, request in enumerate(download_requests):
                task = asyncio.create_task(
                    self._download_with_result(i, request),
                    name=f"download_{i}",
                )
                tasks.append(task)

            # Wait for all downloads to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "success": False,
                            "error": str(result),
                            "type": type(result).__name__,
                        }
                    )
                else:
                    processed_results.append(result)  # type: ignore[arg-type]

            return processed_results

    async def _download_with_result(
        self, index: int, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Download file and return detailed result."""
        start_time = asyncio.get_event_loop().time()

        try:
            await self.download_file_async(request["url"], request["destination"])

            end_time = asyncio.get_event_loop().time()

            return {
                "index": index,
                "success": True,
                "url": request["url"],
                "destination": str(request["destination"]),
                "duration": end_time - start_time,
                "file_size": request["destination"].stat().st_size,
            }

        except Exception as e:
            end_time = asyncio.get_event_loop().time()

            return {
                "index": index,
                "success": False,
                "url": request["url"],
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": end_time - start_time,
            }

    async def stream_large_file_async(self, url: str) -> AsyncGenerator[bytes, None]:
        """Stream large file asynchronously without loading into memory.

        Args:
            url: URL to stream from

        Yields:
            File chunks as bytes
        """
        async with performance_monitor.track_operation("stream_large_file") as op:
            op["url"] = url

            try:
                security_validator.validate_url(url)

                async with AsyncConnectionPool(timeout=self.timeout) as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise PerformanceError(
                                f"HTTP error {response.status} for streaming URL: {url}"
                            )

                        total_downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            total_downloaded += len(chunk)

                            if total_downloaded > self.max_download_size:
                                raise SecurityError(
                                    f"Stream exceeded size limit: {total_downloaded} bytes"
                                )

                            yield chunk

                            # Yield control periodically
                            if total_downloaded % (8192 * 10) == 0:
                                await asyncio.sleep(0)

            except (SecurityError, PerformanceError):
                raise
            except Exception as e:
                self.logger.error(f"Failed to stream {url}: {e}")
                raise PerformanceError(f"Streaming failed: {e}") from e

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for download operations."""
        return {
            "downloader_config": {
                "timeout": self.timeout,
                "max_download_size": self.max_download_size,
                "max_concurrent_downloads": self.max_concurrent_downloads,
                "caching_enabled": self.enable_caching,
            },
            "active_downloads": self._semaphore.locked(),
            "available_slots": self._semaphore._value,
            "cache_stats": cache.get_stats(),
            "operation_metrics": performance_monitor.get_metrics(),
        }


class AsyncTemplateRepositoryClient:
    """Async client for template repository operations."""

    def __init__(
        self,
        base_url: str,
        *,
        downloader: Optional[AsyncTemplateDownloader] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.downloader = downloader or AsyncTemplateDownloader()
        self.logger = logging.getLogger(__name__)

    async def list_templates_async(self) -> List[Dict[str, Any]]:
        """List available templates from repository."""
        try:
            index = await self.downloader.fetch_template_index_async(self.base_url)
            return index.get("templates", [])  # type: ignore[no-any-return]
        except Exception as e:
            self.logger.error(f"Failed to list templates from {self.base_url}: {e}")
            raise PerformanceError(f"Template listing failed: {e}") from e

    async def get_template_metadata_async(self, template_name: str) -> Dict[str, Any]:
        """Get metadata for specific template."""
        templates = await self.list_templates_async()

        for template in templates:
            if template.get("name") == template_name:
                return template

        raise PerformanceError(f"Template not found: {template_name}")

    async def download_template_async(
        self, template_name: str, destination: Path
    ) -> Dict[str, Any]:
        """Download specific template."""
        metadata = await self.get_template_metadata_async(template_name)
        download_url = metadata.get("download_url")

        if not download_url:
            raise PerformanceError(f"No download URL for template: {template_name}")

        # Create full URL if relative
        if download_url.startswith("/"):
            download_url = f"{self.base_url}{download_url}"

        await self.downloader.download_template_bundle_async(download_url, destination)

        return metadata

    async def search_templates_async(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search templates by query."""
        templates = await self.list_templates_async()

        # Simple search implementation
        matching_templates = []
        query_lower = query.lower()

        for template in templates:
            name = template.get("name", "").lower()
            description = template.get("description", "").lower()
            tags = [tag.lower() for tag in template.get("tags", [])]

            if (
                query_lower in name
                or query_lower in description
                or any(query_lower in tag for tag in tags)
            ):
                matching_templates.append(template)

                if len(matching_templates) >= limit:
                    break

        return matching_templates
