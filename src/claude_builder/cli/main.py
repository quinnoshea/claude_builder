"""Main CLI interface for Claude Builder."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.config import ConfigManager
from claude_builder.core.generator import DocumentGenerator
from claude_builder.core.template_manager import TemplateManager
from claude_builder.utils.exceptions import ClaudeBuilderError
from claude_builder.utils.git import GitIntegrationManager
from claude_builder.utils.validation import validate_project_path

INVALID_PROJECT_PATH = "Invalid project path"
PROJECT_PATH_IS_NONE = "project_path is None!"

console = Console()


class ExitCodes:
    """Exit codes for claude-builder."""
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


@click.group(invoke_without_command=True)
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=False)
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
@click.option("--verbose", "-v", count=True, help="Verbose output (can be repeated: -vv, -vvv)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.option("--config", "config_file", type=click.Path(exists=True), help="Use specific configuration file")
@click.option("--template", help="Use specific template (overrides detection)")
@click.option("--list-templates", is_flag=True, help="Show available templates and exit")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: PROJECT_PATH)")
@click.option("--format", "output_format", type=click.Choice(["files", "zip", "tar"]), default="files", help="Output format")
@click.option("--backup-existing", is_flag=True, help="Backup existing files before overwriting")
@click.option("--git-exclude", is_flag=True, help="Add generated files to .git/info/exclude")
@click.option("--git-track", is_flag=True, help="Track generated files in git")
@click.option("--claude-mentions", type=click.Choice(["allowed", "minimal", "forbidden"]), default="minimal", help="Control Claude references")
@click.option("--no-git", is_flag=True, help="Skip all git integration")
@click.option("--agents-only", is_flag=True, help="Only configure agents, skip documentation generation")
@click.option("--no-agents", is_flag=True, help="Skip agent configuration")
@click.option("--custom-agents", type=click.Path(exists=True, file_okay=False), help="Include custom agents from directory")
@click.version_option()
@click.pass_context
def cli(ctx, project_path, **kwargs):
    """Universal Claude Code Environment Generator.
    
    Analyzes any project directory and generates optimized Claude Code development
    environments with intelligent project detection and customizable configurations.
    
    Examples:
        claude-builder ./my-project
        claude-builder ./project --git-exclude --claude-mentions=minimal
        claude-builder ./project --dry-run --verbose
    """

    # Handle list templates
    if kwargs["list_templates"]:
        _list_templates()
        return

    # If no subcommand was called and no project path, show help
    if ctx.invoked_subcommand is None:
        if not project_path:
            click.echo(ctx.get_help())
            return

    # Main execution (only if no subcommand)
    if ctx.invoked_subcommand is None:
        try:
            _execute_main(project_path, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            sys.exit(ExitCodes.INTERRUPTED)
        except ClaudeBuilderError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(e.exit_code)
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            if kwargs["verbose"] > 0:
                console.print_exception()
            sys.exit(ExitCodes.GENERAL_ERROR)


def _execute_main(project_path: str, **kwargs) -> None:
    """Execute the main claude-builder workflow."""
    project_path = Path(project_path).resolve()

    # Validate project path
    validation_result = validate_project_path(project_path)
    if not validation_result.is_valid:
        raise ClaudeBuilderError(
            f"{INVALID_PROJECT_PATH}: {validation_result.error}",
            ExitCodes.PROJECT_NOT_FOUND
        )

    # Set up configuration
    config_manager = ConfigManager()
    config = config_manager.load_config(
        project_path=project_path,
        config_file=kwargs.get("config_file"),
        cli_overrides=kwargs
    )

    if not kwargs["quiet"]:
        console.print(Panel(
            f"[bold blue]Claude Builder[/bold blue]\n"
            f"Analyzing project at: [cyan]{project_path}[/cyan]\n"
            f"Template: [green]{kwargs.get('template', 'auto-detect')}[/green]\n"
            f"Git integration: [yellow]{_get_git_mode(kwargs)}[/yellow]",
            title="Starting Analysis"
        ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=kwargs["quiet"]
    ) as progress:

        # Step 1: Project Analysis
        task1 = progress.add_task("Analyzing project structure...", total=None)
        analyzer = ProjectAnalyzer(config=config.analysis.__dict__)
        analysis = analyzer.analyze(project_path)
        progress.update(task1, completed=True, description="✓ Project analysis complete")

        if kwargs["verbose"] > 0:
            _display_analysis_results(analysis)

        # Step 2: Document Generation
        if not kwargs["agents_only"]:
            task2 = progress.add_task("Generating documentation...", total=None)
            generator = DocumentGenerator(config=config.templates.__dict__)
            generated_content = generator.generate(analysis, project_path)
            progress.update(task2, completed=True, description="✓ Documentation generated")

            # Write files if not dry run
            if not kwargs["dry_run"]:
                _write_generated_files(generated_content, project_path, kwargs)

        # Step 3: Agent Configuration
        if not kwargs["no_agents"]:
            task3 = progress.add_task("Configuring agents...", total=None)
            
            # Initialize agent system
            from claude_builder.core.agents import UniversalAgentSystem
            from claude_builder.core.generator import DocumentGenerator
            
            agent_system = UniversalAgentSystem()
            
            # Configure agents for this project
            agent_config = agent_system.select_agents(analysis)
            
            # Generate AGENTS.md file using DocumentGenerator
            agent_generator = DocumentGenerator({"agents_only": True})
            agent_content = agent_generator.generate(analysis, project_path)
            
            # Extract AGENTS.md content and add to generated files
            if agent_content.files.get("AGENTS.md"):
                generated_content.files["AGENTS.md"] = agent_content.files["AGENTS.md"]
            
            progress.update(task3, completed=True, description="✓ Agents configured")

        # Step 4: Git Integration
        if not kwargs["no_git"] and (kwargs["git_exclude"] or kwargs["git_track"]):
            task4 = progress.add_task("Setting up git integration...", total=None)
            git_manager = GitIntegrationManager()
            git_result = git_manager.integrate(project_path, config.git_integration)
            progress.update(task4, completed=True, description="✓ Git integration complete")

    # Summary
    if not kwargs["quiet"]:
        _display_summary(project_path, kwargs["dry_run"])


def _get_git_mode(kwargs: dict) -> str:
    """Get git integration mode description."""
    if kwargs["no_git"]:
        return "disabled"
    if kwargs["git_exclude"]:
        return "exclude generated files"
    if kwargs["git_track"]:
        return "track generated files"
    return "no changes"


def _list_templates() -> None:
    """List available templates (legacy support)."""
    # Use the new template manager for listing
    try:
        manager = TemplateManager()
        templates = manager.list_available_templates()

        if not templates:
            console.print("[yellow]No templates available[/yellow]")
            return

        from rich.table import Table

        table = Table(title="Available Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Category", style="blue")
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow")

        for template in templates[:10]:  # Limit to first 10
            status = "✓ Installed" if template.installed else "Available"
            table.add_row(
                template.metadata.name,
                template.metadata.version,
                template.metadata.category,
                template.metadata.description[:50] + "..." if len(template.metadata.description) > 50 else template.metadata.description,
                status
            )

        console.print(table)

        if len(templates) > 10:
            console.print(f"\n[dim]... and {len(templates) - 10} more. Use 'claude-builder templates list' for full list[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        # Fallback to hardcoded list
        from rich.table import Table

        table = Table(title="Built-in Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")

        # Built-in templates
        templates = [
            ("python-web", "Language+Framework", "Python web applications (Django, Flask, FastAPI)"),
            ("rust-cli", "Language+Type", "Rust command-line tools"),
            ("javascript-react", "Language+Framework", "React web applications"),
        ]

        for name, type_name, description in templates:
            table.add_row(name, type_name, description)

        console.print(table)


def _display_analysis_results(analysis) -> None:
    """Display project analysis results."""
    console.print("\n[bold]Analysis Results:[/bold]")
    console.print(f"Language: [green]{analysis.language_info.primary or 'Unknown'}[/green] ({analysis.language_info.confidence:.1f}% confidence)")
    if analysis.language_info.secondary:
        console.print(f"Secondary languages: [dim]{', '.join(analysis.language_info.secondary)}[/dim]")
    console.print(f"Framework: [blue]{analysis.framework_info.primary or 'None detected'}[/blue] ({analysis.framework_info.confidence:.1f}% confidence)")
    console.print(f"Project type: [yellow]{analysis.project_type.value.replace('_', ' ').title()}[/yellow]")
    console.print(f"Complexity: [magenta]{analysis.complexity_level.value.title()}[/magenta]")
    console.print(f"Files: [cyan]{analysis.filesystem_info.total_files}[/cyan] total, [cyan]{analysis.filesystem_info.source_files}[/cyan] source")
    if analysis.domain_info and analysis.domain_info.domain:
        console.print(f"Domain: [purple]{analysis.domain_info.domain.replace('_', ' ').title()}[/purple] ({analysis.domain_info.confidence:.1f}% confidence)")
    console.print(f"Overall confidence: [bright_green]{analysis.analysis_confidence:.1f}%[/bright_green]")


def _write_generated_files(generated_content, project_path: Path, kwargs: dict) -> None:
    """Write generated files to disk."""
    # Debug: Check what's None
    if project_path is None:
        raise ValueError(f"{PROJECT_PATH_IS_NONE} kwargs: {kwargs}")
    if kwargs.get("output_dir") is None:
        output_dir = project_path
    else:
        output_dir = Path(kwargs["output_dir"])

    files_written = 0
    for filename, content in generated_content.files.items():
        file_path = output_dir / filename

        # Create directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file if requested
        if kwargs["backup_existing"] and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            file_path.rename(backup_path)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        files_written += 1

    if not kwargs["quiet"]:
        console.print(f"\n[green]✓ Wrote {files_written} files to {output_dir}[/green]")


def _display_summary(project_path: Path, dry_run: bool) -> None:
    """Display operation summary."""
    action = "Would generate" if dry_run else "Generated"
    console.print("\n[bold green]✓ Complete![/bold green]")
    console.print(f"{action} Claude Code environment for [cyan]{project_path}[/cyan]")

    if not dry_run:
        console.print("\nNext steps:")
        console.print("1. Review generated CLAUDE.md file")
        console.print("2. Configure agents using the generated AGENTS.md")
        console.print("3. Start using Claude Code with your optimized environment!")


# Import and register subcommands
from .analyze_commands import analyze
from .config_commands import config
from .generate_commands import generate
from .git_commands import git
from .template_commands import templates

# Register subcommands
cli.add_command(templates)
cli.add_command(analyze)
cli.add_command(generate)
cli.add_command(config)
cli.add_command(git)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
