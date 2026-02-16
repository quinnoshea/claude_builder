"""Main CLI interface for Claude Builder."""

from __future__ import annotations

import sys

from pathlib import Path
from typing import Any

import click

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.config import ConfigManager
from claude_builder.core.generator import DocumentGenerator
from claude_builder.core.models import OutputTarget
from claude_builder.core.template_manager import TemplateManager
from claude_builder.utils.exceptions import ClaudeBuilderError
from claude_builder.utils.git import GitIntegrationManager
from claude_builder.utils.validation import validate_project_path

# Import subcommands
from .agent_commands import agents
from .analyze_commands import analyze
from .config_commands import config
from .generate_commands import generate
from .git_commands import git
from .health_commands import health
from .template_commands import templates


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
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option(
    "--verbose", "-v", count=True, help="Verbose output (can be repeated: -vv, -vvv)"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Use specific configuration file",
)
@click.option("--template", help="Use specific template (overrides detection)")
@click.option(
    "--list-templates", is_flag=True, help="Show available templates and exit"
)
@click.option(
    "--output-dir", type=click.Path(), help="Output directory (default: PROJECT_PATH)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["files", "zip", "tar"]),
    default="files",
    help="Output format",
)
@click.option(
    "--backup-existing", is_flag=True, help="Backup existing files before overwriting"
)
@click.option(
    "--git-exclude", is_flag=True, help="Add generated files to .git/info/exclude"
)
@click.option("--git-track", is_flag=True, help="Track generated files in git")
@click.option(
    "--claude-mentions",
    type=click.Choice(["allowed", "minimal", "forbidden"]),
    default="minimal",
    help="Control Claude references",
)
@click.option("--no-git", is_flag=True, help="Skip all git integration")
@click.option(
    "--agents-only",
    is_flag=True,
    help="Only configure agents, skip documentation generation",
)
@click.option("--no-agents", is_flag=True, help="Skip agent configuration")
@click.option(
    "--custom-agents",
    type=click.Path(exists=True, file_okay=False),
    help="Include custom agents from directory",
)
@click.option(
    "--target",
    type=click.Choice([target.value for target in OutputTarget], case_sensitive=False),
    default=OutputTarget.CLAUDE.value,
    show_default=True,
    help="Output target profile for complete generation",
)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context, project_path: str | None, **kwargs: Any) -> None:
    """Universal Claude Code Environment Generator.

    Analyzes any project directory and generates optimized Claude Code development
    environments with intelligent project detection and customizable configurations.

    \b
    Examples:
        # Quick start - generate complete environment
        claude-builder ./my-project

        # Analyze and generate documentation in one step
        claude-builder analyze project ./k8s-app

        # Suggest agents for a data-heavy pipeline project
        claude-builder agents suggest --project-path ./data-pipeline

        # Interactive analysis (scaffold)
        claude-builder analyze project ./app --interactive

        # Dry run to preview changes
        claude-builder ./project --dry-run --verbose

        # Generate Codex-oriented artifacts from top-level workflow
        claude-builder --target codex ./my-project
    """

    # Handle list templates
    if kwargs["list_templates"]:
        _list_templates()
        return

    # If no subcommand was called and no project path, show help
    if ctx.invoked_subcommand is None and not project_path:
        click.echo(ctx.get_help())
        return

    # Main execution (only if no subcommand)
    if ctx.invoked_subcommand is None:
        if project_path is None:
            click.echo(ctx.get_help())
            return
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


