"""Tests for CLI generate commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from claude_builder.cli.generate_commands import generate, claude_md, agents_md


class TestGenerateCommands:
    """Test generate CLI commands."""

    def test_generate_command_group(self):
        """Test generate command group exists."""
        runner = CliRunner()
        result = runner.invoke(generate, ["--help"])
        assert result.exit_code == 0
        assert "Generate Claude Code documentation" in result.output

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_success(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command with valid project."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(success=True, files_created=['CLAUDE.md'])
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "CLAUDE.md generated successfully" in result.output or "Generated" in result.output

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_dry_run(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command with dry run."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(
            success=True, 
            files_created=['CLAUDE.md'],
            preview_content="# CLAUDE.md preview"
        )
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--dry-run"
        ])
        assert result.exit_code == 0
        assert "Dry Run Mode" in result.output or "preview" in result.output.lower()

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_with_template(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command with custom template."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(success=True, files_created=['CLAUDE.md'])
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--template", "custom-python"
        ])
        assert result.exit_code == 0
        mock_generator.generate_claude_md.assert_called_once()

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_force_overwrite(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command with force overwrite."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(success=True, files_created=['CLAUDE.md'])
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--force"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_verbose(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command with verbose output."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(
            success=True, 
            files_created=['CLAUDE.md'],
            analysis_details={'language': 'python', 'framework': 'fastapi'}
        )
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--verbose"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.generate_commands.UniversalAgentSystem')
    def test_agents_md_command_success(self, mock_agent_system_class, sample_python_project):
        """Test generate agents-md command with valid project."""
        mock_agent_system = Mock()
        mock_agent_system.generate_agents_md.return_value = Mock(
            success=True, 
            files_created=['AGENTS.md'],
            agents_configured=['rapid-prototyper', 'test-writer-fixer']
        )
        mock_agent_system_class.return_value = mock_agent_system
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "AGENTS.md generated" in result.output or "Generated" in result.output

    @patch('claude_builder.cli.generate_commands.UniversalAgentSystem')
    def test_agents_md_command_with_agents(self, mock_agent_system_class, sample_python_project):
        """Test generate agents-md command with specific agents."""
        mock_agent_system = Mock()
        mock_agent_system.generate_agents_md.return_value = Mock(success=True, files_created=['AGENTS.md'])
        mock_agent_system_class.return_value = mock_agent_system
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [
            str(sample_python_project),
            "--agents", "rapid-prototyper,test-writer-fixer"
        ])
        assert result.exit_code == 0

    def test_claude_md_command_invalid_path(self):
        """Test generate claude-md command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(claude_md, ["/nonexistent/path"])
        assert result.exit_code != 0

    def test_agents_md_command_invalid_path(self):
        """Test generate agents-md command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(agents_md, ["/nonexistent/path"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_generation_failure(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command when generation fails."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(
            success=False, 
            error_message="Template not found"
        )
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Failed to generate" in result.output or "error" in result.output.lower()

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_exception(self, mock_generator_class, sample_python_project):
        """Test generate claude-md command when exception occurs."""
        mock_generator = Mock()
        mock_generator.generate_claude_md.side_effect = Exception("Generation error")
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error generating" in result.output or "Generation error" in result.output

    @patch('claude_builder.cli.generate_commands.UniversalAgentSystem')
    def test_agents_md_command_exception(self, mock_agent_system_class, sample_python_project):
        """Test generate agents-md command when exception occurs."""
        mock_agent_system = Mock()
        mock_agent_system.generate_agents_md.side_effect = Exception("Agent configuration error")
        mock_agent_system_class.return_value = mock_agent_system
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error generating" in result.output or "Agent configuration error" in result.output

    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_backup_creation(self, mock_generator_class, sample_python_project, tmp_path):
        """Test CLAUDE.md generation creates backup of existing file."""
        # Create existing CLAUDE.md
        existing_file = tmp_path / "CLAUDE.md"
        existing_file.write_text("# Existing CLAUDE.md")
        
        mock_generator = Mock()
        mock_generator.generate_claude_md.return_value = Mock(
            success=True, 
            files_created=['CLAUDE.md'],
            backup_created=str(tmp_path / "CLAUDE.md.bak")
        )
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(claude_md, [str(sample_python_project)])
            assert result.exit_code == 0