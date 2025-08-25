"""Template management CLI commands for Claude Builder."""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.template_manager import CommunityTemplate, TemplateManager


if TYPE_CHECKING:
    import builtins

FAILED_TO_LIST_TEMPLATES = "Failed to list templates"
FAILED_TO_SEARCH_TEMPLATES = "Failed to search templates"
TEMPLATE_INSTALLATION_FAILED = "Template installation failed"
FAILED_TO_INSTALL_TEMPLATE = "Failed to install template"
TEMPLATE_UNINSTALLATION_FAILED = "Template uninstallation failed"
FAILED_TO_UNINSTALL_TEMPLATE = "Failed to uninstall template"
TEMPLATE_CREATION_FAILED = "Template creation failed"
FAILED_TO_CREATE_TEMPLATE = "Failed to create template"
TEMPLATE_VALIDATION_FAILED = "Template validation failed"
FAILED_TO_VALIDATE_TEMPLATE = "Failed to validate template"
FAILED_TO_GET_TEMPLATE_INFO = "Failed to get template info"


# Define ExitCodes locally to avoid circular import
class ExitCodes:
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    PROJECT_NOT_FOUND = 3
    NOT_A_PROJECT = 4
    ANALYSIS_FAILED = 5
    TEMPLATE_ERROR = 6
    AGENT_ERROR = 7
    GIT_ERROR = 8
    PERMISSION_ERROR = 9
    CONFIG_ERROR = 10
    INTERRUPTED = 128


console = Console()


@dataclass
class TemplateConfig:
    """Configuration for template commands."""

    project_path: str | None = None
    description: str | None = None
    author: str | None = None
    category: str | None = None
    languages: str | None = None
    frameworks: str | None = None
    project_types: str | None = None
    interactive: bool = False


@click.group()
def templates() -> None:
    """Manage templates and template sources."""


# Alias for backward compatibility
template = templates


@templates.command()
@click.option("--installed-only", is_flag=True, help="Show only installed templates")
@click.option("--community-only", is_flag=True, help="Show only community templates")
@click.option("--category", help="Filter by category")
@click.option("--language", help="Filter by primary language")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "list"]),
    default="table",
    help="Output format",
)
def list(
    *,
    installed_only: bool,
    community_only: bool,
    category: str | None,
    language: str | None,
    output_format: str,
) -> None:
    """List available templates."""
    try:
        manager = TemplateManager()

        include_installed = not community_only
        include_community = not installed_only

        templates = manager.list_available_templates(
            include_installed=include_installed, include_community=include_community
        )

        # Apply filters
        if category:
            templates = [
                t for t in templates if t.metadata.category.lower() == category.lower()
            ]

        if language:
            templates = [
                t
                for t in templates
                if language.lower() in [l.lower() for l in t.metadata.languages]
            ]

        # Display results
        if output_format == "json":
            _display_templates_json(templates)
        elif output_format == "list":
            _display_templates_list(templates)
        else:
            _display_templates_table(templates)

    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        msg = f"{FAILED_TO_LIST_TEMPLATES}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument("query", required=True)
@click.option(
    "--project-path",
    type=click.Path(exists=True, file_okay=False),
    help="Analyze project and rank templates by compatibility",
)
@click.option("--limit", type=int, default=10, help="Maximum number of results")
def search(query: str, project_path: str | None, limit: int) -> None:
    """Search for templates matching query."""
    try:
        manager = TemplateManager()

        # Analyze project if path provided
        project_analysis = None
        if project_path:
            analyzer = ProjectAnalyzer()
            project_analysis = analyzer.analyze(Path(project_path))

        # Search templates
        templates = manager.search_templates(query, project_analysis)
        templates = templates[:limit]  # Limit results

        if not templates:
            console.print(f"[yellow]No templates found matching '{query}'[/yellow]")
            return

        console.print(f"[bold]Search Results for '{query}'[/bold]")
        if project_path:
            console.print(f"[dim]Ranked by compatibility with {project_path}[/dim]")
        console.print()

        _display_templates_table(
            templates, show_compatibility=project_analysis is not None
        )

    except Exception as e:
        console.print(f"[red]Error searching templates: {e}[/red]")
        msg = f"{FAILED_TO_SEARCH_TEMPLATES}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument("template_id", required=True)
