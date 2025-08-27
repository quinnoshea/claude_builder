"""
Unit tests for advanced template management components.

Tests the sophisticated template system including:
- Template ecosystem management
- Template versioning and updates
- Template marketplace integration
- Custom template creation and sharing
- Template performance optimization
"""

from unittest.mock import ANY, MagicMock, patch

import pytest

from claude_builder.core.template_manager import (
    TemplateBuilder,
    TemplateEcosystem,
    TemplateManager,
    TemplateMarketplace,
    TemplateRepository,
    TemplateVersion,
)


class TestTemplateVersion:
    """Test suite for TemplateVersion model."""

    def test_version_creation(self):
        """Test template version creation and properties."""
        version = TemplateVersion(
            version="1.2.0",
            template_name="python-fastapi",
            changelog="Added async support",
            compatibility=["python>=3.8"],
            author="Claude Builder Team",
        )

        assert version.version == "1.2.0"
        assert version.template_name == "python-fastapi"
        assert version.changelog == "Added async support"
        assert "python>=3.8" in version.compatibility
        assert version.author == "Claude Builder Team"

    def test_version_comparison(self):
        """Test version comparison and ordering."""
        v1 = TemplateVersion(version="1.0.0", template_name="test")
        v2 = TemplateVersion(version="1.1.0", template_name="test")
        v3 = TemplateVersion(version="2.0.0", template_name="test")

        assert v1 < v2
        assert v2 < v3
        assert v3 > v1
        assert v2.is_compatible_with(v1)
        assert not v3.is_breaking_change_from(v2)

    def test_semantic_versioning(self):
        """Test semantic versioning compliance."""
        version = TemplateVersion(version="1.2.3-alpha.1", template_name="test")

        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "alpha.1"
        assert version.is_prerelease() is True

    def test_compatibility_checking(self):
        """Test version compatibility checking."""
        version = TemplateVersion(
            version="2.0.0",
            template_name="test",
            compatibility=["python>=3.8", "claude-builder>=1.0.0"],
        )

        assert version.is_compatible_with_environment(
            {"python": "3.9.0", "claude-builder": "1.1.0"}
        )
        assert not version.is_compatible_with_environment({"python": "3.7.0"})


