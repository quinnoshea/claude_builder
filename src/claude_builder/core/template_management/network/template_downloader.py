"""Template download and network operations.

This module handles all network-related operations for template management,
including downloading templates, fetching metadata, and repository access.
Extracted from template_manager.py to reduce complexity and improve maintainability.
"""

import json
import logging
import tempfile

from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from claude_builder.utils.exceptions import SecurityError
from claude_builder.utils.security import security_validator


class TemplateDownloader:
    """Handles template download and network operations with security validation."""

    def __init__(self, *, timeout: int = 30, max_download_size: int = 50 * 1024 * 1024):
        """Initialize downloader with configurable limits.

        Args:
            timeout: Network request timeout in seconds
            max_download_size: Maximum download size in bytes (50MB default)
        """
        self.timeout = timeout
        self.max_download_size = max_download_size
        self.logger = logging.getLogger(__name__)

    def download_file(self, url: str, destination: Path) -> None:
        """Download file from URL with comprehensive security validation.

        Args:
            url: URL to download from
            destination: Local path to save file

        Raises:
            SecurityError: If URL validation fails or download exceeds limits
            HTTPError: If HTTP request fails
            URLError: If network connection fails
        """
        try:
            # Comprehensive URL validation with whitelist
            security_validator.validate_url(url)

            # Validate destination path against traversal
            security_validator.validate_file_path(str(destination.name))

            request = Request(url, headers={"User-Agent": "Claude-Builder/0.1.0"})

            self.logger.info(f"Downloading file from validated URL: {url}")
            with urlopen(request, timeout=self.timeout) as response:
                # Check content length to prevent large downloads
                content_length = response.headers.get("Content-Length")
                if content_length:
                    size = int(content_length)
                    if size > self.max_download_size:
                        raise SecurityError(
                            f"File too large: {size} bytes > {self.max_download_size} bytes"
                        )

                # Read with size limit to prevent zip bombs
                with destination.open("wb") as f:
                    downloaded = 0
                    chunk_size = 8192

                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        downloaded += len(chunk)
                        if downloaded > self.max_download_size:
                            raise SecurityError(
                                f"Download exceeded size limit: {downloaded} bytes"
                            )

                        f.write(chunk)

            self.logger.info(
                f"Successfully downloaded {downloaded} bytes to {destination}"
            )

        except SecurityError:
            # Re-raise security errors as-is
            raise
        except (HTTPError, URLError) as e:
            self.logger.error(f"Failed to download {url}: {e}")
            raise SecurityError(f"Download failed: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {url}: {e}")
            raise SecurityError(f"Download error: {e}") from e

    def fetch_template_index(self, source_url: str) -> Dict[str, Any]:
        """Fetch template index from repository source.

        Args:
            source_url: Base URL of template repository

        Returns:
            Parsed JSON index data

        Raises:
            SecurityError: If URL validation fails or content is invalid
            json.JSONDecodeError: If response is not valid JSON
        """
        index_url = urljoin(source_url, "index.json")

        # Comprehensive URL validation
        security_validator.validate_url(index_url)

        request = Request(index_url, headers={"User-Agent": "Claude-Builder/0.1.0"})

        self.logger.info(f"Fetching template index from validated URL: {index_url}")

        with urlopen(request, timeout=10) as response:
            # Limit response size for index files
            max_index_size = 1024 * 1024  # 1MB limit for index
            content = response.read(max_index_size)

            if len(content) >= max_index_size:
                raise SecurityError("Template index too large (>1MB)")

            data = json.loads(content.decode("utf-8"))
            if not isinstance(data, dict):
                raise SecurityError("Template index must be a JSON object")
            return data

    def download_and_extract_template(
        self, template_url: str, template_name: str, extract_to: Optional[Path] = None
    ) -> Path:
        """Download and extract template to temporary or specified location.

        Args:
            template_url: URL of template zip file
            template_name: Name of template for file naming
            extract_to: Optional directory to extract to (uses temp dir if None)

        Returns:
            Path to extracted template root directory

        Raises:
            SecurityError: If download or extraction fails security validation
        """
        # Use provided directory or create temporary directory
        if extract_to:
            temp_dir_obj = None
            temp_path = extract_to
            temp_path.mkdir(parents=True, exist_ok=True)
        else:
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_path = Path(temp_dir_obj.name)

        try:
            # Download template
            zip_path = temp_path / f"{template_name}.zip"
            self.download_file(template_url, zip_path)

            # Safe zip extraction with path traversal protection
            extract_path = temp_path / "extracted"
            security_validator.safe_extract_zip(zip_path, extract_path)

            # Find template root (may be in subdirectory)
            template_root = self._find_template_root(extract_path)
            if not template_root:
                raise SecurityError(
                    "Downloaded template does not contain template.json"
                )

            return template_root

        except Exception as e:
            # Clean up temporary directory on error
            if temp_dir_obj:
                temp_dir_obj.cleanup()
            raise SecurityError(f"Failed to download and extract template: {e}") from e

    def _find_template_root(self, extract_path: Path) -> Optional[Path]:
        """Find the root directory of an extracted template.

        Args:
            extract_path: Path where template was extracted

        Returns:
            Path to template root directory containing template.json, or None
        """
        # Look for template.json at root level first
        if (extract_path / "template.json").exists():
            return extract_path

        # Look in subdirectories (one level deep)
        for subdir in extract_path.iterdir():
            if subdir.is_dir() and (subdir / "template.json").exists():
                return subdir

        return None


