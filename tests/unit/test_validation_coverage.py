"""Comprehensive tests for utils.validation module to increase coverage."""

import pytest


pytestmark = pytest.mark.failing

import tempfile

from pathlib import Path
from unittest.mock import MagicMock, patch

from claude_builder.utils.validation import (
    ConfigValidator,
    DataValidator,
    PathValidator,
    ProjectValidator,
    ValidationError,
    ValidationResult,
    validate_config_file,
    validate_directory_structure,
    validate_output_directory,
    validate_project_path,
    validate_template_name,
)


def test_validation_result_post_init():
    """Test ValidationResult __post_init__ method - covers lines 18-21."""
    result = ValidationResult(is_valid=True)
    assert result.warnings == []
    assert result.suggestions == []

    # Test with None values
    result_none = ValidationResult(is_valid=False, warnings=None, suggestions=None)
    assert result_none.warnings == []
    assert result_none.suggestions == []


def test_validate_project_path_nonexistent():
    """Test validate_project_path with nonexistent path - covers lines 28-32."""
    nonexistent = Path("/nonexistent/path")
    result = validate_project_path(nonexistent)

    assert not result.is_valid
    assert "does not exist" in result.error


def test_validate_project_path_file_not_directory(temp_dir):
    """Test validate_project_path with file instead of directory - covers
    lines 35-39."""
    temp_file = temp_dir / "test_file.txt"
    temp_file.touch()

    result = validate_project_path(temp_file)

    assert not result.is_valid
    assert "not a directory" in result.error


def test_validate_project_path_no_read_permission():
    """Test validate_project_path with no read permissions - covers lines 42-46."""
    with patch("os.access", return_value=False):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = validate_project_path(temp_dir)
            assert not result.is_valid
            assert "No read permission" in result.error
        finally:
            temp_dir.rmdir()


def test_validate_project_path_empty_directory(temp_dir):
    """Test validate_project_path with empty directory - covers lines 52-54."""
    result = validate_project_path(temp_dir)

    assert result.is_valid
    assert "Directory is empty" in result.warnings
    assert "Ensure this is the correct project directory" in result.suggestions


def test_validate_project_path_with_project_files(temp_dir):
    """Test validate_project_path with common project files - covers lines 57-64."""
    # Create a package.json file
    (temp_dir / "package.json").touch()

    result = validate_project_path(temp_dir)

    assert result.is_valid
    # Should not have the "no project files" warning
    assert not any("No common project files" in w for w in result.warnings)


def test_validate_project_path_with_source_files(temp_dir):
    """Test validate_project_path with source files - covers lines 68-77."""
    # Create a Python source file
    (temp_dir / "main.py").touch()

    result = validate_project_path(temp_dir)

    assert result.is_valid
    # Should not have the "no source code" warning since we have a .py file
    assert not any("No common project files" in w for w in result.warnings)


def test_validate_project_path_no_source_files(temp_dir):
    """Test validate_project_path without source files - covers lines 75-77."""
    # Create a non-source file
    (temp_dir / "README.txt").touch()

    result = validate_project_path(temp_dir)

    assert result.is_valid
    assert "No common project files or source code detected" in result.warnings
    assert "Verify this is a software project directory" in result.suggestions


def test_validate_project_path_large_directory(temp_dir):
    """Test validate_project_path with large directory - covers lines 80-87."""
    with patch("pathlib.Path.rglob") as mock_rglob:
        # Mock a large number of files
        mock_files = [MagicMock(is_file=lambda: True) for _ in range(15000)]
        mock_rglob.return_value = mock_files

        result = validate_project_path(temp_dir)

        assert result.is_valid
        assert any("Large project detected" in w for w in result.warnings)
        assert any("Analysis may take longer" in s for s in result.suggestions)


def test_validate_project_path_oserror_during_file_count(temp_dir):
    """Test validate_project_path with OSError during file count - covers
    lines 85-87."""
    with patch("pathlib.Path.rglob", side_effect=OSError("Permission denied")):
        result = validate_project_path(temp_dir)

        assert result.is_valid
        # Should not crash and continue normally


def test_validate_project_path_with_git(temp_dir):
    """Test validate_project_path with git repository - covers lines 90-91."""
    (temp_dir / ".git").mkdir()

    result = validate_project_path(temp_dir)

    assert result.is_valid
    # Should not suggest initializing git since .git exists
    assert not any("Initialize git repository" in s for s in result.suggestions)


def test_validate_project_path_without_git(temp_dir):
    """Test validate_project_path without git repository - covers lines 90-91."""
    result = validate_project_path(temp_dir)

    assert result.is_valid
    assert (
        "Initialize git repository for better project management" in result.suggestions
    )


