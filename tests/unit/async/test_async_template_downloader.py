"""Tests for async template downloader.

Tests the AsyncTemplateDownloader and AsyncTemplateRepositoryClient components.
"""

import json
import tempfile

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


aiohttp = pytest.importorskip("aiohttp")

from claude_builder.core.template_management.network.async_template_downloader import (
    AsyncTemplateDownloader,
    AsyncTemplateRepositoryClient,
)
from claude_builder.utils.exceptions import PerformanceError, SecurityError


class TestAsyncTemplateDownloader:
    """Test async template downloader functionality."""

    @pytest.fixture
    def downloader(self):
        """Create downloader for testing."""
        return AsyncTemplateDownloader(
            timeout=5,
            max_download_size=1024 * 1024,  # 1MB
            max_concurrent_downloads=3,
        )

    @pytest.mark.asyncio
    async def test_download_file_async_success(self, downloader):
        """Test successful file download."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            destination = Path(tmp.name)

        try:
            # Mock aiohttp session
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {"Content-Length": "100"}
            mock_response.content.iter_chunked = AsyncMock(
                return_value=iter([b"test content", b" more content"])
            )

            with patch(
                "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
            ) as mock_pool:
                mock_session = AsyncMock()
                mock_get_context = AsyncMock()
                mock_get_context.__aenter__.return_value = mock_response
                mock_get_context.__aexit__.return_value = None
                mock_session.get.return_value = mock_get_context
                mock_pool.return_value.__aenter__.return_value = mock_session
                mock_pool.return_value.__aexit__.return_value = None

                with patch(
                    "claude_builder.core.template_management.network.async_template_downloader.security_validator"
                ) as mock_validator:
                    mock_validator.validate_url.return_value = None
                    mock_validator.validate_file_path.return_value = None

                    await downloader.download_file_async(
                        "https://example.com/test.zip", destination
                    )

            # Verify file was created (would contain mocked content)
            assert destination.exists()

        finally:
            if destination.exists():
                destination.unlink()

    @pytest.mark.asyncio
    async def test_download_file_security_validation(self, downloader):
        """Test security validation during download."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            destination = Path(tmp.name)

        try:
            # Mock security validator to raise SecurityError
            with patch(
                "claude_builder.utils.security.security_validator"
            ) as mock_validator:
                mock_validator.validate_url.side_effect = SecurityError("Invalid URL")

                with pytest.raises(SecurityError, match="Invalid URL"):
                    await downloader.download_file_async(
                        "http://malicious.com/test.zip", destination
                    )

        finally:
            if destination.exists():
                destination.unlink()

    @pytest.mark.asyncio
    async def test_download_file_size_limit(self, downloader):
        """Test download size limit enforcement."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            destination = Path(tmp.name)

        try:
            # Mock response with large content length
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {
                "Content-Length": str(2 * 1024 * 1024)
            }  # 2MB (exceeds 1MB limit)

            with patch(
                "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
            ) as mock_pool:
                mock_session = AsyncMock()
                mock_get_context = AsyncMock()
                mock_get_context.__aenter__.return_value = mock_response
                mock_get_context.__aexit__.return_value = None
                mock_session.get.return_value = mock_get_context
                mock_pool.return_value.__aenter__.return_value = mock_session
                mock_pool.return_value.__aexit__.return_value = None

                with patch(
                    "claude_builder.core.template_management.network.async_template_downloader.security_validator"
                ) as mock_validator:
                    mock_validator.validate_url.return_value = None
                    mock_validator.validate_file_path.return_value = None

                    with pytest.raises(SecurityError, match="File too large"):
                        await downloader.download_file_async(
                            "https://example.com/large.zip", destination
                        )

        finally:
            if destination.exists():
                destination.unlink()

    @pytest.mark.asyncio
    async def test_download_file_http_error(self, downloader):
        """Test handling of HTTP errors."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            destination = Path(tmp.name)

        try:
            # Mock response with error status
            mock_response = AsyncMock()
            mock_response.status = 404

            with patch(
                "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
            ) as mock_pool:
                mock_session = AsyncMock()
                mock_get_context = AsyncMock()
                mock_get_context.__aenter__.return_value = mock_response
                mock_get_context.__aexit__.return_value = None
                mock_session.get.return_value = mock_get_context
                mock_pool.return_value.__aenter__.return_value = mock_session
                mock_pool.return_value.__aexit__.return_value = None

                with patch(
                    "claude_builder.core.template_management.network.async_template_downloader.security_validator"
                ) as mock_validator:
                    mock_validator.validate_url.return_value = None
                    mock_validator.validate_file_path.return_value = None

                    with pytest.raises(PerformanceError, match="HTTP error 404"):
                        await downloader.download_file_async(
                            "https://example.com/missing.zip", destination
                        )

        finally:
            if destination.exists():
                destination.unlink()

    @pytest.mark.asyncio
    async def test_fetch_template_index_async(self, downloader):
        """Test fetching template index."""
        index_data = {
            "templates": [
                {"name": "template1", "version": "1.0"},
                {"name": "template2", "version": "2.0"},
            ]
        }

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps(index_data)

        with patch(
            "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
        ) as mock_pool:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_pool.return_value.__aenter__.return_value = mock_session

            with patch(
                "claude_builder.utils.security.security_validator"
            ) as mock_validator:
                mock_validator.validate_url.return_value = None

                result = await downloader.fetch_template_index_async(
                    "https://example.com/templates"
                )

        assert result == index_data
        assert len(result["templates"]) == 2

    @pytest.mark.asyncio
    async def test_fetch_template_index_invalid_json(self, downloader):
        """Test handling of invalid JSON in template index."""
        # Mock response with invalid JSON
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "invalid json content"

        with patch(
            "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
        ) as mock_pool:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_pool.return_value.__aenter__.return_value = mock_session

            with patch(
                "claude_builder.utils.security.security_validator"
            ) as mock_validator:
                mock_validator.validate_url.return_value = None

                with pytest.raises(PerformanceError, match="Invalid JSON"):
                    await downloader.fetch_template_index_async(
                        "https://example.com/templates"
                    )

    @pytest.mark.asyncio
    async def test_download_template_bundle_async(self, downloader):
        """Test template bundle download and extraction."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            extract_dir = Path(tmp_dir) / "extracted"

            # Mock successful download
            with patch.object(
                downloader, "download_file_async", new_callable=AsyncMock
            ) as mock_download:
                with patch(
                    "claude_builder.utils.security.security_validator"
                ) as mock_validator:
                    mock_validator.safe_extract_zip.return_value = None

                    await downloader.download_template_bundle_async(
                        "https://example.com/template.zip", extract_dir
                    )

            # Verify download was called
            mock_download.assert_called_once()

            # Verify extraction was attempted
            mock_validator.safe_extract_zip.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_download_async(self, downloader):
        """Test batch download functionality."""
        download_requests = [
            {
                "url": "https://example.com/file1.zip",
                "destination": Path("/tmp/file1.zip"),
            },
            {
                "url": "https://example.com/file2.zip",
                "destination": Path("/tmp/file2.zip"),
            },
        ]

        # Mock successful downloads
        with patch.object(
            downloader, "download_file_async", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = None

            # Mock file stats for successful results
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                results = await downloader.batch_download_async(download_requests)

        assert len(results) == 2
        for result in results:
            assert "success" in result
            assert "url" in result
            assert "destination" in result

    @pytest.mark.asyncio
    async def test_batch_download_with_errors(self, downloader):
        """Test batch download with some failures."""
        download_requests = [
            {
                "url": "https://example.com/good.zip",
                "destination": Path("/tmp/good.zip"),
            },
            {"url": "https://example.com/bad.zip", "destination": Path("/tmp/bad.zip")},
        ]

        # Mock first success, second failure
        async def mock_download(url, dest):
            if "bad" in url:
                raise PerformanceError("Download failed")

        with patch.object(downloader, "download_file_async", side_effect=mock_download):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                results = await downloader.batch_download_async(download_requests)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "error" in results[1]

    @pytest.mark.asyncio
    async def test_stream_large_file_async(self, downloader):
        """Test streaming large files."""
        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = [
            b"chunk1",
            b"chunk2",
            b"chunk3",
        ]

        with patch(
            "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
        ) as mock_pool:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_pool.return_value.__aenter__.return_value = mock_session

            with patch(
                "claude_builder.utils.security.security_validator"
            ) as mock_validator:
                mock_validator.validate_url.return_value = None

                chunks = []
                async for chunk in downloader.stream_large_file_async(
                    "https://example.com/large.file"
                ):
                    chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0] == b"chunk1"
        assert chunks[1] == b"chunk2"
        assert chunks[2] == b"chunk3"

    @pytest.mark.asyncio
    async def test_stream_large_file_size_limit(self, downloader):
        """Test size limit enforcement during streaming."""
        # Mock response that exceeds size limit
        large_chunk = b"x" * (downloader.max_download_size + 1)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = [large_chunk]

        with patch(
            "claude_builder.core.template_management.network.async_template_downloader.AsyncConnectionPool"
        ) as mock_pool:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_pool.return_value.__aenter__.return_value = mock_session

            with patch(
                "claude_builder.utils.security.security_validator"
            ) as mock_validator:
                mock_validator.validate_url.return_value = None

                with pytest.raises(SecurityError, match="Stream exceeded size limit"):
                    async for chunk in downloader.stream_large_file_async(
                        "https://example.com/too_large.file"
                    ):
                        pass

    def test_get_performance_stats(self, downloader):
        """Test performance statistics retrieval."""
        stats = downloader.get_performance_stats()

        assert "downloader_config" in stats
        assert "timeout" in stats["downloader_config"]
        assert "max_download_size" in stats["downloader_config"]
        assert "max_concurrent_downloads" in stats["downloader_config"]
        assert "caching_enabled" in stats["downloader_config"]

        assert "active_downloads" in stats
        assert "available_slots" in stats
        assert "cache_stats" in stats
        assert "operation_metrics" in stats


class TestAsyncTemplateRepositoryClient:
    """Test async template repository client functionality."""

    @pytest.fixture
    def repository_client(self):
        """Create repository client for testing."""
        mock_downloader = AsyncMock()
        return AsyncTemplateRepositoryClient(
            "https://example.com/templates",
            downloader=mock_downloader,
        )

    @pytest.mark.asyncio
    async def test_list_templates_async(self, repository_client):
        """Test listing templates from repository."""
        index_data = {
            "templates": [
                {"name": "python", "description": "Python template"},
                {"name": "rust", "description": "Rust template"},
            ]
        }

        # Mock downloader response
        repository_client.downloader.fetch_template_index_async.return_value = (
            index_data
        )

        templates = await repository_client.list_templates_async()

        assert len(templates) == 2
        assert templates[0]["name"] == "python"
        assert templates[1]["name"] == "rust"

    @pytest.mark.asyncio
    async def test_get_template_metadata_async_found(self, repository_client):
        """Test getting template metadata for existing template."""
        templates = [
            {"name": "python", "version": "1.0", "description": "Python template"},
            {"name": "rust", "version": "2.0", "description": "Rust template"},
        ]

        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": templates
        }

        metadata = await repository_client.get_template_metadata_async("python")

        assert metadata["name"] == "python"
        assert metadata["version"] == "1.0"
        assert metadata["description"] == "Python template"

    @pytest.mark.asyncio
    async def test_get_template_metadata_async_not_found(self, repository_client):
        """Test getting template metadata for non-existent template."""
        templates = [
            {"name": "python", "version": "1.0"},
        ]

        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": templates
        }

        with pytest.raises(PerformanceError, match="Template not found: nonexistent"):
            await repository_client.get_template_metadata_async("nonexistent")

    @pytest.mark.asyncio
    async def test_download_template_async(self, repository_client):
        """Test downloading specific template."""
        template_metadata = {
            "name": "python",
            "version": "1.0",
            "download_url": "/templates/python.zip",
        }

        # Mock getting metadata
        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": [template_metadata]
        }

        # Mock template bundle download
        repository_client.downloader.download_template_bundle_async = AsyncMock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = Path(tmp_dir)

            result = await repository_client.download_template_async(
                "python", destination
            )

        assert result["name"] == "python"
        assert result["version"] == "1.0"

        # Verify download was called with full URL
        repository_client.downloader.download_template_bundle_async.assert_called_once_with(
            "https://example.com/templates/templates/python.zip", destination
        )

    @pytest.mark.asyncio
    async def test_download_template_async_no_download_url(self, repository_client):
        """Test downloading template without download URL."""
        template_metadata = {
            "name": "python",
            "version": "1.0",
            # No download_url
        }

        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": [template_metadata]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = Path(tmp_dir)

            with pytest.raises(PerformanceError, match="No download URL"):
                await repository_client.download_template_async("python", destination)

    @pytest.mark.asyncio
    async def test_search_templates_async(self, repository_client):
        """Test searching templates."""
        templates = [
            {
                "name": "python-web",
                "description": "Python web application",
                "tags": ["python", "web"],
            },
            {
                "name": "python-cli",
                "description": "Python CLI application",
                "tags": ["python", "cli"],
            },
            {
                "name": "rust-web",
                "description": "Rust web service",
                "tags": ["rust", "web"],
            },
        ]

        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": templates
        }

        # Search for "python"
        results = await repository_client.search_templates_async("python", limit=10)

        assert len(results) == 2
        assert all("python" in t["name"].lower() for t in results)

        # Search for "web"
        results = await repository_client.search_templates_async("web", limit=10)

        assert len(results) == 2
        assert all(
            "web" in t["description"].lower() or "web" in t["tags"] for t in results
        )

        # Search with limit
        results = await repository_client.search_templates_async("python", limit=1)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_templates_async_no_matches(self, repository_client):
        """Test searching with no matching templates."""
        templates = [
            {"name": "python", "description": "Python template", "tags": ["python"]},
        ]

        repository_client.downloader.fetch_template_index_async.return_value = {
            "templates": templates
        }

        results = await repository_client.search_templates_async(
            "nonexistent", limit=10
        )

        assert len(results) == 0
