"""Infrastructure and DevOps detector (P1.4).

Detects Infrastructure-as-Code, orchestration, observability, secrets, and
security tools by leveraging FilePatterns. Provides simple confidence bucketing
based on aggregate pattern scores to help downstream consumers tune output.
"""

from __future__ import annotations

from pathlib import Path

from claude_builder.analysis.tool_recommendations import (
    get_display_name,
    get_recommendations,
)
from claude_builder.core.models import ToolMetadata
from claude_builder.utils.file_patterns import FilePatterns


# Categorization helpers
ORCHESTRATION_TOOLS = {"kubernetes", "helm", "nomad", "docker"}
SECRETS_MANAGEMENT_TOOLS = {"vault", "sops"}


class InfrastructureDetector:
    """Detects infrastructure, observability, and security tools for a project."""

    def __init__(self, project_path: Path) -> None:
        self.project_path = Path(project_path)
        self._raw: dict[str, dict[str, float]] = {}

    def _classify_confidence(self, scores: dict[str, float]) -> dict[str, str]:
        """Map raw scores to confidence buckets.

        Thresholds (aligned with P1.4 guidance):
        - high:   score >= 12 (multiple strong indicators)
        - medium: score >= 8  (one strong indicator)
        - low:    score >  0  (pattern-only)
        """
        HIGH_THRESHOLD = 12.0
        MEDIUM_THRESHOLD = 8.0

        buckets: dict[str, str] = {}
        for tool, score in scores.items():
            if score >= HIGH_THRESHOLD:
                buckets[tool] = "high"
            elif score >= MEDIUM_THRESHOLD:
                buckets[tool] = "medium"
            elif score > 0.0:
                buckets[tool] = "low"
        return buckets

    def detect(self) -> dict[str, list[str]]:
        """Return categorized lists only (for analyzer integration)."""
        self._raw = FilePatterns.detect_all_devops_tools(self.project_path)

        infra_scores = self._raw.get("infrastructure", {})
        obsv_scores = self._raw.get("observability", {})
        sec_scores = self._raw.get("security", {})

        infra_tools = set(infra_scores.keys())
        sec_tools = set(sec_scores.keys())

        infrastructure_as_code = sorted(
            tool
            for tool in infra_tools
            if tool not in ORCHESTRATION_TOOLS and tool not in SECRETS_MANAGEMENT_TOOLS
        )
        orchestration_tools = sorted(
            tool for tool in infra_tools if tool in ORCHESTRATION_TOOLS
        )

        # Secrets may be detected via infra (vault) and security (sops)
        secrets_management = sorted(
            {t for t in infra_tools if t in SECRETS_MANAGEMENT_TOOLS}
            | {t for t in sec_tools if t in SECRETS_MANAGEMENT_TOOLS}
        )

        observability = sorted(obsv_scores.keys())
        security_tools = sorted(
            t for t in sec_tools if t not in SECRETS_MANAGEMENT_TOOLS
        )

        return {
            "infrastructure_as_code": infrastructure_as_code,
            "orchestration_tools": orchestration_tools,
            "secrets_management": secrets_management,
            "observability": observability,
            "security_tools": security_tools,
            # MLOps-related fields are populated by an optional detector (future work)
            "data_pipeline": [],
            "mlops_tools": [],
        }

    def detect_with_confidence(self) -> tuple[dict[str, list[str]], dict[str, str]]:
        """Return categorized lists plus a {tool: bucket} confidence map."""
        categorized = self.detect()

        # Merge scores from all categories so bucket map covers all tools
        all_scores: dict[str, float] = {}
        for cat in ("infrastructure", "observability", "security"):
            for k, v in self._raw.get(cat, {}).items():
                all_scores[k] = max(all_scores.get(k, 0.0), v)

        return categorized, self._classify_confidence(all_scores)

    def detect_with_metadata(
        self,
    ) -> tuple[dict[str, list[str]], dict[str, ToolMetadata]]:
        """Return categorized lists plus rich metadata for each detected tool."""

        categorized, confidence_map = self.detect_with_confidence()
        metadata: dict[str, ToolMetadata] = {}

        for category in ("infrastructure", "observability", "security"):
            for tool, score in self._raw.get(category, {}).items():
                files = FilePatterns.collect_tool_examples(
                    self.project_path, category, tool
                )
                recommendations = get_recommendations(tool)
                entry = ToolMetadata(
                    name=get_display_name(tool),
                    slug=tool,
                    category=category,
                    confidence=confidence_map.get(tool, "unknown"),
                    score=score,
                    files=files,
                    recommendations=recommendations,
                )

                existing = metadata.get(tool)
                if existing is None or (existing.score or 0.0) < (entry.score or 0.0):
                    metadata[tool] = entry

        return categorized, metadata
