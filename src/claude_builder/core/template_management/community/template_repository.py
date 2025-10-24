"""Community template repository management.

This module handles community template discovery, installation, and management.
Extracted from template_manager.py to improve modularity and maintainability.
"""

import json
import logging
import shutil

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from claude_builder.core.models import ProjectAnalysis, ValidationResult
from claude_builder.core.template_management.network.template_downloader import (
    TemplateDownloader,
    TemplateRepositoryClient,
)
from claude_builder.core.template_management.validation.template_validator import (
    ComprehensiveTemplateValidator,
)


class TemplateMetadata:
    """Metadata for a community template."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize template metadata from data dictionary."""
        self.name: str = data.get("name", "")
        self.version: str = data.get("version", "1.0.0")
        self.description: str = data.get("description", "")
        self.author: str = data.get("author", "")
        self.category: str = data.get("category", "general")
        self.tags: List[str] = data.get("tags", [])
        self.languages: List[str] = data.get("languages", [])
        self.frameworks: List[str] = data.get("frameworks", [])
        self.project_types: List[str] = data.get("project_types", [])
        self.min_builder_version: str = data.get("min_builder_version", "0.1.0")
        self.homepage: Optional[str] = data.get("homepage")
        self.repository: Optional[str] = data.get("repository")
        self.license: str = data.get("license", "MIT")
        self.created: Optional[str] = data.get("created")
        self.updated: Optional[str] = data.get("updated")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "project_types": self.project_types,
            "min_builder_version": self.min_builder_version,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "created": self.created,
            "updated": self.updated,
        }

    @property
    def is_compatible(self) -> bool:
        """Check if template is compatible with current builder version."""
        # Simple version comparison - in production this would be more sophisticated
        try:
            current_version = "0.1.0"  # Would be imported from version module
            # Simple semantic version comparison (just for testing)
            current_parts = [int(x) for x in current_version.split(".")]
            required_parts = [int(x) for x in self.min_builder_version.split(".")]

            # Pad to same length
            max_len = max(len(current_parts), len(required_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))

            return current_parts >= required_parts
        except Exception:
            return True  # Default to compatible if comparison fails


class CommunityTemplate:
    """Represents a community template with metadata and source information."""

    def __init__(
        self,
        metadata: TemplateMetadata,
        source_url: Optional[str] = None,
        local_path: Optional[Path] = None,
    ):
        """Initialize community template.

        Args:
            metadata: Template metadata
            source_url: URL to download template from
            local_path: Local path if template is installed
        """
        self.metadata = metadata
        self.source_url = source_url
        self.local_path = local_path
        self.installed = local_path is not None

    @property
    def id(self) -> str:
        """Unique template identifier."""
        return f"{self.metadata.author}/{self.metadata.name}"

    @property
    def display_name(self) -> str:
        """Human-readable template name."""
        return f"{self.metadata.name} v{self.metadata.version}"

    def matches_project(self, analysis: ProjectAnalysis) -> Tuple[bool, float]:
        """Check if template matches project analysis.

        Args:
            analysis: Project analysis to match against

        Returns:
            Tuple of (matches, compatibility_score_percentage)
        """
        score = 0.0
        max_score = 0.0

        # Language matching (high weight)
        if self.metadata.languages:
            max_score += 40
            if analysis.language and analysis.language.lower() in [
                l.lower() for l in self.metadata.languages
            ]:
                score += 40

        # Framework matching (high weight)
        if self.metadata.frameworks:
            max_score += 30
            if analysis.framework and analysis.framework.lower() in [
                f.lower() for f in self.metadata.frameworks
            ]:
                score += 30

        # Project type matching (medium weight)
        if self.metadata.project_types:
            max_score += 20
            if analysis.project_type.value in self.metadata.project_types:
                score += 20

        # Tag/category matching (low weight)
        max_score += 10
        if self.metadata.category and analysis.domain_info.domain:
            if self.metadata.category.lower() in analysis.domain_info.domain.lower():
                score += 10

        match_percentage = (score / max_score * 100) if max_score > 0 else 0
        return match_percentage >= 50, match_percentage