def test_validate_template_name_empty():
    """Test validate_template_name with empty name - covers lines 102-106."""
    result = validate_template_name("")

    assert not result.is_valid
    assert "cannot be empty" in result.error


def test_validate_template_name_invalid_characters():
    """Test validate_template_name with invalid characters - covers lines 109-113."""
    result = validate_template_name("invalid@name")

    assert not result.is_valid
    assert "can only contain letters, numbers, hyphens, and underscores" in result.error


def test_validate_template_name_valid():
    """Test validate_template_name with valid name - covers line 115."""
    result = validate_template_name("valid-template_name123")

    assert result.is_valid


def test_validate_config_file_nonexistent(temp_dir):
    """Test validate_config_file with nonexistent file - covers lines 120-124."""
    nonexistent = temp_dir / "nonexistent.json"
    result = validate_config_file(nonexistent)

    assert not result.is_valid
    assert "not found" in result.error


def test_validate_config_file_directory_not_file(temp_dir):
    """Test validate_config_file with directory - covers lines 126-130."""
    subdir = temp_dir / "config_dir"
    subdir.mkdir()

    result = validate_config_file(subdir)

    assert not result.is_valid
    assert "not a file" in result.error


def test_validate_config_file_invalid_extension(temp_dir):
    """Test validate_config_file with invalid extension - covers lines 134-138."""
    invalid_file = temp_dir / "config.txt"
    invalid_file.touch()

    result = validate_config_file(invalid_file)

    assert not result.is_valid
    assert "must have .json or .toml extension" in result.error


def test_validate_config_file_no_read_permission(temp_dir):
    """Test validate_config_file without read permission - covers lines 141-145."""
    config_file = temp_dir / "config.json"
    config_file.touch()

    with patch("os.access", return_value=False):
        result = validate_config_file(config_file)

        assert not result.is_valid
        assert "No read permission" in result.error


def test_validate_config_file_valid(temp_dir):
    """Test validate_config_file with valid file - covers line 147."""
    config_file = temp_dir / "config.json"
    config_file.touch()

    result = validate_config_file(config_file)

    assert result.is_valid


def test_validate_output_directory_nonexistent_no_create(temp_dir):
    """Test validate_output_directory with nonexistent dir, no create - covers
    lines 152, 161-165."""
    nonexistent = temp_dir / "nonexistent"
    result = validate_output_directory(nonexistent, create_if_missing=False)

    assert not result.is_valid
    assert "does not exist" in result.error


def test_validate_output_directory_create_success(temp_dir):
    """Test validate_output_directory with successful creation - covers
    lines 153-156."""
    new_dir = temp_dir / "new_output_dir"
    result = validate_output_directory(new_dir, create_if_missing=True)

    assert result.is_valid
    assert new_dir.exists()


def test_validate_output_directory_create_failure():
    """Test validate_output_directory with creation failure - covers lines 156-160."""
    with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
        nonexistent = Path("/nonexistent/path")
        result = validate_output_directory(nonexistent, create_if_missing=True)

        assert not result.is_valid
        assert "Cannot create output directory" in result.error


def test_validate_output_directory_file_not_directory(temp_dir):
    """Test validate_output_directory with file - covers lines 167-171."""
    temp_file = temp_dir / "output_file.txt"
    temp_file.touch()

    result = validate_output_directory(temp_file)

    assert not result.is_valid
    assert "not a directory" in result.error


def test_validate_output_directory_no_write_permission(temp_dir):
    """Test validate_output_directory without write permission - covers
    lines 174-178."""
    with patch("os.access", return_value=False):
        result = validate_output_directory(temp_dir)

        assert not result.is_valid
        assert "No write permission" in result.error


def test_validate_output_directory_valid(temp_dir):
    """Test validate_output_directory with valid directory - covers line 180."""
    result = validate_output_directory(temp_dir)

    assert result.is_valid


def test_validate_directory_structure_nonexistent():
    """Test validate_directory_structure with nonexistent directory - covers
    lines 193-197."""
    nonexistent = Path("/nonexistent/path")
    result = validate_directory_structure(nonexistent, {})

    assert not result.is_valid
    assert "does not exist" in result.error


def test_validate_directory_structure_file_not_directory(temp_dir):
    """Test validate_directory_structure with file - covers lines 199-203."""
    temp_file = temp_dir / "test_file.txt"
    temp_file.touch()

    result = validate_directory_structure(temp_file, {})

    assert not result.is_valid
    assert "not a directory" in result.error


