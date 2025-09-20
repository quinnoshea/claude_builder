"""Validation utilities for Claude Builder."""

import os
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    project_type: Optional[str] = None
    detected_files: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.errors is None:
            self.errors = []
        # Support both error (singular) and errors (plural)
        if self.error and self.error not in self.errors:
            self.errors.append(self.error)

    def has_errors(self) -> bool:
        return len(self.errors or []) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings or []) > 0


def validate_project_path(project_path: Path) -> ValidationResult:
    """Validate that a project path is suitable for analysis."""

    # Check if path exists
    if not project_path.exists():
        return ValidationResult(
            is_valid=False, error=f"Path does not exist: {project_path}"
        )

    # Check if it's a directory
    if not project_path.is_dir():
        return ValidationResult(
            is_valid=False, error=f"Path is not a directory: {project_path}"
        )

    # Check if we have read permissions
    if not os.access(project_path, os.R_OK):
        return ValidationResult(
            is_valid=False, error=f"No read permission for directory: {project_path}"
        )

    warnings = []
    suggestions = []

    # Check if directory is empty
    if not any(project_path.iterdir()):
        warnings.append("Directory is empty")
        suggestions.append("Ensure this is the correct project directory")

    # Check for common project indicators
    common_files = [
        "package.json",
        "Cargo.toml",
        "pyproject.toml",
        "requirements.txt",
        "pom.xml",
        "build.gradle",
        "go.mod",
        "composer.json",
    ]

    has_project_indicators = any(
        (project_path / file).exists() for file in common_files
    )

    if not has_project_indicators:
        # Check for source files (be resilient to permission errors)
        source_extensions = {".py", ".rs", ".js", ".ts", ".java", ".go", ".cpp", ".c"}
        try:
            has_source_files = any(
                file.suffix in source_extensions
                for file in project_path.rglob("*")
                if file.is_file()
            )
        except OSError:
            has_source_files = False

        if not has_source_files:
            warnings.append("No common project files or source code detected")
            suggestions.append("Verify this is a software project directory")

    # Check for very large directories (performance warning)
    try:
        file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
        max_file_count_threshold = 10000
        if file_count > max_file_count_threshold:
            warnings.append(f"Large project detected ({file_count} files)")
            suggestions.append("Analysis may take longer than usual")
    except OSError:
        # Skip if we can't count files (permissions, etc.)
        pass

    # Check if it's a git repository
    if not (project_path / ".git").exists():
        suggestions.append("Initialize git repository for better project management")

    return ValidationResult(is_valid=True, warnings=warnings, suggestions=suggestions)


def validate_template_name(template_name: str) -> ValidationResult:
    """Validate template name."""
    if not template_name:
        return ValidationResult(is_valid=False, error="Template name cannot be empty")

    # Check for valid characters
    if not template_name.replace("-", "").replace("_", "").isalnum():
        return ValidationResult(
            is_valid=False,
            error=(
                "Template name can only contain letters, numbers, hyphens, "
                "and underscores"
            ),
        )

    return ValidationResult(is_valid=True)


def validate_config_file(config_path: Path) -> ValidationResult:
    """Validate configuration file."""
    if not config_path.exists():
        return ValidationResult(
            is_valid=False, error=f"Configuration file not found: {config_path}"
        )

    if not config_path.is_file():
        return ValidationResult(
            is_valid=False, error=f"Configuration path is not a file: {config_path}"
        )

    # Check file extension
    valid_extensions = {".json", ".toml"}
    if config_path.suffix.lower() not in valid_extensions:
        return ValidationResult(
            is_valid=False,
            error=(
                f"Configuration file must have .json or .toml extension, "
                f"got: {config_path.suffix}"
            ),
        )

    # Check if readable
    if not os.access(config_path, os.R_OK):
        return ValidationResult(
            is_valid=False,
            error=f"No read permission for configuration file: {config_path}",
        )

    return ValidationResult(is_valid=True)


