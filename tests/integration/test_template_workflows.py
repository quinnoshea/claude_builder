"""
Integration tests for template workflows.

Tests the complete template processing pipeline including:
- Template discovery and loading
- Template rendering with real data
- Template inheritance and composition
- Multi-template generation workflows
- Template ecosystem integration
"""

from unittest.mock import Mock, patch

import pytest


pytestmark = pytest.mark.failing

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.generator import DocumentGenerator
from claude_builder.core.template_manager import TemplateManager


class TestTemplateWorkflowIntegration:
    """Test suite for template workflow integration."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_template_discovery_and_rendering_modular(
        self, temp_dir, sample_python_project
    ):
        """Test template discovery and rendering with modular architecture."""
        # Mock modular components
        mock_downloader = Mock()
        mock_repository_client = Mock()
        mock_validator = Mock()
        mock_community_manager = Mock()

        # Mock community manager behavior
        mock_community_template = Mock()
        mock_community_template.metadata.to_dict.return_value = {
            "name": "python-template",
            "version": "1.0.0",
            "description": "Python project template",
            "author": "test",
        }
        mock_community_template.source_url = None
        mock_community_template.local_path = None

        mock_community_manager.list_available_templates.return_value = [
            mock_community_template
        ]

        with patch(
            "claude_builder.core.template_manager.TemplateDownloader",
            return_value=mock_downloader,
        ), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient",
            return_value=mock_repository_client,
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator",
            return_value=mock_validator,
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            # Initialize template manager with modular components
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test coordination layer delegates to modular components
            available_templates = template_manager.list_available_templates()

            # Verify delegation occurred
            mock_community_manager.list_available_templates.assert_called_once()
            assert len(available_templates) == 1
            assert available_templates[0].metadata.name == "python-template"

    def test_template_discovery_and_rendering_fallback(
        self, temp_dir, sample_python_project
    ):
        """Test template discovery falls back to legacy when modular unavailable."""
        # Test with modular components unavailable
        with patch(
            "claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False
        ):
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should use legacy implementation
            assert template_manager.community_manager is None

            # Legacy implementation should work
            available_templates = template_manager.list_available_templates()
            assert isinstance(
                available_templates, list
            )  # Should return empty list but not fail

    def test_coordination_layer_template_rendering(
        self, temp_dir, sample_python_project
    ):
        """Test coordination layer handles template rendering requests properly."""
        # Initialize template manager with coordination layer
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test get_template method returns Template objects for test compatibility
        claude_template = template_manager.get_template("claude-instructions.md")
        readme_template = template_manager.get_template("readme.md")
        contributing_template = template_manager.get_template("contributing.md")

        # Should return Template objects for backward compatibility
        assert claude_template is not None
        assert readme_template is not None
        assert contributing_template is not None

        # Template objects should be renderable
        context = {
            "project_name": "test-project",
            "project_type": "python",
            "framework": "fastapi",
        }

        claude_rendered = claude_template.render(**context)
        readme_rendered = readme_template.render(**context)
        contributing_rendered = contributing_template.render(**context)

        # Verify rendered content contains expected elements
        assert "test-project" in claude_rendered
        assert "test-project" in readme_rendered
        assert "test-project" in contributing_rendered

        # Test template manager provides backward compatibility
        assert hasattr(template_manager, "render_template")
        assert hasattr(template_manager, "get_templates_by_type")
        assert hasattr(template_manager, "select_template_for_project")

    def test_template_manager_coordination_methods(
        self, temp_dir, sample_python_project
    ):
        """Test template manager coordination methods work properly."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test coordination layer methods
        documentation_templates = template_manager.get_templates_by_type(
            "documentation"
        )
        assert len(documentation_templates) >= 1

        # Test template selection for project type
        selected_template = template_manager.select_template_for_project(
            "claude_instructions", "python"
        )
        assert selected_template is not None
        assert hasattr(selected_template, "render")

        # Test batch rendering coordination
        from claude_builder.core.template_manager import TemplateContext

        context = TemplateContext(
            project_name="test-project", language="python", framework="fastapi"
        )

        templates = {
            "claude.md": "# {{ project_name }} Claude Instructions",
            "readme.md": "# {{ project_name }}\n\nFramework: {{ framework }}",
        }

        results = template_manager.render_batch(templates, context)
        assert len(results) == 2
        assert "test-project" in results["claude.md"]
        assert "fastapi" in results["readme.md"]

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_modular_template_validation(self, temp_dir, sample_python_project):
        """Test template validation through coordination layer with modular components."""
        # Mock modular validator
        mock_validator = Mock()
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validation_result.errors = []
        mock_validation_result.warnings = []
        mock_validation_result.suggestions = ["Template validated successfully"]
        mock_validator.validate_template.return_value = mock_validation_result

        with patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator",
            return_value=mock_validator,
        ), patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager"
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test validation through coordination layer
            test_template_path = temp_dir / "test_template"
            test_template_path.mkdir()
            (test_template_path / "template.json").write_text("{}")

            result = template_manager.validate_template_directory(test_template_path)

            # Should use modern validator when available
            mock_validator.validate_template.assert_called_once_with(test_template_path)
            assert result.is_valid
            assert "Template validated successfully" in result.suggestions

    def test_legacy_template_validation_fallback(self, temp_dir, sample_python_project):
        """Test template validation falls back to legacy validator."""
        with patch(
            "claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False
        ):
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Create a basic template for validation
            test_template_path = temp_dir / "test_template"
            test_template_path.mkdir()

            # Create required files for legacy validation
            (test_template_path / "template.json").write_text(
                """{
  "name": "test",
  "version": "1.0.0",
  "description": "Test template",
  "author": "test"
}"""
            )
            (test_template_path / "claude_instructions.md").write_text(
                "# Test Template"
            )

            # Test validation through coordination layer
            result = template_manager.validate_template_directory(test_template_path)

            # Should use legacy validator and succeed
            assert result.is_valid
            assert len(result.errors) == 0

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_template_search_coordination(self, temp_dir, sample_python_project):
        """Test template search through coordination layer with modular components."""
        # Mock community manager search
        mock_community_manager = Mock()
        mock_search_results = [Mock()]
        mock_search_results[0].metadata.to_dict.return_value = {
            "name": "python-fastapi-template",
            "version": "1.0.0",
            "description": "FastAPI Python template",
            "author": "test",
        }
        mock_community_manager.search_templates.return_value = mock_search_results

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Analyze project for search context
            analyzer = ProjectAnalyzer()
            analysis_result = analyzer.analyze(sample_python_project)

            # Test search coordination
            search_results = template_manager.search_templates(
                "python", analysis_result
            )

            # Verify delegation to modular components
            mock_community_manager.search_templates.assert_called_once_with(
                "python", analysis_result
            )
            assert len(search_results) == 1
            assert search_results[0].metadata.name == "python-fastapi-template"

    def test_template_search_fallback(self, temp_dir, sample_python_project):
        """Test template search falls back to legacy implementation."""
        with patch(
            "claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False
        ):
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should use legacy search implementation
            search_results = template_manager.search_templates("python")

            # Legacy implementation should return empty list but not fail
            assert isinstance(search_results, list)
            assert template_manager.community_manager is None

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_template_installation_coordination(self, temp_dir, sample_python_project):
        """Test template installation through coordination layer."""
        # Mock community manager installation
        mock_community_manager = Mock()
        mock_install_result = Mock()
        mock_install_result.is_valid = True
        mock_install_result.errors = []
        mock_install_result.warnings = []
        mock_install_result.suggestions = ["Template installed successfully"]
        mock_community_manager.install_template.return_value = mock_install_result

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test installation coordination
            result = template_manager.install_template(
                "python-fastapi-template", force=True
            )

            # Verify delegation to modular components
            mock_community_manager.install_template.assert_called_once_with(
                "python-fastapi-template", force=True
            )
            assert result.is_valid
            assert "Template installed successfully" in result.suggestions

    def test_template_installation_fallback(self, temp_dir, sample_python_project):
        """Test template installation falls back to legacy implementation."""
        with patch(
            "claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False
        ):
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test legacy installation - should handle gracefully
            result = template_manager.install_template("nonexistent-template")

            # Legacy implementation should return appropriate error
            assert not result.is_valid
            assert "Template not found" in " ".join(result.errors)
            assert template_manager.community_manager is None

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_template_uninstallation_coordination(
        self, temp_dir, sample_python_project
    ):
        """Test template uninstallation through coordination layer."""
        # Mock community manager uninstallation
        mock_community_manager = Mock()
        mock_uninstall_result = Mock()
        mock_uninstall_result.is_valid = True
        mock_uninstall_result.errors = []
        mock_uninstall_result.warnings = []
        mock_uninstall_result.suggestions = ["Template uninstalled successfully"]
        mock_community_manager.uninstall_template.return_value = mock_uninstall_result

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Test uninstallation coordination
            result = template_manager.uninstall_template("python-fastapi-template")

            # Verify delegation to modular components
            mock_community_manager.uninstall_template.assert_called_once_with(
                "python-fastapi-template"
            )
            assert result.is_valid
            assert "Template uninstalled successfully" in result.suggestions

    def test_template_legacy_compatibility_methods(
        self, temp_dir, sample_python_project
    ):
        """Test legacy compatibility methods work through coordination layer."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test get_template_info method (legacy compatibility)
        template_info = template_manager.get_template_info("test-template")
        # Should return None for non-existent template but not error
        assert template_info is None

        # Test render_all_templates (legacy compatibility)
        from claude_builder.core.template_manager import TemplateContext

        context = TemplateContext(
            project_name="test-project", description="A test project"
        )

        all_rendered = template_manager.render_all_templates(context)
        assert isinstance(all_rendered, dict)
        assert "claude.md" in all_rendered
        assert "test-project" in all_rendered["claude.md"]

        # Test create_custom_template coordination

        project_path = temp_dir / "sample_project"
        project_path.mkdir()
        (project_path / "__init__.py").write_text("")  # Make it look like a project

        template_config = {
            "description": "Custom test template",
            "author": "test-user",
            "category": "custom",
        }

        result = template_manager.create_custom_template(
            "test-custom-template", project_path, template_config
        )

        # Should succeed and create template
        assert result.is_valid
        custom_template_path = (
            template_manager.templates_dir / "custom" / "test-custom-template"
        )
        assert custom_template_path.exists()
        assert (custom_template_path / "template.json").exists()


class TestTemplateEcosystemIntegration:
    """Test suite for template ecosystem integration."""

    @pytest.mark.skip(reason="TemplateEcosystem not yet implemented")
    def test_multi_repository_template_workflow(self, temp_dir, sample_python_project):
        """Test workflow with multiple template repositories."""
        # Create multiple template repositories
        official_repo = temp_dir / "official_templates"
        community_repo = temp_dir / "community_templates"
        personal_repo = temp_dir / "personal_templates"

        for repo in [official_repo, community_repo, personal_repo]:
            repo.mkdir()

        # Official repository templates
        (official_repo / "python_basic.md").write_text(
            """---
