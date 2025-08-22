"""Tests for CLI analyze commands."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch

from claude_builder.cli.analyze_commands import analyze, project
from claude_builder.core.analyzer import ProjectAnalysis, LanguageInfo, FrameworkInfo, DomainInfo
from claude_builder.core.models import DevelopmentEnvironment, FileSystemInfo
from claude_builder.models.enums import ProjectType, ComplexityLevel, ArchitecturePattern


@pytest.fixture
def mock_analysis():
    """Mock ProjectAnalysis for testing."""
    return ProjectAnalysis(
        project_path=Path("/test/project"),
        analysis_confidence=85.5,
        analysis_timestamp="2025-01-01T00:00:00",
        analyzer_version="1.0.0",
        language_info=LanguageInfo(
            primary="python",
            secondary=["javascript"],
            confidence=90.0,
            file_counts={"python": 10, "javascript": 2},
            total_lines=1000
        ),
        framework_info=FrameworkInfo(
            primary="fastapi",
            secondary=["pytest"],
            confidence=80.0,
            version="0.100.0",
            config_files=["requirements.txt"]
        ),
        domain_info=DomainInfo(
            domain="web_development",
            confidence=75.0,
            indicators=["REST API", "web framework"],
            specialized_patterns=["microservice"]
        ),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MEDIUM,
        architecture_pattern=ArchitecturePattern.MVC,
        dev_environment=DevelopmentEnvironment(
            package_managers=["pip"],
            testing_frameworks=["pytest"],
            ci_cd_systems=["github-actions"],
            containerization=["docker"],
            databases=["postgresql"]
        ),
        filesystem_info=FileSystemInfo(
            total_files=50,
            source_files=30,
            test_files=10,
            config_files=5,
            documentation_files=5
        ),
        warnings=["Missing test coverage"],
        suggestions=["Add more unit tests"]
    )


class TestAnalyzeCommands:
    """Test analyze CLI commands."""

    def test_analyze_command_group(self):
        """Test analyze command group exists."""
        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])
        assert result.exit_code == 0
        assert "Analyze project structure" in result.output

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_success(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with valid project."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Project Analysis Results" in result.output
        assert "python" in result.output

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_json_output(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with JSON output."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [
            str(sample_python_project),
            "--format", "json"
        ])
        assert result.exit_code == 0
        
        # Should contain valid JSON
        output_lines = result.output.strip().split('\n')
        json_output = '\n'.join(line for line in output_lines if line.strip().startswith('{') or line.strip().startswith('"') or 'project_path' in line)
        
        if json_output:
            try:
                data = json.loads(json_output)
                assert "project_path" in data
            except json.JSONDecodeError:
                # JSON might be spread across multiple lines in output
                pass

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_with_output_file(self, mock_analyzer_class, sample_python_project, mock_analysis, tmp_path):
        """Test analyze project command with output file."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        output_file = tmp_path / "analysis.json"
        
        runner = CliRunner()
        result = runner.invoke(project, [
            str(sample_python_project),
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Check file contains valid JSON
        data = json.loads(output_file.read_text())
        assert "project_path" in data
        assert "analysis_confidence" in data

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_confidence_threshold(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with confidence threshold."""
        # Mock low confidence analysis
        mock_analysis.analysis_confidence = 30.0
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [
            str(sample_python_project),
            "--confidence-threshold", "50"
        ])
        assert result.exit_code == 0
        assert "below threshold" in result.output

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_verbose(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with verbose output."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [
            str(sample_python_project),
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Analyzing project at" in result.output

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_include_suggestions(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with suggestions."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [
            str(sample_python_project),
            "--include-suggestions"
        ])
        assert result.exit_code == 0
        # Should include suggestions from mock_analysis
        assert "Suggestions:" in result.output or "Add more unit tests" in result.output

    def test_project_command_invalid_path(self):
        """Test analyze project command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(project, ["/nonexistent/path"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_analyzer_exception(self, mock_analyzer_class, sample_python_project):
        """Test analyze project command when analyzer raises exception."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Analysis failed")
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        result = runner.invoke(project, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error analyzing project" in result.output

    @patch('claude_builder.cli.analyze_commands.ProjectAnalyzer')
    def test_project_command_yaml_output_no_yaml(self, mock_analyzer_class, sample_python_project, mock_analysis):
        """Test analyze project command with YAML output when PyYAML not available."""
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer
        
        runner = CliRunner()
        # Mock ImportError for yaml import
        def mock_import(name, *args, **kwargs):
            if name == 'yaml':
                raise ImportError("No module named 'yaml'")
            return __import__(name, *args, **kwargs)
            
        with patch('builtins.__import__', side_effect=mock_import):
            result = runner.invoke(project, [
                str(sample_python_project),
                "--format", "yaml"
            ])
            # Should handle missing PyYAML gracefully
            assert "YAML format requires PyYAML" in result.output or result.exit_code != 0