@click.option("--force", is_flag=True, help="Force reinstallation if already installed")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be installed without actually installing",
)
def install(template_id: str, *, force: bool, dry_run: bool) -> None:
    """Install a community template."""
    try:
        manager = TemplateManager()

        if dry_run:
            # Find template and show what would be installed
            template = manager._find_community_template(template_id)
            if not template:
                console.print(f"[red]Template not found: {template_id}[/red]")
                return

            console.print(
                Panel(
                    f"[bold]Would install template:[/bold]\n\n"
                    f"**Name**: {template.metadata.name}\n"
                    f"**Version**: {template.metadata.version}\n"
                    f"**Author**: {template.metadata.author}\n"
                    f"**Description**: {template.metadata.description}\n"
                    f"**Category**: {template.metadata.category}\n"
                    f"**Languages**: {', '.join(template.metadata.languages)}\n"
                    f"**Frameworks**: {', '.join(template.metadata.frameworks)}",
                    title="Dry Run - Template Installation",
                )
            )
            return

        # Confirm installation for non-official templates
        if "/" not in template_id or not template_id.startswith("official/"):
            if not Confirm.ask(
                f"Install template '{template_id}' from community source?"
            ):
                console.print("[yellow]Installation cancelled[/yellow]")
                return

        # Install template
        console.print(f"[cyan]Installing template: {template_id}[/cyan]")
        result = manager.install_template(template_id, force=force)

        if result.is_valid:
            console.print("[green]✓ Template installed successfully[/green]")
            for suggestion in result.suggestions:
                console.print(f"  {suggestion}")
        else:
            console.print("[red]Installation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(TEMPLATE_INSTALLATION_FAILED)

    except Exception as e:
        console.print(f"[red]Error installing template: {e}[/red]")
        msg = f"{FAILED_TO_INSTALL_TEMPLATE}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument("template_name", required=True)
@click.option("--force", is_flag=True, help="Force uninstallation without confirmation")
def uninstall(template_name: str, *, force: bool) -> None:
    """Uninstall an installed template."""
    try:
        manager = TemplateManager()

        # Check if template is installed
        template = manager.get_template_info(template_name)
        if not template or not template.installed:
            console.print(f"[red]Template not installed: {template_name}[/red]")
            return

        # Confirm uninstallation
        if not force:
            if not Confirm.ask(f"Uninstall template '{template_name}'?"):
                console.print("[yellow]Uninstallation cancelled[/yellow]")
                return

        # Uninstall template
        console.print(f"[cyan]Uninstalling template: {template_name}[/cyan]")
        result = manager.uninstall_template(template_name)

        if result.is_valid:
            console.print("[green]✓ Template uninstalled successfully[/green]")
            for suggestion in result.suggestions:
                console.print(f"  {suggestion}")
        else:
            console.print("[red]Uninstallation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(TEMPLATE_UNINSTALLATION_FAILED)

    except Exception as e:
        console.print(f"[red]Error uninstalling template: {e}[/red]")
        msg = f"{FAILED_TO_UNINSTALL_TEMPLATE}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument("name", required=True)
@click.option(
    "--project-path",
    type=click.Path(exists=True, file_okay=False),
    help="Create template from existing project",
)
@click.option("--description", help="Template description")
@click.option("--author", help="Template author")
@click.option("--category", help="Template category")
@click.option("--languages", help="Comma-separated list of languages")
@click.option("--frameworks", help="Comma-separated list of frameworks")
@click.option("--project-types", help="Comma-separated list of project types")
@click.option("--interactive", is_flag=True, help="Interactive template creation")
def create(name: str, **kwargs: Any) -> None:
    """Create a custom template."""
    # Create config from kwargs
    config = TemplateConfig(**kwargs)

    try:
        # Interactive mode
        if config.interactive:
            description = config.description or Prompt.ask("Template description")
            author = config.author or Prompt.ask("Author name", default="local-user")
            category = config.category or Prompt.ask("Category", default="custom")
            languages = config.languages or Prompt.ask(
                "Languages (comma-separated)", default=""
            )
            frameworks = config.frameworks or Prompt.ask(
                "Frameworks (comma-separated)", default=""
            )
            project_types = config.project_types or Prompt.ask(
                "Project types (comma-separated)", default=""
            )
        else:
            description = config.description or ""
            author = config.author or ""
            category = config.category or ""
            languages = config.languages or ""
            frameworks = config.frameworks or ""
            project_types = config.project_types or ""

        # Set defaults
        description = description or f"Custom template for {name}"
        author = author or "local-user"
        category = category or "custom"

        # Parse comma-separated values
        languages_list = [l.strip() for l in (languages or "").split(",") if l.strip()]
        frameworks_list = [
            f.strip() for f in (frameworks or "").split(",") if f.strip()
        ]
        project_types_list = [
            p.strip() for p in (project_types or "").split(",") if p.strip()
        ]

        # Template configuration
        template_config = {
            "description": description,
            "author": author,
            "category": category,
            "languages": languages_list,
            "frameworks": frameworks_list,
            "project_types": project_types_list,
        }

        manager = TemplateManager()

        if config.project_path:
            # Create from existing project
            console.print(
                f"[cyan]Creating template '{name}' from project: "
                f"{config.project_path}[/cyan]"
            )
            result = manager.create_custom_template(
                name, Path(config.project_path), template_config
            )
        else:
            # Create empty template structure
            console.print(f"[cyan]Creating empty template: {name}[/cyan]")
            # TODO: Implement empty template creation
            console.print(
                "[yellow]Empty template creation not yet implemented[/yellow]"
            )
            console.print("Use --project-path to create template from existing project")
            return

        if result.is_valid:
            console.print("[green]✓ Custom template created successfully[/green]")
            for suggestion in result.suggestions:
                console.print(f"  {suggestion}")

            if result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")
        else:
            console.print("[red]Template creation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(TEMPLATE_CREATION_FAILED)

    except Exception as e:
        console.print(f"[red]Error creating template: {e}[/red]")
        msg = f"{FAILED_TO_CREATE_TEMPLATE}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument(
    "template_path", type=click.Path(exists=True, file_okay=False), required=True
)
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["detailed", "summary", "json"]),
    default="detailed",
    help="Output format",
)
def validate(template_path: str, *, strict: bool, output_format: str) -> None:
    """Validate a template directory."""
    try:
        manager = TemplateManager()
        path = Path(template_path)

        console.print(f"[cyan]Validating template: {path}[/cyan]")
        result = manager.validate_template_directory(path)

        if output_format == "json":
            # JSON output
            validation_data = {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "suggestions": result.suggestions,
            }
            console.print(json.dumps(validation_data, indent=2))
            return

        # Display validation results
        if result.is_valid and not result.warnings:
            console.print("[green]✓ Template is valid[/green]")
        elif result.is_valid:
            console.print("[yellow]⚠ Template is valid with warnings[/yellow]")
        else:
            console.print("[red]✗ Template validation failed[/red]")

        if result.errors:
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")

        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")

        if result.suggestions:
            console.print("\n[blue]Suggestions:[/blue]")
            for suggestion in result.suggestions:
                console.print(f"  • {suggestion}")

        # Exit with error code if validation failed
        if not result.is_valid or (strict and result.warnings):
            raise click.ClickException(TEMPLATE_VALIDATION_FAILED)

    except Exception as e:
        console.print(f"[red]Error validating template: {e}[/red]")
        msg = f"{FAILED_TO_VALIDATE_TEMPLATE}: {e}"
        raise click.ClickException(msg)


