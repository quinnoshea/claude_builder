"""Template validation framework.

This module provides comprehensive template validation including structure,
metadata, content quality, and security checks. Extracted from template_manager.py
to improve maintainability and separation of concerns.
"""

import json
import logging

from pathlib import Path
from typing import List

from claude_builder.core.models import ValidationResult


class TemplateStructureValidator:
    """Validates template directory structure and required files."""

    def __init__(self) -> None:
        """Initialize structure validator with file requirements."""
        self.required_files = [
            "template.json",  # Metadata file
            "claude_instructions.md",  # At minimum, must have Claude instructions
        ]
        self.recommended_files = [
            "agents_config.md",
            "development_guide.md",
            "README.md",
        ]
        self.logger = logging.getLogger(__name__)

    def validate_structure(self, template_path: Path) -> ValidationResult:
        """Validate template directory structure.

        Args:
            template_path: Path to template directory

        Returns:
            ValidationResult with structure validation results
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not template_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Template path does not exist: {template_path}"],
            )

        if not template_path.is_dir():
            return ValidationResult(
                is_valid=False,
                errors=[f"Template path is not a directory: {template_path}"],
            )

        # Check required files
        for required_file in self.required_files:
            file_path = template_path / required_file
            if not file_path.exists():
                errors.append(f"Required file missing: {required_file}")

        # Check recommended files
        for recommended_file in self.recommended_files:
            file_path = template_path / recommended_file
            if not file_path.exists():
                warnings.append(f"Recommended file missing: {recommended_file}")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


class TemplateMetadataValidator:
    """Validates template metadata files and content."""

    def __init__(self) -> None:
        """Initialize metadata validator."""
        self.required_fields = ["name", "version", "description", "author"]
        self.optional_fields = [
            "category",
            "tags",
            "languages",
            "frameworks",
            "project_types",
            "min_builder_version",
            "homepage",
            "repository",
            "license",
            "created",
            "updated",
        ]
        self.logger = logging.getLogger(__name__)

    def validate_metadata(self, template_path: Path) -> ValidationResult:
        """Validate template metadata.

        Args:
            template_path: Path to template directory

        Returns:
            ValidationResult with metadata validation results
        """
        errors: List[str] = []
        warnings: List[str] = []

        metadata_file = template_path / "template.json"
        if not metadata_file.exists():
            return ValidationResult(
                is_valid=False, errors=["Missing template.json metadata file"]
            )

        try:
            with metadata_file.open(encoding="utf-8") as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False, errors=[f"Invalid JSON in template.json: {e}"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False, errors=[f"Cannot read template.json: {e}"]
            )

        # Validate required metadata fields
        for field in self.required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Required metadata field missing or empty: {field}")

        # Validate field types
        self._validate_field_types(metadata, errors)

        # Validate version format (basic check)
        self._validate_version_format(metadata, warnings)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _validate_field_types(self, metadata: dict, errors: List[str]) -> None:
        """Validate metadata field types."""
        list_fields = ["languages", "frameworks", "tags", "project_types"]

        for field in list_fields:
            if field in metadata and not isinstance(metadata[field], list):
                errors.append(f"'{field}' field must be a list")

        string_fields = [
            "name",
            "version",
            "description",
            "author",
            "category",
            "license",
        ]
        for field in string_fields:
            if field in metadata and not isinstance(metadata[field], str):
                errors.append(f"'{field}' field must be a string")

    def _validate_version_format(self, metadata: dict, warnings: List[str]) -> None:
        """Validate version format (basic semantic version check)."""
        if "version" in metadata:
            version = metadata["version"]
            if (
                not isinstance(version, str)
                or not version.replace(".", "")
                .replace("-", "")
                .replace("_", "")
                .replace("+", "")
                .isalnum()
            ):
                warnings.append("Version format may not follow semantic versioning")


class TemplateContentValidator:
    """Validates template content quality and completeness."""

    def __init__(self) -> None:
        """Initialize content validator."""
        self.min_content_length = 100
        self.template_variable_patterns = ["${", "{{", "{%"]
        self.logger = logging.getLogger(__name__)

    def validate_content_quality(self, template_path: Path) -> ValidationResult:
        """Validate content quality and completeness.

        Args:
            template_path: Path to template directory

        Returns:
            ValidationResult with content quality validation results
        """
        warnings: List[str] = []
        suggestions: List[str] = []

        # Check for template variables in files
        template_files = list(template_path.glob("**/*.md"))

        for file_path in template_files:
            try:
                with file_path.open(encoding="utf-8") as f:
                    content = f.read()

                # Check for template variables
                has_variables = any(
                    pattern in content for pattern in self.template_variable_patterns
                )
                if not has_variables:
                    warnings.append(
                        f"File {file_path.name} appears to have no template variables"
                    )

                # Check minimum content length
                if len(content) < self.min_content_length:
                    warnings.append(
                        f"File {file_path.name} appears to have very little content"
                    )

                # Check for common issues
                if "TODO" in content.upper():
                    suggestions.append(f"File {file_path.name} contains TODO items")

                # Check for placeholder content
                placeholder_indicators = ["PLACEHOLDER", "EXAMPLE", "SAMPLE"]
                if any(
                    indicator in content.upper() for indicator in placeholder_indicators
                ):
                    suggestions.append(
                        f"File {file_path.name} may contain placeholder content"
                    )

            except Exception as e:
                warnings.append(f"Could not analyze content of {file_path.name}: {e}")

        return ValidationResult(
            is_valid=True, warnings=warnings, suggestions=suggestions
        )


class TemplateSecurityValidator:
    """Validates template security and safety."""

    def __init__(self) -> None:
        """Initialize security validator."""
        self.dangerous_extensions = {
            ".exe",
            ".bat",
            ".sh",
            ".ps1",
            ".py",
            ".js",
            ".php",
            ".pl",
            ".rb",
            ".jar",
            ".app",
            ".dmg",
            ".deb",
            ".rpm",
        }
        self.suspicious_patterns = [
            "eval(",
            "exec(",
            "system(",
            "shell_exec",
            "subprocess",
            "os.system",
            "os.popen",
            "__import__",
            "importlib",
            "curl ",
            "wget ",
            "download",
            "http://",
            "https://",
            "<script",
            "</script>",
            "javascript:",
            "vbscript:",
        ]
        self.logger = logging.getLogger(__name__)

    def validate_security(self, template_path: Path) -> ValidationResult:
        """Validate template for security issues.

        Args:
            template_path: Path to template directory

        Returns:
            ValidationResult with security validation results
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for potentially dangerous files
        executable_files = []
        for ext in self.dangerous_extensions:
            executable_files.extend(list(template_path.glob(f"**/*{ext}")))

        if executable_files:
            warnings.append(
                f"Template contains executable files: "
                f"{[f.name for f in executable_files]}"
            )

        # Check for suspicious content in template files
        template_files = list(template_path.glob("**/*.md"))
        template_files.extend(template_path.glob("**/*.txt"))
        template_files.extend(template_path.glob("**/*.json"))

        for file_path in template_files:
            try:
                with file_path.open(encoding="utf-8") as f:
                    content = f.read().lower()

                # Check for potentially dangerous patterns
                found_patterns = [
                    pattern
                    for pattern in self.suspicious_patterns
                    if pattern in content
                ]

                if found_patterns:
                    warnings.append(
                        f"File {file_path.name} contains potentially suspicious "
                        f"patterns: {found_patterns}"
                    )

                # Check for hardcoded credentials patterns
                credential_patterns = [
                    "password=",
                    "pwd=",
                    "pass=",
                    "secret=",
                    "token=",
                    "key=",
                    "api_key=",
                    "private",
                    "credential",
                ]
                found_credentials = [
                    pattern for pattern in credential_patterns if pattern in content
                ]

                if found_credentials:
                    warnings.append(
                        f"File {file_path.name} may contain hardcoded credentials "
                        f"or sensitive information: {found_credentials}"
                    )

            except (OSError, UnicodeDecodeError):
                # Ignore read errors for security check
                continue

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


