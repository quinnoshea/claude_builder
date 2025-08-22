"""
Unit tests for the core data models.

Tests the data model classes including:
- ProjectInfo model validation and serialization
- AnalysisResult model structure and properties
- Configuration models and defaults
- Model relationships and dependencies
- Serialization and deserialization
"""

from datetime import datetime

import pytest

from claude_builder.core.models import (
    AnalysisResult,
    DependencyInfo,
    FileStructure,
    GenerationConfig,
    ProjectInfo,
)
from claude_builder.core.models import (
    TestFrameworkInfo as FrameworkInfo,  # Use test-compatible version
)


class TestProjectInfo:
    """Test suite for ProjectInfo model."""

    def test_project_info_minimal(self):
        """Test ProjectInfo creation with minimal required fields."""
        project = ProjectInfo(
            name="test-project",
            project_type="python"
        )

        assert project.name == "test-project"
        assert project.project_type == "python"
        assert project.framework is None
        assert project.description is None
        assert project.version is None

    def test_project_info_complete(self):
        """Test ProjectInfo creation with all fields."""
        project = ProjectInfo(
            name="complete-project",
            project_type="rust",
            framework="axum",
            description="A complete test project",
            version="1.0.0",
            language_version="1.70.0",
            main_directory="src"
        )

        assert project.name == "complete-project"
        assert project.project_type == "rust"
        assert project.framework == "axum"
        assert project.description == "A complete test project"
        assert project.version == "1.0.0"
        assert project.language_version == "1.70.0"
        assert project.main_directory == "src"

    def test_project_info_validation_empty_name(self):
        """Test ProjectInfo validation with empty name."""
        with pytest.raises(ValueError):
            ProjectInfo(name="", project_type="python")

    def test_project_info_validation_invalid_type(self):
        """Test ProjectInfo validation with invalid project type."""
        with pytest.raises(ValueError):
            ProjectInfo(name="test", project_type="invalid-type")

    def test_project_info_serialization(self):
        """Test ProjectInfo serialization to dictionary."""
        project = ProjectInfo(
            name="serialize-test",
            project_type="javascript",
            framework="react",
            description="Test serialization"
        )

        data = project.dict()

        assert data["name"] == "serialize-test"
        assert data["project_type"] == "javascript"
        assert data["framework"] == "react"
        assert data["description"] == "Test serialization"

    def test_project_info_deserialization(self):
        """Test ProjectInfo deserialization from dictionary."""
        data = {
            "name": "deserialize-test",
            "project_type": "python",
            "framework": "fastapi",
            "description": "Test deserialization",
            "version": "0.1.0"
        }

        project = ProjectInfo(**data)

        assert project.name == "deserialize-test"
        assert project.project_type == "python"
        assert project.framework == "fastapi"
        assert project.description == "Test deserialization"
        assert project.version == "0.1.0"

    def test_project_info_equality(self):
        """Test ProjectInfo equality comparison."""
        project1 = ProjectInfo(name="test", project_type="python")
        project2 = ProjectInfo(name="test", project_type="python")
        project3 = ProjectInfo(name="different", project_type="python")

        assert project1 == project2
        assert project1 != project3

    def test_project_info_repr(self):
        """Test ProjectInfo string representation."""
        project = ProjectInfo(
            name="repr-test",
            project_type="rust",
            framework="clap"
        )

        repr_str = repr(project)
        assert "repr-test" in repr_str
        assert "rust" in repr_str
        assert "clap" in repr_str


class TestFrameworkInfo:
    """Test suite for FrameworkInfo model."""

    def test_framework_info_creation(self):
        """Test FrameworkInfo creation and properties."""
        framework = FrameworkInfo(
            name="fastapi",
            version="0.100.0",
            category="web",
            description="Modern web framework"
        )

        assert framework.name == "fastapi"
        assert framework.version == "0.100.0"
        assert framework.category == "web"
        assert framework.description == "Modern web framework"

    def test_framework_info_minimal(self):
        """Test FrameworkInfo with minimal information."""
        framework = FrameworkInfo(name="click")

        assert framework.name == "click"
        assert framework.version is None
        assert framework.category is None
        assert framework.description is None


