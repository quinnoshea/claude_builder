"""Shared configuration helpers for enhanced CLI UX features."""

from __future__ import annotations

import os

from dataclasses import dataclass


def _truthy_env(name: str, default: bool) -> bool:
    """Return ``True`` when the environment variable is set to a truthy value."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class UXConfig:
    """Runtime configuration for CLI UX helpers."""

    quiet: bool
    verbose: int
    suggestions_enabled: bool
    legacy_mode: bool
    plain_output: bool

    def without_suggestions(self) -> "UXConfig":
        """Return a copy with suggestions disabled."""

        return UXConfig(
            quiet=self.quiet,
            verbose=self.verbose,
            suggestions_enabled=False,
            legacy_mode=self.legacy_mode,
            plain_output=self.plain_output,
        )


LEGACY_ENV = "CLAUDE_BUILDER_LEGACY_MODE"
SUGGESTIONS_ENV = "CLAUDE_BUILDER_SHOW_SUGGESTIONS"


def build_ux_config(
    *, quiet: bool, verbose: int, no_suggestions: bool, plain_output: bool
) -> UXConfig:
    """Create a :class:`UXConfig` instance honouring environment switches."""

    legacy_mode = _truthy_env(LEGACY_ENV, False)
    suggestions_env = _truthy_env(SUGGESTIONS_ENV, True)

    suggestions_enabled = (
        not quiet
        and not no_suggestions
        and suggestions_env
        and not legacy_mode
        and not plain_output
    )

    return UXConfig(
        quiet=quiet,
        verbose=verbose,
        suggestions_enabled=suggestions_enabled,
        legacy_mode=legacy_mode,
        plain_output=plain_output,
    )