def validate_output_directory(
    output_dir: Path, *, create_if_missing: bool = False
) -> ValidationResult:
    """Validate output directory."""
    if not output_dir.exists():
        if create_if_missing:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return ValidationResult(
                    is_valid=False, error=f"Cannot create output directory: {e}"
                )
        else:
            return ValidationResult(
                is_valid=False, error=f"Output directory does not exist: {output_dir}"
            )

    if not output_dir.is_dir():
        return ValidationResult(
            is_valid=False, error=f"Output path is not a directory: {output_dir}"
        )

    # Check write permissions
    if not os.access(output_dir, os.W_OK):
        return ValidationResult(
            is_valid=False,
            error=f"No write permission for output directory: {output_dir}",
        )

    return ValidationResult(is_valid=True)


def validate_directory_structure(
    directory: Path, expected_structure: dict
) -> ValidationResult:
    """Validate that a directory has the expected structure.

    Args:
        directory: Directory to validate
        expected_structure: Dict describing expected files/folders

    Returns:
        ValidationResult indicating if structure is valid
    """
    if not directory.exists():
        return ValidationResult(
            is_valid=False, error=f"Directory does not exist: {directory}"
        )

    if not directory.is_dir():
        return ValidationResult(
            is_valid=False, error=f"Path is not a directory: {directory}"
        )

    warnings = []
    suggestions = []

    # Check for required files/directories
    for item_name, item_info in expected_structure.items():
        item_path = directory / item_name

        if isinstance(item_info, dict):
            # It's a directory with nested structure
            if not item_path.exists():
                warnings.append(f"Missing directory: {item_name}")
                suggestions.append(f"Create directory: {item_path}")
            elif item_path.is_file():
                warnings.append(f"Expected directory but found file: {item_name}")
            else:
                # Recursively validate subdirectory
                sub_result = validate_directory_structure(item_path, item_info)
                warnings.extend(
                    [f"{item_name}/{w}" for w in (sub_result.warnings or [])]
                )
                suggestions.extend(
                    [f"{item_name}/{s}" for s in (sub_result.suggestions or [])]
                )
        # It's a file (item_info would be file extension or True)
        elif not item_path.exists():
            warnings.append(f"Missing file: {item_name}")
            suggestions.append(f"Create file: {item_path}")
        elif item_path.is_dir():
            warnings.append(f"Expected file but found directory: {item_name}")

    # Structure is valid even with warnings (missing files can be created)
    return ValidationResult(is_valid=True, warnings=warnings, suggestions=suggestions)


# Placeholder classes for test compatibility
class ConfigValidator:
    """Enhanced ConfigValidator class."""

    def __init__(self) -> None:
        self.rules: list[Any] = []

    def validate_project_config(self, config: dict) -> ValidationResult:
        """Validate project configuration."""
        return self.validate_config(config)

    def validate_config(self, config: dict) -> ValidationResult:
        """Validate configuration with detailed analysis."""
        errors: list[str] = []
        warnings: list[str] = []

        # Validate project section
        if "project" in config:
            project_config = config["project"]

            # Validate project name
            if "name" not in project_config or not project_config["name"]:
                errors.append("Project name is required and cannot be empty")

            # Validate project type
            if "type" in project_config:
                valid_types = {
                    "python",
                    "rust",
                    "javascript",
                    "java",
                    "go",
                    "multi_language",
                }
                if project_config["type"] not in valid_types:
                    errors.append(f"Invalid project type: {project_config['type']}")

        # Validate analysis section
        if "analysis" in config:
            analysis_config = config["analysis"]

            # Validate analysis depth
            if "depth" in analysis_config:
                valid_depths = {"shallow", "standard", "deep"}
                if analysis_config["depth"] not in valid_depths:
                    errors.append(f"Invalid analysis depth: {analysis_config['depth']}")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def add_validation_rule(self, rule: Any) -> None:
        """Add validation rule."""
        self.rules.append(rule)


class DataValidator:
    """Enhanced DataValidator class."""

    def validate_version(self, version: str) -> bool:
        """Validate version string."""
        pattern = r"^\d+\.\d+\.\d+.*$"
        return bool(re.match(pattern, version))

    def validate_email(self, email: str) -> bool:
        """Validate email address."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_project_name(self, name: str) -> bool:
        """Validate project name."""
        if not name:
            return False

        # Check for spaces
        if " " in name:
            return False

        # Check if starts with number
        if name[0].isdigit():
            return False

        # Check for valid characters (letters, numbers, hyphens, underscores)
        pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
        return bool(re.match(pattern, name))


class ValidationError:
    """Placeholder ValidationError class for test compatibility."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        self.message = message
        self.field = field
        self.code = code
        self.context = context or {}

    def __str__(self) -> str:
        return self.message


