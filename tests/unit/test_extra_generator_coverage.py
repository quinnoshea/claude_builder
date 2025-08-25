"""Additional tests for core.generator module to boost coverage to 60%+."""

import tempfile

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_builder.core.generator import DocumentGenerator, TemplateLoader
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


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_analysis():
    """Create a sample ProjectAnalysis for testing."""
    analysis = ProjectAnalysis(
        project_path=Path("/test/project"),
        language_info=LanguageInfo(primary="python", confidence=95.0),
        framework_info=FrameworkInfo(primary="django", confidence=88.0),
        project_type=ProjectType.WEB_APPLICATION,
        complexity_level=ComplexityLevel.MODERATE,
        architecture_pattern=ArchitecturePattern.MVC,
        dev_environment=DevelopmentEnvironment(
            package_managers=["pip", "poetry"],
            testing_frameworks=["pytest"],
            ci_cd_systems=["github_actions"],
        ),
        filesystem_info=FileSystemInfo(total_files=150, source_files=85, test_files=25),
        analysis_confidence=91.5,
    )
    return analysis


def test_document_generator_basic_init():
    """Test DocumentGenerator basic initialization - covers __init__."""
    generator = DocumentGenerator()
    assert generator.config == {}
    assert hasattr(generator, "template_manager")
    assert hasattr(generator, "agent_system")


def test_document_generator_with_custom_config():
    """Test DocumentGenerator with custom config - covers config handling."""
    config = {"test_key": "test_value", "nested": {"key": "value"}}
    generator = DocumentGenerator(config=config)
    assert generator.config == config
    assert generator.config["test_key"] == "test_value"
    assert generator.config["nested"]["key"] == "value"


def test_create_template_variables_minimal_analysis():
    """Test _create_template_variables with minimal analysis - covers edge cases."""
    generator = DocumentGenerator()

    # Minimal analysis
    analysis = ProjectAnalysis(
        project_path=Path("/minimal"),
        language_info=LanguageInfo(primary=None),
        framework_info=FrameworkInfo(primary=None),
        project_type=ProjectType.UNKNOWN,
        complexity_level=ComplexityLevel.SIMPLE,
        architecture_pattern=ArchitecturePattern.UNKNOWN,
        filesystem_info=FileSystemInfo(total_files=1, source_files=0, test_files=0),
    )

    variables = generator._create_template_variables(analysis)

    # Check fallback values
    assert variables["project_name"] == "minimal"
    assert variables["language"] == "Unknown"
    assert variables["framework"] == "None"
    assert variables["has_tests"] == "No"
    assert variables["complexity"] == "Simple"
    assert "timestamp" in variables
    assert "date" in variables


def test_create_template_variables_without_dev_environment(sample_analysis):
    """Test _create_template_variables without dev environment - covers None handling."""
    generator = DocumentGenerator()

    # Remove dev environment
    sample_analysis.dev_environment = None

    variables = generator._create_template_variables(sample_analysis)

    # Should handle None gracefully
    assert "package_managers" in variables
    assert "testing_frameworks" in variables
    assert "ci_cd_systems" in variables


def test_get_template_info_basic():
    """Test _get_template_info basic functionality - covers template info."""
    with patch(
        "claude_builder.core.generator.CoreTemplateManager"
    ) as mock_template_manager:
        mock_manager = MagicMock()
        mock_manager.list_available_templates.return_value = ["template1", "template2"]
        mock_template_manager.return_value = mock_manager

        generator = DocumentGenerator()
        template_info = generator._get_template_info()

        assert template_info["templates_available"] == ["template1", "template2"]
        assert template_info["template_count"] == 2


def test_get_feature_workflow_template_basic():
    """Test _get_feature_workflow_template basic structure - covers workflow template."""
    generator = DocumentGenerator()
    template = generator._get_feature_workflow_template()

    assert "Feature Development Workflow" in template
    assert "Planning Phase" in template
    assert "Implementation Phase" in template
    assert "${project_name}" in template
    assert isinstance(template, str)
    assert len(template) > 100  # Should be substantial