@templates.command()
@click.argument("template_name", required=True)
def info(template_name: str) -> None:
    """Show detailed information about a template."""
    try:
        manager = TemplateManager()
        template = manager.get_template_info(template_name)

        if not template:
            console.print(f"[red]Template not found: {template_name}[/red]")
            return

        # Display template information
        status = (
            "[green]Installed[/green]"
            if template.installed
            else "[yellow]Available[/yellow]"
        )

        info_panel = (
            f"[bold]{template.metadata.name}[/bold] "
            f"v{template.metadata.version} ({status})\n\n"
            f"[bold]Description:[/bold] {template.metadata.description}\n"
            f"[bold]Author:[/bold] {template.metadata.author}\n"
            f"[bold]Category:[/bold] {template.metadata.category}\n"
            f"[bold]License:[/bold] {template.metadata.license}\n\n"
            f"[bold]Compatibility:[/bold]\\n"
        )

        # Add compatibility information
        languages = (
            ", ".join(template.metadata.languages)
            if template.metadata.languages
            else "Any"
        )
        frameworks = (
            ", ".join(template.metadata.frameworks)
            if template.metadata.frameworks
            else "Any"
        )
        project_types = (
            ", ".join(template.metadata.project_types)
            if template.metadata.project_types
            else "Any"
        )
        tags = ", ".join(template.metadata.tags) if template.metadata.tags else "None"

        info_panel += (
            f"  Languages: {languages}\\n"
            f"  Frameworks: {frameworks}\\n"
            f"  Project Types: {project_types}\\n\\n"
            f"[bold]Tags:[/bold] {tags}"
        )

        if template.metadata.homepage:
            info_panel += f"\n[bold]Homepage:[/bold] {template.metadata.homepage}"

        if template.metadata.repository:
            info_panel += f"\n[bold]Repository:[/bold] {template.metadata.repository}"

        if template.metadata.created:
            info_panel += f"\n[bold]Created:[/bold] {template.metadata.created}"

        if template.metadata.updated:
            info_panel += f"\n[bold]Updated:[/bold] {template.metadata.updated}"

        console.print(Panel(info_panel, title=f"Template Info: {template_name}"))

        # Show installation command if not installed
        if not template.installed:
            console.print(
                f"\n[blue]To install:[/blue] "
                f"claude-builder templates install {template.id}"
            )

    except Exception as e:
        console.print(f"[red]Error getting template info: {e}[/red]")
        msg = f"{FAILED_TO_GET_TEMPLATE_INFO}: {e}"
        raise click.ClickException(msg)


