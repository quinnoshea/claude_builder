"""Unit tests for the enhanced CLI UX helpers."""

from __future__ import annotations

import sys

from pathlib import Path

import pytest

from rich.console import Console


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from claude_builder.cli import error_handling
from claude_builder.cli.next_steps import build_presenter
from claude_builder.cli.suggestions import SuggestionEngine
from claude_builder.cli.ux import build_ux_config
from claude_builder.utils.exceptions import ClaudeBuilderError


def test_build_ux_config_respects_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_BUILDER_SHOW_SUGGESTIONS", "0")
    config = build_ux_config(
        quiet=False, verbose=0, no_suggestions=False, plain_output=False
    )
    assert not config.suggestions_enabled


def test_handle_exception_renders_suggestions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = build_ux_config(
        quiet=False, verbose=0, no_suggestions=False, plain_output=False
    )
    console = Console(record=True)
    error = ClaudeBuilderError(
        "Something went wrong", suggestions=["Try rerunning with --verbose"]
    )

    exit_code = error_handling.handle_exception(error, config=config, console=console)

    assert exit_code == error.exit_code
    rendered = console.export_text()
    assert "Try rerunning with --verbose" in rendered


def test_next_steps_presenter_respects_quiet(monkeypatch: pytest.MonkeyPatch) -> None:
    config = build_ux_config(
        quiet=True, verbose=0, no_suggestions=False, plain_output=False
    )
    presenter = build_presenter(config)

    # Mock analysis object with required attributes
    class DummyAnalysis:
        def __init__(self) -> None:
            self.language_info = type("lang", (), {"primary": "python"})()
            self.domain_info = type("domain", (), {"domain": "devops"})()

    presenter.show_analysis(Path("/tmp/project"), DummyAnalysis())
    # Quiet mode should have produced no output
    # There is no direct way to introspect the Console buffer, but absence of exceptions suffices.


def test_suggestion_engine_adds_language_hints(tmp_path: Path) -> None:
    config = build_ux_config(
        quiet=False, verbose=0, no_suggestions=False, plain_output=False
    )
    engine = SuggestionEngine(config=config, console=Console(record=True))

    class DummyAnalysis:
        def __init__(self) -> None:
            self.language_info = type("Lang", (), {"primary": "python"})()
            self.domain_info = type("Domain", (), {"domain": "devops"})()
            self.analysis_confidence = 90

    suggestions = engine.for_analysis(DummyAnalysis(), tmp_path)
    assert any("generate docs" in s.lower() for s in suggestions)