class ComprehensiveTemplateValidator:
    """Comprehensive template validator combining all validation types."""

    def __init__(self) -> None:
        """Initialize comprehensive validator."""
        self.structure_validator = TemplateStructureValidator()
        self.metadata_validator = TemplateMetadataValidator()
        self.content_validator = TemplateContentValidator()
        self.security_validator = TemplateSecurityValidator()
        self.logger = logging.getLogger(__name__)

    def validate_template(self, template_path: Path) -> ValidationResult:
        """Run comprehensive template validation.

        Args:
            template_path: Path to template directory

        Returns:
            Combined ValidationResult from all validators
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []
        all_suggestions: List[str] = []

        if not template_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Template path does not exist: {template_path}"],
            )

        # Run all validators
        validators_and_names = [
            (self.structure_validator.validate_structure, "structure"),
            (self.metadata_validator.validate_metadata, "metadata"),
            (self.content_validator.validate_content_quality, "content"),
            (self.security_validator.validate_security, "security"),
        ]

        for validator_func, validator_name in validators_and_names:
            try:
                result = validator_func(template_path)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                all_suggestions.extend(result.suggestions)

                self.logger.debug(
                    f"Template {validator_name} validation: "
                    f"{len(result.errors)} errors, {len(result.warnings)} warnings"
                )
            except Exception as e:
                error_msg = f"Error during {validator_name} validation: {e}"
                all_errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)

        is_valid = len(all_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
        )

    def validate_template_directory_batch(
        self, template_paths: List[Path]
    ) -> dict[Path, ValidationResult]:
        """Validate multiple template directories.

        Args:
            template_paths: List of paths to template directories

        Returns:
            Dictionary mapping paths to their validation results
        """
        results = {}

        for template_path in template_paths:
            try:
                result = self.validate_template(template_path)
                results[template_path] = result
            except Exception as e:
                results[template_path] = ValidationResult(
                    is_valid=False, errors=[f"Validation failed with error: {e}"]
                )
                self.logger.error(
                    f"Failed to validate {template_path}: {e}", exc_info=True
                )

        return results

    def get_validation_summary(self, results: dict[Path, ValidationResult]) -> dict:
        """Generate summary statistics from validation results.

        Args:
            results: Dictionary of validation results

        Returns:
            Summary statistics dictionary
        """
        total_templates = len(results)
        valid_templates = sum(1 for result in results.values() if result.is_valid)
        total_errors = sum(len(result.errors) for result in results.values())
        total_warnings = sum(len(result.warnings) for result in results.values())

        return {
            "total_templates": total_templates,
            "valid_templates": valid_templates,
            "invalid_templates": total_templates - valid_templates,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validation_rate": (
                valid_templates / total_templates if total_templates > 0 else 0.0
            ),
        }
