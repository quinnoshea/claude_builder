"""Unit tests for template downloader module.

Tests comprehensive template downloading functionality including:
- TemplateDownloader network operations and security
- TemplateRepositoryClient repository access
- Security validation and error handling
- Mock network requests for reliable testing
"""

import json

from unittest.mock import MagicMock, Mock, patch
from urllib.error import URLError

import pytest

from claude_builder.core.template_management.network.template_downloader import (
    TemplateDownloader,
    TemplateRepositoryClient,
)
from claude_builder.utils.exceptions import SecurityError


class TestTemplateDownloader:
    """Test suite for TemplateDownloader class."""

    @pytest.fixture
    def downloader(self):
        """Create a TemplateDownloader instance for testing."""
        return TemplateDownloader(timeout=10, max_download_size=1024 * 1024)  # 1MB

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        mock_resp = Mock()
        content = b"test content"
        mock_resp.read.side_effect = [content, b""]  # Return content once, then empty
        mock_resp.headers = {"Content-Length": str(len(content))}
        return mock_resp

    def test_downloader_initialization(self):
        """Test TemplateDownloader initialization with custom parameters."""
        downloader = TemplateDownloader(timeout=60, max_download_size=10 * 1024 * 1024)

        assert downloader.timeout == 60
        assert downloader.max_download_size == 10 * 1024 * 1024
        assert downloader.logger is not None

    def test_downloader_default_initialization(self):
        """Test TemplateDownloader initialization with default parameters."""
        downloader = TemplateDownloader()

        assert downloader.timeout == 30
        assert downloader.max_download_size == 50 * 1024 * 1024

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_file_success(
        self, mock_validator, mock_urlopen, downloader, temp_dir, mock_response
    ):
        """Test successful file download with security validation."""
        # Setup mocks
        mock_validator.validate_url.return_value = None
        mock_validator.validate_file_path.return_value = None
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test download
        destination = temp_dir / "test_file.zip"
        downloader.download_file("https://example.com/file.zip", destination)

        # Verify security validation was called
        mock_validator.validate_url.assert_called_once_with(
            "https://example.com/file.zip"
        )
        mock_validator.validate_file_path.assert_called_once_with("test_file.zip")

        # Verify file was written
        assert destination.exists()
        assert destination.read_bytes() == b"test content"

    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_file_url_validation_failure(
        self, mock_validator, downloader, temp_dir
    ):
        """Test download failure due to URL validation."""
        # Setup mock to raise SecurityError
        mock_validator.validate_url.side_effect = SecurityError("Invalid URL")

        destination = temp_dir / "test_file.zip"

        with pytest.raises(SecurityError, match="Invalid URL"):
            downloader.download_file("https://malicious.com/file.zip", destination)

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_file_size_limit_exceeded_header(
        self, mock_validator, mock_urlopen, downloader, temp_dir
    ):
        """Test download failure when content-length exceeds size limit."""
        # Setup mocks
        mock_validator.validate_url.return_value = None
        mock_validator.validate_file_path.return_value = None

        large_response = Mock()
        large_response.headers = {
            "Content-Length": str(2 * 1024 * 1024)
        }  # 2MB > 1MB limit
        mock_urlopen.return_value.__enter__.return_value = large_response

        destination = temp_dir / "test_file.zip"

        with pytest.raises(SecurityError, match="File too large"):
            downloader.download_file("https://example.com/large_file.zip", destination)

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_file_size_limit_exceeded_during_download(
        self, mock_validator, mock_urlopen, downloader, temp_dir
    ):
        """Test download failure when actual download exceeds size limit."""
        # Setup mocks
        mock_validator.validate_url.return_value = None
        mock_validator.validate_file_path.return_value = None

        # Create a response that claims small size but returns large content
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB content
        mock_response = Mock()
        mock_response.headers = {}  # No Content-Length header
        mock_response.read.side_effect = [
            large_content[:8192],
            large_content[8192:],
        ]  # Chunked
        mock_urlopen.return_value.__enter__.return_value = mock_response

        destination = temp_dir / "test_file.zip"

        with pytest.raises(SecurityError, match="Download exceeded size limit"):
            downloader.download_file("https://example.com/file.zip", destination)

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_file_network_error(
        self, mock_validator, mock_urlopen, downloader, temp_dir
    ):
        """Test download failure due to network error."""
        # Setup mocks
        mock_validator.validate_url.return_value = None
        mock_validator.validate_file_path.return_value = None
        mock_urlopen.side_effect = URLError("Network error")

        destination = temp_dir / "test_file.zip"

        with pytest.raises(SecurityError, match="Download failed"):
            downloader.download_file("https://example.com/file.zip", destination)

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_template_index_success(
        self, mock_validator, mock_urlopen, downloader
    ):
        """Test successful template index fetching."""
        # Setup mocks
        mock_validator.validate_url.return_value = None

        index_data = {"templates": [{"name": "test", "version": "1.0.0"}]}
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(index_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test fetch
        result = downloader.fetch_template_index("https://example.com/templates/")

        assert result == index_data
        mock_validator.validate_url.assert_called_once_with(
            "https://example.com/templates/index.json"
        )

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_template_index_invalid_json(
        self, mock_validator, mock_urlopen, downloader
    ):
        """Test template index fetch with invalid JSON."""
        # Setup mocks
        mock_validator.validate_url.return_value = None

        mock_response = Mock()
        mock_response.read.return_value = b"invalid json content"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            downloader.fetch_template_index("https://example.com/templates/")

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_template_index_not_dict(
        self, mock_validator, mock_urlopen, downloader
    ):
        """Test template index fetch with non-dictionary response."""
        # Setup mocks
        mock_validator.validate_url.return_value = None

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(["not", "a", "dict"]).encode(
            "utf-8"
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(SecurityError, match="Template index must be a JSON object"):
            downloader.fetch_template_index("https://example.com/templates/")

    @patch(
        "claude_builder.core.template_management.network.template_downloader.urlopen"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_template_index_too_large(
        self, mock_validator, mock_urlopen, downloader
    ):
        """Test template index fetch with oversized response."""
        # Setup mocks
        mock_validator.validate_url.return_value = None

        # Create a response larger than 1MB limit
        large_response = b"x" * (1024 * 1024 + 1)
        mock_response = Mock()
        mock_response.read.return_value = large_response
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(SecurityError, match="Template index too large"):
            downloader.fetch_template_index("https://example.com/templates/")

    @patch.object(TemplateDownloader, "download_file")
    @patch.object(TemplateDownloader, "_find_template_root")
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    @patch(
        "claude_builder.core.template_management.network.template_downloader.tempfile.TemporaryDirectory"
    )
    def test_download_and_extract_template_success(
        self,
        mock_temp_dir,
        mock_validator,
        mock_find_root,
        mock_download,
        downloader,
        temp_dir,
    ):
        """Test successful template download and extraction."""
        # Setup mocks
        mock_temp_dir_obj = Mock()
        mock_temp_dir_obj.name = str(temp_dir)
        mock_temp_dir.return_value = mock_temp_dir_obj

        extracted_path = temp_dir / "extracted" / "template"
        extracted_path.mkdir(parents=True)
        (extracted_path / "template.json").write_text('{"name": "test"}')

        mock_find_root.return_value = extracted_path
        mock_validator.safe_extract_zip.return_value = None

        # Test download and extraction
        result = downloader.download_and_extract_template(
            "https://example.com/template.zip", "test-template"
        )

        assert result == extracted_path
        mock_download.assert_called_once()
        mock_validator.safe_extract_zip.assert_called_once()
        mock_find_root.assert_called_once()

    @patch.object(TemplateDownloader, "download_file")
    @patch.object(TemplateDownloader, "_find_template_root")
    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_download_and_extract_template_no_template_json(
        self, mock_validator, mock_find_root, mock_download, downloader, temp_dir
    ):
        """Test template download failure when template.json not found."""
        # Setup mocks
        mock_find_root.return_value = None  # No template.json found
        mock_validator.safe_extract_zip.return_value = None

        with pytest.raises(
            SecurityError, match="Downloaded template does not contain template.json"
        ):
            downloader.download_and_extract_template(
                "https://example.com/template.zip", "test-template", temp_dir
            )

    def test_find_template_root_at_root_level(self, downloader, temp_dir):
        """Test finding template root when template.json is at root level."""
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()
        (extract_path / "template.json").write_text('{"name": "test"}')

        result = downloader._find_template_root(extract_path)

        assert result == extract_path

    def test_find_template_root_in_subdirectory(self, downloader, temp_dir):
        """Test finding template root when template.json is in subdirectory."""
        extract_path = temp_dir / "extracted"
        template_subdir = extract_path / "template-main"
        template_subdir.mkdir(parents=True)
        (template_subdir / "template.json").write_text('{"name": "test"}')

        result = downloader._find_template_root(extract_path)

        assert result == template_subdir

    def test_find_template_root_not_found(self, downloader, temp_dir):
        """Test finding template root when template.json doesn't exist."""
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        result = downloader._find_template_root(extract_path)

        assert result is None


class TestTemplateRepositoryClient:
    """Test suite for TemplateRepositoryClient class."""

    @pytest.fixture
    def mock_downloader(self):
        """Create a mock TemplateDownloader."""
        return MagicMock(spec=TemplateDownloader)

    @pytest.fixture
    def repository_client(self, mock_downloader):
        """Create a TemplateRepositoryClient for testing."""
        return TemplateRepositoryClient(
            downloader=mock_downloader,
            official_repository="https://official.repo.com",
            community_sources=[
                "https://community1.repo.com",
                "https://community2.repo.com",
            ],
        )

    def test_repository_client_initialization_with_defaults(self):
        """Test TemplateRepositoryClient initialization with default parameters."""
        client = TemplateRepositoryClient()

        assert client.downloader is not None
        assert (
            client.official_repository
            == "https://raw.githubusercontent.com/claude-builder/templates/main"
        )
        assert (
            "https://raw.githubusercontent.com/claude-builder/community-templates/main"
            in client.community_sources
        )

    def test_repository_client_initialization_with_custom_params(self, mock_downloader):
        """Test TemplateRepositoryClient initialization with custom parameters."""
        client = TemplateRepositoryClient(
            downloader=mock_downloader,
            official_repository="https://custom.official.repo",
            community_sources=["https://custom.community.repo"],
        )

        assert client.downloader == mock_downloader
        assert client.official_repository == "https://custom.official.repo"
        assert client.community_sources == ["https://custom.community.repo"]

    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_templates_from_source_success(
        self, mock_validator, repository_client, mock_downloader
    ):
        """Test successful template fetching from source."""
        # Setup mock responses
        index_data = {
            "templates": [
                {
                    "name": "python-web",
                    "version": "1.0.0",
                    "description": "Python web template",
                    "author": "test",
                },
                {
                    "name": "rust-cli",
                    "version": "2.0.0",
                    "description": "Rust CLI template",
                    "author": "test",
                },
            ]
        }

        mock_downloader.fetch_template_index.return_value = index_data
        mock_validator.validate_template_metadata.side_effect = (
            lambda x: x
        )  # Return input as-is
        mock_validator.validate_url.return_value = None

        # Test fetching templates
        templates = repository_client.fetch_templates_from_source(
            "https://test.repo.com"
        )

        assert len(templates) == 2
        assert templates[0]["name"] == "python-web"
        assert templates[1]["name"] == "rust-cli"

        # Verify source URLs were added
        assert (
            templates[0]["source_url"]
            == "https://test.repo.com/templates/python-web.zip"
        )
        assert (
            templates[1]["source_url"] == "https://test.repo.com/templates/rust-cli.zip"
        )

    def test_fetch_templates_from_source_security_error(
        self, repository_client, mock_downloader
    ):
        """Test template fetching with security error in metadata."""
        # Setup mock to raise SecurityError during index fetch
        mock_downloader.fetch_template_index.side_effect = SecurityError(
            "Invalid repository"
        )

        # Should handle error gracefully and return empty list
        templates = repository_client.fetch_templates_from_source(
            "https://malicious.repo.com"
        )

        assert templates == []

    def test_fetch_templates_from_source_network_error(
        self, repository_client, mock_downloader
    ):
        """Test template fetching with network error."""
        # Setup mock to raise URLError
        mock_downloader.fetch_template_index.side_effect = URLError("Connection failed")

        # Should handle error gracefully and return empty list
        templates = repository_client.fetch_templates_from_source(
            "https://unreachable.repo.com"
        )

        assert templates == []

    def test_fetch_templates_from_source_json_decode_error(
        self, repository_client, mock_downloader
    ):
        """Test template fetching with JSON decode error."""
        # Setup mock to raise JSONDecodeError
        mock_downloader.fetch_template_index.side_effect = json.JSONDecodeError(
            "Invalid JSON", "", 0
        )

        # Should handle error gracefully and return empty list
        templates = repository_client.fetch_templates_from_source(
            "https://invalid.json.repo.com"
        )

        assert templates == []

    @patch(
        "claude_builder.core.template_management.network.template_downloader.security_validator"
    )
    def test_fetch_templates_from_source_partial_failure(
        self, mock_validator, repository_client, mock_downloader
    ):
        """Test template fetching with some templates failing validation."""
        # Setup mock responses with one valid and one invalid template
        index_data = {
            "templates": [
                {"name": "valid-template", "version": "1.0.0"},
                {"name": "invalid-template", "version": "1.0.0"},
            ]
        }

        mock_downloader.fetch_template_index.return_value = index_data

        # First template validates, second raises SecurityError
        mock_validator.validate_template_metadata.side_effect = [
            {"name": "valid-template", "version": "1.0.0"},  # Valid
            SecurityError("Invalid template metadata"),  # Invalid
        ]
        mock_validator.validate_url.return_value = None

        # Test fetching templates
        templates = repository_client.fetch_templates_from_source(
            "https://test.repo.com"
        )

        # Should only return valid template
        assert len(templates) == 1
        assert templates[0]["name"] == "valid-template"

    def test_discover_all_templates(self, repository_client):
        """Test discovering templates from all configured sources."""

        # Mock fetch_templates_from_source to return different results for different sources
        def mock_fetch(source_url):
            if "official" in source_url:
                return [{"name": "official-template", "source": "official"}]
            elif "community1" in source_url:
                return [{"name": "community1-template", "source": "community1"}]
            elif "community2" in source_url:
                return [{"name": "community2-template", "source": "community2"}]
            return []

        repository_client.fetch_templates_from_source = mock_fetch

        # Test discovery
        all_templates = repository_client.discover_all_templates()

        assert len(all_templates) == 3
        template_names = [t["name"] for t in all_templates]
        assert "official-template" in template_names
        assert "community1-template" in template_names
        assert "community2-template" in template_names

    def test_find_template_metadata_found_by_name(self, repository_client):
        """Test finding template metadata by name."""
        # Mock discover_all_templates
        mock_templates = [
            {"name": "python-web", "author": "official"},
            {"name": "rust-cli", "author": "community"},
        ]
        repository_client.discover_all_templates = MagicMock(
            return_value=mock_templates
        )

        # Test finding by name
        result = repository_client.find_template_metadata("python-web")

        assert result is not None
        assert result["name"] == "python-web"
        assert result["author"] == "official"

    def test_find_template_metadata_found_by_author_name(self, repository_client):
        """Test finding template metadata by author/name format."""
        # Mock discover_all_templates
        mock_templates = [
            {"name": "python-web", "author": "official"},
            {"name": "rust-cli", "author": "community"},
        ]
        repository_client.discover_all_templates = MagicMock(
            return_value=mock_templates
        )

        # Test finding by author/name format
        result = repository_client.find_template_metadata("community/rust-cli")

        assert result is not None
        assert result["name"] == "rust-cli"
        assert result["author"] == "community"

    def test_find_template_metadata_not_found(self, repository_client):
        """Test finding template metadata when template doesn't exist."""
        # Mock discover_all_templates to return empty list
        repository_client.discover_all_templates = MagicMock(return_value=[])

        # Test finding non-existent template
        result = repository_client.find_template_metadata("non-existent-template")

        assert result is None
