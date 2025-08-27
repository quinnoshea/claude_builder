"""Unit tests for template validator module.

Tests comprehensive template validation functionality including:
- TemplateStructureValidator directory structure validation
- TemplateMetadataValidator JSON metadata validation
- TemplateContentValidator content quality checks
- TemplateSecurityValidator security pattern detection
- ComprehensiveTemplateValidator orchestrated validation
- ValidationResult handling and batch operations
"""

import json

from unittest.mock import patch

import pytest

from claude_builder.core.models import ValidationResult
from claude_builder.core.template_management.validation.template_validator import (
    ComprehensiveTemplateValidator,
    TemplateContentValidator,
    TemplateMetadataValidator,
    TemplateSecurityValidator,
    TemplateStructureValidator,
)


class TestTemplateStructureValidator:
    """Test suite for TemplateStructureValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a TemplateStructureValidator instance for testing."""
        return TemplateStructureValidator()

    def test_validator_initialization(self, validator):
        """Test TemplateStructureValidator initialization."""
        assert "template.json" in validator.required_files
        assert "claude_instructions.md" in validator.required_files
        assert "agents_config.md" in validator.recommended_files
        assert "development_guide.md" in validator.recommended_files
        assert "README.md" in validator.recommended_files
        assert validator.logger is not None

    def test_validate_structure_valid_template(self, validator, temp_dir):
        """Test validation of a valid template structure."""
        template_path = temp_dir / "valid_template"
        template_path.mkdir()

        # Create required files
        (template_path / "template.json").write_text('{"name": "test"}')
        (template_path / "claude_instructions.md").write_text("# Instructions")

        # Create recommended files
        (template_path / "agents_config.md").write_text("# Agents")
        (template_path / "README.md").write_text("# README")

        result = validator.validate_structure(template_path)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) <= 1  # May warn about missing development_guide.md

    def test_validate_structure_missing_required_files(self, validator, temp_dir):
        """Test validation with missing required files."""
        template_path = temp_dir / "incomplete_template"
        template_path.mkdir()

        # Only create one required file, missing the other
        (template_path / "template.json").write_text('{"name": "test"}')
        # Missing claude_instructions.md

        result = validator.validate_structure(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("claude_instructions.md" in error for error in result.errors)

    def test_validate_structure_missing_recommended_files(self, validator, temp_dir):
        """Test validation with missing recommended files generates warnings."""
        template_path = temp_dir / "minimal_template"
        template_path.mkdir()

        # Create only required files
        (template_path / "template.json").write_text('{"name": "test"}')
        (template_path / "claude_instructions.md").write_text("# Instructions")

        result = validator.validate_structure(template_path)

        assert result.is_valid is True  # Valid because required files exist
        assert len(result.warnings) >= 2  # Should warn about missing recommended files
        assert any("agents_config.md" in warning for warning in result.warnings)
        assert any("README.md" in warning for warning in result.warnings)

    def test_validate_structure_nonexistent_path(self, validator, temp_dir):
        """Test validation of non-existent template path."""
        nonexistent_path = temp_dir / "does_not_exist"

        result = validator.validate_structure(nonexistent_path)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "does not exist" in result.errors[0]

    def test_validate_structure_file_instead_of_directory(self, validator, temp_dir):
        """Test validation when path points to a file instead of directory."""
        file_path = temp_dir / "not_a_directory.txt"
        file_path.write_text("This is a file, not a directory")

        result = validator.validate_structure(file_path)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "not a directory" in result.errors[0]


class TestTemplateMetadataValidator:
    """Test suite for TemplateMetadataValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a TemplateMetadataValidator instance for testing."""
        return TemplateMetadataValidator()

    @pytest.fixture
    def valid_metadata(self):
        """Create valid metadata for testing."""
        return {
            "name": "test-template",
            "version": "1.0.0",
            "description": "A test template",
            "author": "Test Author",
            "category": "testing",
            "tags": ["test", "sample"],
            "languages": ["python"],
            "frameworks": ["django"],
            "project_types": ["web_app"],
            "license": "MIT",
        }

    def test_validator_initialization(self, validator):
        """Test TemplateMetadataValidator initialization."""
        assert "name" in validator.required_fields
        assert "version" in validator.required_fields
        assert "description" in validator.required_fields
        assert "author" in validator.required_fields
        assert "category" in validator.optional_fields
        assert "tags" in validator.optional_fields
        assert validator.logger is not None

    def test_validate_metadata_valid(self, validator, temp_dir, valid_metadata):
        """Test validation of valid metadata."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(valid_metadata, f)

        result = validator.validate_metadata(template_path)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_metadata_missing_file(self, validator, temp_dir):
        """Test validation when template.json is missing."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()
        # No template.json file created

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Missing template.json" in result.errors[0]

    def test_validate_metadata_invalid_json(self, validator, temp_dir):
        """Test validation with invalid JSON in metadata file."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        metadata_file = template_path / "template.json"
        metadata_file.write_text("{ invalid json content")

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid JSON" in result.errors[0]

    def test_validate_metadata_missing_required_fields(self, validator, temp_dir):
        """Test validation with missing required fields."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        incomplete_metadata = {
            "name": "test-template",
            "version": "1.0.0",
            # Missing description and author
        }

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(incomplete_metadata, f)

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 2  # Missing description and author
        assert any("description" in error for error in result.errors)
        assert any("author" in error for error in result.errors)

    def test_validate_metadata_empty_required_fields(self, validator, temp_dir):
        """Test validation with empty required fields."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        metadata_with_empty_fields = {
            "name": "",  # Empty name
            "version": "1.0.0",
            "description": "A test template",
            "author": "",  # Empty author
        }

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(metadata_with_empty_fields, f)

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any("name" in error for error in result.errors)
        assert any("author" in error for error in result.errors)

    def test_validate_field_types_invalid_list_fields(
        self, validator, temp_dir, valid_metadata
    ):
        """Test validation with invalid types for list fields."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        invalid_metadata = valid_metadata.copy()
        invalid_metadata["tags"] = "not a list"  # Should be a list
        invalid_metadata["languages"] = "also not a list"  # Should be a list

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_metadata, f)

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any(
            "tags" in error and "must be a list" in error for error in result.errors
        )
        assert any(
            "languages" in error and "must be a list" in error
            for error in result.errors
        )

    def test_validate_field_types_invalid_string_fields(
        self, validator, temp_dir, valid_metadata
    ):
        """Test validation with invalid types for string fields."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        invalid_metadata = valid_metadata.copy()
        invalid_metadata["name"] = 123  # Should be a string
        invalid_metadata["description"] = ["not", "a", "string"]  # Should be a string

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_metadata, f)

        result = validator.validate_metadata(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any(
            "name" in error and "must be a string" in error for error in result.errors
        )
        assert any(
            "description" in error and "must be a string" in error
            for error in result.errors
        )

    def test_validate_version_format_valid(self, validator, temp_dir, valid_metadata):
        """Test validation with valid version formats."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        valid_versions = ["1.0.0", "2.1.3", "1.0.0-alpha.1", "3.2.1-beta+build.123"]

        for version in valid_versions:
            test_metadata = valid_metadata.copy()
            test_metadata["version"] = version

            metadata_file = template_path / "template.json"
            with metadata_file.open("w", encoding="utf-8") as f:
                json.dump(test_metadata, f)

            result = validator.validate_metadata(template_path)

            # Should be valid or have at most warnings (no errors)
            assert result.is_valid is True, f"Version {version} should be valid"

    def test_validate_version_format_warning(self, validator, temp_dir, valid_metadata):
        """Test validation with potentially invalid version formats generates warnings."""
        template_path = temp_dir / "test_template"
        template_path.mkdir()

        questionable_metadata = valid_metadata.copy()
        questionable_metadata["version"] = (
            "invalid-version!@#"  # Contains special chars
        )

        metadata_file = template_path / "template.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(questionable_metadata, f)

        result = validator.validate_metadata(template_path)

        # Should still be valid but have warnings
        assert result.is_valid is True  # No errors for version format, just warnings
        assert len(result.warnings) >= 1
        assert any("Version format" in warning for warning in result.warnings)


