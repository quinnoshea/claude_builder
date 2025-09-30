"""CLI UI utilities for claude-builder.

Provides reusable Rich-based UI components for consistent CLI experience.
"""

from __future__ import annotations

import sys

from contextlib import contextmanager
from typing import Generator

from rich.console import Console


def is_interactive_tty() -> bool:
    """Return True if both stdin and stdout are TTY devices."""
    return sys.stdin.isatty() and sys.stdout.isatty()


@contextmanager
def status_indicator(
    console: Console,
    message: str,
    spinner: str = "dots",
) -> Generator[None, None, None]:
    """Context manager for displaying a Rich status spinner."""
    with console.status(f"[cyan]{message}[/cyan]", spinner=spinner):
        yield


def confirm_action(console: Console, prompt: str, default: bool = False) -> bool:
    """Prompt for confirmation (placeholder for future wizard work)."""
    # from rich.prompt import Confirm
    # return Confirm.ask(prompt, default=default, console=console)
    return default
