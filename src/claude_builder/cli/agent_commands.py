"""Agent suggestion CLI commands for Claude Builder.

Provides an ergonomic entry point to surface agent recommendations based on:
- Natural-language trigger phrases (P2.3.2/3)
- Detected DevOps/MLOps signals from project analysis (P2.3.1)
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from rich.console import Console
from rich.table import Table

from claude_builder.core.agents import AgentRegistry, AgentSelector
from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.models import AgentInfo


console = Console()


@click.group()
def agents() -> None:
    """Agent-related commands for Claude Builder.

    \b
    Examples:
        # Suggest agents based on project analysis
        claude-builder agents suggest --project-path ./my-project

        # Suggest agents from natural language description
        claude-builder agents suggest --text "pipeline is failing"

        # Filter by domain
        claude-builder agents suggest --domain mlops --domain devops

        # JSON output for automation
        claude-builder agents suggest --text "k8s cluster security" --json
    """


@agents.command()
@click.option(
    "--project-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    help="Project directory to analyze (default: current directory)",
)
@click.option("--text", help="Suggest agents based on a natural-language phrase")
@click.option(
    "--domain",
    multiple=True,
    type=click.Choice(["infra", "devops", "mlops"], case_sensitive=False),
    help=(
        "Filter suggestions by domain (repeatable). Example: "
        "--domain devops --domain mlops"
    ),
)
@click.option("--mlops", is_flag=True, help="Filter suggestions to MLOps/Data agents")
@click.option(
    "--devops", is_flag=True, help="Filter suggestions to DevOps/Infra agents"
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option("--verbose", "-v", count=True, help="Verbose output")
def suggest(
    project_path: str,
    text: Optional[str],
    domain: tuple[str, ...],
    mlops: bool,
    devops: bool,
    output_json: bool,
    verbose: int,
) -> None:
    """Suggest agents from triggers or environment signals.

    If --text is provided, suggestions are based on trigger phrases.
    Otherwise, a quick analysis runs and environment-driven suggestions are shown.
    Use --mlops/--devops to focus results, and --json for machine output.
    """
    # Resolve unified domain option into legacy flags (back-compat)
    if domain:
        dset = {d.lower() for d in domain}
        mlops = mlops or ("mlops" in dset)
        devops = devops or ("devops" in dset) or ("infra" in dset)

    registry = AgentRegistry()
    selector = AgentSelector(registry)

    suggestions: List[AgentInfo] = []
    reasons: Dict[str, str] = {}

    if text:
        if verbose:
            console.print(f"[cyan]Trigger phrase:[/cyan] {text}")
        trigger_agents = selector.select_from_text(text)
        for a in trigger_agents:
            if a.name not in reasons:
                suggestions.append(a)
                reasons[a.name] = f"trigger: {text}"
        source = "text"
    else:
        path = Path(project_path).resolve()
        if verbose:
            console.print(f"[cyan]Analyzing project:[/cyan] {path}")
        analyzer = ProjectAnalyzer()
        analysis = analyzer.analyze(path)

        env_agents = selector.select_environment_agents(analysis)
        for a in env_agents:
            if a.name not in reasons:
                suggestions.append(a)
                # coarse-grained reason buckets
                if _is_devops_agent(a.name):
                    reasons[a.name] = "env: DevOps infrastructure"
                elif _is_mlops_agent(a.name):
                    reasons[a.name] = "env: MLOps/Data tools"
                else:
                    reasons[a.name] = "env: detected tools"

        # If no specific focus requested, include comparative core/domain/workflow picks
        if not mlops and not devops:
            for a in selector.select_core_agents(analysis):
                if a.name not in reasons:
                    suggestions.append(a)
                    reasons[a.name] = (
                        f"core: {analysis.language_info.primary or 'general'}"
                    )
            for a in selector.select_domain_agents(analysis):
                if a.name not in reasons:
                    suggestions.append(a)
                    reasons[a.name] = (
                        f"domain: {analysis.domain_info.domain or 'general'}"
                    )
            for a in selector.select_workflow_agents(analysis):
                if a.name not in reasons:
                    suggestions.append(a)
                    reasons[a.name] = f"workflow: {analysis.complexity_level.value}"
        source = "env"

    # Focus filters
    if mlops:
        suggestions = [a for a in suggestions if _is_mlops_agent(a.name)]
    if devops:
        suggestions = [a for a in suggestions if _is_devops_agent(a.name)]

    # Sort by confidence (desc)
    suggestions.sort(key=lambda a: (a.confidence or 0.5), reverse=True)

    if output_json:
        _print_json(suggestions, reasons, source)
    else:
        _print_table(suggestions, reasons, project_path, text)


def _is_devops_agent(name: str) -> bool:
    name_l = name.lower()
    devops_keywords = [
        "terraform",
        "ansible",
        "kubernetes",
        "helm",
        "pulumi",
        "cloudformation",
        "packer",
        "observability",
        "ci",
        "pipeline",
        "security",
    ]
    return any(k in name_l for k in devops_keywords)


def _is_mlops_agent(name: str) -> bool:
    name_l = name.lower()
    mlops_keywords = [
        "mlops",
        "mlflow",
        "kubeflow",
        "dbt",
        "airflow",
        "prefect",
        "dvc",
        "data-quality",
        "analyst",
        "pipeline",
        "model",
    ]
    return any(k in name_l for k in mlops_keywords)


def _print_json(agents: List[AgentInfo], reasons: Dict[str, str], source: str) -> None:
    payload: List[Dict[str, Any]] = []
    for a in agents:
        payload.append(
            {
                "name": a.name,
                "role": a.role,
                "confidence": a.confidence or 0.5,
                "source": source,
                "reasons": [reasons.get(a.name, "")],
                "description": a.description,
                "use_cases": a.use_cases,
            }
        )
    # Use click.echo to avoid Rich markup processing of JSON content
    click.echo(json.dumps(payload, indent=2))


def _print_table(
    agents: List[AgentInfo],
    reasons: Dict[str, str],
    project_path: str,
    text: Optional[str],
) -> None:
    if not agents:
        console.print("[yellow]No agent suggestions found.[/yellow]")
        return

    table = Table(title="Agent Suggestions")
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Role", style="green")
    table.add_column("Confidence", style="magenta", justify="right")
    table.add_column("Reason", style="blue")

    for a in agents[:15]:
        conf = f"{(a.confidence or 0.5) * 100:.0f}%"
        table.add_row(a.name, a.role or "", conf, reasons.get(a.name, ""))

    console.print()
    if text:
        console.print(f"[bold]Suggestions for:[/bold] '{text}'")
    else:
        console.print(f"[bold]Suggestions for:[/bold] {project_path}")
    console.print(table)
    if len(agents) > 15:
        console.print(
            f"\n[dim]... and {len(agents) - 15} more. Use --json for the full list.[/dim]"
        )
