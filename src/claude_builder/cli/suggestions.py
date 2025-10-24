"""Context-aware suggestions for CLI output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from rich.panel import Panel
from rich.text import Text


if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console

    from claude_builder.core.models import ProjectAnalysis

    from .ux import UXConfig

LANGUAGE_HINTS: dict[str, tuple[str, ...]] = {
    "python": (
        "Run `claude-builder generate docs` to scaffold project documentation.",
        "Create virtualenv instructions by enabling the Python template.",
    ),
    "javascript": (
        "Consider generating frontend-focused docs with the web templates.",
        "Add package.json metadata so detection can suggest npm scripts.",
    ),
    "typescript": ("Leverage the TypeScript template for stricter linting guidance.",),
    "rust": ("Pin the rust-cli template if you prefer a minimal agent set.",),
    "go": ("Generate docs with `--template go-service` for deployment notes.",),
}

DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "devops": (
        "Explore DevOps templates via `claude-builder generate docs --domain devops`.",
        "Use `claude-builder agents suggest --project-path <dir>` for infra agents.",
    ),
    "mlops": (
        "Review experiment tracking guidance with the MLOps templates.",
        "Enable data quality checks using `claude-builder agents suggest`.",
    ),
}


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


@dataclass
class SuggestionEngine:
    """Generate and render suggestions based on CLI context."""

    config: UXConfig
    console: Console

    def for_analysis(self, analysis: ProjectAnalysis, project_path: Path) -> list[str]:
        hints: list[str] = []

        language = (analysis.language_info.primary or "").lower()
        hints.extend(LANGUAGE_HINTS.get(language, ()))

        domain = (
            analysis.domain_info.domain.lower()
            if analysis.domain_info and analysis.domain_info.domain
            else ""
        )
        hints.extend(DOMAIN_HINTS.get(domain, ()))

        if analysis.analysis_confidence < 70:
            hints.append(
                "Confidence is low – pass `--template` or lower `--confidence-threshold` to guide detection."
            )

        if not hints:
            hints.extend(
                (
                    f"Generate documentation: claude-builder generate docs {project_path}",
                    f"Create a complete environment: claude-builder generate complete {project_path}",
                )
            )

        return _unique(hints)

    def for_generation(
        self, written_files: Iterable[str], project_path: Path
    ) -> list[str]:
        files = list(written_files)
        hints: list[str] = [
            "Review CLAUDE.md for the recommended development workflow.",
            "Open AGENTS.md to understand how to brief your AI teammates.",
        ]

        if any(str(f).startswith(".claude/agents") for f in files):
            hints.append(
                "Start Claude Code with the generated agent set for the quickest hand-off."
            )

        hints.append(
            "Commit the generated assets once you are satisfied: git add . && git commit"
        )

        return _unique(hints)

    def render(self, title: str, suggestions: Iterable[str]) -> None:
        if not self.config.suggestions_enabled:
            return

        items = [s for s in suggestions if s]
        if not items:
            return

        if self.config.quiet:
            return

        if self.config.legacy_mode or self.config.plain_output:
            for suggestion in items:
                self.console.print(f"• {suggestion}")
            return

        body = Text()
        for idx, suggestion in enumerate(items, start=1):
            body.append(f"{idx}. ", style="bold blue")
            body.append(f"{suggestion}\n")

        self.console.print(Panel(body, title=title, border_style="blue"))
