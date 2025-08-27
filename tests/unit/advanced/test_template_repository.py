"""Unit tests for template repository module.

Tests comprehensive community template management functionality including:
- TemplateMetadata class functionality
- CommunityTemplate class and project matching
- CommunityTemplateManager template lifecycle management
- Template installation/uninstallation workflows
- Custom template creation
- Template discovery and search capabilities
"""

import json

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_builder.core.models import ProjectAnalysis, ProjectType, ValidationResult
from claude_builder.core.template_management.community.template_repository import (
    CommunityTemplate,
    CommunityTemplateManager,
    TemplateMetadata,
)
from claude_builder.core.template_management.network.template_downloader import (
    TemplateDownloader,
    TemplateRepositoryClient,
)
from claude_builder.core.template_management.validation.template_validator import (
    ComprehensiveTemplateValidator,
)


class TestTemplateMetadata:
    """Test suite for TemplateMetadata class."""

    @pytest.fixture
    def sample_metadata_data(self):
        """Create sample metadata data for testing."""
        return {
            "name": "python-web-template",
            "version": "1.2.0",
            "description": "A comprehensive Python web application template",
            "author": "Claude Builder Team",
            "category": "web",
            "tags": ["python", "web", "fastapi", "modern"],
            "languages": ["python"],
            "frameworks": ["fastapi", "pydantic"],
            "project_types": ["web_api", "microservice"],
            "min_builder_version": "0.1.0",
            "homepage": "https://example.com/template",
            "repository": "https://github.com/user/template",
            "license": "MIT",
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-15T12:30:00Z",
        }

    def test_metadata_initialization_complete(self, sample_metadata_data):
        """Test TemplateMetadata initialization with complete data."""
        metadata = TemplateMetadata(sample_metadata_data)

        assert metadata.name == "python-web-template"
        assert metadata.version == "1.2.0"
        assert metadata.description == "A comprehensive Python web application template"
        assert metadata.author == "Claude Builder Team"
        assert metadata.category == "web"
        assert metadata.tags == ["python", "web", "fastapi", "modern"]
        assert metadata.languages == ["python"]
        assert metadata.frameworks == ["fastapi", "pydantic"]
        assert metadata.project_types == ["web_api", "microservice"]
        assert metadata.min_builder_version == "0.1.0"
        assert metadata.homepage == "https://example.com/template"
        assert metadata.repository == "https://github.com/user/template"
        assert metadata.license == "MIT"
        assert metadata.created == "2024-01-01T00:00:00Z"
        assert metadata.updated == "2024-01-15T12:30:00Z"

    def test_metadata_initialization_minimal(self):
        """Test TemplateMetadata initialization with minimal data."""
        minimal_data = {"name": "minimal-template"}
        metadata = TemplateMetadata(minimal_data)

        assert metadata.name == "minimal-template"
        assert metadata.version == "1.0.0"  # Default
        assert metadata.description == ""  # Default
        assert metadata.author == ""  # Default
        assert metadata.category == "general"  # Default
        assert metadata.tags == []  # Default
        assert metadata.languages == []  # Default
        assert metadata.frameworks == []  # Default
        assert metadata.project_types == []  # Default
        assert metadata.min_builder_version == "0.1.0"  # Default
        assert metadata.homepage is None  # Default
        assert metadata.repository is None  # Default
        assert metadata.license == "MIT"  # Default
        assert metadata.created is None  # Default
        assert metadata.updated is None  # Default

    def test_metadata_to_dict(self, sample_metadata_data):
        """Test TemplateMetadata to_dict conversion."""
        metadata = TemplateMetadata(sample_metadata_data)
        result_dict = metadata.to_dict()

        # Should contain all fields
        for key, value in sample_metadata_data.items():
            assert result_dict[key] == value

        # Should be a complete dictionary representation
        expected_keys = {
            "name",
            "version",
            "description",
            "author",
            "category",
            "tags",
            "languages",
            "frameworks",
            "project_types",
            "min_builder_version",
            "homepage",
            "repository",
            "license",
            "created",
            "updated",
        }
        assert set(result_dict.keys()) == expected_keys

    def test_metadata_is_compatible_current_version(self, sample_metadata_data):
        """Test TemplateMetadata compatibility checking with current version."""
        metadata = TemplateMetadata(sample_metadata_data)

        # Should be compatible with current version (0.1.0 >= 0.1.0)
        assert metadata.is_compatible is True

    def test_metadata_is_compatible_future_version(self):
        """Test TemplateMetadata compatibility with future required version."""
        future_data = {
            "name": "future-template",
            "min_builder_version": "2.0.0",  # Future version
        }
        metadata = TemplateMetadata(future_data)

        # Should not be compatible with future version requirement (2.0.0 > 0.1.0)
        assert metadata.is_compatible is False

    def test_metadata_is_compatible_exception_handling(self):
        """Test TemplateMetadata compatibility with invalid version format."""
        invalid_data = {
            "name": "invalid-version-template",
            "min_builder_version": "not-a-version",
        }
        metadata = TemplateMetadata(invalid_data)

        # Should handle exception gracefully and default to compatible
        assert metadata.is_compatible is True


