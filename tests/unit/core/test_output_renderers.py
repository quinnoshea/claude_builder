"""Tests for target-specific output renderers."""

from pathlib import Path

import pytest

from claude_builder.core.models import (
    EnvironmentBundle,
    OutputTarget,
    RenderedTargetOutput,
    SubagentFile,
)
from claude_builder.core.output_renderers import (
    ClaudeTargetRenderer,
    get_target_renderer,
)


def _sample_environment() -> EnvironmentBundle:
    return EnvironmentBundle(
        claude_md="# Sample Project\n\nProject-level instructions.",
        subagent_files=[
            SubagentFile(
                name="test-writer-fixer.md",
                content="---\nname: test-writer-fixer\n---\n\nFix tests.",
                path=".claude/agents/test-writer-fixer.md",
            ),
            SubagentFile(
                name="backend-architect.md",
                content="---\nname: backend-architect\n---\n\nDesign backend systems.",
                path=".claude/agents/backend-architect.md",
            ),
        ],
        agents_md="# AGENTS\n\nAgent usage guide.",
        metadata={"project_type": "cli_tool", "language": "python"},
        generation_timestamp="2026-02-16T00:00:00+00:00",
    )


def _snapshot_text(rendered: RenderedTargetOutput) -> str:
    sections: list[str] = []
    for artifact in rendered.artifacts:
        sections.append(f"## {artifact.path}\n{artifact.content}")
    return "\n\n".join(sections) + "\n"


def test_claude_renderer_snapshot() -> None:
    renderer = ClaudeTargetRenderer()
    rendered = renderer.render(_sample_environment())

    snapshot_path = (
        Path(__file__).parent / "__snapshots__" / "claude_target_artifacts_snapshot.md"
    )
    expected = (
        snapshot_path.read_text(encoding="utf-8")
        .replace("<!-- markdownlint-disable -->\n\n", "")
        .replace("<!-- markdownlint-disable -->\n", "")
    )

    assert rendered.target == OutputTarget.CLAUDE
    assert rendered.total_files == 4
    assert _snapshot_text(rendered) == expected


def test_claude_renderer_custom_agents_dir_paths() -> None:
    renderer = ClaudeTargetRenderer()
    rendered = renderer.render(_sample_environment(), agents_dir=".agents/custom")

    assert rendered.get_paths() == [
        "CLAUDE.md",
        ".agents/custom/test-writer-fixer.md",
        ".agents/custom/backend-architect.md",
        "AGENTS.md",
    ]


def test_get_target_renderer_rejects_unimplemented_targets() -> None:
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        get_target_renderer(OutputTarget.CODEX)

    with pytest.raises(NotImplementedError, match="not implemented yet"):
        get_target_renderer(OutputTarget.GEMINI)
