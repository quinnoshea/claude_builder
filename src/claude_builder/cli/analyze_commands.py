"""Analysis CLI commands for Claude Builder."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any


try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

import click

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_builder.core.analyzer import ProjectAnalyzer


FAILED_TO_ANALYZE_PROJECT = "Failed to analyze project"
PYYAML_NOT_AVAILABLE = "PyYAML not available"

console = Console()


@click.group()
def analyze() -> None:
    """Analyze project structure and characteristics."""


@analyze.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--output", "-o", type=click.Path(), help="Save analysis to file (JSON format)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.option(
    "--confidence-threshold",
    type=int,
    default=0,
    help="Minimum confidence for reporting (0-100)",
)
@click.option(
    "--include-suggestions", is_flag=True, help="Include improvement suggestions"
)
@click.option("--verbose", "-v", count=True, help="Verbose output")
def project(project_path: str, **options: Any) -> None:
    """Analyze a project directory."""
    # Extract options
    output = options.get("output")
    output_format = options.get("output_format", "table")
    confidence_threshold = options.get("confidence_threshold", 0)
    include_suggestions = options.get("include_suggestions", False)
    verbose = options.get("verbose", 0)

    try:
        path = Path(project_path).resolve()

        if verbose > 0:
            console.print(f"[cyan]Analyzing project at: {path}[/cyan]")

        # Create analyzer and run analysis
        analyzer = ProjectAnalyzer()
        analysis = analyzer.analyze(path)

        # Apply confidence threshold
        if analysis.analysis_confidence < confidence_threshold:
            console.print(
                f"[yellow]Analysis confidence {analysis.analysis_confidence:.1f}% "
                f"is below threshold {confidence_threshold}%[/yellow]"
            )
            if not include_suggestions:
                return

        # Display results based on format
        if output_format == "json":
            _display_analysis_json(analysis, include_suggestions=include_suggestions)
        elif output_format == "yaml":
            _display_analysis_yaml(analysis, include_suggestions=include_suggestions)
        else:
            _display_analysis_table(
                analysis, include_suggestions=include_suggestions, verbose=verbose
            )

        # Save to file if requested
        if output:
            _save_analysis_to_file(
                analysis, Path(output), include_suggestions=include_suggestions
            )
            console.print(f"[green]Analysis saved to: {output}[/green]")

    except Exception as e:
        error_msg = f"{FAILED_TO_ANALYZE_PROJECT}: {e}"
        console.print(f"[red]Error analyzing project: {e}[/red]")
        raise click.ClickException(error_msg) from e


def _display_analysis_table(
    analysis: Any, *, include_suggestions: bool = False, verbose: int = 0
) -> None:
    """Display analysis in table format."""
    _show_analysis_summary(analysis)
    _show_language_table(analysis)
    _show_framework_table(analysis, show_verbose=verbose > 0)
    _show_characteristics_table(analysis)

    if verbose > 0:
        _show_filesystem_table(analysis)

    _show_dev_environment_table(analysis, show_verbose=verbose > 0)
    _show_domain_table(analysis)
    _show_warnings_and_suggestions(analysis, include_suggestions=include_suggestions)


def _show_analysis_summary(analysis: Any) -> None:
    """Show main analysis summary panel."""
    console.print(
        Panel(
            f"[bold blue]Project Analysis Results[/bold blue]\n\n"
            f"**Path**: {analysis.project_path}\n"
            f"**Overall Confidence**: {analysis.analysis_confidence:.1f}%\n"
            f"**Analysis Time**: {analysis.analysis_timestamp or 'Unknown'}",
            title="Analysis Summary",
        )
    )


def _show_language_table(analysis: Any) -> None:
    """Show language analysis table."""
    lang_table = Table(title="Language Analysis")
    lang_table.add_column("Attribute", style="cyan")
    lang_table.add_column("Value", style="green")
    lang_table.add_column("Confidence", style="yellow")

    lang_table.add_row(
        "Primary Language",
        analysis.language_info.primary or "Unknown",
        f"{analysis.language_info.confidence:.1f}%",
    )

    if analysis.language_info.secondary:
        lang_table.add_row(
            "Secondary Languages", ", ".join(analysis.language_info.secondary), "-"
        )

    console.print(lang_table)


def _show_framework_table(analysis: Any, *, show_verbose: bool) -> None:
    """Show framework analysis table if needed."""
    if not (analysis.framework_info.primary or show_verbose):
        return

    fw_table = Table(title="Framework Analysis")
    fw_table.add_column("Attribute", style="cyan")
    fw_table.add_column("Value", style="green")
    fw_table.add_column("Confidence", style="yellow")

    fw_table.add_row(
        "Primary Framework",
        analysis.framework_info.primary or "None detected",
        f"{analysis.framework_info.confidence:.1f}%",
    )

    if analysis.framework_info.secondary:
        fw_table.add_row(
            "Secondary Frameworks",
            ", ".join(analysis.framework_info.secondary),
            "-",
        )

    if analysis.framework_info.version:
        fw_table.add_row("Version", analysis.framework_info.version, "-")

    console.print(fw_table)


def _show_characteristics_table(analysis: Any) -> None:
    """Show project characteristics table."""
    char_table = Table(title="Project Characteristics")
    char_table.add_column("Characteristic", style="cyan")
    char_table.add_column("Value", style="green")

    char_table.add_row(
        "Project Type", analysis.project_type.value.replace("_", " ").title()
    )
    char_table.add_row("Complexity Level", analysis.complexity_level.value.title())
    char_table.add_row(
        "Architecture Pattern",
        analysis.architecture_pattern.value.replace("_", " ").title(),
    )

    console.print(char_table)


def _show_filesystem_table(analysis: Any) -> None:
    """Show file system analysis table."""
    fs_table = Table(title="File System Analysis")
    fs_table.add_column("Metric", style="cyan")
    fs_table.add_column("Count", style="green")

    fs_info = analysis.filesystem_info
    fs_table.add_row("Total Files", str(fs_info.total_files))
    fs_table.add_row("Total Directories", str(fs_info.total_directories))
    fs_table.add_row("Source Files", str(fs_info.source_files))
    fs_table.add_row("Test Files", str(fs_info.test_files))
    fs_table.add_row("Config Files", str(fs_info.config_files))
    fs_table.add_row("Documentation Files", str(fs_info.documentation_files))

    console.print(fs_table)


def _show_dev_environment_table(analysis: Any, *, show_verbose: bool) -> None:
    """Show development environment table if needed."""
    if not (analysis.dev_environment.package_managers or show_verbose):
        return

    dev_table = Table(title="Development Environment")
    dev_table.add_column("Category", style="cyan")
    dev_table.add_column("Detected Tools", style="green")

    if analysis.dev_environment.package_managers:
        dev_table.add_row(
            "Package Managers", ", ".join(analysis.dev_environment.package_managers)
        )

    if analysis.dev_environment.testing_frameworks:
        dev_table.add_row(
            "Testing Frameworks",
            ", ".join(analysis.dev_environment.testing_frameworks),
        )

    if analysis.dev_environment.ci_cd_systems:
        dev_table.add_row(
            "CI/CD Systems", ", ".join(analysis.dev_environment.ci_cd_systems)
        )

    if analysis.dev_environment.containerization:
        dev_table.add_row(
            "Containerization", ", ".join(analysis.dev_environment.containerization)
        )

    if analysis.dev_environment.databases:
        dev_table.add_row("Databases", ", ".join(analysis.dev_environment.databases))

    console.print(dev_table)


def _show_domain_table(analysis: Any) -> None:
    """Show domain analysis table if domain detected."""
    if not analysis.domain_info.domain:
        return

    domain_table = Table(title="Domain Analysis")
    domain_table.add_column("Attribute", style="cyan")
    domain_table.add_column("Value", style="green")
    domain_table.add_column("Confidence", style="yellow")

    domain_table.add_row(
        "Domain",
        analysis.domain_info.domain.replace("_", " ").title(),
        f"{analysis.domain_info.confidence:.1f}%",
    )

    if analysis.domain_info.indicators:
        domain_table.add_row(
            "Indicators", ", ".join(analysis.domain_info.indicators), "-"
        )

    console.print(domain_table)


def _show_warnings_and_suggestions(analysis: Any, *, include_suggestions: bool) -> None:
    """Show warnings and suggestions if present."""
    if analysis.warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for warning in analysis.warnings:
            console.print(f"  ⚠ {warning}")

    if include_suggestions and analysis.suggestions:
        console.print("[blue]Suggestions:[/blue]")
        for suggestion in analysis.suggestions:
            console.print(f"  💡 {suggestion}")


def _display_analysis_json(analysis: Any, *, include_suggestions: bool = False) -> None:
    """Display analysis in JSON format."""
    data = _analysis_to_dict(analysis, include_suggestions=include_suggestions)
    console.print(json.dumps(data, indent=2))


def _display_analysis_yaml(analysis: Any, *, include_suggestions: bool = False) -> None:
    """Display analysis in YAML format."""
    if yaml is None:
        console.print("[red]YAML format requires PyYAML to be installed[/red]")  # type: ignore[unreachable]
        console.print("Try: pip install PyYAML")
        raise click.ClickException(PYYAML_NOT_AVAILABLE)

    data = _analysis_to_dict(analysis, include_suggestions=include_suggestions)
    console.print(yaml.dump(data, default_flow_style=False))


def _analysis_to_dict(
    analysis: Any, *, include_suggestions: bool = False
) -> dict[str, Any]:
    """Convert analysis to dictionary."""
    data = {
        "project_path": str(analysis.project_path),
        "analysis_confidence": analysis.analysis_confidence,
        "analysis_timestamp": analysis.analysis_timestamp,
        "analyzer_version": analysis.analyzer_version,
        "language_info": {
            "primary": analysis.language_info.primary,
            "secondary": analysis.language_info.secondary,
            "confidence": analysis.language_info.confidence,
            "file_counts": analysis.language_info.file_counts,
            "total_lines": analysis.language_info.total_lines,
        },
        "framework_info": {
            "primary": analysis.framework_info.primary,
            "secondary": analysis.framework_info.secondary,
            "confidence": analysis.framework_info.confidence,
            "version": analysis.framework_info.version,
            "config_files": analysis.framework_info.config_files,
        },
        "domain_info": {
            "domain": analysis.domain_info.domain,
            "confidence": analysis.domain_info.confidence,
            "indicators": analysis.domain_info.indicators,
            "specialized_patterns": analysis.domain_info.specialized_patterns,
        },
        "project_type": analysis.project_type.value,
        "complexity_level": analysis.complexity_level.value,
        "architecture_pattern": analysis.architecture_pattern.value,
        "development_environment": {
            "package_managers": analysis.dev_environment.package_managers,
            "testing_frameworks": analysis.dev_environment.testing_frameworks,
            "linting_tools": analysis.dev_environment.linting_tools,
            "ci_cd_systems": analysis.dev_environment.ci_cd_systems,
            "containerization": analysis.dev_environment.containerization,
            "databases": analysis.dev_environment.databases,
            "documentation_tools": analysis.dev_environment.documentation_tools,
        },
        "filesystem_info": {
            "total_files": analysis.filesystem_info.total_files,
            "total_directories": analysis.filesystem_info.total_directories,
            "source_files": analysis.filesystem_info.source_files,
            "test_files": analysis.filesystem_info.test_files,
            "config_files": analysis.filesystem_info.config_files,
            "documentation_files": analysis.filesystem_info.documentation_files,
            "asset_files": analysis.filesystem_info.asset_files,
            "ignore_patterns": analysis.filesystem_info.ignore_patterns,
            "root_files": analysis.filesystem_info.root_files,
        },
        "warnings": analysis.warnings,
    }

    if include_suggestions:
        data["suggestions"] = analysis.suggestions

    return data


def _save_analysis_to_file(
    analysis: Any, output_path: Path, *, include_suggestions: bool = False
) -> None:
    """Save analysis to file."""
    data = _analysis_to_dict(analysis, include_suggestions=include_suggestions)

    if output_path.suffix.lower() in [".yaml", ".yml"]:
        if yaml is None:
            # Fallback to JSON
            console.print("[yellow]YAML not available, saving as JSON instead[/yellow]")  # type: ignore[unreachable]
            output_path = output_path.with_suffix(".json")
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            with output_path.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
    else:
        # Default to JSON
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