class TestCommunityTemplate:
    """Test suite for CommunityTemplate class."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample TemplateMetadata for testing."""
        return TemplateMetadata(
            {
                "name": "python-fastapi-template",
                "version": "1.0.0",
                "description": "FastAPI template",
                "author": "community-author",
                "languages": ["python"],
                "frameworks": ["fastapi"],
                "project_types": ["web_api"],
            }
        )

    @pytest.fixture
    def sample_project_analysis(self):
        """Create sample ProjectAnalysis for testing."""
        from claude_builder.core.models import DomainInfo, FrameworkInfo, LanguageInfo

        return ProjectAnalysis(
            project_path=Path("/test/project"),
            language_info=LanguageInfo(primary="python"),
            framework_info=FrameworkInfo(primary="fastapi"),
            project_type=ProjectType.API_SERVICE,
            domain_info=DomainInfo(domain="web_api"),
        )

    def test_community_template_initialization(self, sample_metadata):
        """Test CommunityTemplate initialization."""
        template = CommunityTemplate(
            metadata=sample_metadata,
            source_url="https://example.com/template.zip",
            local_path=Path("/local/template"),
        )

        assert template.metadata == sample_metadata
        assert template.source_url == "https://example.com/template.zip"
        assert template.local_path == Path("/local/template")
        assert template.installed is True  # Has local_path

    def test_community_template_initialization_not_installed(self, sample_metadata):
        """Test CommunityTemplate initialization without local path."""
        template = CommunityTemplate(
            metadata=sample_metadata, source_url="https://example.com/template.zip"
        )

        assert template.metadata == sample_metadata
        assert template.source_url == "https://example.com/template.zip"
        assert template.local_path is None
        assert template.installed is False  # No local_path

    def test_community_template_id_property(self, sample_metadata):
        """Test CommunityTemplate id property."""
        template = CommunityTemplate(metadata=sample_metadata)

        assert template.id == "community-author/python-fastapi-template"

    def test_community_template_display_name_property(self, sample_metadata):
        """Test CommunityTemplate display_name property."""
        template = CommunityTemplate(metadata=sample_metadata)

        assert template.display_name == "python-fastapi-template v1.0.0"

    def test_matches_project_perfect_match(
        self, sample_metadata, sample_project_analysis
    ):
        """Test project matching with perfect compatibility."""
        template = CommunityTemplate(metadata=sample_metadata)

        matches, score = template.matches_project(sample_project_analysis)

        assert matches is True
        assert (
            score >= 70
        )  # Should be high score for good match (language + framework + type = 90 out of 100 max)

    def test_matches_project_language_mismatch(self, sample_project_analysis):
        """Test project matching with language mismatch."""
        rust_metadata = TemplateMetadata(
            {
                "name": "rust-template",
                "languages": ["rust"],  # Doesn't match Python project
                "frameworks": ["actix-web"],
                "project_types": ["web_api"],
            }
        )

        template = CommunityTemplate(metadata=rust_metadata)

        matches, score = template.matches_project(sample_project_analysis)

        assert matches is False  # Language mismatch should cause low score
        assert score < 50

    def test_matches_project_partial_match(self, sample_project_analysis):
        """Test project matching with partial compatibility."""
        partial_metadata = TemplateMetadata(
            {
                "name": "python-django-template",
                "languages": ["python"],  # Matches
                "frameworks": ["django"],  # Doesn't match FastAPI
                "project_types": ["web_app"],  # Doesn't match API_SERVICE exactly
            }
        )

        template = CommunityTemplate(metadata=partial_metadata)

        matches, score = template.matches_project(sample_project_analysis)

        # Should match due to language but have moderate score
        assert score > 0
        assert score < 90  # Not perfect due to framework/type mismatch

    def test_matches_project_no_metadata(self, sample_project_analysis):
        """Test project matching with minimal metadata."""
        minimal_metadata = TemplateMetadata(
            {
                "name": "generic-template"
                # No languages, frameworks, or project_types specified
            }
        )

        template = CommunityTemplate(metadata=minimal_metadata)

        matches, score = template.matches_project(sample_project_analysis)

        assert score == 0  # No matching criteria
        assert matches is False

    def test_matches_project_domain_match(self, sample_project_analysis):
        """Test project matching with domain/category matching."""
        domain_metadata = TemplateMetadata(
            {
                "name": "web-template",
                "category": "web",  # Should match domain "web_api"
                "languages": ["javascript"],  # Different language
            }
        )

        template = CommunityTemplate(metadata=domain_metadata)

        matches, score = template.matches_project(sample_project_analysis)

        # Should get some points for category/domain match
        assert score > 0
        assert score < 50  # But not enough to be considered a match