def _execute_main(project_path: str, **kwargs: Any) -> None:
    """Execute the main claude-builder workflow."""
    project_path_obj = Path(project_path).resolve()

    # Validate project path
    validation_result = validate_project_path(project_path_obj)
    if not validation_result.is_valid:
        msg = f"{INVALID_PROJECT_PATH}: {validation_result.error}"
        raise ClaudeBuilderError(
            msg,
            ExitCodes.PROJECT_NOT_FOUND,
        )

    # Set up configuration
    config_manager = ConfigManager()
    config = config_manager.load_config(
        project_path=project_path_obj,
        config_file=kwargs.get("config_file"),
        cli_overrides=kwargs,
    )
    target = _resolve_target(kwargs)
    output_mode = _get_output_mode(kwargs)

    if not kwargs["quiet"]:
        console.print(
            Panel(
                f"[bold blue]Claude Builder[/bold blue]\n"
                f"Analyzing project at: [cyan]{project_path_obj}[/cyan]\n"
                f"Template: [green]{kwargs.get('template', 'auto-detect')}[/green]\n"
                f"Output mode: [blue]{output_mode}[/blue]\n"
                f"Git integration: [yellow]{_get_git_mode(kwargs)}[/yellow]",
                title="Starting Analysis",
            )
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=kwargs["quiet"],
    ) as progress:
        # Step 1: Project Analysis
        task1 = progress.add_task("Analyzing project structure...", total=None)
        analyzer = ProjectAnalyzer(config=config.analysis.__dict__)
        analysis = analyzer.analyze(project_path_obj)
        progress.update(
            task1, completed=True, description="✓ Project analysis complete"
        )

        if kwargs["verbose"] > 0:
            _display_analysis_results(analysis)

        # Step 2: Complete Environment Generation
        if not (kwargs["agents_only"] or kwargs["no_agents"]):
            task2 = progress.add_task(
                f"Generating {target.value} artifacts...", total=None
            )

            template_manager = TemplateManager()
            rendered_output = template_manager.generate_target_artifacts(
                analysis,
                target=target,
            )

            progress.update(
                task2,
                completed=True,
                description=f"✓ {target.value.title()} artifacts generated",
            )

            # Write files if not dry run
            if not kwargs["dry_run"]:
                _write_target_artifacts(rendered_output, project_path_obj, kwargs)

        elif kwargs["agents_only"]:
            # Legacy: agents-only mode
            task2 = progress.add_task("Configuring agents...", total=None)

            template_manager = TemplateManager()
            rendered_output = template_manager.generate_target_artifacts(
                analysis,
                target=target,
            )

            progress.update(task2, completed=True, description="✓ Agents configured")

            # Write only AGENTS.md if not dry run
            if not kwargs["dry_run"]:
                agents_artifact = next(
                    (
                        artifact
                        for artifact in rendered_output.artifacts
                        if artifact.path == "AGENTS.md"
                    ),
                    None,
                )
                if agents_artifact is None:
                    msg = f"Generated {target.value} output is missing AGENTS.md"
                    raise ClaudeBuilderError(msg, ExitCodes.AGENT_ERROR)

                if kwargs.get("output_dir") is None:
                    output_dir = project_path_obj
                else:
                    output_dir = Path(kwargs["output_dir"])
                output_dir.mkdir(parents=True, exist_ok=True)

                agents_path = output_dir / "AGENTS.md"
                if kwargs["backup_existing"] and agents_path.exists():
                    backup_path = agents_path.with_suffix(agents_path.suffix + ".bak")
                    agents_path.rename(backup_path)

                with agents_path.open("w", encoding="utf-8") as f:
                    f.write(agents_artifact.content)

        elif not kwargs["no_agents"]:
            # Legacy: documentation without agents
            task2 = progress.add_task("Generating documentation...", total=None)
            generator = DocumentGenerator(config=config.templates.__dict__)
            generated_content = generator.generate(analysis, project_path_obj)
            progress.update(
                task2, completed=True, description="✓ Documentation generated"
            )

            # Write files if not dry run
            if not kwargs["dry_run"]:
                _write_generated_files(generated_content, project_path_obj, kwargs)

        # Step 4: Git Integration
        if not kwargs["no_git"] and (kwargs["git_exclude"] or kwargs["git_track"]):
            task4 = progress.add_task("Setting up git integration...", total=None)
            git_manager = GitIntegrationManager()
            git_manager.integrate(project_path_obj, config.git_integration)
            progress.update(
                task4, completed=True, description="✓ Git integration complete"
            )

    # Summary
    if not kwargs["quiet"]:
        _display_summary(
            project_path_obj,
            dry_run=kwargs["dry_run"],
            target=target,
            output_mode=output_mode,
        )


def _get_output_mode(kwargs: dict[str, Any]) -> str:
    """Get output mode description."""
    if kwargs["agents_only"]:
        return "agents only"
    if kwargs["no_agents"]:
        return "documentation only"
    target = _resolve_target(kwargs)
    if target == OutputTarget.CLAUDE:
        return "complete environment (CLAUDE.md + subagents + AGENTS.md)"
    if target == OutputTarget.CODEX:
        return "complete environment (AGENTS.md + .agents/skills/*/SKILL.md)"
    return "complete environment (GEMINI.md + AGENTS.md + .gemini/agents/*.md)"