def test_validate_directory_structure_missing_directory(temp_dir):
    """Test validate_directory_structure with missing directory - covers
    lines 214-216."""
    expected_structure = {"src": {"main.py": True}}

    result = validate_directory_structure(temp_dir, expected_structure)

    assert result.is_valid  # Still valid, just with warnings
    assert "Missing directory: src" in result.warnings
    assert any("Create directory:" in s for s in result.suggestions)


def test_validate_directory_structure_file_instead_of_directory(temp_dir):
    """Test validate_directory_structure with file where directory expected -
    covers lines 217-218."""
    # Create a file where we expect a directory
    (temp_dir / "src").touch()
    expected_structure = {"src": {"main.py": True}}

    result = validate_directory_structure(temp_dir, expected_structure)

    assert result.is_valid
    assert "Expected directory but found file: src" in result.warnings


def test_validate_directory_structure_recursive(temp_dir):
    """Test validate_directory_structure recursively - covers lines 221-223."""
    # Create the directory structure
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    # Missing nested file
    expected_structure = {"src": {"main.py": True, "utils": {"helper.py": True}}}

    result = validate_directory_structure(temp_dir, expected_structure)

    assert result.is_valid
    # Should have nested warnings/suggestions
    assert any("src/" in w for w in result.warnings)
    assert any("src/" in s for s in result.suggestions)


def test_validate_directory_structure_missing_file(temp_dir):
    """Test validate_directory_structure with missing file - covers lines 225-227."""
    expected_structure = {"README.md": True}

    result = validate_directory_structure(temp_dir, expected_structure)

    assert result.is_valid
    assert "Missing file: README.md" in result.warnings
    assert any("Create file:" in s for s in result.suggestions)


def test_validate_directory_structure_directory_instead_of_file(temp_dir):
    """Test validate_directory_structure with directory where file expected -
    covers lines 228-229."""
    # Create directory where we expect a file
    (temp_dir / "README.md").mkdir()
    expected_structure = {"README.md": True}

    result = validate_directory_structure(temp_dir, expected_structure)

    assert result.is_valid
    assert "Expected file but found directory: README.md" in result.warnings


def test_config_validator_add_rule():
    """Test ConfigValidator add_validation_rule method - covers line 257."""
    validator = ConfigValidator()
    rule = "test_rule"
    validator.add_validation_rule(rule)

    assert rule in validator.rules


def test_path_validator_methods():
    """Test PathValidator methods - covers lines 311, 314."""
    validator = PathValidator()

    # Test validate_path
    assert validator.validate_path(".")  # Current directory should exist
    assert not validator.validate_path("/nonexistent/path")

    # Test validate_project_structure
    result = validator.validate_project_structure(".")
    assert result.is_valid


def test_project_validator_methods():
    """Test ProjectValidator methods - covers lines 327, 330."""
    validator = ProjectValidator()

    # Test add_validation_rule
    rule = "test_rule"
    validator.add_validation_rule(rule)
    assert rule in validator.validation_rules

    # Test check_project_structure
    assert validator.check_project_structure(".") is True


def test_data_validator_version():
    """Test DataValidator validate_version method."""
    validator = DataValidator()

    # Valid versions
    assert validator.validate_version("1.0.0")
    assert validator.validate_version("2.1.3-alpha")

    # Invalid versions
    assert not validator.validate_version("")
    assert not validator.validate_version("1.0")
    assert not validator.validate_version("invalid")


def test_data_validator_email():
    """Test DataValidator validate_email method."""
    validator = DataValidator()

    # Valid emails
    assert validator.validate_email("user@example.com")
    assert validator.validate_email("test.email+tag@domain.co.uk")

    # Invalid emails
    assert not validator.validate_email("")
    assert not validator.validate_email("invalid-email")
    assert not validator.validate_email("user@")


def test_validation_result_placeholder():
    """Test placeholder ValidationResult class."""
    result = ValidationResult(is_valid=True, errors=["error1"], warnings=["warning1"])

    assert result.is_valid
    assert result.has_errors()
    assert result.has_warnings()

    result_no_issues = ValidationResult(is_valid=True)
    assert not result_no_issues.has_errors()
    assert not result_no_issues.has_warnings()


def test_validation_error_placeholder():
    """Test placeholder ValidationError class."""
    error = ValidationError(
        message="Test error",
        field="test_field",
        code="TEST_CODE",
        context={"key": "value"},
    )

    assert str(error) == "Test error"
    assert error.field == "test_field"
    assert error.code == "TEST_CODE"
    assert error.context == {"key": "value"}