class PathValidator:
    """Enhanced PathValidator class."""

    def __init__(self) -> None:
        self.valid_paths: List[str] = []

    def validate_path(self, path: str) -> bool:
        return Path(path).exists()

    def is_valid_file(self, file_path: Union[str, Path]) -> bool:
        """Check if path is a valid file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return bool(file_path.exists() and file_path.is_file())

    def is_valid_directory(self, dir_path: Union[str, Path]) -> bool:
        """Check if path is a valid directory."""
        if isinstance(dir_path, str):
            dir_path = Path(dir_path)
        return bool(dir_path.exists() and dir_path.is_dir())

    def is_readable(self, path: Any) -> bool:
        """Check if path is readable."""
        if isinstance(path, str):
            path = Path(path)
        return path.exists() and os.access(path, os.R_OK)

    def is_writable(self, path: Any) -> bool:
        """Check if path is writable."""
        if isinstance(path, str):
            path = Path(path)
        return path.exists() and os.access(path, os.W_OK)

    def validate_project_structure(self, project_path: str) -> ValidationResult:
        """Validate project structure."""
        path = Path(project_path)

        if not self.is_valid_directory(path):
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid project directory: {project_path}"],
                warnings=[],
            )

        return ValidationResult(is_valid=True, errors=[], warnings=[])


class ProjectValidator:
    """Enhanced ProjectValidator class."""

    def __init__(self) -> None:
        self.validation_rules: List[Any] = []
        from .file_patterns import ProjectTypeDetector

        self.type_detector = ProjectTypeDetector()

    def validate_project(self, project_path: Any) -> ValidationResult:
        """Validate project with comprehensive analysis."""
        if isinstance(project_path, str):
            project_path = Path(project_path)

        errors: List[str] = []
        warnings: List[str] = []
        detected_files: List[str] = []

        # Basic path validation
        if not project_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Project path does not exist: {project_path}"],
                warnings=warnings,
            )

        # Detect project type
        project_type = self.type_detector.detect_project_type(str(project_path))

        # Get project files for analysis
        project_files = [f.name for f in project_path.rglob("*") if f.is_file()]
        detected_files = project_files[:20]  # Limit for performance

        # Validate based on project type
        if project_type == "unknown":
            if not project_files:
                errors.append("Empty project directory")
            else:
                # Check if it's really a software project
                source_extensions = {
                    ".py",
                    ".rs",
                    ".js",
                    ".ts",
                    ".java",
                    ".go",
                    ".cpp",
                    ".c",
                    ".h",
                }
                has_source_files = any(
                    Path(f).suffix.lower() in source_extensions for f in project_files
                )
                config_files = {
                    "package.json",
                    "Cargo.toml",
                    "pyproject.toml",
                    "requirements.txt",
                    "pom.xml",
                    "build.gradle",
                    "go.mod",
                }
                has_config_files = any(f in config_files for f in project_files)

                if not has_source_files and not has_config_files:
                    errors.append("No recognizable project structure found")
                else:
                    warnings.append("Could not determine project type")

        # Check for specific project type indicators
        project_indicators = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt"],
            "rust": ["Cargo.toml"],
            "javascript": ["package.json"],
            "java": ["pom.xml", "build.gradle"],
        }

        if project_type in project_indicators:
            required_files = project_indicators[project_type]
            found_indicators = [f for f in required_files if f in project_files]
            if found_indicators:
                detected_files.extend(found_indicators)
            else:
                warnings.append(f"No standard {project_type} project files found")

        is_valid = len(errors) == 0

        # Create enhanced ValidationResult
        result = ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
        result.project_type = project_type
        result.detected_files = detected_files

        return result

    def add_validation_rule(self, rule: Any) -> None:
        self.validation_rules.append(rule)

    def check_project_structure(self, project_path: str) -> bool:
        result = self.validate_project(project_path)
        return result.is_valid
