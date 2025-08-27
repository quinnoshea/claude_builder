"""
Unit tests for TemplateManager coordination layer.

Tests the main TemplateManager class coordination logic that delegates
to modular components when available and falls back to legacy implementation.
Focuses on testing the coordination layer specifically, not the individual
modular components (which have their own test suites).
"""

from unittest.mock import Mock, patch

from claude_builder.core.template_manager import (
    CommunityTemplate,
    TemplateManager,
    ValidationResult,
)


class TestTemplateManagerCoordinationCore:
    """Core coordination layer tests for TemplateManager."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_initialization_with_modular_components(self, temp_dir):
        """Test TemplateManager initializes modular components when available."""
        # Mock all modular components to succeed
        with patch(
            "claude_builder.core.template_manager.TemplateDownloader"
        ) as mock_downloader, patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ) as mock_repo_client, patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ) as mock_validator, patch(
            "claude_builder.core.template_manager.CommunityTemplateManager"
        ) as mock_community_mgr:

            mock_downloader_instance = Mock()
            mock_repo_client_instance = Mock()
            mock_validator_instance = Mock()
            mock_community_mgr_instance = Mock()

            mock_downloader.return_value = mock_downloader_instance
            mock_repo_client.return_value = mock_repo_client_instance
            mock_validator.return_value = mock_validator_instance
            mock_community_mgr.return_value = mock_community_mgr_instance

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should initialize all modular components
            mock_downloader.assert_called_once()
            mock_repo_client.assert_called_once_with(mock_downloader_instance)
            # Validator is called twice: once for TemplateManager, once for legacy TemplateValidator
            assert mock_validator.call_count >= 1
            mock_community_mgr.assert_called_once_with(
                templates_dir=template_manager.templates_dir,
                downloader=mock_downloader_instance,
                repository_client=mock_repo_client_instance,
                validator=mock_validator_instance,
            )

            # Should have community manager set
            assert template_manager.community_manager is mock_community_mgr_instance

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_initialization_without_modular_components(self, temp_dir):
        """Test TemplateManager initializes without modular components when unavailable."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should not have community manager when modular components unavailable
        assert template_manager.community_manager is None

        # Should still have legacy components
        assert hasattr(template_manager, "validator")
        assert hasattr(template_manager, "loader")
        assert hasattr(template_manager, "renderer")
        assert template_manager.validator is not None
        assert template_manager.loader is not None
        assert template_manager.renderer is not None

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_initialization_with_component_failures(self, temp_dir):
        """Test TemplateManager gracefully handles modular component initialization failures."""
        # Mock some components to fail during initialization
        with patch(
            "claude_builder.core.template_manager.TemplateDownloader",
            side_effect=Exception("Downloader failed"),
        ), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient",
            side_effect=Exception("Repository failed"),
        ):

            # Should not raise exception, should fall back gracefully
            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should have community_manager as None due to failures
            assert template_manager.community_manager is None

            # Should still have working legacy components
            assert template_manager.validator is not None
            assert template_manager.loader is not None
            assert template_manager.renderer is not None


class TestTemplateManagerListAvailableCoordination:
    """Test coordination of list_available_templates method."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_delegates_to_modular_when_available(self, temp_dir):
        """Test list_available_templates delegates to modular component when available."""
        # Mock modular community manager
        mock_community_manager = Mock()
        mock_modern_template = Mock()
        mock_modern_template.metadata.to_dict.return_value = {
            "name": "modern-template",
            "version": "1.0.0",
            "description": "Modern template",
            "author": "test",
        }
        mock_modern_template.source_url = None
        mock_modern_template.local_path = None

        mock_community_manager.list_available_templates.return_value = [
            mock_modern_template
        ]

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Call the method under test
            result = template_manager.list_available_templates(
                include_installed=True, include_community=True
            )

            # Should delegate to modular component
            mock_community_manager.list_available_templates.assert_called_once_with(
                include_installed=True, include_community=True
            )

            # Should convert and return results
            assert len(result) == 1
            assert isinstance(result[0], CommunityTemplate)
            assert result[0].metadata.name == "modern-template"

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_uses_legacy_when_modular_unavailable(self, temp_dir):
        """Test list_available_templates uses legacy implementation when modular unavailable."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should use legacy implementation
        result = template_manager.list_available_templates()

        # Should return list (may be empty, but should not fail)
        assert isinstance(result, list)
        assert template_manager.community_manager is None

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_conversion_handles_none_template(self, temp_dir):
        """Test template conversion handles None template gracefully."""
        # Mock community manager to return None template
        mock_community_manager = Mock()
        mock_community_manager.list_available_templates.return_value = [None]

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Should handle None template without error
            result = template_manager.list_available_templates()

            assert len(result) == 1
            assert isinstance(result[0], CommunityTemplate)
            assert result[0].metadata.name == "unknown"  # Default fallback


