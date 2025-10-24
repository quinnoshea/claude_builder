"""Utility modules for Claude Builder."""

from claude_builder.utils.exceptions import (
    AnalysisError,
    ClaudeBuilderError,
    ConfigError,
    GenerationError,
)
from claude_builder.utils.validation import ValidationResult, validate_project_path


# Optional CLI UI helpers (status/TTY checks)
try:  # pragma: no cover - import surface only
    from claude_builder.utils.cli_ui import (
        confirm_action,
        is_interactive_tty,
        status_indicator,
    )
except Exception:  # pragma: no cover
    confirm_action = None  # type: ignore
    is_interactive_tty = None  # type: ignore
    status_indicator = None  # type: ignore


__all__ = [
    "AnalysisError",
    "ClaudeBuilderError",
    "ConfigError",
    "GenerationError",
    "ValidationResult",
    # CLI UI (may be None if optional module missing)
    "confirm_action",
    "is_interactive_tty",
    "status_indicator",
    "validate_project_path",
]
