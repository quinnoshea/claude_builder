"""Target-specific renderers for generated instruction artifacts."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Protocol

from claude_builder.core.models import (
    EnvironmentBundle,
    GeneratedArtifact,
    OutputTarget,
    RenderedTargetOutput,
)


class TargetRenderer(Protocol):
    """Contract for rendering target-specific artifacts."""

    target: OutputTarget

    def render(
        self,
        environment: EnvironmentBundle,
        *,
        agents_dir: str = ".claude/agents",
    ) -> RenderedTargetOutput:
        """Render target-specific artifacts from an environment bundle."""


def _normalise_agents_dir(agents_dir: str) -> str:
    """Normalize an agents directory to portable posix-style relative form."""
    normalized = PurePosixPath(agents_dir).as_posix().rstrip("/")
    if normalized in ("", "."):
        return ""
    return normalized


class ClaudeTargetRenderer:
    """Render current Claude-format files as generic artifacts."""

    target = OutputTarget.CLAUDE

    def render(
        self,
        environment: EnvironmentBundle,
        *,
        agents_dir: str = ".claude/agents",
    ) -> RenderedTargetOutput:
        """Render Claude output artifacts in stable order."""
        normalized_agents_dir = _normalise_agents_dir(agents_dir)
        artifacts: list[GeneratedArtifact] = [
            GeneratedArtifact(
                path="CLAUDE.md",
                content=environment.claude_md,
                description="Project documentation",
            )
        ]

        for subagent in environment.subagent_files:
            if normalized_agents_dir:
                subagent_path = f"{normalized_agents_dir}/{subagent.name}"
            else:
                subagent_path = subagent.name

            artifacts.append(
                GeneratedArtifact(
                    path=subagent_path,
                    content=subagent.content,
                    description="Specialized subagent definition",
                )
            )

        artifacts.append(
            GeneratedArtifact(
                path="AGENTS.md",
                content=environment.agents_md,
                description="Agent usage guide",
            )
        )

        metadata = dict(environment.metadata)
        if environment.generation_timestamp:
            metadata["generation_timestamp"] = environment.generation_timestamp

        return RenderedTargetOutput(
            target=self.target,
            artifacts=artifacts,
            metadata=metadata,
        )


def get_target_renderer(target: OutputTarget) -> TargetRenderer:
    """Return renderer for a target or raise if not implemented yet."""
    if target == OutputTarget.CLAUDE:
        return ClaudeTargetRenderer()

    msg = (
        f"Target '{target.value}' is defined but not implemented yet. "
        "Supported today: claude"
    )
    raise NotImplementedError(msg)
