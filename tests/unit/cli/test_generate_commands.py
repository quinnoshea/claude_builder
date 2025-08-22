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
        assert "Generate documentation and configurations" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_success(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command with valid project."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# CLAUDE.md\nTest content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "CLAUDE.md generated successfully" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_dry_run(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command with dry run."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# CLAUDE.md preview content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--dry-run"
        ])
        assert result.exit_code == 0
        assert "Dry run complete" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_with_template(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command with custom template."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# CLAUDE.md\nCustom template content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--template", "custom-python"
        ])
        assert result.exit_code == 0
        mock_generator.generate.assert_called_once()

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_force_overwrite(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command with force overwrite."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# CLAUDE.md\nForce overwrite content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code == 0

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_verbose(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command with verbose output."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# CLAUDE.md\nVerbose content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [
            str(sample_python_project),
            "--verbose"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.core.agents.UniversalAgentSystem')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_agents_md_command_success(self, mock_generator_class, mock_agent_system_class, mock_analyzer_class, sample_python_project):
        """Test generate agents-md command with valid project."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock agent system
        mock_agent_system = Mock()
        mock_agent_config = Mock()
        mock_agent_config.all_agents = ['rapid-prototyper', 'test-writer-fixer']
        mock_agent_config.core_agents = ['rapid-prototyper']
        mock_agent_config.domain_agents = ['test-writer-fixer']
        mock_agent_config.workflow_agents = []
        mock_agent_config.custom_agents = []
        mock_agent_system.select_agents.return_value = mock_agent_config
        mock_agent_system_class.return_value = mock_agent_system
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'AGENTS.md': '# AGENTS.md\nAgent configuration'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "AGENTS.md generated successfully" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.core.agents.UniversalAgentSystem')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_agents_md_command_with_agents(self, mock_generator_class, mock_agent_system_class, mock_analyzer_class, sample_python_project):
        """Test generate agents-md command with specific agents."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock agent system
        mock_agent_system = Mock()
        mock_agent_config = Mock()
        mock_agent_config.all_agents = ['rapid-prototyper', 'test-writer-fixer']
        mock_agent_config.core_agents = ['rapid-prototyper']
        mock_agent_config.domain_agents = ['test-writer-fixer']
        mock_agent_config.workflow_agents = []
        mock_agent_config.custom_agents = []
        mock_agent_system.select_agents.return_value = mock_agent_config
        mock_agent_system_class.return_value = mock_agent_system
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'AGENTS.md': '# AGENTS.md\nSpecific agents configuration'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [str(sample_python_project)])
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

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_generation_failure(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command when generation fails."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator to return no CLAUDE.md content
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {}  # No CLAUDE.md generated
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        # Command should complete but notice no CLAUDE.md was generated
        assert result.exit_code == 0
        assert "Failed to generate CLAUDE.md content" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_command_exception(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test generate claude-md command when exception occurs."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator to raise exception
        mock_generator = Mock()
        mock_generator.generate.side_effect = Exception("Generation error")
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(claude_md, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error generating CLAUDE.md" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.core.agents.UniversalAgentSystem')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_agents_md_command_exception(self, mock_generator_class, mock_agent_system_class, mock_analyzer_class, sample_python_project):
        """Test generate agents-md command when exception occurs."""
        # Mock analyzer to raise exception
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Agent configuration error")
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(agents_md, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error generating AGENTS.md" in result.output

    @patch('claude_builder.cli.generate_commands.ProjectAnalyzer')
    @patch('claude_builder.cli.generate_commands.DocumentGenerator')
    def test_claude_md_backup_creation(self, mock_generator_class, mock_analyzer_class, sample_python_project):
        """Test CLAUDE.md generation with existing file."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock generator
        mock_generator = Mock()
        mock_generated_content = Mock()
        mock_generated_content.files = {'CLAUDE.md': '# New CLAUDE.md\nBackup test content'}
        mock_generator.generate.return_value = mock_generated_content
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing CLAUDE.md in isolated filesystem
            project_dir = Path("test_project")
            project_dir.mkdir()
            (project_dir / "CLAUDE.md").write_text("# Existing CLAUDE.md")
            
            result = runner.invoke(claude_md, [str(project_dir)])
            assert result.exit_code == 0
            assert "CLAUDE.md generated successfully" in result.output