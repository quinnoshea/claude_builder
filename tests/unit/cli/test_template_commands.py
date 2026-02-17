"""Tests for CLI template commands."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.template_commands import templates


class TestTemplateCommands:
    """Test template CLI commands."""

    def test_template_command_group(self):
        """Test template command group exists."""
        runner = CliRunner()
        result = runner.invoke(templates, ["--help"])
        assert result.exit_code == 0
        assert "Manage templates and template sources" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_list_templates_command(self, mock_template_manager_class):
        """Test templates list command."""
        mock_template_manager = Mock()

        # Create mock templates with proper structure
        mock_template1 = Mock()
        mock_template1.metadata.name = "base"
        mock_template1.metadata.version = "1.0"
        mock_template1.metadata.author = "Claude Builder"
        mock_template1.metadata.category = "Base"
        mock_template1.metadata.languages = ["Any"]
        mock_template1.metadata.description = "Base template"
        mock_template1.installed = True

        mock_template2 = Mock()
        mock_template2.metadata.name = "python"
        mock_template2.metadata.version = "1.2"
        mock_template2.metadata.author = "Claude Builder"
        mock_template2.metadata.category = "Language"
        mock_template2.metadata.languages = ["Python"]
        mock_template2.metadata.description = "Python project template"
        mock_template2.installed = False

        mock_template_manager.list_available_templates.return_value = [
            mock_template1,
            mock_template2,
        ]
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["list"])
        assert result.exit_code == 0
        assert "base" in result.output
        assert "python" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_list_templates_command_json_format(self, mock_template_manager_class):
        """Test templates list command with JSON format."""
        mock_template_manager = Mock()

        # Create mock template with proper structure for JSON
        mock_template = Mock()
        mock_template.id = "base-template"
        mock_template.installed = True
        mock_template.metadata.to_dict.return_value = {
            "name": "base",
            "version": "1.0",
            "description": "Base template",
            "author": "Claude Builder",
            "category": "Base",
            "languages": ["Any"],
        }

        mock_template_manager.list_available_templates.return_value = [mock_template]
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["list", "--format", "json"])
        assert result.exit_code == 0
        assert "base" in result.output
        assert "base-template" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_list_templates_command_filter_category(self, mock_template_manager_class):
        """Test templates list command with category filter."""
        mock_template_manager = Mock()

        # Create mock template with proper structure
        mock_template = Mock()
        mock_template.metadata.name = "python-web"
        mock_template.metadata.version = "1.0"
        mock_template.metadata.author = "Claude Builder"
        mock_template.metadata.category = "language"  # This will be filtered
        mock_template.metadata.languages = ["Python"]
        mock_template.metadata.description = "Python web template"
        mock_template.installed = False

        mock_template_manager.list_available_templates.return_value = [mock_template]
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["list", "--category", "language"])
        assert result.exit_code == 0
        assert "python-web" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_show_template_command(self, mock_template_manager_class):
        """Test templates show command."""
        mock_template_manager = Mock()

        # Create mock template with proper metadata structure
        mock_template = Mock()
        mock_template.installed = True
        mock_template.id = "python-template"
        mock_template.metadata.name = "python"
        mock_template.metadata.version = "1.2"
        mock_template.metadata.description = "Python project template"
        mock_template.metadata.category = "language"
        mock_template.metadata.author = "Claude Builder Team"
        mock_template.metadata.license = "MIT"
        mock_template.metadata.languages = ["Python"]
        mock_template.metadata.frameworks = ["Django", "FastAPI"]
        mock_template.metadata.project_types = ["Web", "API"]
        mock_template.metadata.tags = ["python", "web"]
        mock_template.metadata.homepage = None
        mock_template.metadata.repository = None
        mock_template.metadata.created = None
        mock_template.metadata.updated = None

        mock_template_manager.get_template_info.return_value = mock_template
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["info", "python"])
        assert result.exit_code == 0
        assert "python" in result.output
        assert "Python project template" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_show_template_command_with_content(self, mock_template_manager_class):
        """Test templates info command with template that has content."""
        mock_template_manager = Mock()

        # Create proper mock template structure matching CLI expectations
        mock_template = Mock()
        mock_template.installed = True
        mock_template.id = "python-template"
        mock_template.metadata.name = "python"
        mock_template.metadata.version = "1.2"
        mock_template.metadata.description = "Python template"
        mock_template.metadata.author = "Claude Builder"
        mock_template.metadata.category = "language"
        mock_template.metadata.license = "MIT"
        mock_template.metadata.languages = ["Python"]
        mock_template.metadata.frameworks = ["Django", "FastAPI"]
        mock_template.metadata.project_types = ["Web", "API"]
        mock_template.metadata.tags = ["python", "web"]
        mock_template.metadata.homepage = None
        mock_template.metadata.repository = None
        mock_template.metadata.created = None
        mock_template.metadata.updated = None

        mock_template_manager.get_template_info.return_value = mock_template
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["info", "python"])
        assert result.exit_code == 0
        assert "python" in result.output
        assert "Python template" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_install_template_command(self, mock_template_manager_class):
        """Test templates install command."""
        mock_template_manager = Mock()

        # Create proper mock result structure matching CLI expectations
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template installed successfully"]
        mock_result.errors = []

        mock_template_manager.install_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        # Use input parameter to simulate user confirmation for non-official templates
        result = runner.invoke(
            templates, ["install", "community/django-rest"], input="y\n"
        )
        assert result.exit_code == 0
        assert "installed successfully" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_install_template_command_with_version(self, mock_template_manager_class):
        """Test templates install command.

        Note: --version option doesn't exist in actual CLI.
        """
        mock_template_manager = Mock()

        # Create proper mock result structure
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template installed successfully"]
        mock_result.errors = []

        mock_template_manager.install_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        # Install command doesn't have --version option, just install template ID
        result = runner.invoke(templates, ["install", "community/fastapi"], input="y\n")
        assert result.exit_code == 0
        assert "installed successfully" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_install_template_command_force(self, mock_template_manager_class):
        """Test templates install command with force option."""
        mock_template_manager = Mock()

        # Create proper mock result structure
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = [
            "Template installed successfully with force overwrite"
        ]
        mock_result.errors = []

        mock_template_manager.install_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(
            templates, ["install", "python-advanced", "--force"], input="y\n"
        )
        assert result.exit_code == 0
        assert "installed successfully" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_create_template_empty_scaffold(self, mock_template_manager_class):
        """Test templates create without --project-path."""
        mock_template_manager = Mock()
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template scaffold created"]
        mock_result.warnings = []
        mock_result.errors = []
        mock_template_manager.create_custom_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["create", "my-template"])
        assert result.exit_code == 0
        assert "not yet implemented" not in result.output.lower()
        assert "created successfully" in result.output
        mock_template_manager.create_custom_template.assert_called_once()

        call_args = mock_template_manager.create_custom_template.call_args.args
        assert call_args[0] == "my-template"
        assert isinstance(call_args[1], Path)
        assert call_args[2]["name"] == "my-template"
        assert call_args[2]["source_project"] is None

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_create_template_from_project_includes_source(
        self, mock_template_manager_class
    ):
        """Test templates create with --project-path includes source_project metadata."""
        mock_template_manager = Mock()
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template created"]
        mock_result.warnings = []
        mock_result.errors = []
        mock_template_manager.create_custom_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            project_dir = Path("sample_project")
            project_dir.mkdir()

            result = runner.invoke(
                templates, ["create", "my-template", "--project-path", str(project_dir)]
            )
            assert result.exit_code == 0
            mock_template_manager.create_custom_template.assert_called_once()

            call_args = mock_template_manager.create_custom_template.call_args.args
            assert call_args[0] == "my-template"
            assert call_args[1] == project_dir.resolve()
            assert call_args[2]["source_project"] == str(project_dir.resolve())

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_uninstall_template_command(self, mock_template_manager_class):
        """Test templates uninstall command."""
        mock_template_manager = Mock()

        # Mock template info to show it's installed
        mock_template = Mock()
        mock_template.installed = True
        mock_template_manager.get_template_info.return_value = mock_template

        # Mock uninstall result
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template uninstalled successfully"]
        mock_result.errors = []

        mock_template_manager.uninstall_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        # Provide confirmation input
        result = runner.invoke(templates, ["uninstall", "old-template"], input="y\n")
        assert result.exit_code == 0
        assert "uninstalled successfully" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_uninstall_template_command_with_confirmation(
        self, mock_template_manager_class
    ):
        """Test templates uninstall command with force option."""
        mock_template_manager = Mock()

        # Mock template info to show it's installed
        mock_template = Mock()
        mock_template.installed = True
        mock_template_manager.get_template_info.return_value = mock_template

        # Mock uninstall result with proper structure
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.suggestions = ["Template uninstalled successfully"]
        mock_result.errors = []

        mock_template_manager.uninstall_template.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["uninstall", "old-template", "--force"])
        assert result.exit_code == 0
        assert "uninstalled successfully" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_validate_template_command_valid(self, mock_template_manager_class):
        """Test templates validate command with valid template directory."""
        mock_template_manager = Mock()

        # Create proper validation result structure
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.suggestions = []

        mock_template_manager.validate_template_directory.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a test template directory
            import os

            os.makedirs("test_template")
            result = runner.invoke(templates, ["validate", "test_template"])
            assert result.exit_code == 0
            assert "valid" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_validate_template_command_invalid(self, mock_template_manager_class):
        """Test templates validate command with invalid template."""
        mock_template_manager = Mock()
        mock_template_manager.validate_template.return_value = Mock(
            is_valid=False,
            template_name="broken-template",
            validation_errors=[
                "Missing required metadata",
                "Invalid syntax in template",
            ],
            validation_warnings=["Deprecated variable usage"],
        )
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["validate", "broken-template"])
        assert result.exit_code != 0

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_show_template_not_found(self, mock_template_manager_class):
        """Test templates info command with non-existent template."""
        mock_template_manager = Mock()
        mock_template_manager.get_template_info.return_value = None
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["info", "nonexistent"])
        # Info command returns normally but shows "not found" message
        assert result.exit_code == 0
        assert "not found" in result.output

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_install_template_failure(self, mock_template_manager_class):
        """Test templates install command when installation fails."""
        mock_template_manager = Mock()
        mock_template_manager.install_template.return_value = Mock(
            success=False, error_message="Template repository not accessible"
        )
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["install", "invalid/template"])
        assert result.exit_code != 0

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_template_command_exception_handling(self, mock_template_manager_class):
        """Test template command exception handling."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.side_effect = Exception(
            "Template manager error"
        )
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["list"])
        assert result.exit_code != 0

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_list_templates_empty_result(self, mock_template_manager_class):
        """Test templates list command with no templates available."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.return_value = []
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        result = runner.invoke(templates, ["list"])
        assert result.exit_code == 0

    @patch("claude_builder.cli.template_commands.TemplateManager")
    def test_validate_template_with_warnings_only(self, mock_template_manager_class):
        """Test templates validate command with warnings but no errors."""
        mock_template_manager = Mock()

        # Create proper validation result with warnings
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.errors = []
        mock_result.warnings = [
            "Deprecated syntax used",
            "Consider updating variable names",
        ]
        mock_result.suggestions = []

        mock_template_manager.validate_template_directory.return_value = mock_result
        mock_template_manager_class.return_value = mock_template_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a test template directory
            import os

            os.makedirs("test_template")
            result = runner.invoke(templates, ["validate", "test_template"])
            assert result.exit_code == 0  # Valid with warnings
            assert "warnings" in result.output.lower()
            assert "Deprecated syntax" in result.output