class TestTemplateRepository:
    """Test suite for TemplateRepository class."""

    def test_repository_initialization(self, temp_dir):
        """Test template repository initialization."""
        repo = TemplateRepository(repository_path=temp_dir)

        assert repo.repository_path == temp_dir
        assert repo.templates == {}
        assert repo.metadata_file.exists()

    def test_add_template_to_repository(self, temp_dir):
        """Test adding template to repository."""
        repo = TemplateRepository(repository_path=temp_dir)

        template_content = """---
name: test-template
version: 1.0.0
type: documentation
author: Test Author
---
# {{ project_name }}
Test template content
"""

        template_path = temp_dir / "test-template.md"
        template_path.write_text(template_content)

        repo.add_template(template_path)

        assert "test-template" in repo.templates
        assert repo.templates["test-template"].version == "1.0.0"
        assert repo.templates["test-template"].author == "Test Author"

    def test_template_versioning(self, temp_dir):
        """Test template versioning in repository."""
        repo = TemplateRepository(repository_path=temp_dir)

        # Add initial version
        v1_content = """---
name: versioned-template
version: 1.0.0
---
# Version 1.0.0 content
"""
        v1_path = temp_dir / "versioned-template-v1.md"
        v1_path.write_text(v1_content)
        repo.add_template(v1_path)

        # Add newer version
        v2_content = """---
name: versioned-template
version: 1.1.0
---
# Version 1.1.0 content with improvements
"""
        v2_path = temp_dir / "versioned-template-v2.md"
        v2_path.write_text(v2_content)
        repo.add_template(v2_path)

        # Should track both versions
        versions = repo.get_template_versions("versioned-template")
        assert len(versions) == 2

        # Should return latest version by default
        latest = repo.get_template("versioned-template")
        assert latest.version == "1.1.0"

        # Should be able to get specific version
        specific = repo.get_template("versioned-template", version="1.0.0")
        assert specific.version == "1.0.0"

    def test_template_search(self, temp_dir):
        """Test template search functionality."""
        repo = TemplateRepository(repository_path=temp_dir)

        # Add multiple templates
        templates = [
            ("python-web.md", "python", "web", "Python web application template"),
            ("python-cli.md", "python", "cli", "Python CLI application template"),
            ("rust-web.md", "rust", "web", "Rust web application template"),
            ("js-react.md", "javascript", "frontend", "React frontend template"),
        ]

        for filename, language, category, description in templates:
            content = f"""---
name: {filename[:-3]}
language: {language}
category: {category}
description: {description}
---
Template content for {filename}
"""
            template_path = temp_dir / filename
            template_path.write_text(content)
            repo.add_template(template_path)

        # Test search by language
        python_templates = repo.search_templates(language="python")
        assert len(python_templates) == 2

        # Test search by category
        web_templates = repo.search_templates(category="web")
        assert len(web_templates) == 2

        # Test combined search
        python_web = repo.search_templates(language="python", category="web")
        assert len(python_web) == 1
        assert python_web[0].name == "python-web"

    def test_template_dependencies(self, temp_dir):
        """Test template dependency management."""
        repo = TemplateRepository(repository_path=temp_dir)

        # Base template
        base_content = """---
name: base-template
version: 1.0.0
type: base
---
{% block header %}Default header{% endblock %}
{% block content %}{% endblock %}
"""
        base_path = temp_dir / "base-template.md"
        base_path.write_text(base_content)
        repo.add_template(base_path)

        # Child template with dependency
        child_content = """---
name: child-template
version: 1.0.0
extends: base-template
dependencies:
  - base-template: ">=1.0.0"
---
{% extends 'base-template.md' %}
{% block content %}Child content{% endblock %}
"""
        child_path = temp_dir / "child-template.md"
        child_path.write_text(child_content)
        repo.add_template(child_path)

        # Should resolve dependencies
        dependencies = repo.get_template_dependencies("child-template")
        assert "base-template" in dependencies

        # Should validate dependency compatibility
        assert repo.validate_dependencies("child-template")

    def test_repository_synchronization(self, temp_dir):
        """Test repository synchronization with remote sources."""
        repo = TemplateRepository(repository_path=temp_dir)

        # Mock remote repository
        with patch(
            "claude_builder.core.template_manager.RemoteTemplateRepository"
        ) as mock_remote:
            mock_remote_instance = MagicMock()
            mock_remote_instance.list_templates.return_value = [
                {
                    "name": "remote-template",
                    "version": "1.0.0",
                    "url": "https://example.com/template",
                }
            ]
            mock_remote.return_value = mock_remote_instance

            # Sync with remote
            repo.sync_with_remote("https://templates.claude-builder.com")

            # Should have attempted to fetch remote templates
            mock_remote_instance.list_templates.assert_called_once()

    def test_template_validation(self, temp_dir):
        """Test template validation and quality checks."""
        repo = TemplateRepository(repository_path=temp_dir)

        # Valid template
        valid_content = """---
name: valid-template
version: 1.0.0
type: documentation
description: A valid template
author: Test Author
---
# {{ project_name }}
This is a valid template with proper structure.
"""
        valid_path = temp_dir / "valid-template.md"
        valid_path.write_text(valid_content)

        # Invalid template
        invalid_content = """---
name: invalid-template
# Missing required fields
---
# {{ undefined_variable }}
This template references undefined variables.
"""
        invalid_path = temp_dir / "invalid-template.md"
        invalid_path.write_text(invalid_content)

        # Should successfully add valid template
        repo.add_template(valid_path)
        assert "valid-template" in repo.templates

        # Should reject invalid template
        with pytest.raises(Exception):
            repo.add_template(invalid_path, validate=True)


