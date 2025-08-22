"""
Unit tests for validation utilities.

Tests the validation functions and classes including:
- Project structure validation
- Configuration validation
- File and path validation
- Data format validation
- Custom validation rules
"""

from pathlib import Path

from claude_builder.utils.validation import (
    ConfigValidator,
    DataValidator,
    PathValidator,
    ProjectValidator,
    ValidationError,
    ValidationResult,
)


class TestProjectValidator:
    """Test suite for ProjectValidator class."""

    def test_valid_python_project(self, sample_python_project):
        """Test validation of valid Python project."""
        validator = ProjectValidator()
        result = validator.validate_project(sample_python_project)

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.project_type == "python"

    def test_invalid_project_structure(self, temp_dir):
        """Test validation of invalid project structure."""
        # Create incomplete project
        (temp_dir / "random_file.txt").touch()

        validator = ProjectValidator()
        result = validator.validate_project(temp_dir)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.project_type == "unknown"

    def test_project_type_detection(self, sample_rust_project):
        """Test project type detection validation."""
        validator = ProjectValidator()
        result = validator.validate_project(sample_rust_project)

        assert result.is_valid
        assert result.project_type == "rust"
        assert "Cargo.toml" in result.detected_files


class TestConfigValidator:
    """Test suite for ConfigValidator class."""

    def test_valid_configuration(self):
        """Test validation of valid configuration."""
        validator = ConfigValidator()
        config = {
            "project": {"name": "test-project", "type": "python"},
            "analysis": {"depth": "standard"},
        }

        result = validator.validate_config(config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_configuration(self):
        """Test validation of invalid configuration."""
        validator = ConfigValidator()
        config = {
            "project": {
                "name": "",  # Invalid empty name
                "type": "invalid_type",  # Invalid type
            },
            "analysis": {"depth": "invalid_depth"},  # Invalid depth
        }

        result = validator.validate_config(config)
        assert not result.is_valid
        assert len(result.errors) >= 3


class TestPathValidator:
    """Test suite for PathValidator class."""

    def test_valid_paths(self, temp_dir):
        """Test validation of valid paths."""
        validator = PathValidator()

        # Create test files
        test_file = temp_dir / "test.txt"
        test_file.touch()

        assert validator.is_valid_file(test_file)
        assert validator.is_valid_directory(temp_dir)
        assert validator.is_readable(test_file)
        assert validator.is_writable(temp_dir)

    def test_invalid_paths(self):
        """Test validation of invalid paths."""
        validator = PathValidator()

        invalid_file = Path("/nonexistent/file.txt")
        invalid_dir = Path("/nonexistent/directory")

        assert not validator.is_valid_file(invalid_file)
        assert not validator.is_valid_directory(invalid_dir)
        assert not validator.is_readable(invalid_file)


class TestDataValidator:
    """Test suite for DataValidator class."""

    def test_validate_project_name(self):
        """Test project name validation."""
        validator = DataValidator()

        # Valid names
        assert validator.validate_project_name("my-project")
        assert validator.validate_project_name("my_project")
        assert validator.validate_project_name("MyProject")

        # Invalid names
        assert not validator.validate_project_name("")
        assert not validator.validate_project_name("my project")  # spaces
        assert not validator.validate_project_name("123project")  # starts with number

    def test_validate_version_string(self):
        """Test version string validation."""
        validator = DataValidator()

        # Valid versions
        assert validator.validate_version("1.0.0")
        assert validator.validate_version("2.1.3-alpha")
        assert validator.validate_version("0.1.0-beta.1")

        # Invalid versions
        assert not validator.validate_version("")
        assert not validator.validate_version("1.0")
        assert not validator.validate_version("invalid")

    def test_validate_email(self):
        """Test email validation."""
        validator = DataValidator()

        # Valid emails
        assert validator.validate_email("user@example.com")
        assert validator.validate_email("test.email+tag@domain.co.uk")

        # Invalid emails
        assert not validator.validate_email("")
        assert not validator.validate_email("invalid-email")
        assert not validator.validate_email("user@")


class TestValidationResult:
    """Test suite for ValidationResult class."""

    def test_successful_validation(self):
        """Test successful validation result."""
        result = ValidationResult(is_valid=True, errors=[], warnings=["Minor warning"])

        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.has_warnings()
        assert not result.has_errors()

    def test_failed_validation(self):
        """Test failed validation result."""
        errors = [
            ValidationError("Field 'name' is required"),
            ValidationError("Invalid project type"),
        ]

        result = ValidationResult(is_valid=False, errors=errors, warnings=[])

        assert not result.is_valid
        assert len(result.errors) == 2
        assert result.has_errors()
        assert not result.has_warnings()


class TestValidationError:
    """Test suite for ValidationError class."""

    def test_error_creation(self):
        """Test validation error creation."""
        error = ValidationError(
            message="Required field missing",
            field="project.name",
            code="REQUIRED_FIELD",
        )

        assert error.message == "Required field missing"
        assert error.field == "project.name"
        assert error.code == "REQUIRED_FIELD"
        assert str(error) == "Required field missing"

    def test_error_with_context(self):
        """Test validation error with additional context."""
        error = ValidationError(
            message="Invalid value",
            field="project.type",
            code="INVALID_VALUE",
            context={
                "value": "invalid_type",
                "allowed": ["python", "rust", "javascript"],
            },
        )

        assert error.context["value"] == "invalid_type"
        assert "python" in error.context["allowed"]
