"""Lightweight helpers to enrich CLI help output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


if TYPE_CHECKING:
    from .ux import UXConfig


def show_getting_started(config: UXConfig, *, console: Console | None = None) -> None:
    if config.quiet or config.plain_output or config.legacy_mode:
        return

    render_console = console or Console()

    content = """
# Getting Started

1. `claude-builder analyze project ./my-project`
2. `claude-builder generate docs ./my-project`
3. `claude-builder generate complete ./my-project`

Common flags:
- `--dry-run` – preview without writing files.
- `--template <name>` – override detection with a specific template.
- `--no-suggestions` – silence contextual hints.
"""

    render_console.print(
        Panel(Markdown(content), title="Claude Builder", border_style="blue")
    )