class TemplateRepositoryClient:
    """Client for fetching template metadata from remote repositories."""

    def __init__(
        self,
        downloader: Optional[TemplateDownloader] = None,
        official_repository: str = "https://raw.githubusercontent.com/quinnoshea/claude-builder-templates/main/",
        community_sources: Optional[List[str]] = None,
    ):
        """Initialize repository client.

        Args:
            downloader: Template downloader instance (creates default if None)
            official_repository: URL of official template repository
            community_sources: List of community repository URLs
        """
        self.downloader = downloader or TemplateDownloader()
        self.official_repository = official_repository
        self.community_sources = community_sources or [
            "https://raw.githubusercontent.com/quinnoshea/claude-builder-community/main/"
        ]
        self.logger = logging.getLogger(__name__)

    def fetch_templates_from_source(self, source_url: str) -> List[Dict[str, Any]]:
        """Fetch template listings from a remote source.

        Args:
            source_url: Base URL of template repository

        Returns:
            List of template metadata dictionaries
        """
        templates: List[Dict[str, Any]] = []

        try:
            # Fetch template index with security validation
            index_data = self.downloader.fetch_template_index(source_url)

            # Parse template entries with security validation
            for template_data in index_data.get("templates", []):
                try:
                    # Validate and sanitize metadata
                    safe_metadata = security_validator.validate_template_metadata(
                        template_data
                    )

                    # Add source URL for download
                    template_name = safe_metadata.get("name", "unknown")
                    template_url = urljoin(source_url, f"templates/{template_name}.zip")
                    security_validator.validate_url(template_url)

                    safe_metadata["source_url"] = template_url
                    templates.append(safe_metadata)

                except SecurityError as e:
                    # Log security violations
                    self.logger.warning(f"Security violation in template metadata: {e}")
                    continue
                except (ValueError, KeyError) as e:
                    # Log validation errors
                    self.logger.warning(f"Invalid template metadata: {e}")
                    continue
                except Exception as e:
                    # Log unexpected errors with context
                    self.logger.error(
                        f"Unexpected error parsing template metadata: {e}",
                        exc_info=True,
                    )
                    continue

        except SecurityError as e:
            # Log security violations in template source
            self.logger.error(
                f"Security violation accessing template source {source_url}: {e}"
            )
        except (URLError, HTTPError) as e:
            # Log network errors properly
            self.logger.warning(
                f"Network error accessing template source {source_url}: {e}"
            )
        except json.JSONDecodeError as e:
            # Log malformed JSON
            self.logger.warning(f"Invalid JSON from template source {source_url}: {e}")
        except Exception as e:
            # Log unexpected errors with full context
            self.logger.error(
                f"Unexpected error fetching from {source_url}: {e}", exc_info=True
            )

        return templates

    def discover_all_templates(self) -> List[Dict[str, Any]]:
        """Discover templates from all configured sources.

        Returns:
            Combined list of template metadata from all sources
        """
        all_templates: List[Dict[str, Any]] = []

        # Try official repository first
        templates = self.fetch_templates_from_source(self.official_repository)
        all_templates.extend(templates)

        # Try community sources
        for source in self.community_sources:
            templates = self.fetch_templates_from_source(source)
            all_templates.extend(templates)

        return all_templates

    def find_template_metadata(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Find metadata for a specific template across all sources.

        Args:
            template_id: Template identifier (name or author/name format)

        Returns:
            Template metadata if found, None otherwise
        """
        all_templates = self.discover_all_templates()

        for template_data in all_templates:
            template_name = template_data.get("name", "")
            template_author = template_data.get("author", "")

            # Check both name and author/name format
            if template_id in (template_name, f"{template_author}/{template_name}"):
                return template_data

        return None
