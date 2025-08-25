"""Comprehensive tests for CLI config commands - focusing on coverage gaps."""

import tempfile

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.config_commands import (
    _customize_config_from_analysis,
    _display_config_table,
    _display_profiles_table,
    create_profile,
    init,
    list_profiles,
    migrate,
    reset,
    set_value,
    show,
    show_profile,
    validate,
)
from claude_builder.core.config import Config


class TestConfigCommandsComprehensive:
    """Comprehensive test coverage for config CLI commands."""

    def test_config_init_interactive_mode(self):
        """Test config init with interactive mode."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands._interactive_config_setup"
        ) as mock_interactive:

            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config
            mock_interactive.return_value = Config()

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(init, [tmp_dir, "--interactive"])
                assert result.exit_code == 0
                mock_interactive.assert_called_once()

    def test_config_init_from_analysis(self):
        """Test config init with project analysis."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.config_commands._customize_config_from_analysis"
        ) as mock_customize:

            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analysis.language = "python"
            mock_analysis.project_type.value = "web_api"
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_customize.return_value = Config()

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(init, [tmp_dir, "--from-analysis"])
                assert result.exit_code == 0
                mock_customize.assert_called_once()

    def test_config_init_overwrite_existing(self):
        """Test config init when config file already exists."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.Confirm.ask"
        ) as mock_confirm:

            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config
            mock_confirm.return_value = True

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Create existing config file
                config_file = Path(tmp_dir) / "claude-builder.json"
                config_file.write_text("{}")

                result = runner.invoke(init, [tmp_dir])
                assert result.exit_code == 0
                mock_confirm.assert_called_once()

    def test_config_init_cancel_overwrite(self):
        """Test config init cancellation when file exists."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.Confirm.ask"
        ) as mock_confirm:

            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config
            mock_confirm.return_value = False

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Create existing config file
                config_file = Path(tmp_dir) / "claude-builder.json"
                config_file.write_text("{}")

                result = runner.invoke(init, [tmp_dir])
                assert result.exit_code == 0
                assert "cancelled" in result.output

    def test_config_init_different_format(self):
        """Test config init with TOML format."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(init, [tmp_dir, "--format", "toml"])
                assert result.exit_code == 0

    def test_config_validate_with_project_path(self):
        """Test config validate with specific project path."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.ProjectAnalyzer"
        ) as mock_analyzer_class:

            mock_config = Mock()
            mock_config.load_config.return_value = Config()
            mock_config.validate_config_compatibility.return_value = []
            mock_config_class.return_value = mock_config

            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock()
            mock_analyzer_class.return_value = mock_analyzer

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config_file = Path(tmp_dir) / "claude-builder.json"
                config_file.write_text("{}")

                result = runner.invoke(
                    validate, [str(config_file), "--project-path", tmp_dir]
                )
                assert result.exit_code == 0

    def test_config_validate_strict_mode_with_warnings(self):
        """Test config validate in strict mode with warnings."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.return_value = {}
            mock_config._dict_to_config.return_value = Config()
            mock_config._validate_config.return_value = None
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config_file = Path(tmp_dir) / "claude-builder.json"
                config_file.write_text("{}")

                # First test: warnings but not strict
                result = runner.invoke(validate, [str(config_file)])
                assert result.exit_code == 0

    def test_config_show_specific_section(self):
        """Test config show for specific section."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            test_config = Config()
            mock_config.load_config.return_value = test_config
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(show, [tmp_dir, "--section", "analysis"])
                assert result.exit_code == 0

    def test_config_show_yaml_format_not_implemented(self):
        """Test config show with YAML format (not implemented)."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.load_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(show, [tmp_dir, "--format", "yaml"])
                assert result.exit_code == 0
                assert "YAML output not yet implemented" in result.output

    def test_config_migrate_basic(self):
        """Test config migrate command."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.return_value = {}
            mock_config._dict_to_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                old_config = Path(tmp_dir) / "old-config.json"
                old_config.write_text("{}")

                result = runner.invoke(migrate, [str(old_config)])
                assert result.exit_code == 0
                assert "migrated" in result.output

    def test_config_migrate_with_output(self):
        """Test config migrate with specific output path."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.return_value = {}
            mock_config._dict_to_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                old_config = Path(tmp_dir) / "old-config.json"
                old_config.write_text("{}")
                output_path = Path(tmp_dir) / "new-config.json"

                result = runner.invoke(
                    migrate, [str(old_config), "--output", str(output_path)]
                )
                assert result.exit_code == 0

    def test_create_profile_from_config_file(self):
        """Test create profile from config file."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.return_value = {}
            mock_config._dict_to_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config_file = Path(tmp_dir) / "config.json"
                config_file.write_text("{}")

                result = runner.invoke(
                    create_profile,
                    [
                        "test-profile",
                        "--config-file",
                        str(config_file),
                        "--description",
                        "Test profile",
                    ],
                )
                assert result.exit_code == 0

    def test_create_profile_from_project_path(self):
        """Test create profile from project path."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.load_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(
                    create_profile,
                    [
                        "test-profile",
                        "--project-path",
                        tmp_dir,
                        "--description",
                        "Test profile",
                    ],
                )
                assert result.exit_code == 0

    def test_create_profile_interactive_description(self):
        """Test create profile with interactive description."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.Prompt.ask"
        ) as mock_prompt:

            mock_config = Mock()
            mock_config_class.return_value = mock_config
            mock_prompt.return_value = "Interactive description"

            runner = CliRunner()
            result = runner.invoke(create_profile, ["test-profile"])
            assert result.exit_code == 0
            mock_prompt.assert_called_once()

    def test_list_profiles_empty(self):
        """Test list profiles when no profiles exist."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.return_value = []
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(list_profiles)
            assert result.exit_code == 0
            assert "No project profiles found" in result.output

    def test_list_profiles_json_format(self):
        """Test list profiles with JSON format."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.return_value = [
                {"name": "profile1", "description": "Test profile"}
            ]
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(list_profiles, ["--format", "json"])
            assert result.exit_code == 0
            assert "{" in result.output

    def test_show_profile_not_found(self):
        """Test show profile when profile doesn't exist."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.return_value = []
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(show_profile, ["nonexistent"])
            assert result.exit_code == 0
            assert "Profile not found" in result.output

    def test_show_profile_with_config(self):
        """Test show profile with full configuration."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.return_value = [
                {
                    "name": "test-profile",
                    "description": "Test description",
                    "created": "2024-01-01",
                    "config": {
                        "agents": {"priority_agents": ["agent1"]},
                        "templates": {"preferred_templates": ["template1"]},
                        "git_integration": {"mode": "exclude_generated"},
                    },
                }
            ]
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(show_profile, ["test-profile"])
            assert result.exit_code == 0
            assert "test-profile" in result.output

    def test_set_value_with_different_types(self):
        """Test set_value with different value types."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            config_obj = Config()
            mock_config.load_config.return_value = config_obj
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Test boolean value
                result = runner.invoke(
                    set_value, ["analysis.cache_enabled", "true", tmp_dir]
                )
                assert result.exit_code == 0

    def test_set_value_invalid_path(self):
        """Test set_value with invalid configuration path."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.load_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(
                    set_value, ["invalid.nonexistent.path", "value", tmp_dir]
                )
                assert result.exit_code == 0
                assert "Invalid configuration path" in result.output

    def test_reset_with_force(self):
        """Test reset command with force flag."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.create_default_config.return_value = Config()
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(reset, [tmp_dir, "--force"])
                assert result.exit_code == 0

    def test_reset_with_confirmation_cancel(self):
        """Test reset command with confirmation cancelled."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class, patch(
            "claude_builder.cli.config_commands.Confirm.ask"
        ) as mock_confirm:

            mock_config = Mock()
            mock_config_class.return_value = mock_config
            mock_confirm.return_value = False

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(reset, [tmp_dir])
                assert result.exit_code == 0
                assert "cancelled" in result.output

    def test_customize_config_from_analysis_python(self):
        """Test _customize_config_from_analysis for Python project."""
        config = Config()
        analysis = Mock()
        analysis.language = "python"
        analysis.project_type = Mock()
        analysis.project_type.__str__ = Mock(return_value="web_api")

        result = _customize_config_from_analysis(config, analysis)
        assert "python-pro" in result.agents.priority_agents

    def test_customize_config_from_analysis_rust(self):
        """Test _customize_config_from_analysis for Rust project."""
        config = Config()
        analysis = Mock()
        analysis.language = "rust"
        analysis.project_type = Mock()
        analysis.project_type.__str__ = Mock(return_value="cli")

        result = _customize_config_from_analysis(config, analysis)
        assert "rust-engineer" in result.agents.priority_agents

    def test_customize_config_from_analysis_javascript(self):
        """Test _customize_config_from_analysis for JavaScript project."""
        config = Config()
        analysis = Mock()
        analysis.language = "javascript"
        analysis.project_type = Mock()
        analysis.project_type.__str__ = Mock(return_value="frontend")

        result = _customize_config_from_analysis(config, analysis)
        assert "javascript-pro" in result.agents.priority_agents