class TestTemplateManagerSearchCoordination:
    """Test coordination of search_templates method."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_delegates_search_to_modular(self, temp_dir):
        """Test search_templates delegates to modular component."""
        # Mock community manager search
        mock_community_manager = Mock()
        mock_search_result = Mock()
        mock_search_result.metadata.to_dict.return_value = {
            "name": "search-result",
            "version": "1.0.0",
            "description": "Search result template",
            "author": "test",
        }
        mock_community_manager.search_templates.return_value = [mock_search_result]

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator"
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager",
            return_value=mock_community_manager,
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Create mock project analysis
            mock_analysis = Mock()

            # Call search method
            result = template_manager.search_templates("python", mock_analysis)

            # Should delegate to modular component
            mock_community_manager.search_templates.assert_called_once_with(
                "python", mock_analysis
            )

            # Should convert and return results
            assert len(result) == 1
            assert isinstance(result[0], CommunityTemplate)
            assert result[0].metadata.name == "search-result"

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_search_legacy_fallback(self, temp_dir):
        """Test search_templates falls back to legacy implementation."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should use legacy search
        result = template_manager.search_templates("python")

        # Should return list without error
        assert isinstance(result, list)


class TestTemplateManagerInstallationCoordination:
    """Test coordination of template installation methods."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_install_delegates_to_modular(self, temp_dir):
        """Test install_template delegates to modular component."""
        # Mock community manager installation
        mock_community_manager = Mock()
        mock_install_result = ValidationResult(
            is_valid=True, suggestions=["Template installed successfully"]
        )
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

            # Call install method
            result = template_manager.install_template("python-template", force=True)

            # Should delegate to modular component
            mock_community_manager.install_template.assert_called_once_with(
                "python-template", force=True
            )

            # Should return result
            assert result.is_valid
            assert "Template installed successfully" in result.suggestions

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_uninstall_delegates_to_modular(self, temp_dir):
        """Test uninstall_template delegates to modular component."""
        # Mock community manager uninstallation
        mock_community_manager = Mock()
        mock_uninstall_result = ValidationResult(
            is_valid=True, suggestions=["Template uninstalled successfully"]
        )
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

            # Call uninstall method
            result = template_manager.uninstall_template("python-template")

            # Should delegate to modular component
            mock_community_manager.uninstall_template.assert_called_once_with(
                "python-template"
            )

            # Should return result
            assert result.is_valid
            assert "Template uninstalled successfully" in result.suggestions

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_install_legacy_fallback(self, temp_dir):
        """Test install_template falls back to legacy implementation."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should use legacy implementation
        result = template_manager.install_template("nonexistent-template")

        # Should return error result
        assert not result.is_valid
        assert "Template not found" in " ".join(result.errors)

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_uninstall_legacy_fallback(self, temp_dir):
        """Test uninstall_template falls back to legacy implementation."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should use legacy implementation
        result = template_manager.uninstall_template("nonexistent-template")

        # Should return error result
        assert not result.is_valid
        assert "Template not installed" in " ".join(result.errors)


class TestTemplateManagerValidationCoordination:
    """Test coordination of template validation methods."""

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", True)
    def test_validation_delegates_to_modern_validator(self, temp_dir):
        """Test validate_template_directory uses modern validator when available."""
        # Mock modern validator
        mock_validator = Mock()
        mock_validation_result = ValidationResult(
            is_valid=True, suggestions=["Modern validation passed"]
        )
        mock_validator.validate_template.return_value = mock_validation_result

        with patch("claude_builder.core.template_manager.TemplateDownloader"), patch(
            "claude_builder.core.template_manager.TemplateRepositoryClient"
        ), patch(
            "claude_builder.core.template_manager.ComprehensiveTemplateValidator",
            return_value=mock_validator,
        ), patch(
            "claude_builder.core.template_manager.CommunityTemplateManager"
        ):

            template_manager = TemplateManager(template_directory=str(temp_dir))

            # Create test template path
            test_path = temp_dir / "test_template"
            test_path.mkdir()

            # Call validation method
            result = template_manager.validate_template_directory(test_path)

            # Should use modern validator
            mock_validator.validate_template.assert_called_once_with(test_path)

            # Should return modern validation result
            assert result.is_valid
            assert "Modern validation passed" in result.suggestions

    @patch("claude_builder.core.template_manager.MODULAR_COMPONENTS_AVAILABLE", False)
    def test_validation_falls_back_to_legacy(self, temp_dir):
        """Test validate_template_directory falls back to legacy validator."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Create basic valid template for testing
        test_path = temp_dir / "test_template"
        test_path.mkdir()
        (test_path / "template.json").write_text(
            """{
  "name": "test",
  "version": "1.0.0",
  "description": "Test",
  "author": "test"
}"""
        )
        (test_path / "claude_instructions.md").write_text("# Test Template")

        # Should use legacy validator
        result = template_manager.validate_template_directory(test_path)

        # Should return validation result
        assert hasattr(result, "is_valid")
        assert result.is_valid  # Should pass basic validation