class TestCommunityTemplateManager:
    """Test suite for CommunityTemplateManager class."""

    @pytest.fixture
    def mock_downloader(self):
        """Create a mock TemplateDownloader."""
        return MagicMock(spec=TemplateDownloader)

    @pytest.fixture
    def mock_repository_client(self):
        """Create a mock TemplateRepositoryClient."""
        return MagicMock(spec=TemplateRepositoryClient)

    @pytest.fixture
    def mock_validator(self):
        """Create a mock ComprehensiveTemplateValidator."""
        return MagicMock(spec=ComprehensiveTemplateValidator)

    @pytest.fixture
    def manager(
        self, temp_dir, mock_downloader, mock_repository_client, mock_validator
    ):
        """Create a CommunityTemplateManager for testing."""
        return CommunityTemplateManager(
            templates_dir=temp_dir / "templates",
            downloader=mock_downloader,
            repository_client=mock_repository_client,
            validator=mock_validator,
        )

    def test_manager_initialization_with_defaults(self, temp_dir):
        """Test CommunityTemplateManager initialization with defaults."""
        manager = CommunityTemplateManager()

        assert manager.templates_dir == Path.home() / ".claude-builder" / "templates"
        assert manager.downloader is not None
        assert manager.repository_client is not None
        assert manager.validator is not None
        assert manager.logger is not None

    def test_manager_initialization_with_custom_params(
        self, temp_dir, mock_downloader, mock_repository_client, mock_validator
    ):
        """Test CommunityTemplateManager initialization with custom parameters."""
        custom_templates_dir = temp_dir / "custom_templates"

        manager = CommunityTemplateManager(
            templates_dir=custom_templates_dir,
            downloader=mock_downloader,
            repository_client=mock_repository_client,
            validator=mock_validator,
        )

        assert manager.templates_dir == custom_templates_dir
        assert manager.downloader == mock_downloader
        assert manager.repository_client == mock_repository_client
        assert manager.validator == mock_validator
        assert custom_templates_dir.exists()  # Should create directory

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_list_available_templates_all(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test listing all available templates (installed + community)."""
        # Setup mock returns
        installed_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "installed", "author": "user"}),
            local_path=Path("/local/installed"),
        )
        community_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "community", "author": "user"}),
            source_url="https://example.com/community.zip",
        )

        mock_list_installed.return_value = [installed_template]
        mock_discover.return_value = [community_template]

        templates = manager.list_available_templates()

        assert len(templates) == 2
        template_names = [t.metadata.name for t in templates]
        assert "installed" in template_names
        assert "community" in template_names

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_list_available_templates_installed_only(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test listing only installed templates."""
        installed_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "installed", "author": "user"}),
            local_path=Path("/local/installed"),
        )

        mock_list_installed.return_value = [installed_template]

        templates = manager.list_available_templates(
            include_installed=True, include_community=False
        )

        assert len(templates) == 1
        assert templates[0].metadata.name == "installed"
        mock_discover.assert_not_called()

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_list_available_templates_community_only(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test listing only community templates."""
        community_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "community", "author": "user"}),
            source_url="https://example.com/community.zip",
        )

        mock_discover.return_value = [community_template]

        templates = manager.list_available_templates(
            include_installed=False, include_community=True
        )

        assert len(templates) == 1
        assert templates[0].metadata.name == "community"
        mock_list_installed.assert_not_called()

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_list_available_templates_duplicate_preference(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test that installed templates are preferred over community duplicates."""
        # Same template available both locally and remotely
        installed_template = CommunityTemplate(
            metadata=TemplateMetadata(
                {"name": "duplicate", "author": "user", "version": "1.1.0"}
            ),
            local_path=Path("/local/duplicate"),
        )
        community_template = CommunityTemplate(
            metadata=TemplateMetadata(
                {"name": "duplicate", "author": "user", "version": "1.0.0"}
            ),
            source_url="https://example.com/duplicate.zip",
        )

        mock_list_installed.return_value = [installed_template]
        mock_discover.return_value = [community_template]

        templates = manager.list_available_templates()

        assert len(templates) == 1  # Deduplicated
        assert templates[0].installed is True  # Installed version preferred
        assert templates[0].metadata.version == "1.1.0"  # Local version

    @patch.object(CommunityTemplateManager, "list_available_templates")
    def test_search_templates_by_query(self, mock_list_available, manager):
        """Test searching templates by query string."""
        # Setup mock templates
        python_web_template = CommunityTemplate(
            metadata=TemplateMetadata(
                {
                    "name": "python-web",
                    "description": "Python web application template",
                    "tags": ["python", "web", "fastapi"],
                    "languages": ["python"],
                    "frameworks": ["fastapi"],
                }
            )
        )

        rust_cli_template = CommunityTemplate(
            metadata=TemplateMetadata(
                {
                    "name": "rust-cli",
                    "description": "Rust command-line tool template",
                    "tags": ["rust", "cli", "command-line"],
                    "languages": ["rust"],
                    "frameworks": ["clap"],
                }
            )
        )

        python_cli_template = CommunityTemplate(
            metadata=TemplateMetadata(
                {
                    "name": "python-cli",
                    "description": "Python CLI application template",
                    "tags": ["python", "cli"],
                    "languages": ["python"],
                    "frameworks": ["click"],
                }
            )
        )

        mock_list_available.return_value = [
            python_web_template,
            rust_cli_template,
            python_cli_template,
        ]

        # Search for "python" should return python templates
        python_results = manager.search_templates("python")
        python_names = [t.metadata.name for t in python_results]
        assert "python-web" in python_names
        assert "python-cli" in python_names
        assert "rust-cli" not in python_names

        # Search for "cli" should return CLI templates
        cli_results = manager.search_templates("cli")
        cli_names = [t.metadata.name for t in cli_results]
        assert "rust-cli" in cli_names
        assert "python-cli" in cli_names
        assert "python-web" not in cli_names

    @patch.object(CommunityTemplateManager, "list_available_templates")
    def test_search_templates_with_project_analysis(
        self, mock_list_available, manager, sample_analysis
    ):
        """Test searching templates with project analysis for ranking."""
        # Create templates with different compatibility scores
        perfect_match = CommunityTemplate(
            metadata=TemplateMetadata(
                {
                    "name": "perfect-match",
                    "description": "Perfect matching template",
                    "languages": ["python"],
                    "frameworks": ["fastapi"],
                    "project_types": ["web_api"],
                }
            )
        )

        partial_match = CommunityTemplate(
            metadata=TemplateMetadata(
                {
                    "name": "partial-match",
                    "description": "Partial matching template",
                    "languages": ["python"],  # Matches language only
                    "frameworks": ["django"],
                    "project_types": ["web_app"],
                }
            )
        )

        mock_list_available.return_value = [
            partial_match,
            perfect_match,
        ]  # Intentionally out of order

        # Search for "template" with project analysis
        results = manager.search_templates("template", project_analysis=sample_analysis)

        assert len(results) == 2
        # Should be sorted by compatibility score (perfect match first)
        assert results[0].metadata.name == "perfect-match"
        assert results[1].metadata.name == "partial-match"

    def test_install_template_success(
        self, manager, mock_repository_client, mock_downloader, mock_validator
    ):
        """Test successful template installation."""
        # Setup mock repository response
        template_metadata = {
            "name": "test-template",
            "version": "1.0.0",
            "author": "test-author",
            "source_url": "https://example.com/test-template.zip",
        }
        mock_repository_client.find_template_metadata.return_value = template_metadata

        # Setup mock download and validation
        mock_downloader.download_and_extract_template.return_value = Path(
            "/tmp/extracted"
        )
        mock_validator.validate_template.return_value = ValidationResult(is_valid=True)

        # Mock copytree for installation
        with patch(
            "claude_builder.core.template_management.community.template_repository.shutil.copytree"
        ) as mock_copytree:
            result = manager.install_template("test-template")

        assert result.is_valid is True
        assert len(result.errors) == 0
        mock_repository_client.find_template_metadata.assert_called_once_with(
            "test-template"
        )
        mock_downloader.download_and_extract_template.assert_called_once()
        mock_validator.validate_template.assert_called_once()
        mock_copytree.assert_called_once()

    def test_install_template_not_found(self, manager, mock_repository_client):
        """Test template installation when template is not found."""
        mock_repository_client.find_template_metadata.return_value = None

        result = manager.install_template("non-existent-template")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Template not found" in result.errors[0]

    def test_install_template_already_installed(
        self, manager, mock_repository_client, temp_dir
    ):
        """Test template installation when template is already installed."""
        template_metadata = {
            "name": "existing-template",
            "version": "1.0.0",
            "author": "test-author",
        }
        mock_repository_client.find_template_metadata.return_value = template_metadata

        # Create existing installation directory
        install_path = manager.templates_dir / "community" / "existing-template"
        install_path.mkdir(parents=True)

        result = manager.install_template("existing-template")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "already installed" in result.errors[0]

    def test_install_template_force_reinstall(
        self, manager, mock_repository_client, mock_downloader, mock_validator, temp_dir
    ):
        """Test template force reinstall when already installed."""
        template_metadata = {
            "name": "existing-template",
            "version": "1.0.0",
            "author": "test-author",
            "source_url": "https://example.com/template.zip",
        }
        mock_repository_client.find_template_metadata.return_value = template_metadata

        # Create existing installation directory
        install_path = manager.templates_dir / "community" / "existing-template"
        install_path.mkdir(parents=True)

        # Setup mocks for successful installation
        mock_downloader.download_and_extract_template.return_value = Path(
            "/tmp/extracted"
        )
        mock_validator.validate_template.return_value = ValidationResult(is_valid=True)

        with patch(
            "claude_builder.core.template_management.community.template_repository.shutil.copytree"
        ) as mock_copytree:
            with patch(
                "claude_builder.core.template_management.community.template_repository.shutil.rmtree"
            ) as mock_rmtree:
                result = manager.install_template("existing-template", force=True)

        assert result.is_valid is True
        mock_rmtree.assert_called_once()  # Old version removed
        mock_copytree.assert_called_once()  # New version installed

    def test_install_template_validation_failure(
        self, manager, mock_repository_client, mock_downloader, mock_validator
    ):
        """Test template installation with validation failure."""
        template_metadata = {
            "name": "invalid-template",
            "version": "1.0.0",
            "author": "test-author",
            "source_url": "https://example.com/template.zip",
        }
        mock_repository_client.find_template_metadata.return_value = template_metadata

        # Setup mock download success but validation failure
        mock_downloader.download_and_extract_template.return_value = Path(
            "/tmp/extracted"
        )
        mock_validator.validate_template.return_value = ValidationResult(
            is_valid=False, errors=["Template validation failed"]
        )

        result = manager.install_template("invalid-template")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Template validation failed" in result.errors[0]

    def test_uninstall_template_success(self, manager, temp_dir):
        """Test successful template uninstallation."""
        # Create template directory to uninstall
        template_path = manager.templates_dir / "community" / "test-template"
        template_path.mkdir(parents=True)
        (template_path / "template.json").write_text('{"name": "test-template"}')

        result = manager.uninstall_template("test-template")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.suggestions) == 1
        assert "Template uninstalled" in result.suggestions[0]
        assert not template_path.exists()  # Directory should be removed

    def test_uninstall_template_not_installed(self, manager):
        """Test template uninstallation when template is not installed."""
        result = manager.uninstall_template("non-existent-template")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Template not installed" in result.errors[0]

    def test_uninstall_template_removal_error(self, manager, temp_dir):
        """Test template uninstallation with file removal error."""
        # Create template directory
        template_path = manager.templates_dir / "community" / "problematic-template"
        template_path.mkdir(parents=True)
        (template_path / "template.json").write_text('{"name": "problematic-template"}')

        # Mock rmtree to raise an exception
        with patch(
            "claude_builder.core.template_management.community.template_repository.shutil.rmtree"
        ) as mock_rmtree:
            mock_rmtree.side_effect = OSError("Permission denied")

            result = manager.uninstall_template("problematic-template")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Failed to uninstall" in result.errors[0]

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_get_template_info_installed(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test getting info for installed template."""
        installed_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "installed-template", "author": "user"}),
            local_path=Path("/local/template"),
        )

        mock_list_installed.return_value = [installed_template]

        result = manager.get_template_info("installed-template")

        assert result is not None
        assert result.metadata.name == "installed-template"
        assert result.installed is True
        mock_discover.assert_not_called()  # Should find in installed first

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_get_template_info_community(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test getting info for community template."""
        community_template = CommunityTemplate(
            metadata=TemplateMetadata({"name": "community-template", "author": "user"}),
            source_url="https://example.com/template.zip",
        )

        mock_list_installed.return_value = []  # Not installed
        mock_discover.return_value = [community_template]

        result = manager.get_template_info("community-template")

        assert result is not None
        assert result.metadata.name == "community-template"
        assert result.installed is False

    @patch.object(CommunityTemplateManager, "_list_installed_templates")
    @patch.object(CommunityTemplateManager, "_discover_community_templates")
    def test_get_template_info_not_found(
        self, mock_discover, mock_list_installed, manager
    ):
        """Test getting info for non-existent template."""
        mock_list_installed.return_value = []
        mock_discover.return_value = []

        result = manager.get_template_info("non-existent-template")

        assert result is None

    def test_create_custom_template_success(self, manager, temp_dir, mock_validator):
        """Test successful custom template creation."""
        # Create source project
        project_path = temp_dir / "source_project"
        project_path.mkdir()
        (project_path / "main.py").write_text("print('Hello, World!')")
        (project_path / "requirements.txt").write_text("requests>=2.25.0")

        # Setup mock validation
        mock_validator.validate_template.return_value = ValidationResult(
            is_valid=True, suggestions=["Custom template created successfully"]
        )

        template_config = {
            "description": "Custom Python project template",
            "author": "Test User",
            "category": "custom",
            "languages": ["python"],
            "frameworks": ["requests"],
        }

        result = manager.create_custom_template(
            "my-custom-template", project_path, template_config
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

        # Check template was created
        template_path = manager.templates_dir / "custom" / "my-custom-template"
        assert template_path.exists()

        # Check metadata file
        metadata_file = template_path / "template.json"
        assert metadata_file.exists()
        with metadata_file.open() as f:
            metadata = json.load(f)
        assert metadata["name"] == "my-custom-template"
        assert metadata["description"] == "Custom Python project template"
        assert metadata["author"] == "Test User"

        # Check template files
        assert (template_path / "claude_instructions.md").exists()
        assert (template_path / "README.md").exists()

    def test_create_custom_template_nonexistent_project(self, manager, temp_dir):
        """Test custom template creation with non-existent project."""
        nonexistent_path = temp_dir / "does_not_exist"

        result = manager.create_custom_template("test-template", nonexistent_path, {})

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Project path does not exist" in result.errors[0]

    def test_create_custom_template_validation_failure(
        self, manager, temp_dir, mock_validator
    ):
        """Test custom template creation with validation failure."""
        # Create source project
        project_path = temp_dir / "source_project"
        project_path.mkdir()

        # Setup mock validation failure
        mock_validator.validate_template.return_value = ValidationResult(
            is_valid=False, errors=["Template validation failed"]
        )

        result = manager.create_custom_template("invalid-template", project_path, {})

        assert result.is_valid is False
        assert "Template validation failed" in result.errors[0]

    def test_create_custom_template_exception_handling(self, manager, temp_dir):
        """Test custom template creation with exception during creation."""
        # Create source project
        project_path = temp_dir / "source_project"
        project_path.mkdir()

        # Mock datetime to raise an exception
        with patch(
            "claude_builder.core.template_management.community.template_repository.datetime"
        ) as mock_datetime:
            mock_datetime.now.side_effect = Exception("Simulated error")

            result = manager.create_custom_template("error-template", project_path, {})

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Failed to create custom template" in result.errors[0]

    def test_list_installed_templates(self, manager, temp_dir):
        """Test listing installed templates from both community and custom directories."""
        # Create community template
        community_dir = manager.templates_dir / "community" / "community-template"
        community_dir.mkdir(parents=True)
        community_metadata = {
            "name": "community-template",
            "version": "1.0.0",
            "author": "community",
        }
        with (community_dir / "template.json").open("w") as f:
            json.dump(community_metadata, f)

        # Create custom template
        custom_dir = manager.templates_dir / "custom" / "custom-template"
        custom_dir.mkdir(parents=True)
        custom_metadata = {
            "name": "custom-template",
            "version": "1.0.0",
            "author": "user",
        }
        with (custom_dir / "template.json").open("w") as f:
            json.dump(custom_metadata, f)

        templates = manager._list_installed_templates()

        assert len(templates) == 2
        template_names = [t.metadata.name for t in templates]
        assert "community-template" in template_names
        assert "custom-template" in template_names

        # All should be marked as installed
        for template in templates:
            assert template.installed is True
            assert template.local_path is not None

    def test_list_installed_templates_invalid_metadata(self, manager, temp_dir):
        """Test listing installed templates with invalid metadata files."""
        # Create template with invalid JSON
        invalid_dir = manager.templates_dir / "community" / "invalid-template"
        invalid_dir.mkdir(parents=True)
        (invalid_dir / "template.json").write_text("{ invalid json }")

        # Create template without metadata file
        no_metadata_dir = manager.templates_dir / "community" / "no-metadata-template"
        no_metadata_dir.mkdir(parents=True)

        # Create valid template for comparison
        valid_dir = manager.templates_dir / "community" / "valid-template"
        valid_dir.mkdir(parents=True)
        with (valid_dir / "template.json").open("w") as f:
            json.dump({"name": "valid-template", "version": "1.0.0"}, f)

        templates = manager._list_installed_templates()

        # Should only return valid template, invalid ones should be skipped
        assert len(templates) == 1
        assert templates[0].metadata.name == "valid-template"

    def test_discover_community_templates(self, manager, mock_repository_client):
        """Test discovering community templates from remote sources."""
        # Setup mock repository response
        mock_templates_data = [
            {
                "name": "remote-template-1",
                "version": "1.0.0",
                "author": "remote-author",
                "source_url": "https://example.com/template1.zip",
            },
            {
                "name": "remote-template-2",
                "version": "2.0.0",
                "author": "remote-author",
                "source_url": "https://example.com/template2.zip",
            },
        ]

        mock_repository_client.discover_all_templates.return_value = mock_templates_data

        templates = manager._discover_community_templates()

        assert len(templates) == 2
        assert all(not t.installed for t in templates)  # Not installed
        assert all(t.source_url is not None for t in templates)  # Has source URL

        template_names = [t.metadata.name for t in templates]
        assert "remote-template-1" in template_names
        assert "remote-template-2" in template_names

    def test_discover_community_templates_exception(
        self, manager, mock_repository_client
    ):
        """Test discovering community templates with repository error."""
        # Setup mock to raise exception
        mock_repository_client.discover_all_templates.side_effect = Exception(
            "Repository error"
        )

        templates = manager._discover_community_templates()

        # Should handle exception gracefully and return empty list
        assert templates == []

    def test_discover_community_templates_invalid_data(
        self, manager, mock_repository_client
    ):
        """Test discovering community templates with invalid template data."""
        # Setup mock with some valid and some invalid data
        mock_templates_data = [
            {"name": "valid-template", "version": "1.0.0", "author": "author"},
            {
                "invalid": "template"  # Missing required fields, but TemplateMetadata uses defaults
            },
        ]

        mock_repository_client.discover_all_templates.return_value = mock_templates_data

        templates = manager._discover_community_templates()

        # Current implementation creates templates with defaults for missing fields
        assert len(templates) == 2
        assert templates[0].metadata.name == "valid-template"
        assert templates[1].metadata.name == ""  # Empty default name