class TestTemplateEcosystem:
    """Test suite for TemplateEcosystem class."""

    def test_ecosystem_initialization(self, temp_dir):
        """Test template ecosystem initialization."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        assert ecosystem.base_directory == temp_dir
        assert ecosystem.repositories == {}
        assert ecosystem.global_registry is not None

    def test_multiple_repository_management(self, temp_dir):
        """Test managing multiple template repositories."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        # Create repository directories
        official_repo = temp_dir / "official"
        community_repo = temp_dir / "community"
        private_repo = temp_dir / "private"

        for repo_dir in [official_repo, community_repo, private_repo]:
            repo_dir.mkdir()

        # Register repositories
        ecosystem.register_repository("official", official_repo, priority=1)
        ecosystem.register_repository("community", community_repo, priority=2)
        ecosystem.register_repository(
            "private", private_repo, priority=0
        )  # Highest priority

        assert len(ecosystem.repositories) == 3

        # Should search repositories in priority order
        search_order = ecosystem.get_repository_search_order()
        assert search_order[0] == "private"  # Highest priority first
        assert search_order[1] == "official"
        assert search_order[2] == "community"

    def test_template_discovery_across_repositories(self, temp_dir):
        """Test template discovery across multiple repositories."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        # Create repositories with different templates
        repo1_dir = temp_dir / "repo1"
        repo2_dir = temp_dir / "repo2"
        repo1_dir.mkdir()
        repo2_dir.mkdir()

        # Add templates to repo1
        (repo1_dir / "python-basic.md").write_text(
            """---
name: python-basic
version: 1.0.0
---
Basic Python template
"""
        )

        # Add templates to repo2
        (repo2_dir / "python-advanced.md").write_text(
            """---
