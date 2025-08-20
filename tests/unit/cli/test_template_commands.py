"""Tests for CLI template commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch
import json

from claude_builder.cli.template_commands import templates


class TestTemplateCommands:
    """Test template CLI commands."""

    def test_template_command_group(self):
        """Test template command group exists."""
        runner = CliRunner()
        result = runner.invoke(templates, ["--help"])
        assert result.exit_code == 0
        assert "Manage templates and template sources" in result.output

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_list_templates_command(self, mock_template_manager_class):
        """Test templates list command."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.return_value = [
            Mock(name="base", version="1.0", description="Base template"),
            Mock(name="python", version="1.2", description="Python project template"),
            Mock(name="react", version="2.0", description="React application template")
        ]
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['list'])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_list_templates_command_json_format(self, mock_template_manager_class):
        """Test templates list command with JSON format."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.return_value = [
            Mock(name="base", version="1.0", description="Base template", 
                 to_dict=lambda: {"name": "base", "version": "1.0", "description": "Base template"})
        ]
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['list', "--format", "json"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_list_templates_command_filter_category(self, mock_template_manager_class):
        """Test templates list command with category filter."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.return_value = [
            Mock(name="python-web", version="1.0", category="language", description="Python web template")
        ]
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['list', "--category", "language"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_show_template_command(self, mock_template_manager_class):
        """Test templates show command."""
        mock_template_manager = Mock()
        mock_template_manager.get_template_info.return_value = Mock(
            name="python",
            version="1.2",
            description="Python project template",
            category="language",
            author="Claude Builder Team",
            dependencies=["base"],
            variables=["project_name", "python_version"],
            files=["CLAUDE.md", "pyproject.toml"]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['info', "python"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_show_template_command_with_content(self, mock_template_manager_class):
        """Test templates show command with content preview."""
        mock_template_manager = Mock()
        mock_template_manager.get_template_info.return_value = Mock(
            name="python",
            version="1.2", 
            description="Python template",
            preview_content="# CLAUDE.md\n\nPython project template..."
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, [
            'info',
            "python",
            "--show-content"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_install_template_command(self, mock_template_manager_class):
        """Test templates install command."""
        mock_template_manager = Mock()
        mock_template_manager.install_template.return_value = Mock(
            success=True,
            template_name="community/django-rest",
            version="1.0",
            installed_files=["templates/django-rest.md"]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['install', "community/django-rest"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_install_template_command_with_version(self, mock_template_manager_class):
        """Test templates install command with specific version."""
        mock_template_manager = Mock()
        mock_template_manager.install_template.return_value = Mock(
            success=True,
            template_name="community/fastapi",
            version="2.1"
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, [
            'install',
            "community/fastapi",
            "--version", "2.1"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_install_template_command_force(self, mock_template_manager_class):
        """Test templates install command with force option."""
        mock_template_manager = Mock()
        mock_template_manager.install_template.return_value = Mock(
            success=True,
            template_name="python-advanced",
            overwritten=True
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, [
            'install',
            "python-advanced",
            "--force"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_uninstall_template_command(self, mock_template_manager_class):
        """Test templates uninstall command."""
        mock_template_manager = Mock()
        mock_template_manager.uninstall_template.return_value = Mock(
            success=True,
            template_name="old-template",
            removed_files=["templates/old-template.md"]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['uninstall', "old-template"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_uninstall_template_command_with_confirmation(self, mock_template_manager_class):
        """Test templates uninstall command with confirmation."""
        mock_template_manager = Mock()
        mock_template_manager.uninstall_template.return_value = Mock(success=True)
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, [
            'uninstall',
            "old-template",
            "--force"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_validate_template_command_valid(self, mock_template_manager_class):
        """Test templates validate command with valid template."""
        mock_template_manager = Mock()
        mock_template_manager.validate_template.return_value = Mock(
            is_valid=True,
            template_name="python",
            validation_errors=[],
            validation_warnings=[]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['validate', "python"])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_validate_template_command_invalid(self, mock_template_manager_class):
        """Test templates validate command with invalid template."""
        mock_template_manager = Mock()
        mock_template_manager.validate_template.return_value = Mock(
            is_valid=False,
            template_name="broken-template",
            validation_errors=["Missing required metadata", "Invalid syntax in template"],
            validation_warnings=["Deprecated variable usage"]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['validate', "broken-template"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_show_template_not_found(self, mock_template_manager_class):
        """Test templates show command with non-existent template."""
        mock_template_manager = Mock()
        mock_template_manager.get_template_info.return_value = None
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['info', "nonexistent"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_install_template_failure(self, mock_template_manager_class):
        """Test templates install command when installation fails."""
        mock_template_manager = Mock()
        mock_template_manager.install_template.return_value = Mock(
            success=False,
            error_message="Template repository not accessible"
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['install', "invalid/template"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_template_command_exception_handling(self, mock_template_manager_class):
        """Test template command exception handling."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.side_effect = Exception("Template manager error")
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['list'])
        assert result.exit_code != 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_list_templates_empty_result(self, mock_template_manager_class):
        """Test templates list command with no templates available."""
        mock_template_manager = Mock()
        mock_template_manager.list_available_templates.return_value = []
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['list'])
        assert result.exit_code == 0

    @patch('claude_builder.cli.template_commands.TemplateManager')
    def test_validate_template_with_warnings_only(self, mock_template_manager_class):
        """Test templates validate command with warnings but no errors."""
        mock_template_manager = Mock()
        mock_template_manager.validate_template.return_value = Mock(
            is_valid=True,
            template_name="python",
            validation_errors=[],
            validation_warnings=["Deprecated syntax used", "Consider updating variable names"]
        )
        mock_template_manager_class.return_value = mock_template_manager
        
        runner = CliRunner()
        result = runner.invoke(templates, ['validate', "python"])
        assert result.exit_code == 0  # Valid with warnings
        assert "warnings" in result.output.lower()
        assert "Deprecated syntax" in result.output