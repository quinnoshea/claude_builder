"""Tests for CLI config commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch
import json

from claude_builder.cli.config_commands import config, init, show, set_value, validate, reset


class TestConfigCommands:
    """Test config CLI commands."""

    def test_config_command_group(self):
        """Test config command group exists."""
        runner = CliRunner()
        result = runner.invoke(config, ["--help"])
        assert result.exit_code == 0
        assert "Configuration management" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_init_command(self, mock_config_class, sample_python_project):
        """Test config init command."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(init, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Configuration initialized" in result.output or "initialized" in result.output.lower()

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_init_command_with_template(self, mock_config_class, sample_python_project):
        """Test config init command with template."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(init, [
            str(sample_python_project),
            "--template", "python-web"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_show_command(self, mock_config_class, sample_python_project):
        """Test config show command."""
        mock_config = Mock()
        mock_config.load_config.return_value = {
            "project": {"name": "test-project", "type": "python"},
            "generation": {"templates": ["base", "python"]},
            "agents": {"enabled": True}
        }
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Configuration" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_show_command_json_format(self, mock_config_class, sample_python_project):
        """Test config show command with JSON format."""
        mock_config = Mock()
        test_config = {
            "project": {"name": "test-project", "type": "python"}
        }
        mock_config.load_config.return_value = test_config
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [
            str(sample_python_project),
            "--format", "json"
        ])
        assert result.exit_code == 0
        # Should contain JSON output
        assert "{" in result.output and "}" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_show_command_specific_key(self, mock_config_class, sample_python_project):
        """Test config show command for specific key."""
        mock_config = Mock()
        mock_config.get_config_value.return_value = "python"
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [
            str(sample_python_project),
            "--key", "project.type"
        ])
        assert result.exit_code == 0
        assert "python" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_set_command(self, mock_config_class, sample_python_project):
        """Test config set command."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(set_value, [
            str(sample_python_project),
            "project.name",
            "new-project-name"
        ])
        assert result.exit_code == 0
        assert "Configuration updated" in result.output or "updated" in result.output.lower()

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_set_command_json_value(self, mock_config_class, sample_python_project):
        """Test config set command with JSON value."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(set_value, [
            str(sample_python_project),
            "agents.custom",
            '["agent1", "agent2"]',
            "--type", "json"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_validate_command_valid(self, mock_config_class, sample_python_project):
        """Test config validate command with valid config."""
        mock_config = Mock()
        mock_config.validate_config.return_value = (True, [])
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(validate, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✓" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_validate_command_invalid(self, mock_config_class, sample_python_project):
        """Test config validate command with invalid config."""
        mock_config = Mock()
        mock_config.validate_config.return_value = (False, [
            "Missing required field: project.name",
            "Invalid template: nonexistent-template"
        ])
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(validate, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "validation errors" in result.output.lower() or "error" in result.output.lower()
        assert "Missing required field" in result.output

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_reset_command(self, mock_config_class, sample_python_project):
        """Test config reset command."""
        mock_config = Mock()
        mock_config.reset_config.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(reset, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "reset" in result.output.lower() or "restored" in result.output.lower()

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_reset_command_with_backup(self, mock_config_class, sample_python_project):
        """Test config reset command with backup creation."""
        mock_config = Mock()
        mock_config.reset_config.return_value = True
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(reset, [
            str(sample_python_project),
            "--create-backup"
        ])
        assert result.exit_code == 0

    def test_config_init_invalid_path(self):
        """Test config init command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(init, ["/nonexistent/path"])
        assert result.exit_code != 0

    def test_config_show_invalid_path(self):
        """Test config show command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(show, ["/nonexistent/path"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_show_no_config_file(self, mock_config_class, sample_python_project):
        """Test config show command when no config file exists."""
        mock_config = Mock()
        mock_config.load_config.side_effect = FileNotFoundError("Config file not found")
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Config file not found" in result.output or "not found" in result.output.lower()

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_set_invalid_key(self, mock_config_class, sample_python_project):
        """Test config set command with invalid key."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = False
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(set_value, [
            str(sample_python_project),
            "invalid..key",
            "value"
        ])
        assert result.exit_code != 0

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_exception_handling(self, mock_config_class, sample_python_project):
        """Test config command exception handling."""
        mock_config = Mock()
        mock_config.load_config.side_effect = Exception("Configuration error")
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "error" in result.output.lower()

    @patch('claude_builder.cli.config_commands.ConfigManager')
    def test_config_show_yaml_format(self, mock_config_class, sample_python_project):
        """Test config show command with YAML format."""
        mock_config = Mock()
        test_config = {"project": {"name": "test"}}
        mock_config.load_config.return_value = test_config
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(show, [
            str(sample_python_project),
            "--format", "yaml"
        ])
        # Should handle YAML format (or fallback gracefully)
        assert result.exit_code == 0