def _resolve_target(kwargs: dict[str, Any]) -> OutputTarget:
    """Resolve target enum from CLI kwargs."""
    raw_target = str(kwargs.get("target", OutputTarget.CLAUDE.value)).lower()
    return OutputTarget(raw_target)


def _get_git_mode(kwargs: dict[str, Any]) -> str:
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
                (
                    template.metadata.description[:50] + "..."
                    if len(template.metadata.description) > 50
                    else template.metadata.description
                ),
                status,
            )

        console.print(table)

        if len(templates) > 10:
            console.print(
                f"\n[dim]... and {len(templates) - 10} more. "
                f"Use 'claude-builder templates list' for full list[/dim]"
            )

    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        # Fallback to hardcoded list
        from rich.table import Table

        table = Table(title="Built-in Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")

        # Built-in templates
        builtin_templates: list[tuple[str, str, str]] = [
            (
                "python-web",
                "Language+Framework",
                "Python web applications (Django, Flask, FastAPI)",
            ),
            ("rust-cli", "Language+Type", "Rust command-line tools"),
            ("javascript-react", "Language+Framework", "React web applications"),
        ]

        for name, type_name, description in builtin_templates:
            table.add_row(name, type_name, description)

        console.print(table)


def _display_analysis_results(analysis: Any) -> None:
    """Display project analysis results."""
    console.print("\n[bold]Analysis Results:[/bold]")
    console.print(
        f"Language: [green]{analysis.language_info.primary or 'Unknown'}[/green] "
        f"({analysis.language_info.confidence:.1f}% confidence)"
    )
    if analysis.language_info.secondary:
        console.print(
            f"Secondary languages: "
            f"[dim]{', '.join(analysis.language_info.secondary)}[/dim]"
        )
    console.print(
        f"Framework: [blue]{analysis.framework_info.primary or 'None detected'}[/blue] "
        f"({analysis.framework_info.confidence:.1f}% confidence)"
    )
    console.print(
        f"Project type: "
        f"[yellow]{analysis.project_type.value.replace('_', ' ').title()}[/yellow]"
    )
    console.print(
        f"Complexity: [magenta]{analysis.complexity_level.value.title()}[/magenta]"
    )
    console.print(
        f"Files: [cyan]{analysis.filesystem_info.total_files}[/cyan] total, "
        f"[cyan]{analysis.filesystem_info.source_files}[/cyan] source"
    )
    if analysis.domain_info and analysis.domain_info.domain:
        console.print(
            f"Domain: "
            f"[purple]{analysis.domain_info.domain.replace('_', ' ').title()}[/purple] "
            f"({analysis.domain_info.confidence:.1f}% confidence)"
        )
    console.print(
        f"Overall confidence: "
        f"[bright_green]{analysis.analysis_confidence:.1f}%[/bright_green]"
    )


def _write_environment_files(
    environment: Any, project_path: Path, kwargs: dict[str, Any]
) -> None:
    """Write complete environment files to disk."""

    if kwargs.get("output_dir") is None:
        output_dir = project_path
    else:
        output_dir = Path(kwargs["output_dir"])

    files_written = 0

    # Write CLAUDE.md
    claude_path = output_dir / "CLAUDE.md"
    if kwargs["backup_existing"] and claude_path.exists():
        backup_path = claude_path.with_suffix(claude_path.suffix + ".bak")
        claude_path.rename(backup_path)

    with claude_path.open("w", encoding="utf-8") as f:
        f.write(environment.claude_md)
    files_written += 1

    # Write individual subagents
    agents_dir = output_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    for subagent in environment.subagent_files:
        agent_path = agents_dir / subagent.name
        if kwargs["backup_existing"] and agent_path.exists():
            backup_path = agent_path.with_suffix(agent_path.suffix + ".bak")
            agent_path.rename(backup_path)

        with agent_path.open("w", encoding="utf-8") as f:
            f.write(subagent.content)
        files_written += 1

    # Write AGENTS.md
    agents_guide_path = output_dir / "AGENTS.md"
    if kwargs["backup_existing"] and agents_guide_path.exists():
        backup_path = agents_guide_path.with_suffix(agents_guide_path.suffix + ".bak")
        agents_guide_path.rename(backup_path)

    with agents_guide_path.open("w", encoding="utf-8") as f:
        f.write(environment.agents_md)
    files_written += 1

    if not kwargs["quiet"]:
        console.print("\n[green]✓ Generated complete environment:[/green]")
        console.print("   • CLAUDE.md - Project documentation")
        console.print(
            f"   • {len(environment.subagent_files)} subagent files in .claude/agents/"
        )
        console.print("   • AGENTS.md - User guide")
        console.print(f"   • Total: {files_written} files written to {output_dir}")


