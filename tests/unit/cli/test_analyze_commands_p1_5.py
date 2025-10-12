"""P1.5 enhancements: tests for analyze CLI output sections."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.analyze_commands import project
from claude_builder.core.analyzer import (
    DomainInfo,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
)
from claude_builder.core.models import DevelopmentEnvironment, FileSystemInfo
from claude_builder.models.enums import (
    ArchitecturePattern,
    ComplexityLevel,
    ProjectType,
)


def _base_mock_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        project_path=Path("/test/project"),
        analysis_confidence=90.0,
        analysis_timestamp="2025-09-01T00:00:00",
        analyzer_version="1.0.0",
        language_info=LanguageInfo(primary="python", confidence=95.0),
        framework_info=FrameworkInfo(primary="fastapi", confidence=80.0),
        domain_info=DomainInfo(domain="web_development", confidence=70.0),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MODERATE,
        architecture_pattern=ArchitecturePattern.MVC,
        dev_environment=DevelopmentEnvironment(
            package_managers=["pip"],
            testing_frameworks=["pytest"],
            ci_cd_systems=["github_actions"],
            containerization=["docker"],
        ),
        filesystem_info=FileSystemInfo(total_files=1),
    )


@patch("claude_builder.cli.analyze_commands.ProjectAnalyzer")
def test_infrastructure_section_prints_when_tools_detected(
    mock_analyzer_class, tmp_path
):
    mock_analysis = _base_mock_analysis()
    # Inject new fields dynamically to simulate P1.4 analyzer support
    mock_analysis.dev_environment.infrastructure_as_code = ["terraform", "ansible"]
    mock_analysis.dev_environment.orchestration_tools = ["kubernetes", "helm"]
    mock_analysis.dev_environment.secrets_management = ["vault"]
    mock_analysis.dev_environment.observability = ["prometheus"]
    mock_analysis.dev_environment.security_tools = ["trivy"]

    mock_analyzer = Mock()
    mock_analyzer.analyze.return_value = mock_analysis
    mock_analyzer_class.return_value = mock_analyzer

    runner = CliRunner()
    result = runner.invoke(project, [str(tmp_path)])
    assert result.exit_code == 0
    assert "Infrastructure & Platform Details" in result.output
    assert "Infrastructure as Code" in result.output
    assert "Orchestration Platforms" in result.output


@patch("claude_builder.cli.analyze_commands.ProjectAnalyzer")
def test_mlops_section_prints_when_tools_detected(mock_analyzer_class, tmp_path):
    mock_analysis = _base_mock_analysis()
    mock_analysis.dev_environment.data_pipeline = ["airflow", "dbt"]
    mock_analysis.dev_environment.mlops_tools = ["mlflow", "dvc"]

    mock_analyzer = Mock()
    mock_analyzer.analyze.return_value = mock_analysis
    mock_analyzer_class.return_value = mock_analyzer

    runner = CliRunner()
    result = runner.invoke(project, [str(tmp_path)])
    assert result.exit_code == 0
    assert "MLOps & Data Pipeline Details" in result.output
    assert "Data Pipeline" in result.output
    assert "MLOps Tools" in result.output


@patch("claude_builder.cli.analyze_commands.ProjectAnalyzer")
def test_dev_environment_table_includes_new_rows(mock_analyzer_class, tmp_path):
    mock_analysis = _base_mock_analysis()
    mock_analysis.dev_environment.infrastructure_as_code = ["terraform"]
    mock_analysis.dev_environment.mlops_tools = ["mlflow"]

    mock_analyzer = Mock()
    mock_analyzer.analyze.return_value = mock_analysis
    mock_analyzer_class.return_value = mock_analyzer

    runner = CliRunner()
    result = runner.invoke(project, [str(tmp_path)])
    assert result.exit_code == 0
    assert "Development Environment" in result.output
    assert "Infrastructure as Code" in result.output
    assert "MLOps Tools" in result.output
