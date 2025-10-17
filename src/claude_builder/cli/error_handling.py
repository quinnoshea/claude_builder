"""Enhanced error presentation for the CLI."""

from __future__ import annotations

import traceback

from dataclasses import dataclass
from typing import Iterable, Sequence

import click

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from claude_builder.utils.exceptions import ClaudeBuilderError

from .ux import UXConfig


@dataclass
class ErrorSummary:
    """Rendered representation of an error."""

    message: str
    suggestions: Sequence[str]
    context_rows: Sequence[tuple[str, str]]
    exit_code: int


ERROR_HINTS: dict[str, tuple[str, ...]] = {
    "analysiserror": (
        "Verify the project path and that it contains source files.",
        "Run with --verbose to inspect detection details.",
        "Lower the confidence threshold or pin a template with --template.",
    ),
    "generationerror": (
        "Check write permissions for the chosen output directory.",
        "Re-run with --dry-run to preview template output without writing files.",
        "Try specifying a template explicitly if autodetection fails.",
    ),
    "configerror": (
        "Validate configuration files with `claude-builder config validate`.",
        "Confirm paths referenced in the config exist and are readable.",
    ),
    "validationerror": (
        "Inspect the option values provided to the command.",
        "Use --help to review accepted values and formats.",
    ),
    "giterror": (
        "Ensure Git is installed and the repository is initialised.",
        "Run the failing git command manually for additional diagnostics.",
    ),
}


def _normalise_key(name: str) -> str:
    return name.replace("_", "").lower()


def _merge_suggestions(*groups: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for suggestion in group:
            if suggestion and suggestion not in seen:
                seen.add(suggestion)
                result.append(suggestion)
    return result


def build_error_summary(error: Exception) -> ErrorSummary:
    """Create an :class:`ErrorSummary` with context & exit code."""

    if isinstance(error, ClaudeBuilderError):
        context_rows: list[tuple[str, str]] = []
        ctx = getattr(error, "context", None)
        if isinstance(ctx, dict):
            context_rows.extend((str(k), str(v)) for k, v in ctx.items() if v)

        # Introspect additional attributes that may have been attached
        for attr in ("project_path", "file_path", "analysis_stage", "template_name"):
            value = getattr(error, attr, None)
            if value:
                context_rows.append((attr.replace("_", " ").title(), str(value)))

        hint_key = _normalise_key(type(error).__name__)
        hint_suggestions = ERROR_HINTS.get(hint_key, ())
        suggestions = _merge_suggestions(error.suggestions, hint_suggestions)

        exit_code = getattr(error, "exit_code", 1)
        return ErrorSummary(str(error), suggestions, tuple(context_rows), exit_code)

    # Generic fallback
    return ErrorSummary(str(error), (), (), 1)


def render_error(summary: ErrorSummary, config: UXConfig, *, console: Console) -> None:
    """Pretty-print an error summary respecting CLI UX config."""

    if config.quiet or config.plain_output or config.legacy_mode:
        console.print(f"Error: {summary.message}", style="red", soft_wrap=True)
        for suggestion in summary.suggestions:
            console.print(f"  - {suggestion}", style="blue", soft_wrap=True)
        return

    body = Text(summary.message, style="white")

    if summary.context_rows:
        body.append("\n\nContext:\n", style="bold yellow")
        for label, value in summary.context_rows:
            body.append(f"{label}: {value}\n", style="white")

    if summary.suggestions and config.suggestions_enabled:
        body.append("\n\nSuggestions:\n", style="bold blue")
        for suggestion in summary.suggestions:
            body.append(f"• {suggestion}\n", style="blue")

    console.print(Panel(body, title="CLI Error", border_style="red"))


def handle_exception(
    error: Exception,
    *,
    config: UXConfig,
    console: Console | None = None,
    include_traceback: bool = False,
) -> int:
    """Render ``error`` and return the exit code that should be used."""

    active_console = console or Console(stderr=True)

    summary = build_error_summary(error)
    render_error(summary, config, console=active_console)

    if include_traceback and config.verbose > 0 and not config.quiet:
        formatted_tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        active_console.print("\n[dim]Traceback:\n" + formatted_tb + "[/dim]")

    return summary.exit_code


def handle_command_error(
    command_name: str,
    error: Exception,
    *,
    config: UXConfig,
    available_commands: Sequence[str],
    console: Console | None = None,
) -> int:
    """Specialised handler that can emit spelling suggestions for commands."""

    active_console = console or Console(stderr=True)

    if (
        config.suggestions_enabled
        and isinstance(error, click.exceptions.UsageError)
        and command_name
        and available_commands
    ):
        import difflib

        matches = difflib.get_close_matches(
            command_name, available_commands, n=3, cutoff=0.6
        )
        if matches and not config.quiet:
            tip = Panel(
                "\n".join(f"• {match}" for match in matches),
                title="Did you mean?",
                border_style="cyan",
            )
            render_console = active_console or Console()
            render_console.print(tip)

    return handle_exception(error, config=config, console=active_console)