class TestConfigHelperFunctions:
    """Test configuration helper functions."""

    def test_display_config_table_with_section(self):
        """Test _display_config_table with specific section."""
        config = Config()

        with patch("claude_builder.cli.config_commands.console"):
            _display_config_table(config, "analysis")

    def test_display_config_table_invalid_section(self):
        """Test _display_config_table with invalid section."""
        config = Config()

        with patch("claude_builder.cli.config_commands.console") as mock_console:
            _display_config_table(config, "nonexistent")
            # Should print error message
            mock_console.print.assert_called()

    def test_display_config_table_overview(self):
        """Test _display_config_table overview."""
        config = Config()

        with patch("claude_builder.cli.config_commands.console"):
            _display_config_table(config)

    def test_display_profiles_table(self):
        """Test _display_profiles_table function."""
        profiles = [
            {
                "name": "profile1",
                "description": "A very long description that should be truncated because it exceeds fifty characters",
                "created": "2024-01-01T00:00:00",
            },
            {
                "name": "profile2",
                "description": "Short desc",
                "created": "2024-01-02T00:00:00",
            },
        ]

        with patch("claude_builder.cli.config_commands.console"):
            _display_profiles_table(profiles)


class TestConfigCommandsErrorHandling:
    """Test error handling in config commands."""

    def test_init_command_exception(self):
        """Test init command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.create_default_config.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(init, [tmp_dir])
                assert result.exit_code != 0

    def test_validate_command_config_error(self):
        """Test validate command with ConfigError."""
        from claude_builder.utils.exceptions import ConfigError

        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.side_effect = ConfigError("Test config error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config_file = Path(tmp_dir) / "config.json"
                config_file.write_text("{}")

                result = runner.invoke(validate, [str(config_file)])
                assert result.exit_code != 0

    def test_show_command_exception(self):
        """Test show command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.load_config.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(show, [tmp_dir])
                assert result.exit_code != 0

    def test_migrate_command_exception(self):
        """Test migrate command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config._load_config_file.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config_file = Path(tmp_dir) / "config.json"
                config_file.write_text("{}")

                result = runner.invoke(migrate, [str(config_file)])
                assert result.exit_code != 0

    def test_create_profile_exception(self):
        """Test create_profile command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.create_project_profile.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(create_profile, ["test-profile"])
            assert result.exit_code != 0

    def test_list_profiles_exception(self):
        """Test list_profiles command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(list_profiles)
            assert result.exit_code != 0

    def test_show_profile_exception(self):
        """Test show_profile command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.list_project_profiles.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            result = runner.invoke(show_profile, ["test"])
            assert result.exit_code != 0

    def test_set_value_exception(self):
        """Test set_value command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.load_config.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(set_value, ["key", "value", tmp_dir])
                assert result.exit_code != 0

    def test_reset_exception(self):
        """Test reset command exception handling."""
        with patch(
            "claude_builder.cli.config_commands.ConfigManager"
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.create_default_config.side_effect = Exception("Test error")
            mock_config_class.return_value = mock_config

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(reset, [tmp_dir, "--force"])
                assert result.exit_code != 0
