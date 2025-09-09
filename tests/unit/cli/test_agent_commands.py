"""Tests for the agents CLI group (agents suggest)."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

from click.testing import CliRunner

from claude_builder.cli.agent_commands import agents as agents_group
from claude_builder.core.models import (
    DevelopmentEnvironment,
    ProjectAnalysis,
    ProjectType,
)


def test_suggest_text_pipeline_invokes_ci_agent(monkeypatch: Any) -> None:
    """--text 'pipeline is failing' should include ci-pipeline-engineer."""
    # No registry mocking needed; DevOps agents are registered by default
    runner = CliRunner()
    result = runner.invoke(agents_group, ["suggest", "--text", "pipeline is failing"])
    assert result.exit_code == 0
    assert "ci-pipeline-engineer" in result.output


def test_suggest_env_terraform_k8s(monkeypatch: Any, tmp_path: Path) -> None:
    """Project with Terraform+Kubernetes should include appropriate agents."""
    # Patch ProjectAnalyzer.analyze to return synthetic environment
    from claude_builder.cli import agent_commands as mod

    def fake_analyze(self, path: Path) -> ProjectAnalysis:  # type: ignore[override]
        env = DevelopmentEnvironment(
            infrastructure_as_code=["terraform"],
            orchestration_tools=["kubernetes"],
            ci_cd_systems=["github_actions"],
        )
        return ProjectAnalysis(
            project_path=path,
            project_type=ProjectType.API_SERVICE,
            dev_environment=env,
        )

    monkeypatch.setattr(mod.ProjectAnalyzer, "analyze", fake_analyze)

    runner = CliRunner()
    result = runner.invoke(agents_group, ["suggest", "--project-path", str(tmp_path)])
    assert result.exit_code == 0
    # Expect terraform specialist and kubernetes operator at minimum
    assert "terraform-specialist" in result.output
    assert "kubernetes-operator" in result.output
    # CI signal suggests ci-pipeline-engineer
    assert "ci-pipeline-engineer" in result.output


def test_suggest_json_output(monkeypatch: Any) -> None:
    """--json should emit valid JSON array with required fields."""
    runner = CliRunner()
    result = runner.invoke(
        agents_group, ["suggest", "--text", "harden cluster", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert all("name" in item and "role" in item for item in payload)


def test_suggest_mlops_filter(monkeypatch: Any) -> None:
    """--mlops should filter to MLOps-oriented agents."""
    runner = CliRunner()
    res = runner.invoke(agents_group, ["suggest", "--text", "ml pipeline", "--mlops"])
    assert res.exit_code == 0
    # Should include mlops-engineer (mapped from 'ml pipeline')
    assert "mlops-engineer" in res.output
    # And should not include CI agent
    assert "ci-pipeline-engineer" not in res.output