class TestTemplateContentValidator:
    """Test suite for TemplateContentValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a TemplateContentValidator instance for testing."""
        return TemplateContentValidator()

    def test_validator_initialization(self, validator):
        """Test TemplateContentValidator initialization."""
        assert validator.min_content_length == 100
        assert "${" in validator.template_variable_patterns
        assert "{{" in validator.template_variable_patterns
        assert "{%" in validator.template_variable_patterns
        assert validator.logger is not None

    def test_validate_content_quality_good_template(self, validator, temp_dir):
        """Test validation of template with good content quality."""
        template_path = temp_dir / "good_template"
        template_path.mkdir()

        # Create template file with good content
        good_content = """
# {{ project_name }} - Project Template

This is a comprehensive template for {{ project_type }} projects.

## Features

- Feature 1: {{ feature_1 }}
- Feature 2: {{ feature_2 }}
- Feature 3: Uses ${environment_var} for configuration

## Getting Started

1. Clone the repository
2. Install dependencies
3. Configure settings in {{ config_file }}
4. Run the application

This template provides a solid foundation for your project development.
"""

        (template_path / "instructions.md").write_text(good_content)

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True
        assert len(result.errors) == 0
        # May have suggestions but no warnings for good content

    def test_validate_content_quality_no_template_variables(self, validator, temp_dir):
        """Test validation of template with no template variables."""
        template_path = temp_dir / "static_template"
        template_path.mkdir()

        # Create template file without template variables
        static_content = """
# Static Project Template

This is a static template with no variables.
It doesn't use any template substitution patterns.
Everything is hardcoded and not customizable.
"""

        (template_path / "instructions.md").write_text(static_content)

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True  # Still valid, just warnings
        assert len(result.warnings) >= 1
        assert any("no template variables" in warning for warning in result.warnings)

    def test_validate_content_quality_short_content(self, validator, temp_dir):
        """Test validation of template with very short content."""
        template_path = temp_dir / "short_template"
        template_path.mkdir()

        # Create template file with short content
        short_content = "# {{ project_name }}"

        (template_path / "instructions.md").write_text(short_content)

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True  # Still valid, just warnings
        assert len(result.warnings) >= 1
        assert any("very little content" in warning for warning in result.warnings)

    def test_validate_content_quality_todo_items(self, validator, temp_dir):
        """Test validation of template with TODO items generates suggestions."""
        template_path = temp_dir / "todo_template"
        template_path.mkdir()

        # Create template file with TODO items
        todo_content = """
# {{ project_name }} Template

This template is under development.

## TODO Items

- TODO: Add more comprehensive examples
- TODO: Improve documentation
- todo: Fix formatting issues

Please help us complete this template!
"""

        (template_path / "instructions.md").write_text(todo_content)

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True
        assert len(result.suggestions) >= 1
        assert any("TODO items" in suggestion for suggestion in result.suggestions)

    def test_validate_content_quality_placeholder_content(self, validator, temp_dir):
        """Test validation of template with placeholder content."""
        template_path = temp_dir / "placeholder_template"
        template_path.mkdir()

        # Create template file with placeholder content
        placeholder_content = """
# {{ project_name }} - PLACEHOLDER Template

This is a SAMPLE template with EXAMPLE content.

Replace all PLACEHOLDER text with actual content.

## Example Section

This is an EXAMPLE of how to structure your content.
"""

        (template_path / "instructions.md").write_text(placeholder_content)

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True
        assert len(result.suggestions) >= 1
        assert any(
            "placeholder content" in suggestion for suggestion in result.suggestions
        )

    def test_validate_content_quality_file_read_error(self, validator, temp_dir):
        """Test validation when file cannot be read."""
        template_path = temp_dir / "unreadable_template"
        template_path.mkdir()

        # Create a directory instead of file (will cause read error)
        (template_path / "instructions.md").mkdir()

        result = validator.validate_content_quality(template_path)

        assert result.is_valid is True  # Still valid overall
        assert len(result.warnings) >= 1
        assert any(
            "Could not analyze content" in warning for warning in result.warnings
        )