def test_get_testing_workflow_template_basic():
    """Test _get_testing_workflow_template basic structure - covers testing workflow."""
    generator = DocumentGenerator()
    template = generator._get_testing_workflow_template()

    assert "Testing Workflow" in template
    assert "Unit Tests" in template
    assert "Integration Tests" in template
    assert "${project_name}" in template
    assert isinstance(template, str)
    assert len(template) > 100


def test_get_api_documentation_template_basic():
    """Test _get_api_documentation_template basic structure - covers API docs template."""
    generator = DocumentGenerator()
    template = generator._get_api_documentation_template()

    assert "API Design Documentation" in template
    assert "API Overview" in template
    assert "Endpoints" in template
    assert "${project_name}" in template
    assert isinstance(template, str)
    assert len(template) > 100


def test_get_default_claude_template_basic():
    """Test _get_default_claude_template basic structure - covers CLAUDE.md template."""
    generator = DocumentGenerator()
    template = generator._get_default_claude_template()

    assert "# CLAUDE.md" in template
    assert "Project Overview" in template
    assert "Development Commands" in template
    assert "${project_type}" in template
    assert "${language}" in template
    assert isinstance(template, str)
    assert len(template) > 200


def test_get_default_agents_template_basic():
    """Test _get_default_agents_template basic structure - covers AGENTS.md template."""
    generator = DocumentGenerator()
    template = generator._get_default_agents_template()

    assert "Claude Code Agents Configuration" in template
    assert "Recommended Agents for This Project" in template
    assert "Core Development Agents" in template
    assert "${project_name}" in template
    assert isinstance(template, str)
    assert len(template) > 200


def test_get_intelligent_agents_template_basic():
    """Test _get_intelligent_agents_template basic structure - covers intelligent agents template."""
    generator = DocumentGenerator()
    template = generator._get_intelligent_agents_template()

    assert "Intelligent Agent Configuration" in template
    assert "Project-Specific Agent Selection" in template
    assert "Intelligent Workflows" in template
    assert "${analysis_confidence}" in template
    assert isinstance(template, str)
    assert len(template) > 200


def test_get_default_architecture_template_basic():
    """Test _get_default_architecture_template basic structure - covers architecture template."""
    generator = DocumentGenerator()
    template = generator._get_default_architecture_template()

    assert "Architecture Documentation" in template
    assert "System Overview" in template
    assert "Technology Stack" in template
    assert "${project_type}" in template
    assert isinstance(template, str)
    assert len(template) > 200


def test_get_default_performance_template_basic():
    """Test _get_default_performance_template basic structure - covers performance template."""
    generator = DocumentGenerator()
    template = generator._get_default_performance_template()

    assert "Performance Guide" in template
    assert "Performance Targets" in template
    assert "Optimization Strategies" in template
    assert "${project_type}" in template
    assert isinstance(template, str)
    assert len(template) > 200


class TestTemplateLoaderAdditional:
    """Additional TemplateLoader tests to boost coverage."""

    def test_template_loader_basic_init(self):
        """Test TemplateLoader basic initialization - covers __init__."""
        loader = TemplateLoader()
        assert hasattr(loader, "template_manager")
        assert loader.template_manager is not None

    def test_load_templates_empty_list(self):
        """Test loading empty template list - covers edge case."""
        loader = TemplateLoader()
        result = loader.load_templates([])
        assert result == {}

    def test_validate_template_basic_valid(self):
        """Test validating a basic valid template - covers validation success."""
        loader = TemplateLoader()
        valid_template = "Hello ${name}, welcome to ${project}!"
        result = loader.validate_template(valid_template)
        assert result is True

    def test_validate_template_simple_text(self):
        """Test validating simple text without variables - covers simple case."""
        loader = TemplateLoader()
        simple_template = "This is just plain text."
        result = loader.validate_template(simple_template)
        assert result is True

    @patch("claude_builder.core.generator.CoreTemplateManager")
    def test_list_available_templates_empty(self, mock_template_manager):
        """Test listing templates when none available - covers empty case."""
        mock_manager = MagicMock()
        mock_manager.list_available_templates.return_value = []
        mock_template_manager.return_value = mock_manager

        loader = TemplateLoader()
        result = loader.list_available_templates()

        assert result == []
        mock_manager.list_available_templates.assert_called_once()
