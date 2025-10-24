"""Friendly next-step prompts after successful CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .suggestions import SuggestionEngine


if TYPE_CHECKING:
    from pathlib import Path

    from claude_builder.core.models import ProjectAnalysis

    from .ux import UXConfig


@dataclass
class NextStepsPresenter:
    config: UXConfig
    console: Console
    suggestions: SuggestionEngine

    def show_analysis(self, project_path: Path, analysis: ProjectAnalysis) -> None:
        if self.config.quiet or self.config.plain_output:
            if self.config.suggestions_enabled:
                for item in self.suggestions.for_analysis(analysis, project_path):
                    self.console.print(f"• {item}")
            return

        body = Text("Analysis complete!\n\n", style="bold green")
        body.append("Recommended next steps:\n", style="bold yellow")

        for idx, item in enumerate(
            self.suggestions.for_analysis(analysis, project_path), start=1
        ):
            body.append(f"{idx}. ", style="bold blue")
            body.append(f"{item}\n")

        self.console.print(Panel(body, title="Next Steps", border_style="green"))

    def show_generation(self, project_path: Path, written_files: Iterable[str]) -> None:
        if self.config.quiet or self.config.plain_output:
            if self.config.suggestions_enabled:
                for item in self.suggestions.for_generation(
                    written_files, project_path
                ):
                    self.console.print(f"• {item}")
            return

        files = list(written_files)

        body = Text("Generation complete!\n\n", style="bold green")
        if files:
            body.append("Created files:\n", style="bold yellow")
            for name in files[:6]:
                body.append(f"• {name}\n", style="cyan")
            if len(files) > 6:
                body.append(f"…and {len(files) - 6} more\n", style="dim")
            body.append("\n")

        body.append("What to do now:\n", style="bold yellow")
        for idx, item in enumerate(
            self.suggestions.for_generation(files, project_path), start=1
        ):
            body.append(f"{idx}. ", style="bold blue")
            body.append(f"{item}\n")

        self.console.print(Panel(body, title="Next Steps", border_style="green"))


def build_presenter(config: UXConfig) -> NextStepsPresenter:
    console = Console()
    suggestions = SuggestionEngine(config=config, console=console)
    return NextStepsPresenter(config=config, console=console, suggestions=suggestions)
