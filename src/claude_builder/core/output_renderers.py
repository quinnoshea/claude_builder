"""Target-specific renderers for generated instruction artifacts."""

from __future__ import annotations

import json
import re

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


def _extract_front_matter_and_body(content: str) -> tuple[dict[str, str], str]:
    """Extract simple YAML front matter fields and markdown body."""
    if not content.startswith("---\n"):
        return {}, content.strip()

    closing_marker = "\n---\n"
    marker_index = content.find(closing_marker, 4)
    if marker_index == -1:
        return {}, content.strip()

    front_matter = content[4:marker_index]
    body = content[marker_index + len(closing_marker) :].lstrip()
    metadata: dict[str, str] = {}

    for raw_line in front_matter.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()

    return metadata, body


def _retarget_for_gemini(content: str) -> str:
    """Retarget Claude-oriented phrasing for Gemini context files."""
    replacements: tuple[tuple[str, str], ...] = (
        ("CLAUDE.md", "GEMINI.md"),
        ("Claude Code", "Gemini CLI"),
    )

    updated = content
    for source, destination in replacements:
        updated = updated.replace(source, destination)

    return re.sub(r"\bClaude\b", "Gemini", updated)


def _retarget_for_codex(content: str) -> str:
    """Retarget Claude-oriented phrasing for Codex instruction files."""
    replacements: tuple[tuple[str, str], ...] = (
        ("CLAUDE.md", "AGENTS.md"),
        ("Claude Code", "Codex CLI"),
    )

    updated = content
    for source, destination in replacements:
        updated = updated.replace(source, destination)

    return re.sub(r"\bClaude\b", "Codex", updated)


def _make_skill_slug(name: str) -> str:
    """Convert a subagent filename to a skill slug."""
    stem = PurePosixPath(name).name
    if stem.endswith(".md"):
        stem = stem[:-3]
    return stem.strip().lower().replace("_", "-").replace(" ", "-")


def _render_codex_skill_markdown(subagent_name: str, content: str) -> str:
    """Render a Codex SKILL.md document from subagent content."""
    metadata, body = _extract_front_matter_and_body(content)
    slug = _make_skill_slug(subagent_name)
    display_name = metadata.get("name") or slug
    description = metadata.get(
        "description", f"Specialized guidance for {display_name} tasks."
    )
    tools = metadata.get("tools", "")

    sections = [
        f"# {display_name}",
        "",
        "## Purpose",
        description,
        "",
    ]
    if tools:
        sections.extend(["## Suggested Tools", tools, ""])

    sections.extend(
        [
            "## Instructions",
            body or f"Use this skill for {display_name} work in this repository.",
            "",
        ]
    )

    return "\n".join(sections)


def _render_gemini_specialist_markdown(subagent_name: str, content: str) -> str:
    """Render Gemini specialist context markdown from subagent content."""
    metadata, body = _extract_front_matter_and_body(content)
    slug = _make_skill_slug(subagent_name)
    display_name = metadata.get("name") or slug
    description = metadata.get(
        "description", f"Specialized context for {display_name} work."
    )

    lines = [
        f"# {display_name}",
        "",
        "## Scope",
        description,
        "",
        "## Guidance",
        body or f"Apply {display_name} best practices to related changes.",
        "",
    ]
    return "\n".join(lines)


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


class CodexTargetRenderer:
    """Render Codex-friendly AGENTS and skill package artifacts."""

    target = OutputTarget.CODEX

    def render(
        self,
        environment: EnvironmentBundle,
        *,
        agents_dir: str = ".agents/skills",
    ) -> RenderedTargetOutput:
        """Render Codex artifacts with AGENTS.md and SKILL.md files."""
        skills_base = _normalise_agents_dir(agents_dir) or ".agents/skills"
        artifacts: list[GeneratedArtifact] = []

        skill_paths: list[str] = []
        for subagent in environment.subagent_files:
            slug = _make_skill_slug(subagent.name)
            skill_path = f"{skills_base}/{slug}/SKILL.md"
            skill_paths.append(skill_path)
            artifacts.append(
                GeneratedArtifact(
                    path=skill_path,
                    content=_render_codex_skill_markdown(
                        subagent.name, subagent.content
                    ),
                    description="Codex skill definition",
                )
            )

        agents_guide = _retarget_for_codex(environment.agents_md).rstrip()
        if skill_paths:
            listing = "\n".join(f"- `{path}`" for path in skill_paths)
            agents_guide = (
                f"{agents_guide}\n\n## Codex Skills\n"
                "The following skills were generated for Codex:\n"
                f"{listing}\n"
            )

        artifacts.insert(
            0,
            GeneratedArtifact(
                path="AGENTS.md",
                content=agents_guide,
                description="Codex instruction guide",
            ),
        )

        metadata = dict(environment.metadata)
        metadata["skill_count"] = len(skill_paths)
        if environment.generation_timestamp:
            metadata["generation_timestamp"] = environment.generation_timestamp

        return RenderedTargetOutput(
            target=self.target,
            artifacts=artifacts,
            metadata=metadata,
        )


class GeminiContextRenderer:
    """Render Gemini CLI context artifacts."""

    target = OutputTarget.GEMINI

    def render(
        self,
        environment: EnvironmentBundle,
        *,
        agents_dir: str = ".gemini/agents",
    ) -> RenderedTargetOutput:
        """Render GEMINI.md and companion Gemini context artifacts."""
        specialists_base = _normalise_agents_dir(agents_dir) or ".gemini/agents"
        artifacts: list[GeneratedArtifact] = [
            GeneratedArtifact(
                path="GEMINI.md",
                content=_retarget_for_gemini(environment.claude_md),
                description="Primary Gemini CLI project context",
            ),
            GeneratedArtifact(
                path="AGENTS.md",
                content=_retarget_for_gemini(environment.agents_md),
                description="Optional companion context for cross-tool usage",
            ),
        ]

        specialist_paths: list[str] = []
        for subagent in environment.subagent_files:
            slug = _make_skill_slug(subagent.name)
            specialist_path = f"{specialists_base}/{slug}.md"
            specialist_paths.append(specialist_path)
            artifacts.append(
                GeneratedArtifact(
                    path=specialist_path,
                    content=_render_gemini_specialist_markdown(
                        subagent.name, subagent.content
                    ),
                    description="Specialized Gemini context note",
                )
            )

        settings_content = json.dumps(
            {
                "context": {
                    "fileName": [
                        "GEMINI.md",
                        "AGENTS.md",
                    ]
                }
            },
            indent=2,
        )
        artifacts.append(
            GeneratedArtifact(
                path=".gemini/settings.json.example",
                content=f"{settings_content}\n",
                description="Gemini CLI settings example",
            )
        )

        metadata = dict(environment.metadata)
        metadata["specialist_context_count"] = len(specialist_paths)
        if environment.generation_timestamp:
            metadata["generation_timestamp"] = environment.generation_timestamp

        return RenderedTargetOutput(
            target=self.target,
            artifacts=artifacts,
            metadata=metadata,
        )


def get_target_renderer(target: OutputTarget) -> TargetRenderer:
    """Return renderer for a target."""
    if target == OutputTarget.CLAUDE:
        return ClaudeTargetRenderer()
    if target == OutputTarget.CODEX:
        return CodexTargetRenderer()
    return GeminiContextRenderer()