class TestTemplateSecurityValidator:
    """Test suite for TemplateSecurityValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a TemplateSecurityValidator instance for testing."""
        return TemplateSecurityValidator()

    def test_validator_initialization(self, validator):
        """Test TemplateSecurityValidator initialization."""
        assert ".exe" in validator.dangerous_extensions
        assert ".bat" in validator.dangerous_extensions
        assert ".sh" in validator.dangerous_extensions
        assert "eval(" in validator.suspicious_patterns
        assert "system(" in validator.suspicious_patterns
        assert "<script" in validator.suspicious_patterns
        assert validator.logger is not None

    def test_validate_security_clean_template(self, validator, temp_dir):
        """Test validation of clean, secure template."""
        template_path = temp_dir / "clean_template"
        template_path.mkdir()

        # Create clean template files
        clean_content = """
# {{ project_name }} - Clean Template

This is a clean template with no security issues.

## Features

- Uses safe template variables: {{ project_name }}
- Provides documentation and examples
- No executable code or suspicious patterns

## Usage

Simply customize the variables and deploy.
"""

        (template_path / "instructions.md").write_text(clean_content)
        (template_path / "config.json").write_text('{"setting": "value"}')

        result = validator.validate_security(template_path)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_security_dangerous_files(self, validator, temp_dir):
        """Test validation with dangerous executable files."""
        template_path = temp_dir / "dangerous_template"
        template_path.mkdir()

        # Create dangerous files
        (template_path / "malicious.exe").write_bytes(b"fake executable")
        (template_path / "script.bat").write_text("@echo off\necho Hello")
        (template_path / "runner.sh").write_text("#!/bin/bash\necho Running")

        result = validator.validate_security(template_path)

        assert result.is_valid is True  # No errors, but warnings
        assert len(result.warnings) >= 1
        assert any("executable files" in warning for warning in result.warnings)

    def test_validate_security_suspicious_patterns(self, validator, temp_dir):
        """Test validation with suspicious code patterns."""
        template_path = temp_dir / "suspicious_template"
        template_path.mkdir()

        # Create template with suspicious patterns
        suspicious_content = """
# {{ project_name }} - Template with Issues

## Configuration

To run the setup, execute: eval("{{ setup_command }}")

For system integration: os.system("{{ install_command }}")

## Web Components

<script>
    // Suspicious script content
    eval(userInput);
</script>

## Downloads

Download dependencies from: https://suspicious-site.com/packages
"""

        (template_path / "instructions.md").write_text(suspicious_content)

        result = validator.validate_security(template_path)

        assert result.is_valid is True  # No errors, but warnings
        assert len(result.warnings) >= 1
        suspicious_warning = [w for w in result.warnings if "suspicious patterns" in w]
        assert len(suspicious_warning) >= 1

    def test_validate_security_hardcoded_credentials(self, validator, temp_dir):
        """Test validation with potential hardcoded credentials."""
        template_path = temp_dir / "credentials_template"
        template_path.mkdir()

        # Create template with credential-like patterns
        credentials_content = """
# {{ project_name }} Configuration

## Database Setup

database_password=secret123
api_key=abc123def456
private_token={{ user_token }}

## Security Settings

secret=my-secret-value
key=encryption-key-here
"""

        (template_path / "config.md").write_text(credentials_content)

        result = validator.validate_security(template_path)

        assert result.is_valid is True  # No errors, but warnings
        assert len(result.warnings) >= 1
        credentials_warning = [
            w for w in result.warnings if "hardcoded credentials" in w
        ]
        assert len(credentials_warning) >= 1

    def test_validate_security_binary_file_handling(self, validator, temp_dir):
        """Test validation handles binary files gracefully."""
        template_path = temp_dir / "binary_template"
        template_path.mkdir()

        # Create binary file that can't be decoded as UTF-8
        binary_content = bytes(range(256))  # All byte values
        (template_path / "binary_file.dat").write_bytes(binary_content)

        # Also create a normal text file
        (template_path / "text_file.md").write_text("# Normal text file")

        result = validator.validate_security(template_path)

        # Should handle binary files gracefully and not crash
        assert result.is_valid is True
        # May or may not have warnings depending on file extensions