name: python-basic
type: documentation
repository: official
priority: 1
---
# {{ project_name }} - Official Template
Official Python project documentation.
"""
        )

        # Community repository templates
        (community_repo / "python_advanced.md").write_text(
            """---
name: python-advanced
type: documentation
repository: community
priority: 2
---
# {{ project_name }} - Community Template
Advanced Python project with community best practices.
"""
        )

        # Personal repository templates
        (personal_repo / "python_custom.md").write_text(
            """---
name: python-custom
type: documentation
repository: personal
priority: 0
---
# {{ project_name }} - Personal Template
Custom Python template with personal preferences.
"""
        )

        # Test repository priority and template selection
        from claude_builder.core.template_manager import TemplateEcosystem

        ecosystem = TemplateEcosystem(base_directory=temp_dir)
        ecosystem.register_repository("official", official_repo, priority=1)
        ecosystem.register_repository("community", community_repo, priority=2)
        ecosystem.register_repository(
            "personal", personal_repo, priority=0
        )  # Highest priority

        # Should find template from highest priority repository first
        template = ecosystem.get_template("python-custom")
        assert template is not None
        assert "Personal Template" in template.content

        # Should find all matching templates across repositories
        all_python_templates = ecosystem.search_templates(name_pattern="python*")
        assert len(all_python_templates) == 3


class TestTemplatePerformanceIntegration:
    """Test suite for template performance integration."""

    def test_large_template_rendering_performance(
        self, temp_dir, sample_python_project
    ):
        """Test performance with large templates."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        # Create large template with many loops and conditions
        large_template = templates_dir / "large.md"
        large_content = """---
name: large-template
type: documentation
---
# {{ project_name }}

{% for i in range(100) %}
## Section {{ i }}
This is section {{ i }} of the documentation.

{% if i % 10 == 0 %}
### Special Section {{ i }}
This is a special milestone section.
{% endif %}

{% for dep in dependencies %}
- Dependency {{ dep }} in section {{ i }}
{% endfor %}

{% endfor %}

## File Listing
{% for file in all_files %}
- {{ file.path }}: {{ file.size }} bytes
{% endfor %}
"""
        large_template.write_text(large_content)

        template_manager = TemplateManager()
        analyzer = ProjectAnalyzer()
        analysis_result = analyzer.analyze(sample_python_project)
        generator = DocumentGenerator(analysis_result)

        # Add mock data for performance test
        generator.context_data = {
            "all_files": [{"path": f"file_{i}.py", "size": i * 100} for i in range(50)]
        }

        import time

        start_time = time.time()

        template = template_manager.get_template("large.md")
        rendered_content = generator.render_template_with_manager(
            template, template_manager
        )

        end_time = time.time()
        render_time = end_time - start_time

        # Should complete in reasonable time
        assert render_time < 5.0  # Less than 5 seconds
        assert len(rendered_content) > 1000  # Should produce substantial output
        assert "Section 99" in rendered_content  # Should complete all loops