class CommunityTemplateManager:
    """Manages community template discovery, installation, and lifecycle."""

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        downloader: Optional[TemplateDownloader] = None,
        repository_client: Optional[TemplateRepositoryClient] = None,
        validator: Optional[ComprehensiveTemplateValidator] = None,
    ):
        """Initialize community template manager.

        Args:
            templates_dir: Directory to store templates (default: ~/.claude-builder/templates)
            downloader: Template downloader instance
            repository_client: Repository client instance
            validator: Template validator instance
        """
        self.templates_dir = templates_dir or (
            Path.home() / ".claude-builder" / "templates"
        )
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.downloader = downloader or TemplateDownloader()
        self.repository_client = repository_client or TemplateRepositoryClient(
            self.downloader
        )
        self.validator = validator or ComprehensiveTemplateValidator()
        self.logger = logging.getLogger(__name__)

    def list_available_templates(
        self, *, include_installed: bool = True, include_community: bool = True
    ) -> List[CommunityTemplate]:
        """List all available templates.

        Args:
            include_installed: Whether to include locally installed templates
            include_community: Whether to include remote community templates

        Returns:
            List of available community templates
        """
        templates = []

        if include_installed:
            templates.extend(self._list_installed_templates())

        if include_community:
            templates.extend(self._discover_community_templates())

        # Remove duplicates, preferring installed versions
        unique_templates = {}
        for template in templates:
            key = template.id
            if key not in unique_templates or template.installed:
                unique_templates[key] = template

        return list(unique_templates.values())

    def search_templates(
        self, query: str, project_analysis: Optional[ProjectAnalysis] = None
    ) -> List[CommunityTemplate]:
        """Search for templates matching query and project analysis.

        Args:
            query: Search query string
            project_analysis: Optional project analysis for compatibility ranking

        Returns:
            List of matching templates, ranked by relevance
        """
        all_templates = self.list_available_templates()

        # Filter by query
        query_lower = query.lower()
        matching_templates = []

        for template in all_templates:
            # Check name, description, tags, languages, frameworks
            search_text = (
                f"{template.metadata.name} {template.metadata.description} "
                f"{' '.join(template.metadata.tags)} "
                f"{' '.join(template.metadata.languages)} "
                f"{' '.join(template.metadata.frameworks)}"
            ).lower()

            if query_lower in search_text:
                matching_templates.append(template)

        # If project analysis provided, rank by compatibility
        if project_analysis:
            template_scores = []
            for template in matching_templates:
                matches, score = template.matches_project(project_analysis)
                template_scores.append((template, score))

            # Sort by compatibility score
            template_scores.sort(key=lambda x: x[1], reverse=True)
            matching_templates = [template for template, _ in template_scores]

        return matching_templates

    def install_template(
        self, template_id: str, *, force: bool = False
    ) -> ValidationResult:
        """Install a community template.

        Args:
            template_id: Template identifier (name or author/name)
            force: Whether to reinstall if already installed

        Returns:
            ValidationResult indicating success/failure and details
        """
        # Find template in community sources
        template_metadata = self.repository_client.find_template_metadata(template_id)
        if not template_metadata:
            return ValidationResult(
                is_valid=False, errors=[f"Template not found: {template_id}"]
            )

        template = CommunityTemplate(
            metadata=TemplateMetadata(template_metadata),
            source_url=template_metadata.get("source_url"),
        )

        # Check if already installed
        install_path = self.templates_dir / "community" / template.metadata.name
        if install_path.exists() and not force:
            return ValidationResult(
                is_valid=False,
                errors=[
                    f"Template already installed: {template_id}. "
                    f"Use --force to reinstall."
                ],
            )

        # Download and install
        try:
            return self._download_and_install_template(template, install_path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Failed to install template {template_id}: {e}"],
            )

    def uninstall_template(self, template_name: str) -> ValidationResult:
        """Uninstall an installed template.

        Args:
            template_name: Name of template to uninstall

        Returns:
            ValidationResult indicating success/failure
        """
        template_path = self.templates_dir / "community" / template_name

        if not template_path.exists():
            return ValidationResult(
                is_valid=False, errors=[f"Template not installed: {template_name}"]
            )

        try:
            shutil.rmtree(template_path)
            return ValidationResult(
                is_valid=True, suggestions=[f"Template uninstalled: {template_name}"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Failed to uninstall template {template_name}: {e}"],
            )

    def get_template_info(self, template_name: str) -> Optional[CommunityTemplate]:
        """Get detailed information about a template.

        Args:
            template_name: Name of template

        Returns:
            CommunityTemplate instance if found, None otherwise
        """
        # Check installed templates first
        installed_templates = self._list_installed_templates()
        for template in installed_templates:
            if template.metadata.name == template_name:
                return template

        # Check community templates
        community_templates = self._discover_community_templates()
        for template in community_templates:
            if template.metadata.name == template_name:
                return template

        return None

    def create_custom_template(
        self, name: str, project_path: Path, template_config: Dict[str, Any]
    ) -> ValidationResult:
        """Create a custom template from existing project.

        Args:
            name: Name for the custom template
            project_path: Path to source project
            template_config: Configuration for template creation

        Returns:
            ValidationResult indicating success/failure
        """
        # Validate inputs
        if not project_path.exists():
            return ValidationResult(
                is_valid=False, errors=["Project path does not exist"]
            )

        # Create template directory
        template_path = self.templates_dir / "custom" / name
        template_path.mkdir(parents=True, exist_ok=True)

        try:
            # Create metadata
            metadata = {
                "name": name,
                "version": "1.0.0",
                "description": template_config.get(
                    "description", f"Custom template for {name}"
                ),
                "author": template_config.get("author", "local-user"),
                "category": template_config.get("category", "custom"),
                "languages": template_config.get("languages", []),
                "frameworks": template_config.get("frameworks", []),
                "project_types": template_config.get("project_types", []),
                "created": datetime.now(tz=timezone.utc).isoformat(),
                "updated": datetime.now(tz=timezone.utc).isoformat(),
            }

            # Write metadata
            with (template_path / "template.json").open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Generate template files from project analysis
            self._generate_template_files(project_path, template_path, template_config)

            # Validate created template
            validation_result = self.validator.validate_template(template_path)

            if validation_result.is_valid:
                validation_result.suggestions.append(
                    f"Custom template created: {template_path}"
                )

            return validation_result

        except Exception as e:
            # Clean up on failure
            if template_path.exists():
                shutil.rmtree(template_path)
            return ValidationResult(
                is_valid=False, errors=[f"Failed to create custom template: {e}"]
            )

    def _list_installed_templates(self) -> List[CommunityTemplate]:
        """List locally installed templates."""
        templates = []

        # Check community templates directory
        community_dir = self.templates_dir / "community"
        if community_dir.exists():
            for template_dir in community_dir.iterdir():
                if template_dir.is_dir():
                    template = self._load_local_template(template_dir)
                    if template:
                        templates.append(template)

        # Check custom templates directory
        custom_dir = self.templates_dir / "custom"
        if custom_dir.exists():
            for template_dir in custom_dir.iterdir():
                if template_dir.is_dir():
                    template = self._load_local_template(template_dir)
                    if template:
                        templates.append(template)

        return templates

    def _load_local_template(self, template_path: Path) -> Optional[CommunityTemplate]:
        """Load template from local directory."""
        metadata_file = template_path / "template.json"
        if not metadata_file.exists():
            return None

        try:
            with metadata_file.open(encoding="utf-8") as f:
                metadata_data = json.load(f)

            metadata = TemplateMetadata(metadata_data)
            return CommunityTemplate(metadata, local_path=template_path)
        except Exception as e:
            self.logger.warning(f"Failed to load template from {template_path}: {e}")
            return None

    def _discover_community_templates(self) -> List[CommunityTemplate]:
        """Discover community templates from remote sources."""
        templates = []

        try:
            template_data_list = self.repository_client.discover_all_templates()

            for template_data in template_data_list:
                try:
                    metadata = TemplateMetadata(template_data)
                    template = CommunityTemplate(
                        metadata, source_url=template_data.get("source_url")
                    )
                    templates.append(template)
                except Exception as e:
                    self.logger.warning(f"Failed to create template from data: {e}")
                    continue
        except Exception as e:
            self.logger.exception(f"Failed to discover community templates: {e}")

        return templates

    def _download_and_install_template(
        self, template: CommunityTemplate, install_path: Path
    ) -> ValidationResult:
        """Download and install a template."""
        if not template.source_url:
            return ValidationResult(
                is_valid=False, errors=["Template has no source URL"]
            )

        try:
            # Download and extract template
            template_root = self.downloader.download_and_extract_template(
                template.source_url, template.metadata.name
            )

            # Validate before installation
            validation_result = self.validator.validate_template(template_root)
            if not validation_result.is_valid:
                return validation_result

            # Install template
            if install_path.exists():
                shutil.rmtree(install_path)

            shutil.copytree(template_root, install_path)

            validation_result.suggestions.append(
                f"Template installed to: {install_path}"
            )
            return validation_result

        except Exception as e:
            return ValidationResult(
                is_valid=False, errors=[f"Failed to download and install template: {e}"]
            )

    def _generate_template_files(
        self, project_path: Path, template_path: Path, config: Dict[str, Any]
    ) -> None:
        """Generate template files from a project.

        This is a simplified implementation that would be expanded
        to integrate with the actual project analysis and generation system.
        """
        # Create basic template structure
        claude_instructions = f"""# {config.get('name', 'Custom Template')} - Claude Instructions

This is a custom template created from project analysis.

## Project Overview
- **Name**: {config.get('name', 'Custom Template')}
- **Languages**: {', '.join(config.get('languages', []))}
- **Frameworks**: {', '.join(config.get('frameworks', []))}

## Development Guidelines

Follow the patterns established in the original project at {project_path}.
"""

        # Write Claude instructions
        with (template_path / "claude_instructions.md").open(
            "w", encoding="utf-8"
        ) as f:
            f.write(claude_instructions)

        # Create basic README
        readme_content = f"""# {config.get('name', 'Custom Template')}

{config.get('description', 'A custom template generated from project analysis.')}

## Usage

This template is automatically used by Claude Builder when it matches your
project characteristics.

## Template Variables

- `${{project_name}}` - Name of the project
- `${{project_path}}` - Path to the project

---

*Generated by Claude Builder Template Creator*
*Created: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with (template_path / "README.md").open("w", encoding="utf-8") as f:
            f.write(readme_content)