class TestComprehensiveTemplateValidator:
    """Test suite for ComprehensiveTemplateValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a ComprehensiveTemplateValidator instance for testing."""
        return ComprehensiveTemplateValidator()

    def test_validator_initialization(self, validator):
        """Test ComprehensiveTemplateValidator initialization."""
        assert validator.structure_validator is not None
        assert validator.metadata_validator is not None
        assert validator.content_validator is not None
        assert validator.security_validator is not None
        assert validator.logger is not None

    def test_validate_template_complete_valid(self, validator, temp_dir):
        """Test validation of completely valid template."""
        template_path = temp_dir / "complete_template"
        template_path.mkdir()

        # Create complete template structure
        metadata = {
            "name": "complete-template",
            "version": "1.0.0",
            "description": "A complete test template",
            "author": "Test Author",
            "category": "testing",
            "tags": ["test", "complete"],
            "languages": ["python"],
            "frameworks": ["django"],
        }

        with (template_path / "template.json").open("w") as f:
            json.dump(metadata, f, indent=2)

        instructions_content = """
# {{ project_name }} - Complete Template

This is a comprehensive template for {{ project_type }} projects.

## Features

- Feature 1: {{ feature_1 }}
- Feature 2: {{ feature_2 }}
- Configuration via {{ config_file }}

## Getting Started

1. Initialize project structure
2. Configure settings
3. Run development server
4. Deploy to production

This template includes all necessary components for rapid development.
"""

        (template_path / "claude_instructions.md").write_text(instructions_content)
        (template_path / "README.md").write_text(
            "# Complete Template\n\nDocumentation here."
        )
        (template_path / "agents_config.md").write_text(
            "# Agent Configuration\n\nAgent setup here."
        )

        result = validator.validate_template(template_path)

        assert result.is_valid is True
        assert len(result.errors) == 0
        # May have suggestions but should be valid

    def test_validate_template_nonexistent(self, validator, temp_dir):
        """Test validation of non-existent template."""
        nonexistent_path = temp_dir / "does_not_exist"

        result = validator.validate_template(nonexistent_path)

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("does not exist" in error for error in result.errors)

    def test_validate_template_multiple_issues(self, validator, temp_dir):
        """Test validation of template with multiple issues across validators."""
        template_path = temp_dir / "problematic_template"
        template_path.mkdir()

        # Create problematic metadata (missing required fields)
        incomplete_metadata = {
            "name": "problematic-template"
            # Missing version, description, author
        }

        with (template_path / "template.json").open("w") as f:
            json.dump(incomplete_metadata, f)

        # Create problematic content
        problematic_content = """
# Static Template

This template has no variables and suspicious content.

To setup: eval("rm -rf /")  # Dangerous command

TODO: Fix everything
"""

        (template_path / "claude_instructions.md").write_text(problematic_content)

        # Add dangerous file
        (template_path / "malware.exe").write_bytes(b"fake malware")

        result = validator.validate_template(template_path)

        assert result.is_valid is False
        assert len(result.errors) >= 1  # From metadata validation
        assert len(result.warnings) >= 1  # From security and content validation
        assert len(result.suggestions) >= 1  # From content validation (TODO)

    def test_validate_template_validator_exception(self, validator, temp_dir):
        """Test validation when individual validator raises exception."""
        template_path = temp_dir / "exception_template"
        template_path.mkdir()

        # Create minimal valid structure
        (template_path / "template.json").write_text('{"name": "test"}')
        (template_path / "claude_instructions.md").write_text("# Test")

        # Mock one validator to raise an exception
        with patch.object(
            validator.metadata_validator, "validate_metadata"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Simulated validator error")

            result = validator.validate_template(template_path)

            assert result.is_valid is False
            assert len(result.errors) >= 1
            assert any("metadata validation" in error for error in result.errors)

    def test_validate_template_directory_batch(self, validator, temp_dir):
        """Test batch validation of multiple template directories."""
        # Create multiple templates
        template_paths = []

        for i in range(3):
            template_path = temp_dir / f"template_{i}"
            template_path.mkdir()
            template_paths.append(template_path)

            # Create basic structure (some valid, some invalid)
            if i == 0:  # Valid template
                metadata = {
                    "name": f"template-{i}",
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                }
                with (template_path / "template.json").open("w") as f:
                    json.dump(metadata, f)
                (template_path / "claude_instructions.md").write_text(
                    "# {{ project_name }}"
                )
            elif i == 1:  # Invalid metadata
                (template_path / "template.json").write_text(
                    '{"name": "template-1"}'
                )  # Missing required fields
                (template_path / "claude_instructions.md").write_text("# Instructions")
            else:  # Missing files
                (template_path / "template.json").write_text('{"name": "template-2"}')
                # Missing claude_instructions.md

        results = validator.validate_template_directory_batch(template_paths)

        assert len(results) == 3
        assert results[template_paths[0]].is_valid is True  # Valid template
        assert results[template_paths[1]].is_valid is False  # Invalid metadata
        assert results[template_paths[2]].is_valid is False  # Missing files

    def test_validate_template_directory_batch_exception(self, validator, temp_dir):
        """Test batch validation when individual validation raises exception."""
        template_path = temp_dir / "exception_template"
        template_path.mkdir()

        # Mock validate_template to raise an exception
        with patch.object(validator, "validate_template") as mock_validate:
            mock_validate.side_effect = Exception("Simulated validation error")

            results = validator.validate_template_directory_batch([template_path])

            assert len(results) == 1
            assert results[template_path].is_valid is False
            assert "Validation failed with error" in results[template_path].errors[0]

    def test_get_validation_summary(self, validator, temp_dir):
        """Test generation of validation summary statistics."""
        # Create mock validation results
        results = {}

        # Valid result
        valid_path = temp_dir / "valid"
        results[valid_path] = ValidationResult(
            is_valid=True, warnings=["minor warning"], suggestions=["suggestion"]
        )

        # Invalid result with errors
        invalid_path = temp_dir / "invalid"
        results[invalid_path] = ValidationResult(
            is_valid=False, errors=["error 1", "error 2"], warnings=["warning 1"]
        )

        # Another invalid result
        invalid_path2 = temp_dir / "invalid2"
        results[invalid_path2] = ValidationResult(
            is_valid=False, errors=["error 3"], warnings=["warning 2", "warning 3"]
        )

        summary = validator.get_validation_summary(results)

        assert summary["total_templates"] == 3
        assert summary["valid_templates"] == 1
        assert summary["invalid_templates"] == 2
        assert summary["total_errors"] == 3
        assert summary["total_warnings"] == 4
        assert summary["validation_rate"] == 1 / 3  # 33.33%

    def test_get_validation_summary_empty(self, validator):
        """Test validation summary with empty results."""
        summary = validator.get_validation_summary({})

        assert summary["total_templates"] == 0
        assert summary["valid_templates"] == 0
        assert summary["invalid_templates"] == 0
        assert summary["total_errors"] == 0
        assert summary["total_warnings"] == 0
        assert summary["validation_rate"] == 0.0