name: python-advanced
version: 1.0.0
---
Advanced Python template
"""
        )

        ecosystem.register_repository("repo1", repo1_dir)
        ecosystem.register_repository("repo2", repo2_dir)

        # Should discover templates from both repositories
        all_templates = ecosystem.discover_all_templates()
        template_names = [t.name for t in all_templates]

        assert "python-basic" in template_names
        assert "python-advanced" in template_names
        assert len(all_templates) == 2

    def test_template_conflict_resolution(self, temp_dir):
        """Test resolution of template name conflicts."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        # Create repositories with conflicting template names
        high_priority_repo = temp_dir / "high_priority"
        low_priority_repo = temp_dir / "low_priority"
        high_priority_repo.mkdir()
        low_priority_repo.mkdir()

        # Same template name in both repositories
        (high_priority_repo / "common-template.md").write_text(
            """---
name: common-template
version: 2.0.0
---
High priority version
"""
        )

        (low_priority_repo / "common-template.md").write_text(
            """---
name: common-template
version: 1.0.0
---
Low priority version
"""
        )

        ecosystem.register_repository("high", high_priority_repo, priority=1)
        ecosystem.register_repository("low", low_priority_repo, priority=2)

        # Should return template from high-priority repository
        template = ecosystem.get_template("common-template")
        assert template.version == "2.0.0"
        assert "High priority version" in template.content

    def test_ecosystem_updates_and_synchronization(self, temp_dir):
        """Test ecosystem-wide updates and synchronization."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        # Mock repository update mechanisms
        with patch.object(ecosystem, "_check_for_updates") as mock_check:
            mock_check.return_value = {
                "repo1": ["template1", "template2"],
                "repo2": ["template3"],
            }

            with patch.object(ecosystem, "_download_updates") as mock_download:
                # Trigger ecosystem update
                updates = ecosystem.check_for_updates()
                ecosystem.apply_updates(updates)

                # Should have checked all repositories for updates
                mock_check.assert_called_once()
                mock_download.assert_called_once()

    def test_template_recommendation_system(self, temp_dir):
        """Test intelligent template recommendation system."""
        ecosystem = TemplateEcosystem(base_directory=temp_dir)

        # Mock project analysis
        project_context = {
            "project_type": "python",
            "framework": "fastapi",
            "features": ["api", "database", "authentication"],
            "complexity": "medium",
        }

        # Mock template metadata for recommendation
        with patch.object(ecosystem, "_analyze_template_suitability") as mock_analyze:
            mock_analyze.return_value = [
                {
                    "template": "python-fastapi-complete",
                    "score": 0.95,
                    "reasons": ["exact framework match", "includes auth"],
                },
                {
                    "template": "python-web-basic",
                    "score": 0.75,
                    "reasons": ["language match", "web framework"],
                },
                {"template": "generic-api", "score": 0.60, "reasons": ["api support"]},
            ]

            recommendations = ecosystem.recommend_templates(project_context)

            # Should return recommendations sorted by score
            assert len(recommendations) == 3
            assert recommendations[0]["template"] == "python-fastapi-complete"
            assert recommendations[0]["score"] == 0.95


class TestTemplateMarketplace:
    """Test suite for TemplateMarketplace class."""

    def test_marketplace_initialization(self):
        """Test template marketplace initialization."""
        marketplace = TemplateMarketplace(
            marketplace_url="https://templates.claude-builder.com",
            api_key="test-api-key",
        )

        assert marketplace.marketplace_url == "https://templates.claude-builder.com"
        assert marketplace.api_key == "test-api-key"
        assert marketplace.cache is not None

    def test_browse_marketplace_templates(self):
        """Test browsing marketplace templates."""
        marketplace = TemplateMarketplace("https://test-marketplace.com")

        # Mock API response
        mock_response = {
            "templates": [
                {
                    "name": "python-fastapi-pro",
                    "version": "2.1.0",
                    "author": "Claude Team",
                    "description": "Professional FastAPI template",
                    "downloads": 1500,
                    "rating": 4.8,
                    "tags": ["python", "fastapi", "api", "professional"],
                },
                {
                    "name": "react-typescript-starter",
                    "version": "3.0.0",
                    "author": "React Community",
                    "description": "Modern React + TypeScript starter",
                    "downloads": 3200,
                    "rating": 4.9,
                    "tags": ["react", "typescript", "frontend", "modern"],
                },
            ]
        }

        with patch.object(marketplace, "_make_api_request") as mock_request:
            mock_request.return_value = mock_response

            templates = marketplace.browse_templates()

            assert len(templates) == 2
            assert templates[0]["name"] == "python-fastapi-pro"
            assert templates[1]["name"] == "react-typescript-starter"

    def test_search_marketplace_templates(self):
        """Test searching marketplace templates."""
        marketplace = TemplateMarketplace("https://test-marketplace.com")

        # Mock search results
        with patch.object(marketplace, "_make_api_request") as mock_request:
            mock_request.return_value = {
                "results": [
                    {"name": "python-cli-advanced", "score": 0.95},
                    {"name": "python-web-basic", "score": 0.80},
                ]
            }

            results = marketplace.search_templates(
                query="python cli", filters={"language": "python", "category": "cli"}
            )

            assert len(results) == 2
            assert results[0]["name"] == "python-cli-advanced"
            mock_request.assert_called_with(
                "GET",
                "/search",
                params={"q": "python cli", "language": "python", "category": "cli"},
            )

    def test_download_template_from_marketplace(self, temp_dir):
        """Test downloading template from marketplace."""
        marketplace = TemplateMarketplace("https://test-marketplace.com")

        # Mock template download
        template_content = """---
name: marketplace-template
version: 1.0.0
author: Marketplace Author
---
# {{ project_name }}
Downloaded from marketplace
"""

        with patch.object(marketplace, "_download_template_content") as mock_download:
            mock_download.return_value = template_content

            template_path = marketplace.download_template(
                "marketplace-template", destination=temp_dir
            )

            assert template_path.exists()
            assert template_path.name == "marketplace-template.md"
            content = template_path.read_text()
            assert "Downloaded from marketplace" in content

    def test_publish_template_to_marketplace(self, temp_dir):
        """Test publishing template to marketplace."""
        marketplace = TemplateMarketplace(
            "https://test-marketplace.com", api_key="test-key"
        )

        # Create template to publish
        template_path = temp_dir / "my-template.md"
        template_content = """---