def _display_templates_table(
    templates: builtins.list[CommunityTemplate], *, show_compatibility: bool = False
) -> None:
    """Display templates in table format."""
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="green")
    table.add_column("Author", style="blue")
    table.add_column("Category", style="magenta")
    table.add_column("Languages", style="white")
    table.add_column("Status", style="yellow")

    if show_compatibility:
        table.add_column("Compatibility", style="bright_green")

    for template in templates:
        status = "✓ Installed" if template.installed else "Available"
        languages = (
            ", ".join(template.metadata.languages)
            if template.metadata.languages
            else "Any"
        )

        row = [
            template.metadata.name,
            template.metadata.version,
            template.metadata.author,
            template.metadata.category,
            languages,
            status,
        ]

        if show_compatibility:
            # This would be computed during search
            row.append("N/A")  # Placeholder for compatibility score

        table.add_row(*row)

    console.print(table)


def _display_templates_list(templates: builtins.list[CommunityTemplate]) -> None:
    """Display templates in simple list format."""
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return

    for template in templates:
        status = "[green]✓[/green]" if template.installed else "[yellow]○[/yellow]"
        console.print(
            f"{status} {template.metadata.name} - {template.metadata.description}"
        )


def _display_templates_json(templates: builtins.list[CommunityTemplate]) -> None:
    """Display templates in JSON format."""
    template_data = []
    for template in templates:
        data = template.metadata.to_dict()
        data["installed"] = template.installed
        data["id"] = template.id
        template_data.append(data)

    console.print(json.dumps(template_data, indent=2))


# Function aliases for backward compatibility with tests
list_templates = templates.commands["list"]
show_template = templates.commands["info"]
validate_template = templates.commands["validate"]
