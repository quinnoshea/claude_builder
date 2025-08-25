"""Comprehensive tests for CLI generate commands - targeting 50% coverage."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

try:
    import yaml
except ImportError:
    yaml = None

from click.testing import CliRunner

from claude_builder.cli.generate_commands import (
    _display_generation_preview,
    _load_analysis_from_file,
    _write_generated_files,
    agents,
    agents_md,
    claude_md,
    docs,
)


class TestGenerateCommandsComprehensive:
    """Comprehensive test coverage for generate CLI commands."""

    def test_generate_docs_command_basic(self):
        """Test docs command basic functionality."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            # Setup mocks
            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {
                "CLAUDE.md": "# Test Content",
                "README.md": "# README",
            }
            mock_content.template_info = ["base", "python"]
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(docs, [tmp_dir])
                assert result.exit_code == 0
                assert "Documentation generated successfully" in result.output

    def test_generate_docs_with_from_analysis(self):
        """Test docs command with existing analysis file."""
        with patch(
            "claude_builder.cli.generate_commands._load_analysis_from_file"
        ) as mock_load, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analysis = Mock()
            mock_load.return_value = mock_analysis

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"CLAUDE.md": "# Test Content"}
            mock_content.template_info = ["base"]
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                analysis_file = Path(tmp_dir) / "analysis.json"
                analysis_file.write_text("{}")

                result = runner.invoke(
                    docs, [tmp_dir, "--from-analysis", str(analysis_file)]
                )
                assert result.exit_code == 0
                mock_load.assert_called_once()

    def test_generate_docs_with_partial_sections(self):
        """Test docs command with partial section generation."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {
                "CLAUDE.md": "# CLAUDE Content",
                "AGENTS.md": "# Agent Content",
                "README.md": "# README Content",
            }
            mock_content.template_info = ["base"]
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(docs, [tmp_dir, "--partial", "claude,agents"])
                assert result.exit_code == 0

    def test_generate_docs_with_all_options(self):
        """Test docs command with all options."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class, patch(
            "claude_builder.cli.generate_commands._write_generated_files"
        ) as mock_write:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"CLAUDE.md": "# Test"}
            mock_content.template_info = ["base"]
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_dir = Path(tmp_dir) / "output"
                result = runner.invoke(
                    docs,
                    [
                        tmp_dir,
                        "--template",
                        "custom",
                        "--output-dir",
                        str(output_dir),
                        "--format",
                        "zip",
                        "--backup-existing",
                        "--verbose",
                        "--verbose",
                    ],
                )
                assert result.exit_code == 0
                mock_write.assert_called_once()

    def test_generate_docs_dry_run(self):
        """Test docs command in dry run mode."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class, patch(
            "claude_builder.cli.generate_commands._display_generation_preview"
        ) as mock_preview:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"CLAUDE.md": "# Test"}
            mock_content.template_info = ["base"]
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(docs, [tmp_dir, "--dry-run"])
                assert result.exit_code == 0
                assert "Dry run complete" in result.output
                mock_preview.assert_called_once()

    def test_generate_agents_command_basic(self):
        """Test agents command basic functionality."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.core.agents.UniversalAgentSystem"
        ) as mock_agent_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_agent_system = Mock()
            mock_agent_config = Mock()
            mock_agent_config.all_agents = ["agent1", "agent2"]
            mock_agent_config.core_agents = ["agent1"]
            mock_agent_config.domain_agents = ["agent2"]
            mock_agent_config.workflow_agents = []
            mock_agent_config.custom_agents = []
            mock_agent_system.select_agents.return_value = mock_agent_config
            mock_agent_class.return_value = mock_agent_system

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"AGENTS.md": "# Agent Config"}
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(agents, [tmp_dir])
                assert result.exit_code == 0

    def test_generate_agents_multiple_files(self):
        """Test agents command with multiple agent files."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.core.agents.UniversalAgentSystem"
        ) as mock_agent_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_agent_system = Mock()
            mock_agent_config = Mock()
            mock_agent_config.all_agents = ["agent1", "agent2"]
            mock_agent_config.core_agents = ["agent1"]
            mock_agent_config.domain_agents = ["agent2"]
            mock_agent_config.workflow_agents = []
            mock_agent_config.custom_agents = []
            mock_agent_system.select_agents.return_value = mock_agent_config
            mock_agent_class.return_value = mock_agent_system

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {
                "AGENTS.md": "# Main Config",
                "agents/core.md": "# Core Agents",
                "agents/domain.md": "# Domain Agents",
            }
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(agents, [tmp_dir])
                assert result.exit_code == 0

    def test_claude_md_command_comprehensive(self):
        """Test claude_md command with comprehensive options."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"CLAUDE.md": "# Comprehensive CLAUDE.md Content"}
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_file = Path(tmp_dir) / "custom_claude.md"
                result = runner.invoke(
                    claude_md,
                    [
                        tmp_dir,
                        "--template",
                        "advanced",
                        "--output-file",
                        str(output_file),
                        "--verbose",
                    ],
                )
                assert result.exit_code == 0

    def test_claude_md_no_content_generated(self):
        """Test claude_md when no CLAUDE.md content is generated."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"README.md": "# No CLAUDE.md here"}
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(claude_md, [tmp_dir])
                assert result.exit_code == 0
                assert "Failed to generate CLAUDE.md content" in result.output

    def test_agents_md_command_comprehensive(self):
        """Test agents_md command with comprehensive options."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.core.agents.UniversalAgentSystem"
        ) as mock_agent_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_agent_system = Mock()
            mock_agent_config = Mock()
            mock_agent_config.all_agents = ["agent1", "agent2", "agent3"]
            mock_agent_config.core_agents = ["agent1"]
            mock_agent_config.domain_agents = ["agent2"]
            mock_agent_config.workflow_agents = ["agent3"]
            mock_agent_config.custom_agents = []
            mock_agent_system.select_agents.return_value = mock_agent_config
            mock_agent_class.return_value = mock_agent_system

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"AGENTS.md": "# Comprehensive Agent Configuration"}
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                agents_dir = Path(tmp_dir) / "custom_agents"
                output_file = Path(tmp_dir) / "custom_agents.md"
                result = runner.invoke(
                    agents_md,
                    [
                        tmp_dir,
                        "--agents-dir",
                        str(agents_dir),
                        "--output-file",
                        str(output_file),
                        "--verbose",
                    ],
                )
                assert result.exit_code == 0

    def test_agents_md_no_content_generated(self):
        """Test agents_md when no AGENTS.md content is generated."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class, patch(
            "claude_builder.core.agents.UniversalAgentSystem"
        ) as mock_agent_class, patch(
            "claude_builder.cli.generate_commands.DocumentGenerator"
        ) as mock_generator_class:

            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            mock_agent_system = Mock()
            mock_agent_config = Mock()
            mock_agent_config.all_agents = []
            mock_agent_config.core_agents = []
            mock_agent_config.domain_agents = []
            mock_agent_config.workflow_agents = []
            mock_agent_config.custom_agents = []
            mock_agent_system.select_agents.return_value = mock_agent_config
            mock_agent_class.return_value = mock_agent_system

            mock_generator = Mock()
            mock_content = Mock()
            mock_content.files = {"README.md": "# No AGENTS.md here"}
            mock_generator.generate.return_value = mock_content
            mock_generator_class.return_value = mock_generator

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(agents_md, [tmp_dir])
                assert result.exit_code == 0
                assert "Failed to generate AGENTS.md content" in result.output


class TestGenerateHelperFunctions:
    """Test generate command helper functions."""

    def test_load_analysis_from_json_file(self):
        """Test loading analysis from JSON file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test analysis JSON
            analysis_data = {
                "project_path": tmp_dir,
                "analysis_confidence": 0.95,
                "analysis_timestamp": "2024-01-01T00:00:00",
                "analyzer_version": "1.0.0",
                "language_info": {
                    "primary": "python",
                    "secondary": ["javascript"],
                    "confidence": 0.9,
                    "file_counts": {"py": 10, "js": 5},
                    "total_lines": {"py": 1000, "js": 200},
                },
                "framework_info": {
                    "primary": "fastapi",
                    "secondary": ["react"],
                    "confidence": 0.8,
                    "version": "0.68.0",
                    "config_files": ["pyproject.toml"],
                },
                "domain_info": {
                    "domain": "web_api",
                    "confidence": 0.85,
                    "indicators": ["api", "web"],
                    "specialized_patterns": ["rest"],
                },
                "project_type": "web_api",
                "complexity_level": "medium",
                "architecture_pattern": "mvc",
                "development_environment": {
                    "package_managers": ["pip"],
                    "testing_frameworks": ["pytest"],
                    "linting_tools": ["ruff"],
                    "ci_cd_systems": ["github_actions"],
                    "containerization": ["docker"],
                    "databases": ["postgresql"],
                    "documentation_tools": ["sphinx"],
                },
                "filesystem_info": {
                    "total_files": 100,
                    "total_directories": 20,
                    "source_files": 50,
                    "test_files": 25,
                    "config_files": 10,
                    "documentation_files": 5,
                    "asset_files": 10,
                    "ignore_patterns": [".pyc", "__pycache__"],
                    "root_files": ["README.md", "pyproject.toml"],
                },
                "warnings": ["Large codebase", "Complex dependencies"],
                "suggestions": ["Add more tests", "Improve documentation"],
            }

            analysis_file = Path(tmp_dir) / "analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis_data, f)

            # Test loading
            result = _load_analysis_from_file(analysis_file)
            assert result.language_info.primary == "python"
            assert result.framework_info.primary == "fastapi"
            assert result.analysis_confidence == 0.95

    def test_load_analysis_from_yaml_file(self):
        """Test loading analysis from YAML file."""
        if yaml is None:
            # Skip if YAML not available
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test analysis YAML
            analysis_data = {
                "project_path": tmp_dir,
                "analysis_confidence": 0.9,
                "language_info": {"primary": "rust", "confidence": 0.95},
                "framework_info": {"primary": "axum", "confidence": 0.8},
                "project_type": "cli",
                "complexity_level": "simple",
                "architecture_pattern": "unknown",
            }

            analysis_file = Path(tmp_dir) / "analysis.yaml"
            with open(analysis_file, "w") as f:
                yaml.safe_dump(analysis_data, f)

            # Test loading
            result = _load_analysis_from_file(analysis_file)
            assert result.language_info.primary == "rust"
            assert result.framework_info.primary == "axum"

    def test_load_analysis_invalid_enum_values(self):
        """Test loading analysis with invalid enum values."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_data = {
                "project_path": tmp_dir,
                "project_type": "invalid_type",
                "complexity_level": "invalid_complexity",
                "architecture_pattern": "invalid_pattern",
            }

            analysis_file = Path(tmp_dir) / "analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis_data, f)

            # Should handle invalid enums gracefully
            result = _load_analysis_from_file(analysis_file)
            assert result.project_type.value == "unknown"
            assert result.complexity_level.value == "simple"
            assert result.architecture_pattern.value == "unknown"

    def test_load_analysis_file_not_found(self):
        """Test loading analysis from non-existent file."""
        from claude_builder.utils.exceptions import ClaudeBuilderError

        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_file = Path(tmp_dir) / "nonexistent.json"

            try:
                _load_analysis_from_file(analysis_file)
                assert False, "Expected ClaudeBuilderError"
            except ClaudeBuilderError as e:
                assert "Failed to load analysis" in str(e)

    def test_load_analysis_invalid_json(self):
        """Test loading analysis from invalid JSON file."""
        from claude_builder.utils.exceptions import ClaudeBuilderError

        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_file = Path(tmp_dir) / "invalid.json"
            analysis_file.write_text("{ invalid json")

            try:
                _load_analysis_from_file(analysis_file)
                assert False, "Expected ClaudeBuilderError"
            except ClaudeBuilderError as e:
                assert "Failed to load analysis" in str(e)

    def test_display_generation_preview(self):
        """Test generation preview display."""
        mock_content = Mock()
        mock_content.files = {
            "CLAUDE.md": "# Test content with some length",
            "AGENTS.md": "# Agent configuration content",
            "README.md": "# README content",
        }
        mock_content.template_info = ["base", "python", "fastapi"]

        mock_analysis = Mock()

        with patch("claude_builder.cli.generate_commands.console") as mock_console:
            _display_generation_preview(mock_content, mock_analysis)
            mock_console.print.assert_called()

    def test_write_generated_files_basic(self):
        """Test writing generated files."""
        mock_content = Mock()
        mock_content.files = {
            "CLAUDE.md": "# CLAUDE content",
            "AGENTS.md": "# Agent content",
            "docs/README.md": "# Documentation",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            _write_generated_files(
                mock_content, output_path, backup_existing=False, verbose=0
            )

            # Check files were created
            assert (output_path / "CLAUDE.md").exists()
            assert (output_path / "AGENTS.md").exists()
            assert (output_path / "docs" / "README.md").exists()

    def test_write_generated_files_with_backup(self):
        """Test writing generated files with backup."""
        mock_content = Mock()
        mock_content.files = {"CLAUDE.md": "# New content"}

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            # Create existing file
            existing_file = output_path / "CLAUDE.md"
            existing_file.write_text("# Existing content")

            _write_generated_files(
                mock_content, output_path, backup_existing=True, verbose=1
            )

            # Check backup was created
            backup_file = output_path / "CLAUDE.md.bak"
            assert backup_file.exists()
            assert backup_file.read_text() == "# Existing content"

            # Check new content was written
            assert existing_file.read_text() == "# New content"

    def test_write_generated_files_verbose(self):
        """Test writing generated files with verbose output."""
        mock_content = Mock()
        mock_content.files = {
            "file1.md": "Content 1",
            "file2.md": "Content 2",
            "file3.md": "Content 3",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            with patch("claude_builder.cli.generate_commands.console") as mock_console:
                _write_generated_files(
                    mock_content, output_path, backup_existing=False, verbose=2
                )
                # Should print individual file confirmations
                assert mock_console.print.call_count >= 3


class TestGenerateCommandsErrorHandling:
    """Test error handling in generate commands."""

    def test_docs_command_exception(self):
        """Test docs command exception handling."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(docs, [tmp_dir])
                assert result.exit_code != 0
                assert "Error generating documentation" in result.output

    def test_agents_command_exception(self):
        """Test agents command exception handling."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(agents, [tmp_dir])
                assert result.exit_code != 0
                assert "Error generating agents" in result.output

    def test_claude_md_command_exception(self):
        """Test claude_md command exception handling."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(claude_md, [tmp_dir])
                assert result.exit_code != 0
                assert "Error generating CLAUDE.md" in result.output

    def test_agents_md_command_exception(self):
        """Test agents_md command exception handling."""
        with patch(
            "claude_builder.cli.generate_commands.ProjectAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = runner.invoke(agents_md, [tmp_dir])
                assert result.exit_code != 0
                assert "Error generating AGENTS.md" in result.output

    def test_docs_command_with_from_analysis_error(self):
        """Test docs command with analysis loading error."""
        with patch(
            "claude_builder.cli.generate_commands._load_analysis_from_file"
        ) as mock_load:
            from claude_builder.utils.exceptions import ClaudeBuilderError

            mock_load.side_effect = ClaudeBuilderError("Failed to load analysis")

            runner = CliRunner()
            with tempfile.TemporaryDirectory() as tmp_dir:
                analysis_file = Path(tmp_dir) / "analysis.json"
                analysis_file.write_text("{}")

                result = runner.invoke(
                    docs, [tmp_dir, "--from-analysis", str(analysis_file)]
                )
                assert result.exit_code != 0

    def test_yaml_import_error_handling(self):
        """Test YAML import error handling in analysis loading."""
        from claude_builder.utils.exceptions import ClaudeBuilderError

        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_file = Path(tmp_dir) / "analysis.yaml"
            analysis_file.write_text("project_path: test")

            # This should raise ClaudeBuilderError since yaml import fails in the function
            try:
                _load_analysis_from_file(analysis_file)
                assert False, "Expected ClaudeBuilderError"
            except ClaudeBuilderError as e:
                assert "Failed to load analysis" in str(e)