name: my-custom-template
version: 1.0.0
author: Me
description: My custom template
tags: [custom, test]
---
# {{ project_name }}
My custom template content
"""
        template_path.write_text(template_content)

        # Mock publish response
        with patch.object(marketplace, "_make_api_request") as mock_request:
            mock_request.return_value = {
                "success": True,
                "template_id": "12345",
                "url": "https://test-marketplace.com/templates/my-custom-template",
            }

            result = marketplace.publish_template(template_path)

            assert result["success"] is True
            assert result["template_id"] == "12345"
            mock_request.assert_called_with("POST", "/templates", data=ANY, files=ANY)

    def test_template_ratings_and_reviews(self):
        """Test template ratings and reviews functionality."""
        marketplace = TemplateMarketplace("https://test-marketplace.com")

        # Mock reviews data
        mock_reviews = {
            "average_rating": 4.7,
            "total_reviews": 23,
            "reviews": [
                {
                    "author": "developer1",
                    "rating": 5,
                    "comment": "Excellent template, saved me hours!",
                    "date": "2024-01-15",
                },
                {
                    "author": "developer2",
                    "rating": 4,
                    "comment": "Good template but could use more examples",
                    "date": "2024-01-10",
                },
            ],
        }

        with patch.object(marketplace, "_make_api_request") as mock_request:
            mock_request.return_value = mock_reviews

            reviews = marketplace.get_template_reviews("python-fastapi-pro")

            assert reviews["average_rating"] == 4.7
            assert reviews["total_reviews"] == 23
            assert len(reviews["reviews"]) == 2


class TestTemplateBuilder:
    """Test suite for TemplateBuilder class."""

    def test_interactive_template_creation(self, temp_dir):
        """Test interactive template creation workflow."""
        builder = TemplateBuilder()

        # Mock user inputs
        template_config = {
            "name": "custom-python-api",
            "description": "Custom Python API template",
            "author": "Test Developer",
            "version": "1.0.0",
            "language": "python",
            "framework": "fastapi",
            "features": ["authentication", "database", "testing"],
        }

        # Mock template generation
        with patch.object(builder, "_generate_template_content") as mock_generate:
            mock_generate.return_value = """---
name: {{ name }}
description: {{ description }}
author: {{ author }}
---
# {{ project_name }}
{{ description }}

## Features
{% for feature in features %}
- {{ feature }}
{% endfor %}
"""

            template_path = builder.create_template(
                config=template_config, output_directory=temp_dir
            )

            assert template_path.exists()
            assert template_path.name == "custom-python-api.md"
            mock_generate.assert_called_once_with(template_config)

    def test_template_customization_wizard(self):
        """Test template customization wizard."""
        builder = TemplateBuilder()

        # Mock existing template
        base_template_content = """---
name: base-template
customizable: true
options:
  database:
    type: choice
    choices: [postgresql, mysql, sqlite]
    default: postgresql
  authentication:
    type: boolean
    default: true
  testing:
    type: choice
    choices: [pytest, unittest]
    default: pytest
---
# {{ project_name }}
{% if options.authentication %}
## Authentication
Using OAuth2 authentication
{% endif %}

{% if options.database == 'postgresql' %}
## Database
Using PostgreSQL database
{% endif %}
"""

        customization_choices = {
            "database": "mysql",
            "authentication": False,
            "testing": "unittest",
        }

        with patch.object(builder, "_apply_customizations") as mock_apply:
            mock_apply.return_value = "# Customized template content"

            customized_template = builder.customize_template(
                base_template_content, customization_choices
            )

            assert customized_template is not None
            mock_apply.assert_called_once_with(
                base_template_content, customization_choices
            )

    def test_template_validation_and_testing(self, temp_dir):
        """Test template validation and testing capabilities."""
        builder = TemplateBuilder()

        # Create test template
        template_content = """---
name: test-template
version: 1.0.0
test_cases:
  - name: basic_project
    context:
      project_name: TestProject
      features: [api, database]
    expected_files: [main.py, requirements.txt]
