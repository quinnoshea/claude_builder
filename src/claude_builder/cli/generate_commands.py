"""Generation CLI commands for Claude Builder."""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

import click

from rich.console import Console
from rich.panel import Panel

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.generator import DocumentGenerator
from claude_builder.core.models import ProjectAnalysis
from claude_builder.utils.exceptions import ClaudeBuilderError

from .error_handling import handle_exception
from .next_steps import build_presenter
from .ux import UXConfig, build_ux_config


FAILED_TO_GENERATE_DOCUMENTATION = "Failed to generate documentation"
FAILED_TO_GENERATE_AGENTS = "Failed to generate agents"
FAILED_TO_LOAD_ANALYSIS = "Failed to load analysis from"
FAILED_TO_GENERATE_CLAUDE_MD = "Failed to generate CLAUDE.md"
FAILED_TO_GENERATE_AGENTS_MD = "Failed to generate AGENTS.md"

console = Console()


# Domain constants retained for backwards-compatible generation filters
VALID_DOMAINS = ["infra", "devops", "mlops"]


def _filter_generated_content_by_sections(
    generated_content: Any, sections_filter: list[str]
) -> dict[str, str]:
    """Filter generated content by specified sections."""
    filtered_files = {}

    for section in sections_filter:
        section_lower = section.lower()

        if section_lower == "claude":
            filtered_files.update(
                {
                    k: v
                    for k, v in generated_content.files.items()
                    if "claude" in k.lower()
                }
            )
        elif section_lower == "agents":
            filtered_files.update(
                {
                    k: v
                    for k, v in generated_content.files.items()
                    if "agent" in k.lower()
                }
            )
        elif section_lower == "docs":
            filtered_files.update(
                {
                    k: v
                    for k, v in generated_content.files.items()
                    if k.endswith(".md") and "agent" not in k.lower()
                }
            )
        else:
            # Try to match by filename
            filtered_files.update(
                {
                    k: v
                    for k, v in generated_content.files.items()
                    if section_lower in k.lower()
                }
            )

    return filtered_files


def _get_project_analysis(config: GenerateConfig, path: Path) -> Any:
    """Get project analysis from file or by analyzing the project."""
    if config.from_analysis:
        analysis = _load_analysis_from_file(Path(config.from_analysis))
        if config.verbose > 0:
            console.print(
                f"[green]Loaded analysis from: {config.from_analysis}[/green]"
            )
    else:
        if config.verbose > 0:
            console.print("[cyan]Analyzing project...[/cyan]")
        analyzer = ProjectAnalyzer()
        analysis = analyzer.analyze(path)

    return analysis