def _write_target_artifacts(
    rendered_output: Any, project_path: Path, kwargs: dict[str, Any]
) -> None:
    """Write target-specific artifacts to disk."""
    if kwargs.get("output_dir") is None:
        output_dir = project_path
    else:
        output_dir = Path(kwargs["output_dir"])

    files_written = 0
    for artifact in rendered_output.artifacts:
        file_path = output_dir / artifact.path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if kwargs["backup_existing"] and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            file_path.rename(backup_path)

        with file_path.open("w", encoding="utf-8") as f:
            f.write(artifact.content)

        files_written += 1

    if not kwargs["quiet"]:
        target_name = getattr(rendered_output, "target", OutputTarget.CLAUDE)
        if isinstance(target_name, OutputTarget):
            target_label = target_name.value.title()
        else:
            target_label = str(target_name).title()
        console.print(f"\n[green]✓ Generated {target_label} artifacts:[/green]")
        console.print(f"   • Total: {files_written} files written to {output_dir}")


def _write_generated_files(
    generated_content: Any, project_path: Path, kwargs: dict[str, Any]
) -> None:
    """Write generated files to disk."""
    # Debug: Check what's None
    if project_path is None:
        msg = f"{PROJECT_PATH_IS_NONE} kwargs: {kwargs}"  # type: ignore[unreachable]
        raise ValueError(msg)
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
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)

        files_written += 1

    # Always provide a minimal summary for visibility in tests
    console.print(f"\n[green]✓ Wrote {files_written} files to {output_dir}[/green]")


def _display_summary(
    project_path: Path,
    *,
    dry_run: bool,
    target: OutputTarget = OutputTarget.CLAUDE,
    output_mode: str = "complete environment (CLAUDE.md + subagents + AGENTS.md)",
) -> None:
    """Display operation summary."""
    action = "Would generate" if dry_run else "Generated"
    console.print("\n[bold green]✓ Complete![/bold green]")
    if output_mode == "documentation only":
        console.print(f"{action} documentation for [cyan]{project_path}[/cyan]")
    elif output_mode == "agents only":
        console.print(f"{action} AGENTS.md for [cyan]{project_path}[/cyan]")
    else:
        console.print(
            f"{action} {target.value.title()} environment for [cyan]{project_path}[/cyan]"
        )

    if not dry_run:
        console.print("\nNext steps:")
        if output_mode == "documentation only":
            console.print("1. Review generated documentation files")
            console.print("2. Run full generation to include agent guidance")
            console.print("3. Re-run after major project changes")
            return

        if output_mode == "agents only":
            console.print("1. Review generated AGENTS.md guide")
            console.print("2. Run full generation to include project context files")
            console.print("3. Start using the agent guidance in your workflow")
            return

        if target == OutputTarget.CLAUDE:
            primary_file = "CLAUDE.md"
            specialist_dir = ".claude/agents/"
            tool_name = "Claude Code"
        elif target == OutputTarget.CODEX:
            primary_file = "AGENTS.md"
            specialist_dir = ".agents/skills/"
            tool_name = "Codex CLI"
        else:
            primary_file = "GEMINI.md"
            specialist_dir = ".gemini/agents/"
            tool_name = "Gemini CLI"

        console.print(f"1. Review generated {primary_file} file")
        console.print(f"2. Review specialist files in {specialist_dir}")
        console.print(f"3. Start using {tool_name} with your optimized environment!")


# Register subcommands
cli.add_command(templates)
cli.add_command(agents)
cli.add_command(analyze)
cli.add_command(generate)
cli.add_command(config)
cli.add_command(git)
cli.add_command(health)


def main() -> None:
    """Main entry point for the CLI."""
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