class TestDependencyInfo:
    """Test suite for DependencyInfo model."""

    def test_dependency_info_creation(self):
        """Test DependencyInfo creation and properties."""
        dependency = DependencyInfo(
            name="requests",
            version="2.31.0",
            dependency_type="runtime",
            source="pypi"
        )

        assert dependency.name == "requests"
        assert dependency.version == "2.31.0"
        assert dependency.dependency_type == "runtime"
        assert dependency.source == "pypi"

    def test_dependency_info_dev_dependency(self):
        """Test DependencyInfo for development dependency."""
        dependency = DependencyInfo(
            name="pytest",
            version="7.4.0",
            dependency_type="development"
        )

        assert dependency.name == "pytest"
        assert dependency.dependency_type == "development"

    def test_dependency_info_validation(self):
        """Test DependencyInfo validation."""
        with pytest.raises(ValueError):
            DependencyInfo(name="", version="1.0.0")


class TestFileStructure:
    """Test suite for FileStructure model."""

    def test_file_structure_creation(self):
        """Test FileStructure creation and properties."""
        structure = FileStructure(
            path="src/main.py",
            file_type="file",
            size=1024,
            language="python"
        )

        assert structure.path == "src/main.py"
        assert structure.file_type == "file"
        assert structure.size == 1024
        assert structure.language == "python"

    def test_file_structure_directory(self):
        """Test FileStructure for directory."""
        structure = FileStructure(
            path="src/",
            file_type="directory",
            children=["main.py", "utils.py"]
        )

        assert structure.path == "src/"
        assert structure.file_type == "directory"
        assert "main.py" in structure.children
        assert "utils.py" in structure.children

    def test_file_structure_nested(self):
        """Test nested FileStructure creation."""
        root = FileStructure(
            path="project/",
            file_type="directory",
            children=[
                FileStructure(path="src/main.py", file_type="file", language="python"),
                FileStructure(path="tests/", file_type="directory", children=["test_main.py"])
            ]
        )

        assert root.file_type == "directory"
        assert len(root.children) == 2
        assert root.children[0].language == "python"
        assert root.children[1].file_type == "directory"


