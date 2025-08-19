"""Validation utilities for Claude Builder."""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    error: Optional[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


def validate_project_path(project_path: Path) -> ValidationResult:
    """Validate that a project path is suitable for analysis."""
    
    # Check if path exists
    if not project_path.exists():
        return ValidationResult(
            is_valid=False,
            error=f"Path does not exist: {project_path}"
        )
    
    # Check if it's a directory
    if not project_path.is_dir():
        return ValidationResult(
            is_valid=False,
            error=f"Path is not a directory: {project_path}"
        )
    
    # Check if we have read permissions
    if not os.access(project_path, os.R_OK):
        return ValidationResult(
            is_valid=False,
            error=f"No read permission for directory: {project_path}"
        )
    
    warnings = []
    suggestions = []
    
    # Check if directory is empty
    if not any(project_path.iterdir()):
        warnings.append("Directory is empty")
        suggestions.append("Ensure this is the correct project directory")
    
    # Check for common project indicators
    common_files = [
        'package.json', 'Cargo.toml', 'pyproject.toml', 'requirements.txt',
        'pom.xml', 'build.gradle', 'go.mod', 'composer.json'
    ]
    
    has_project_indicators = any(
        (project_path / file).exists() for file in common_files
    )
    
    if not has_project_indicators:
        # Check for source files
        source_extensions = {'.py', '.rs', '.js', '.ts', '.java', '.go', '.cpp', '.c'}
        has_source_files = any(
            file.suffix in source_extensions
            for file in project_path.rglob('*')
            if file.is_file()
        )
        
        if not has_source_files:
            warnings.append("No common project files or source code detected")
            suggestions.append("Verify this is a software project directory")
    
    # Check for very large directories (performance warning)
    try:
        file_count = sum(1 for _ in project_path.rglob('*') if _.is_file())
        if file_count > 10000:
            warnings.append(f"Large project detected ({file_count} files)")
            suggestions.append("Analysis may take longer than usual")
    except OSError:
        # Skip if we can't count files (permissions, etc.)
        pass
    
    # Check if it's a git repository
    if not (project_path / '.git').exists():
        suggestions.append("Initialize git repository for better project management")
    
    return ValidationResult(
        is_valid=True,
        warnings=warnings,
        suggestions=suggestions
    )


def validate_template_name(template_name: str) -> ValidationResult:
    """Validate template name."""
    if not template_name:
        return ValidationResult(
            is_valid=False,
            error="Template name cannot be empty"
        )
    
    # Check for valid characters
    if not template_name.replace('-', '').replace('_', '').isalnum():
        return ValidationResult(
            is_valid=False,
            error="Template name can only contain letters, numbers, hyphens, and underscores"
        )
    
    return ValidationResult(is_valid=True)


def validate_config_file(config_path: Path) -> ValidationResult:
    """Validate configuration file."""
    if not config_path.exists():
        return ValidationResult(
            is_valid=False,
            error=f"Configuration file not found: {config_path}"
        )
    
    if not config_path.is_file():
        return ValidationResult(
            is_valid=False,
            error=f"Configuration path is not a file: {config_path}"
        )
    
    # Check file extension
    valid_extensions = {'.json', '.toml'}
    if config_path.suffix.lower() not in valid_extensions:
        return ValidationResult(
            is_valid=False,
            error=f"Configuration file must have .json or .toml extension, got: {config_path.suffix}"
        )
    
    # Check if readable
    if not os.access(config_path, os.R_OK):
        return ValidationResult(
            is_valid=False,
            error=f"No read permission for configuration file: {config_path}"
        )
    
    return ValidationResult(is_valid=True)


def validate_output_directory(output_dir: Path, create_if_missing: bool = False) -> ValidationResult:
    """Validate output directory."""
    if not output_dir.exists():
        if create_if_missing:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return ValidationResult(
                    is_valid=False,
                    error=f"Cannot create output directory: {e}"
                )
        else:
            return ValidationResult(
                is_valid=False,
                error=f"Output directory does not exist: {output_dir}"
            )
    
    if not output_dir.is_dir():
        return ValidationResult(
            is_valid=False,
            error=f"Output path is not a directory: {output_dir}"
        )
    
    # Check write permissions
    if not os.access(output_dir, os.W_OK):
        return ValidationResult(
            is_valid=False,
            error=f"No write permission for output directory: {output_dir}"
        )
    
    return ValidationResult(is_valid=True)