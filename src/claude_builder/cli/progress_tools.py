"""Context manager for progress indication that honours quiet modes."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .ux import UXConfig


class NullProgress:
    """Fallback progress object mimicking :class:`Progress`."""

    def __enter__(self) -> "NullProgress":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None

    def add_task(self, *_args: Any, **_kwargs: Any) -> int:
        return -1

    def update(self, *_args: Any, **_kwargs: Any) -> None:
        return None


@contextmanager
def progress_manager(config: UXConfig) -> Iterator[object]:
    if config.quiet or config.plain_output or config.legacy_mode:
        yield NullProgress()
        return

    console = Console()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        yield progress