class TestAnalysisResult:
    """Test suite for AnalysisResult model."""

    def test_analysis_result_creation(self):
        """Test AnalysisResult creation with all components."""
        project_info = ProjectInfo(name="test", project_type="python", framework="fastapi")

        frameworks = [
            FrameworkInfo(name="fastapi", version="0.100.0", category="web")
        ]

        dependencies = [
            DependencyInfo(name="fastapi", version="0.100.0", dependency_type="runtime"),
            DependencyInfo(name="pytest", version="7.4.0", dependency_type="development")
        ]

        file_structure = FileStructure(
            path="project/",
            file_type="directory",
            children=[
                FileStructure(path="src/main.py", file_type="file", language="python")
            ]
        )

        result = AnalysisResult(
            project_info=project_info,
            frameworks=frameworks,
            dependencies=dependencies,
            file_structure=file_structure,
            analysis_timestamp=datetime.now()
        )

        assert result.project_info.name == "test"
        assert len(result.frameworks) == 1
        assert len(result.dependencies) == 2
        assert result.file_structure.file_type == "directory"
        assert result.analysis_timestamp is not None

    def test_analysis_result_minimal(self):
        """Test AnalysisResult with minimal information."""
        project_info = ProjectInfo(name="minimal", project_type="unknown")

        result = AnalysisResult(
            project_info=project_info,
            frameworks=[],
            dependencies=[],
            file_structure=FileStructure(path=".", file_type="directory")
        )

        assert result.project_info.name == "minimal"
        assert len(result.frameworks) == 0
        assert len(result.dependencies) == 0
        assert result.analysis_timestamp is not None  # Auto-generated

    def test_analysis_result_serialization(self):
        """Test AnalysisResult complete serialization."""
        project_info = ProjectInfo(name="serialize", project_type="python")
        frameworks = [FrameworkInfo(name="django")]
        dependencies = [DependencyInfo(name="django", version="4.2.0")]
        file_structure = FileStructure(path=".", file_type="directory")

        result = AnalysisResult(
            project_info=project_info,
            frameworks=frameworks,
            dependencies=dependencies,
            file_structure=file_structure
        )

        data = result.dict()

        assert data["project_info"]["name"] == "serialize"
        assert len(data["frameworks"]) == 1
        assert data["frameworks"][0]["name"] == "django"
        assert len(data["dependencies"]) == 1
        assert data["dependencies"][0]["name"] == "django"
        assert data["file_structure"]["file_type"] == "directory"

    def test_analysis_result_deserialization(self):
        """Test AnalysisResult deserialization from dictionary."""
        data = {
            "project_info": {
                "name": "deserialize",
                "project_type": "rust",
                "framework": "axum"
            },
            "frameworks": [
                {"name": "axum", "version": "0.6.0", "category": "web"}
            ],
            "dependencies": [
                {"name": "axum", "version": "0.6.0", "dependency_type": "runtime"},
                {"name": "tokio", "version": "1.29.0", "dependency_type": "runtime"}
            ],
            "file_structure": {
                "path": ".",
                "file_type": "directory",
                "children": []
            }
        }

        result = AnalysisResult(**data)

        assert result.project_info.name == "deserialize"
        assert result.project_info.project_type == "rust"
        assert len(result.frameworks) == 1
        assert result.frameworks[0].name == "axum"
        assert len(result.dependencies) == 2
        assert result.dependencies[1].name == "tokio"

    def test_analysis_result_filtering(self):
        """Test AnalysisResult filtering capabilities."""
        project_info = ProjectInfo(name="filter-test", project_type="python")

        dependencies = [
            DependencyInfo(name="fastapi", dependency_type="runtime"),
            DependencyInfo(name="pytest", dependency_type="development"),
            DependencyInfo(name="black", dependency_type="development")
        ]

        result = AnalysisResult(
            project_info=project_info,
            frameworks=[],
            dependencies=dependencies,
            file_structure=FileStructure(path=".", file_type="directory")
        )

        # Test filtering methods
        runtime_deps = [d for d in result.dependencies if d.dependency_type == "runtime"]
        dev_deps = [d for d in result.dependencies if d.dependency_type == "development"]

        assert len(runtime_deps) == 1
        assert runtime_deps[0].name == "fastapi"
        assert len(dev_deps) == 2
        assert "pytest" in [d.name for d in dev_deps]
        assert "black" in [d.name for d in dev_deps]


class TestGenerationConfig:
    """Test suite for GenerationConfig model."""

    def test_generation_config_defaults(self):
        """Test GenerationConfig default values."""
        config = GenerationConfig()

        assert config.output_format == "markdown"
        assert config.include_agents is True
        assert config.include_workflow is True
        assert config.template_variant == "comprehensive"
        assert config.create_zip is False

    def test_generation_config_custom(self):
        """Test GenerationConfig with custom values."""
        config = GenerationConfig(
            output_format="html",
            include_agents=False,
            include_workflow=False,
            template_variant="minimal",
            create_zip=True,
            output_directory="custom-output"
        )

        assert config.output_format == "html"
        assert config.include_agents is False
        assert config.include_workflow is False
        assert config.template_variant == "minimal"
        assert config.create_zip is True
        assert config.output_directory == "custom-output"

    def test_generation_config_validation(self):
        """Test GenerationConfig validation."""
        # Valid config should not raise
        config = GenerationConfig(output_format="markdown", template_variant="comprehensive")
        config.validate()

        # Invalid output format should raise
        with pytest.raises(ValueError):
            invalid_config = GenerationConfig(output_format="invalid")
            invalid_config.validate()

        # Invalid template variant should raise
        with pytest.raises(ValueError):
            invalid_config = GenerationConfig(template_variant="invalid")
            invalid_config.validate()

    def test_generation_config_serialization(self):
        """Test GenerationConfig serialization."""
        config = GenerationConfig(
            output_format="html",
            include_agents=False,
            template_variant="minimal"
        )

        data = config.dict()

        assert data["output_format"] == "html"
        assert data["include_agents"] is False
        assert data["template_variant"] == "minimal"
