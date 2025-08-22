"""Simple tests to boost models.py coverage."""

from pathlib import Path

from claude_builder.core.models import (
    ArchitecturePattern,
    ComplexityLevel,
    DevelopmentEnvironment,
    FileSystemInfo,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
)


def test_project_analysis_properties():
    """Test ProjectAnalysis property methods for coverage."""
    # Create minimal ProjectAnalysis instance
    analysis = ProjectAnalysis(
        project_path=Path("/test"),
        language_info=LanguageInfo(primary="python"),
        framework_info=FrameworkInfo(primary="fastapi"),
        filesystem_info=FileSystemInfo(test_files=5),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MEDIUM,
        architecture_pattern=ArchitecturePattern.MONOLITH
    )

    # Test property getters
    assert analysis.language == "python"
    assert analysis.framework == "fastapi"
    assert analysis.has_tests is True

    # Test with no tests
    analysis_no_tests = ProjectAnalysis(
        project_path=Path("/test"),
        filesystem_info=FileSystemInfo(test_files=0)
    )
    assert analysis_no_tests.has_tests is False


def test_language_info_creation():
    """Test LanguageInfo creation for coverage."""
    lang_info = LanguageInfo(primary="rust", confidence=95.0)
    assert lang_info.primary == "rust"
    assert lang_info.confidence == 95.0


def test_framework_info_creation():
    """Test FrameworkInfo creation for coverage."""
    framework_info = FrameworkInfo(primary="axum", confidence=80.0)
    assert framework_info.primary == "axum"
    assert framework_info.confidence == 80.0


def test_filesystem_info_creation():
    """Test FileSystemInfo creation for coverage."""
    fs_info = FileSystemInfo(total_files=100, test_files=20)
    assert fs_info.total_files == 100
    assert fs_info.test_files == 20


def test_project_analysis_additional_properties():
    """Test additional ProjectAnalysis properties for coverage."""
    # Test has_ci_cd property
    analysis_with_ci = ProjectAnalysis(
        project_path=Path("/test"),
        dev_environment=DevelopmentEnvironment(ci_cd_systems=["github_actions"])
    )
    assert analysis_with_ci.has_ci_cd is True

    # Test is_containerized property
    analysis_containerized = ProjectAnalysis(
        project_path=Path("/test"),
        dev_environment=DevelopmentEnvironment(containerization=["docker"])
    )
    assert analysis_containerized.is_containerized is True

    # Test is_web_project property
    web_analysis = ProjectAnalysis(
        project_path=Path("/test"),
        project_type=ProjectType.WEB_APPLICATION
    )
    assert web_analysis.is_web_project is True

    api_analysis = ProjectAnalysis(
        project_path=Path("/test"),
        project_type=ProjectType.API_SERVICE
    )
    assert api_analysis.is_web_project is True

    cli_analysis = ProjectAnalysis(
        project_path=Path("/test"),
        project_type=ProjectType.CLI_TOOL
    )
    assert cli_analysis.is_web_project is False
