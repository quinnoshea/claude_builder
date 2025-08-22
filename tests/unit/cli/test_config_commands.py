"""Tests for CLI config commands."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.config_commands import (
    config,
    init,
    reset,
    set_value,
    show,
    validate,
)


class TestConfigCommands:
    """Test config CLI commands."""

    def test_config_command_group(self):
        """Test config command group exists."""
        runner = CliRunner()
        result = runner.invoke(config, ["--help"])
        assert result.exit_code == 0
        assert "Manage claude-builder configurations" in result.output

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_init_command(self, mock_config_class, sample_python_project):
        """Test config init command."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(init, [str(sample_python_project)])
        assert result.exit_code == 0
        assert (
            "Configuration created successfully" in result.output
            or "initialized" in result.output.lower()
        )

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_init_command_with_format(
        self, mock_config_class, sample_python_project
    ):
        """Test config init command with format option."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(init, [str(sample_python_project), "--format", "toml"])
        assert result.exit_code == 0

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_show_command(self, mock_config_class, sample_python_project):
        """Test config show command."""
        mock_config = Mock()
        config_data = {
            "project": {"name": "test-project", "type": "python"},
            "generation": {"templates": ["base", "python"]},
            "agents": {"enabled": True},
        }
        mock_config.load_config.return_value = config_data
        mock_config._config_to_dict.return_value = config_data
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project), "--format", "json"])
        assert result.exit_code == 0
        assert "project" in result.output

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_show_command_json_format(
        self, mock_config_class, sample_python_project
    ):
        """Test config show command with JSON format."""
        mock_config = Mock()
        test_config = {"project": {"name": "test-project", "type": "python"}}
        mock_config.load_config.return_value = test_config
        mock_config._config_to_dict.return_value = test_config
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project), "--format", "json"])
        assert result.exit_code == 0
        # Should contain JSON output
        assert "{" in result.output and "}" in result.output

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_show_command_specific_section(
        self, mock_config_class, sample_python_project
    ):
        """Test config show command for specific section."""
        mock_config = Mock()
        config_data = {
            "project": {"name": "test-project", "type": "python"},
            "generation": {"templates": ["base", "python"]},
        }
        mock_config.load_config.return_value = config_data
        mock_config._config_to_dict.return_value = config_data
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            show,
            [str(sample_python_project), "--section", "project", "--format", "json"],
        )
        assert result.exit_code == 0
        assert "project" in result.output

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_set_command(self, mock_config_class, sample_python_project):
        """Test config set command."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            set_value, ["project.name", "new-project-name", str(sample_python_project)]
        )
        assert result.exit_code == 0
        assert "Set project.name" in result.output or "updated" in result.output.lower()

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_set_command_json_value(
        self, mock_config_class, sample_python_project
    ):
        """Test config set command with JSON value."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            set_value,
            ["agents.custom", '["agent1", "agent2"]', str(sample_python_project)],
        )
        assert result.exit_code == 0

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_validate_command_valid(
        self, mock_config_class, sample_python_project
    ):
        """Test config validate command with valid config."""
        mock_config = Mock()
        mock_config.validate_config.return_value = (True, [])
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(validate, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✓" in result.output

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_validate_command_invalid(
        self, mock_config_class, sample_python_project
    ):
        """Test config validate command with invalid config."""
        from claude_builder.utils.exceptions import ConfigError

        mock_config = Mock()
        mock_config._load_config_file.side_effect = ConfigError(
            "Missing required field: project.name"
        )
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(validate, [str(sample_python_project)])
        assert result.exit_code != 0
        assert (
            "validation failed" in result.output.lower()
            or "error" in result.output.lower()
        )

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_reset_command(self, mock_config_class, sample_python_project):
        """Test config reset command."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(reset, [str(sample_python_project), "--force"])
        assert result.exit_code == 0
        assert (
            "reset" in result.output.lower() or "configuration" in result.output.lower()
        )

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_reset_command_with_force(
        self, mock_config_class, sample_python_project
    ):
        """Test config reset command with force option."""
        mock_config = Mock()
        mock_config.create_default_config.return_value = True
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(reset, [str(sample_python_project), "--force"])
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

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_show_no_config_file(self, mock_config_class, sample_python_project):
        """Test config show command when no config file exists."""
        mock_config = Mock()
        mock_config.load_config.side_effect = FileNotFoundError("Config file not found")
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project)])
        assert result.exit_code != 0
        assert (
            "Config file not found" in result.output
            or "not found" in result.output.lower()
        )

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_set_invalid_key(self, mock_config_class, sample_python_project):
        """Test config set command with invalid key."""
        mock_config = Mock()
        mock_config.set_config_value.return_value = False
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            set_value, [str(sample_python_project), "invalid..key", "value"]
        )
        assert result.exit_code != 0

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_exception_handling(self, mock_config_class, sample_python_project):
        """Test config command exception handling."""
        mock_config = Mock()
        mock_config.load_config.side_effect = Exception("Configuration error")
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "error" in result.output.lower()

    @patch("claude_builder.cli.config_commands.ConfigManager")
    def test_config_show_yaml_format(self, mock_config_class, sample_python_project):
        """Test config show command with YAML format."""
        mock_config = Mock()
        test_config = {"project": {"name": "test"}}
        mock_config.load_config.return_value = test_config
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(show, [str(sample_python_project), "--format", "yaml"])
        # Should handle YAML format (or fallback gracefully)
        assert result.exit_code == 0