def _write_agent_files(agent_files: dict[str, str], output_path: Path) -> None:
    """Write agent files to disk."""
    if len(agent_files) == 1 and "AGENTS.md" in agent_files:
        # Write single file
        with output_path.open("w", encoding="utf-8") as f:
            f.write(agent_files["AGENTS.md"])
        console.print(f"[green]✓ Agent configuration written to: {output_path}[/green]")
    else:
        # Write multiple files
        for filename, content in agent_files.items():
            file_path = (
                output_path.parent / filename
                if output_path.is_file()
                else output_path / filename
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
        console.print(
            f"[green]✓ Agent files written to: "
            f"{output_path.parent if output_path.is_file() else output_path}[/green]"
        )


@dataclass
class GenerateConfig:
    """Configuration for generation commands."""

    from_analysis: str | None = None
    template: str | None = None
    partial: str | None = None
    output_dir: str | None = None
    output_format: str = "files"
    backup_existing: bool = False
    dry_run: bool = False
    verbose: int = 0
    no_suggestions: bool = False
    # Domain-specific generation filter
    domains: tuple[str, ...] = ()

    # Additional options for specific commands
    agents_dir: str | None = None
    output_file: str | None = None


@click.group()
def generate() -> None:
    """Generate documentation and configurations."""


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option("--template", help="Override template selection")
@click.option("--partial", help="Generate only specific sections (comma-separated)")
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
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option(
    "--domain",
    "domains",
    multiple=True,
    type=click.Choice(VALID_DOMAINS, case_sensitive=False),
    help="Filter generation by domain (repeatable): infra, devops, mlops",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
@click.option(
    "--no-suggestions",
    is_flag=True,
    help="Disable contextual suggestions after generation",
)
@click.pass_context
def docs(ctx: click.Context, project_path: str, **kwargs: Any) -> None:
    """Generate documentation from project analysis."""
    config = GenerateConfig(**kwargs)

    root_obj = ctx.find_root().obj if ctx.find_root() else None
    ux_config: UXConfig | None = None
    if isinstance(root_obj, dict):
        ux_config = root_obj.get("ux_config")
        if ux_config and config.no_suggestions:
            ux_config = ux_config.without_suggestions()
    if ux_config is None:
        ux_config = build_ux_config(
            quiet=False,
            verbose=config.verbose,
            no_suggestions=config.no_suggestions,
            plain_output=not console.is_terminal(),
        )

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating documentation for: {path}[/cyan]")

        # Get project analysis
        analysis = _get_project_analysis(config, path)

        # Configure generator
        generator_config = {"output_format": config.output_format}
        if config.template:
            generator_config["preferred_template"] = config.template

        # Generate content
        generator = DocumentGenerator(generator_config)
        generated_content = generator.generate(analysis, path)

        # Apply partial generation filter if specified
        if config.partial:
            sections_filter = [s.strip() for s in config.partial.split(",")]
            if config.verbose > 0:
                console.print(
                    f"[yellow]Generating only sections: {sections_filter}[/yellow]"
                )
            filtered_files = _filter_generated_content_by_sections(
                generated_content, sections_filter
            )
            generated_content.files = filtered_files

        # If domains specified, re-source CLAUDE.md using TemplateManager for gated sections
        if config.domains:
            from claude_builder.core.template_manager import TemplateManager

            if config.verbose > 0:
                console.print(
                    f"[yellow]Filtering domain sections: {', '.join(config.domains)}[/yellow]"
                )
            tm = TemplateManager()
            env = tm.generate_complete_environment(analysis, domains=config.domains)
            if "CLAUDE.md" in generated_content.files:
                generated_content.files["CLAUDE.md"] = env.claude_md

        # Display what would be generated
        if config.dry_run or config.verbose > 0:
            _display_generation_preview(generated_content)

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write files
        output_path = Path(config.output_dir) if config.output_dir else path
        written_files = _write_generated_files(
            generated_content,
            output_path,
            backup_existing=config.backup_existing,
            verbose=config.verbose,
        )

        console.print("[green]✓ Documentation generated successfully[/green]")
        console.print(f"Output location: {output_path}")

        if ux_config.suggestions_enabled:
            presenter = build_presenter(ux_config)
            presenter.show_generation(path, written_files)

    except Exception as e:
        exit_code = handle_exception(e, config=ux_config, console=console)
        raise click.exceptions.Exit(exit_code) from e


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option(
    "--output-dir", type=click.Path(), help="Output directory (default: PROJECT_PATH)"
)
@click.option(
    "--agents-dir",
    type=click.Path(),
    help="Directory for individual agent files (default: .claude/agents)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option(
    "--domain",
    "domains",
    multiple=True,
    type=click.Choice(VALID_DOMAINS, case_sensitive=False),
    help="Filter generation by domain (repeatable): infra, devops, mlops",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
@click.option(
    "--no-suggestions",
    is_flag=True,
    help="Disable contextual suggestions after generation",
)
@click.pass_context
def complete(ctx: click.Context, project_path: str, **kwargs: Any) -> None:
    """Generate complete Claude Code environment (CLAUDE.md + individual subagents + AGENTS.md)."""
    config = GenerateConfig(**kwargs)

    root_obj = ctx.find_root().obj if ctx.find_root() else None
    ux_config: UXConfig | None = None
    if isinstance(root_obj, dict):
        ux_config = root_obj.get("ux_config")
        if ux_config and config.no_suggestions:
            ux_config = ux_config.without_suggestions()
    if ux_config is None:
        ux_config = build_ux_config(
            quiet=False,
            verbose=config.verbose,
            no_suggestions=config.no_suggestions,
            plain_output=not console.is_terminal(),
        )

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating complete environment for: {path}[/cyan]")

        # Get project analysis
        analysis = _get_project_analysis(config, path)

        # Generate complete environment using TemplateManager
        from claude_builder.core.template_manager import TemplateManager

        template_manager = TemplateManager()
        opts: dict[str, Any] = {}
        if config.domains:
            opts["domains"] = config.domains
        environment = template_manager.generate_complete_environment(analysis, **opts)

        # Display what would be generated
        if config.dry_run or config.verbose > 0:
            _display_environment_preview(environment)

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Determine output paths
        output_dir = Path(config.output_dir) if config.output_dir else path
        agents_dir = (
            Path(config.agents_dir)
            if config.agents_dir
            else output_dir / ".claude" / "agents"
        )

        written_files: list[str] = []

        # Write CLAUDE.md
        claude_path = output_dir / "CLAUDE.md"
        with claude_path.open("w", encoding="utf-8") as f:
            f.write(environment.claude_md)
        written_files.append("CLAUDE.md")

        # Write individual subagents
        agents_dir.mkdir(parents=True, exist_ok=True)
        for subagent in environment.subagent_files:
            agent_path = agents_dir / subagent.name
            with agent_path.open("w", encoding="utf-8") as f:
                f.write(subagent.content)
            try:
                written_files.append(str(agent_path.relative_to(path)))
            except ValueError:
                written_files.append(str(agent_path))

        # Write AGENTS.md
        agents_guide_path = output_dir / "AGENTS.md"
        with agents_guide_path.open("w", encoding="utf-8") as f:
            f.write(environment.agents_md)
        written_files.append("AGENTS.md")

        console.print("[green]✓ Complete environment generated successfully[/green]")
        console.print("Generated:")
        console.print("   • CLAUDE.md - Project documentation")
        console.print(
            f"   • {len(environment.subagent_files)} subagent files in {agents_dir.relative_to(path) if agents_dir.is_relative_to(path) else agents_dir}"
        )
        console.print("   • AGENTS.md - User guide")

        if ux_config.suggestions_enabled:
            presenter = build_presenter(ux_config)
            presenter.show_generation(path, written_files)

    except Exception as e:
        exit_code = handle_exception(e, config=ux_config, console=console)
        raise click.exceptions.Exit(exit_code) from e


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option(
    "--output-dir", type=click.Path(), help="Output directory (default: .claude/agents)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
def subagents(project_path: str, **kwargs: Any) -> None:
    """Generate individual subagent files with YAML front matter."""
    config = GenerateConfig(**kwargs)

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating individual subagents for: {path}[/cyan]")

        # Get project analysis
        analysis = _get_project_analysis(config, path)

        # Generate complete environment to get subagents
        from claude_builder.core.template_manager import TemplateManager

        template_manager = TemplateManager()
        environment = template_manager.generate_complete_environment(analysis)

        # Display what would be generated
        if config.dry_run or config.verbose > 0:
            console.print(
                Panel(
                    f"**Individual Subagent Files**\n\n"
                    f"Files to generate: {len(environment.subagent_files)}\n\n"
                    + "\n".join(
                        [f"  • {sf.name}" for sf in environment.subagent_files]
                    ),
                    title="Subagent Generation Preview",
                )
            )

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write individual subagents
        output_dir = (
            Path(config.output_dir)
            if config.output_dir
            else path / ".claude" / "agents"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        for subagent in environment.subagent_files:
            agent_path = output_dir / subagent.name
            with agent_path.open("w", encoding="utf-8") as f:
                f.write(subagent.content)

        console.print(
            f"[green]✓ {len(environment.subagent_files)} subagent files generated successfully[/green]"
        )
        console.print(f"Output location: {output_dir}")

    except Exception as e:
        console.print(f"[red]Error generating subagents: {e}[/red]")
        msg = f"Failed to generate subagents: {e}"
        raise click.ClickException(msg) from e


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option("--agents-dir", type=click.Path(), help="Custom agents directory")
@click.option(
    "--output-file", type=click.Path(), help="Output file (default: AGENTS.md)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
def agents(project_path: str, **kwargs: Any) -> None:
    """Generate agent configurations."""
    config = GenerateConfig(**kwargs)

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating agent configuration for: {path}[/cyan]")

        # Get project analysis
        analysis = _get_project_analysis(config, path)

        # Generate agent configuration
        from claude_builder.core.agents import UniversalAgentSystem

        agent_system = UniversalAgentSystem()
        agent_config = agent_system.select_agents(analysis)

        if config.verbose > 0:
            console.print(
                f"[green]Selected {len(agent_config.all_agents)} agents[/green]"
            )

        # Generate agent documentation
        generator = DocumentGenerator({"agents_only": True})
        generated_content = generator.generate(analysis, path)

        # Filter to just agent files
        agent_files = {
            k: v
            for k, v in generated_content.files.items()
            if "agent" in k.lower() or k == "AGENTS.md"
        }

        if config.dry_run or config.verbose > 0:
            console.print(
                Panel(
                    f"**Agent Configuration Preview**\n\n"
                    f"Core agents: {len(agent_config.core_agents)}\n"
                    f"Domain agents: {len(agent_config.domain_agents)}\n"
                    f"Workflow agents: {len(agent_config.workflow_agents)}\n"
                    f"Custom agents: {len(agent_config.custom_agents)}\n\n"
                    f"Files to generate: {list(agent_files.keys())}",
                    title="Agent Generation Preview",
                )
            )

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write agent files
        output_path = (
            Path(config.output_file) if config.output_file else path / "AGENTS.md"
        )
        _write_agent_files(agent_files, output_path)

    except Exception as e:
        error_msg = f"{FAILED_TO_GENERATE_AGENTS}: {e}"
        console.print(f"[red]Error generating agents: {e}[/red]")
        raise click.ClickException(error_msg) from e


def _load_data_from_file(analysis_file: Path) -> dict[str, Any]:
    """Load raw data from analysis file."""
    with analysis_file.open(encoding="utf-8") as f:
        if analysis_file.suffix.lower() in [".yaml", ".yml"]:
            if yaml is None:
                msg = "PyYAML is required for YAML support"  # type: ignore[unreachable]
                raise ImportError(msg)
            return yaml.safe_load(f)  # type: ignore[no-any-return]
        return json.load(f)  # type: ignore[no-any-return]


def _populate_basic_fields(analysis: ProjectAnalysis, data: dict[str, Any]) -> None:
    """Populate basic analysis fields."""
    analysis.analysis_confidence = data.get("analysis_confidence", 0.0)
    analysis.analysis_timestamp = data.get("analysis_timestamp")
    analysis.analyzer_version = data.get("analyzer_version")


def _populate_info_fields(analysis: ProjectAnalysis, data: dict[str, Any]) -> None:
    """Populate language, framework, and domain info fields."""
    # Language info
    lang_data = data.get("language_info", {})
    analysis.language_info.primary = lang_data.get("primary")
    analysis.language_info.secondary = lang_data.get("secondary", [])
    analysis.language_info.confidence = lang_data.get("confidence", 0.0)
    analysis.language_info.file_counts = lang_data.get("file_counts", {})
    analysis.language_info.total_lines = lang_data.get("total_lines", {})

    # Framework info
    fw_data = data.get("framework_info", {})
    analysis.framework_info.primary = fw_data.get("primary")
    analysis.framework_info.secondary = fw_data.get("secondary", [])
    analysis.framework_info.confidence = fw_data.get("confidence", 0.0)
    analysis.framework_info.version = fw_data.get("version")
    analysis.framework_info.config_files = fw_data.get("config_files", [])

    # Domain info
    domain_data = data.get("domain_info", {})
    analysis.domain_info.domain = domain_data.get("domain")
    analysis.domain_info.confidence = domain_data.get("confidence", 0.0)
    analysis.domain_info.indicators = domain_data.get("indicators", [])
    analysis.domain_info.specialized_patterns = domain_data.get(
        "specialized_patterns", []
    )


def _populate_enum_fields(analysis: ProjectAnalysis, data: dict[str, Any]) -> None:
    """Populate enum-based fields with proper error handling."""
    from claude_builder.core.models import (
        ArchitecturePattern,
        ComplexityLevel,
        ProjectType,
    )

    try:
        analysis.project_type = ProjectType(data.get("project_type", "unknown"))
    except ValueError:
        analysis.project_type = ProjectType.UNKNOWN

    try:
        analysis.complexity_level = ComplexityLevel(
            data.get("complexity_level", "simple")
        )
    except ValueError:
        analysis.complexity_level = ComplexityLevel.SIMPLE

    try:
        analysis.architecture_pattern = ArchitecturePattern(
            data.get("architecture_pattern", "unknown")
        )
    except ValueError:
        analysis.architecture_pattern = ArchitecturePattern.UNKNOWN


def _populate_environment_fields(
    analysis: ProjectAnalysis, data: dict[str, Any]
) -> None:
    """Populate development environment and filesystem fields."""
    # Development environment
    dev_data = data.get("development_environment", {})
    analysis.dev_environment.package_managers = dev_data.get("package_managers", [])
    analysis.dev_environment.testing_frameworks = dev_data.get("testing_frameworks", [])
    analysis.dev_environment.linting_tools = dev_data.get("linting_tools", [])
    analysis.dev_environment.ci_cd_systems = dev_data.get("ci_cd_systems", [])
    analysis.dev_environment.containerization = dev_data.get("containerization", [])
    analysis.dev_environment.databases = dev_data.get("databases", [])
    analysis.dev_environment.documentation_tools = dev_data.get(
        "documentation_tools", []
    )

    # Filesystem info
    fs_data = data.get("filesystem_info", {})
    analysis.filesystem_info.total_files = fs_data.get("total_files", 0)
    analysis.filesystem_info.total_directories = fs_data.get("total_directories", 0)
    analysis.filesystem_info.source_files = fs_data.get("source_files", 0)
    analysis.filesystem_info.test_files = fs_data.get("test_files", 0)
    analysis.filesystem_info.config_files = fs_data.get("config_files", 0)
    analysis.filesystem_info.documentation_files = fs_data.get("documentation_files", 0)
    analysis.filesystem_info.asset_files = fs_data.get("asset_files", 0)
    analysis.filesystem_info.ignore_patterns = fs_data.get("ignore_patterns", [])
    analysis.filesystem_info.root_files = fs_data.get("root_files", [])


def _load_analysis_from_file(analysis_file: Path) -> ProjectAnalysis:
    """Load project analysis from file."""
    try:
        # Load raw data
        data = _load_data_from_file(analysis_file)

        # Create analysis object
        analysis = ProjectAnalysis(project_path=Path(data["project_path"]))

        # Populate fields using helper functions
        _populate_basic_fields(analysis, data)
        _populate_info_fields(analysis, data)
        _populate_enum_fields(analysis, data)
        _populate_environment_fields(analysis, data)

        # Warnings and suggestions
        analysis.warnings = data.get("warnings", [])
        analysis.suggestions = data.get("suggestions", [])

    except Exception as e:
        error_msg = f"{FAILED_TO_LOAD_ANALYSIS} {analysis_file}: {e}"
        raise ClaudeBuilderError(error_msg) from e
    else:
        return analysis


def _display_environment_preview(environment: Any) -> None:
    """Display preview of complete environment generation."""
    preview_text = "**Complete Environment Generation Preview**\n\n"
    preview_text += f"CLAUDE.md: {len(environment.claude_md):,} characters\n"
    preview_text += f"Individual subagents: {len(environment.subagent_files)} files\n"
    for subagent in environment.subagent_files:
        preview_text += f"  • {subagent.name} ({len(subagent.content):,} chars)\n"
    preview_text += f"AGENTS.md: {len(environment.agents_md):,} characters\n\n"
    preview_text += "**Metadata:**\n"
    if hasattr(environment, "metadata"):
        for key, value in environment.metadata.items():
            preview_text += f"  • {key}: {value}\n"

    console.print(Panel(preview_text, title="Environment Generation Preview"))


def _display_generation_preview(generated_content: Any) -> None:
    """Display preview of what will be generated."""
    files_info = []
    total_size = 0

    for filename, content in generated_content.files.items():
        size = len(content.encode("utf-8"))
        total_size += size
        files_info.append(f"  • {filename} ({size:,} bytes)")

    preview_text = f"**Files to generate ({len(generated_content.files)} total):**\n\n"
    preview_text += "\n".join(files_info)
    preview_text += f"\n\n**Total size:** {total_size:,} bytes"
    preview_text += (
        f"\n**Template info:** {len(generated_content.template_info)} templates used"
    )

    console.print(Panel(preview_text, title="Generation Preview"))


def _write_generated_files(
    generated_content: Any, output_path: Path, *, backup_existing: bool, verbose: int
) -> list[str]:
    """Write generated files to disk and return list of written filenames."""
    written_filenames = []

    for filename, content in generated_content.files.items():
        file_path = output_path / filename

        # Create directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file if requested
        if backup_existing and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            file_path.rename(backup_path)
            if verbose > 0:
                console.print(
                    f"[yellow]Backed up existing file: {backup_path}[/yellow]"
                )

        # Write file
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)

        written_filenames.append(filename)

        if verbose > 1:
            console.print(f"[green]✓ {filename}[/green]")

    if verbose > 0:
        console.print(f"[green]Wrote {len(written_filenames)} files[/green]")

    return written_filenames


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option("--template", help="Override template selection")
@click.option(
    "--output-file", type=click.Path(), help="Output file (default: CLAUDE.md)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option(
    "--domain",
    "domains",
    multiple=True,
    type=click.Choice(VALID_DOMAINS, case_sensitive=False),
    help="Filter CLAUDE.md by domain (repeatable): infra, devops, mlops",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
def claude_md(project_path: str, **kwargs: Any) -> None:
    """Generate CLAUDE.md file."""
    # Create config from kwargs
    config = GenerateConfig(**kwargs)

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating CLAUDE.md for: {path}[/cyan]")

        # Get project analysis
        if config.from_analysis:
            analysis = _load_analysis_from_file(Path(config.from_analysis))
            if config.verbose > 0:
                console.print(
                    f"[green]Loaded analysis from: {config.from_analysis}[/green]"
                )
        else:
            if config.verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Configure generator
        generator_config = {}
        if config.template:
            generator_config["preferred_template"] = config.template

        # Generate CLAUDE.md content
        generator = DocumentGenerator(generator_config)
        generated_content = generator.generate(analysis, path)

        # Extract only CLAUDE.md content
        claude_content = generated_content.files.get("CLAUDE.md")
        if not claude_content:
            console.print("[red]Failed to generate CLAUDE.md content[/red]")
            return

        # If domains specified, re-source CLAUDE.md via TemplateManager
        if config.domains:
            from claude_builder.core.template_manager import TemplateManager

            if config.verbose > 0:
                console.print(
                    f"[yellow]Filtering domain sections: {', '.join(config.domains)}[/yellow]"
                )
            tm = TemplateManager()
            env = tm.generate_complete_environment(analysis, domains=config.domains)
            claude_content = env.claude_md

        if config.dry_run or config.verbose > 0:
            console.print(
                Panel(
                    f"**CLAUDE.md Preview** ({len(claude_content)} characters)\n\n"
                    f"First 200 characters:\n{claude_content[:200]}...",
                    title="CLAUDE.md Generation Preview",
                )
            )

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write CLAUDE.md file
        output_path = (
            Path(config.output_file) if config.output_file else path / "CLAUDE.md"
        )

        with output_path.open("w", encoding="utf-8") as f:
            f.write(claude_content)

        console.print("[green]✓ CLAUDE.md generated successfully[/green]")
        console.print(f"Output location: {output_path}")

    except Exception as e:
        error_msg = f"{FAILED_TO_GENERATE_CLAUDE_MD}: {e}"
        console.print(f"[red]Error generating CLAUDE.md: {e}[/red]")
        raise click.ClickException(error_msg) from e


@generate.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--from-analysis",
    type=click.Path(exists=True, file_okay=True),
    help="Use existing analysis file",
)
@click.option("--agents-dir", type=click.Path(), help="Custom agents directory")
@click.option(
    "--output-file", type=click.Path(), help="Output file (default: AGENTS.md)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
def agents_md(project_path: str, **kwargs: Any) -> None:
    """Generate AGENTS.md file."""
    # Create config from kwargs
    config = GenerateConfig(**kwargs)

    try:
        path = Path(project_path).resolve()

        if config.verbose > 0:
            console.print(f"[cyan]Generating AGENTS.md for: {path}[/cyan]")

        # Get project analysis
        if config.from_analysis:
            analysis = _load_analysis_from_file(Path(config.from_analysis))
            if config.verbose > 0:
                console.print(
                    f"[green]Loaded analysis from: {config.from_analysis}[/green]"
                )
        else:
            if config.verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Generate agent configuration
        from claude_builder.core.agents import UniversalAgentSystem

        agent_system = UniversalAgentSystem()
        agent_config = agent_system.select_agents(analysis)

        if config.verbose > 0:
            console.print(
                f"[green]Selected {len(agent_config.all_agents)} agents[/green]"
            )

        # Generate AGENTS.md content
        generator = DocumentGenerator({"agents_only": True})
        generated_content = generator.generate(analysis, path)

        # Extract only AGENTS.md content
        agents_content = generated_content.files.get("AGENTS.md")
        if not agents_content:
            console.print("[red]Failed to generate AGENTS.md content[/red]")
            return

        if config.dry_run or config.verbose > 0:
            console.print(
                Panel(
                    f"**AGENTS.md Preview**\n\n"
                    f"Core agents: {len(agent_config.core_agents)}\n"
                    f"Domain agents: {len(agent_config.domain_agents)}\n"
                    f"Workflow agents: {len(agent_config.workflow_agents)}\n"
                    f"Custom agents: {len(agent_config.custom_agents)}\n\n"
                    f"Content size: {len(agents_content)} characters",
                    title="AGENTS.md Generation Preview",
                )
            )

        if config.dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write AGENTS.md file
        output_path = (
            Path(config.output_file) if config.output_file else path / "AGENTS.md"
        )

        with output_path.open("w", encoding="utf-8") as f:
            f.write(agents_content)

        console.print("[green]✓ AGENTS.md generated successfully[/green]")
        console.print(f"Output location: {output_path}")

    except Exception as e:
        error_msg = f"{FAILED_TO_GENERATE_AGENTS_MD}: {e}"
        console.print(f"[red]Error generating AGENTS.md: {e}[/red]")
        raise click.ClickException(error_msg) from e