class TestTemplateManagerBackwardCompatibility:
    """Test backward compatibility of TemplateManager coordination."""

    def test_legacy_interface_preservation(self, temp_dir):
        """Test that all legacy interface methods are preserved and functional."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test legacy methods exist and are callable
        legacy_methods = [
            "get_template",
            "get_template_info",
            "get_templates_by_type",
            "render_template",
            "select_template_for_project",
            "render_batch",
            "render_all_templates",
        ]

        for method_name in legacy_methods:
            assert hasattr(template_manager, method_name)
            method = getattr(template_manager, method_name)
            assert callable(method)

    def test_get_template_returns_template_objects(self, temp_dir):
        """Test get_template returns Template objects for backward compatibility."""
        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Should return Template objects
        template = template_manager.get_template("test-template.md")
        assert hasattr(template, "render")
        assert hasattr(template, "name")
        assert hasattr(template, "content")

        # Template should be renderable
        rendered = template.render(project_name="TestProject")
        assert isinstance(rendered, str)
        assert "TestProject" in rendered or "test-template" in rendered.lower()

    def test_render_methods_functional(self, temp_dir):
        """Test template rendering methods work through coordination layer."""
        from claude_builder.core.template_manager import TemplateContext

        template_manager = TemplateManager(template_directory=str(temp_dir))

        # Test render_all_templates
        context = TemplateContext(
            project_name="TestProject", description="A test project"
        )

        all_rendered = template_manager.render_all_templates(context)
        assert isinstance(all_rendered, dict)
        assert len(all_rendered) > 0

        # Test render_batch
        templates = {
            "test1.md": "# {{ project_name }}",
            "test2.md": "## {{ description }}",
        }

        batch_rendered = template_manager.render_batch(templates, context)
        assert isinstance(batch_rendered, dict)
        assert "TestProject" in batch_rendered["test1.md"]
        assert "A test project" in batch_rendered["test2.md"]

    def test_config_parameter_compatibility(self, temp_dir):
        """Test configuration parameter handling maintains compatibility."""
        # Test various initialization patterns

        # With config dict
        config_dict = {"cache_enabled": True, "max_cache_size": 100}
        tm1 = TemplateManager(config=config_dict)
        assert tm1.config["cache_enabled"] is True

        # With template_directory parameter
        tm2 = TemplateManager(template_directory=str(temp_dir))
        assert str(temp_dir) in str(tm2.templates_dir)

        # With kwargs
        tm3 = TemplateManager(enable_caching=True, custom_option="value")
        assert tm3.config["enable_caching"] is True
        assert tm3.config["custom_option"] == "value"

        # Combined parameters
        tm4 = TemplateManager(
            config={"base": "value"}, template_directory=str(temp_dir), extra="param"
        )
        assert tm4.config["base"] == "value"
        assert tm4.config["extra"] == "param"
        assert str(temp_dir) in str(tm4.templates_dir)