---
# {{ project_name }}
Files: main.py, requirements.txt
"""

        template_path = temp_dir / "test-template.md"
        template_path.write_text(template_content)

        # Mock validation
        with patch.object(builder, "_run_template_tests") as mock_test:
            mock_test.return_value = {
                "passed": 1,
                "failed": 0,
                "results": [
                    {
                        "test": "basic_project",
                        "status": "passed",
                        "details": "All files generated correctly",
                    }
                ],
            }

            validation_result = builder.validate_template(template_path)

            assert validation_result["passed"] == 1
            assert validation_result["failed"] == 0
            mock_test.assert_called_once()

    def test_template_packaging_and_distribution(self, temp_dir):
        """Test template packaging for distribution."""
        builder = TemplateBuilder()

        # Create template with assets
        template_dir = temp_dir / "my-template"
        template_dir.mkdir()

        (template_dir / "template.md").write_text(
            """---
name: packaged-template
version: 1.0.0
---
# {{ project_name }}
Template content
"""
        )

        (template_dir / "assets").mkdir()
        (template_dir / "assets" / "logo.png").write_bytes(b"fake image data")
        (template_dir / "examples").mkdir()
        (template_dir / "examples" / "example1.py").write_text("# Example code")

        # Package template
        package_path = builder.package_template(
            template_directory=template_dir, output_directory=temp_dir
        )

        assert package_path.exists()
        assert package_path.suffix == ".zip"
        assert "packaged-template" in package_path.name


class TestTemplateRendererFunctionality:
    """Test suite for TemplateRenderer functionality."""

    def test_template_renderer_initialization(self):
        """Test TemplateRenderer initialization with options."""
        from claude_builder.core.template_manager import TemplateRenderer

        # Basic initialization
        renderer = TemplateRenderer()
        assert renderer.template_engine == "simple"
        assert renderer.enable_cache is False
        assert renderer.render_cache is None

        # Initialization with caching
        cached_renderer = TemplateRenderer(enable_cache=True)
        assert cached_renderer.enable_cache is True
        assert cached_renderer.render_cache == {}

        # Test filters are available
        assert "length" in renderer.filters
        assert "upper" in renderer.filters
        assert "lower" in renderer.filters
        assert "title" in renderer.filters

    def test_template_render_method_coordination(self):
        """Test TemplateRenderer render method with Template objects."""
        from claude_builder.core.template_manager import (
            Template,
            TemplateContext,
            TemplateRenderer,
        )

        renderer = TemplateRenderer()

        # Create template and context
        template = Template(
            name="test.md", content="# {{ project_name }}\n\nLanguage: {{ language }}"
        )

        context = TemplateContext(project_name="TestProject", language="Python")

        # Test rendering coordination
        result = renderer.render(template, context)

        assert "# TestProject" in result
        assert "Language: Python" in result

        # Test with kwargs
        result_kwargs = renderer.render(
            template, project_name="KwargsProject", language="JavaScript"
        )

        assert "# KwargsProject" in result_kwargs
        assert "Language: JavaScript" in result_kwargs

    def test_template_loader_coordination(self, temp_dir):
        """Test TemplateLoader coordination with file system."""
        from claude_builder.core.template_manager import TemplateLoader

        # Create test template files
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        (templates_dir / "test.md").write_text("# {{ project_name }}")
        (templates_dir / "python.md").write_text("## Python Template")

        # Initialize loader
        loader = TemplateLoader(template_directory=str(templates_dir))

        # Test template listing
        available_templates = loader.list_templates()
        assert "test" in available_templates
        assert "python" in available_templates

        # Test template existence check
        assert loader.template_exists("test")
        assert loader.template_exists("python")
        assert not loader.template_exists("nonexistent")

        # Test template loading
        test_content = loader.load_template("test")
        assert test_content == "# {{ project_name }}"

        # Test template object loading
        template_obj = loader.load_template_from_file("test")
        assert template_obj.name == "test"
        assert template_obj.content == "# {{ project_name }}"


class TestTemplateManagerBackwardCompatibility:
    """Test suite ensuring backward compatibility of TemplateManager."""

    def test_legacy_interface_methods_exist(self, temp_dir):
        """Test that all legacy interface methods are preserved."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test that all expected methods exist
        expected_methods = [
            "get_template",
            "get_template_info",
            "get_templates_by_type",
            "render_template",
            "select_template_for_project",
            "render_batch",
            "render_all_templates",
            "list_available_templates",
            "search_templates",
            "install_template",
            "uninstall_template",
            "create_custom_template",
            "validate_template_directory",
        ]

        for method_name in expected_methods:
            assert hasattr(template_manager, method_name)
            assert callable(getattr(template_manager, method_name))

    def test_config_parameter_handling(self, temp_dir):
        """Test TemplateManager handles various config parameter formats."""
        # Test with config dict
        config = {"enable_cache": True, "preferred_template": "python"}
        tm1 = TemplateManager(config=config)
        assert tm1.config["enable_cache"] is True

        # Test with template_directory parameter
        tm2 = TemplateManager(template_directory=str(temp_dir))
        assert str(temp_dir) in str(tm2.templates_dir)

        # Test with kwargs
        tm3 = TemplateManager(enable_cache=True, max_templates=50)
        assert tm3.config["enable_cache"] is True
        assert tm3.config["max_templates"] == 50

        # Test combined parameters
        tm4 = TemplateManager(
            config={"base_option": "value"},
            template_directory=str(temp_dir),
            extra_option="extra_value",
        )
        assert tm4.config["base_option"] == "value"
        assert tm4.config["extra_option"] == "extra_value"
        assert str(temp_dir) in str(tm4.templates_dir)

    def test_templates_cache_compatibility(self, temp_dir):
        """Test templates cache maintains backward compatibility."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should have templates dict for test compatibility
        assert hasattr(template_manager, "templates")
        assert isinstance(template_manager.templates, dict)

        # Getting templates should populate the cache for compatibility
        template1 = template_manager.get_template("test-template.md")
        template2 = template_manager.get_template("test-template.md")

        # Both should be Template objects
        assert hasattr(template1, "render")
        assert hasattr(template2, "render")

        # Test template properties
        assert "test-template" in template1.name or "test-template" in str(
            template1.content
        )

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_coordination_layer_error_handling(self, temp_dir):
        """Test coordination layer handles modular component failures gracefully."""
        # Mock failing modular components
        with patch(
            "claude_builder.core.template_manager.TemplateDownloader",
            side_effect=Exception("Downloader failed"),
        ), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient",
            side_effect=Exception("Repository failed"),
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator",
            side_effect=Exception("Validator failed"),
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            side_effect=Exception("Community manager failed"),
        ):

            # Should initialize successfully despite modular component failures
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should fall back to legacy behavior
            assert template_manager.community_manager is None

            # Legacy methods should still work
            templates = template_manager.list_available_templates()
            assert isinstance(templates, list)

            # Validation should fall back to legacy validator
            test_path = temp_dir / "test"
            test_path.mkdir()
            (test_path / "template.json").write_text("{}")  # Invalid but existing
            result = template_manager.validate_template_directory(test_path)
            assert hasattr(result, "is_valid")

    def test_template_conversion_methods(self, temp_dir):
        """Test internal template conversion methods work correctly."""
        with patch(
            "claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False
        ):
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test _convert_to_legacy_template with no modern template
            result = template_manager._convert_to_legacy_template(None)
            assert result.metadata.name == "unknown"
            assert result.metadata.version == "1.0.0"

    def test_template_manager_initialization_paths(self, temp_dir):
        """Test different TemplateManager initialization paths."""
        # Test default initialization
        tm1 = TemplateManager()
        assert tm1.templates_dir.name == "templates"
        assert tm1.cache_dir.name == "cache"

        # Test with custom template directory
        custom_dir = temp_dir / "custom_templates"
        tm2 = TemplateManager(template_directory=str(custom_dir))
        assert tm2.templates_dir == custom_dir

        # Directories should be created
        assert tm2.templates_dir.exists()
        assert tm2.cache_dir.exists()

        # Test legacy components are always initialized
        assert hasattr(tm2, "validator")
        assert hasattr(tm2, "loader")
        assert hasattr(tm2, "renderer")
        assert tm2.loader is not None
        assert tm2.renderer is not None
