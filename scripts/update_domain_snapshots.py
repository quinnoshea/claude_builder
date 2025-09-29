#!/usr/bin/env python3
"""
Regenerate domain template snapshots for tests/unit/templates/__snapshots__.

This mirrors the inputs used in tests/unit/templates/test_domain_templates.py
to ensure snapshots reflect the current renderer output.
"""
from pathlib import Path

from claude_builder.analysis.tool_recommendations import get_display_name
from claude_builder.core.models import (
    ComplexityLevel,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
    ToolMetadata,
)
from claude_builder.core.template_manager import ModernTemplateManager


def _metadata(
    slug: str,
    *,
    name: str | None = None,
    category: str = "infrastructure",
    confidence: str = "high",
    score: float = 12.0,
    files: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> ToolMetadata:
    return ToolMetadata(
        name=name or get_display_name(slug),
        slug=slug,
        category=category,
        confidence=confidence,
        score=score,
        files=files or [f"{slug}/config.yaml"],
        recommendations=recommendations or [f"Enable best practices for {slug}."],
    )


def _make_analysis(
    tmp_root: Path, tools: dict[str, list[str]], metadata: dict[str, ToolMetadata]
) -> ProjectAnalysis:
    analysis = ProjectAnalysis(
        project_path=tmp_root / "sample",
        language_info=LanguageInfo(primary="python", confidence=95.0),
        framework_info=FrameworkInfo(primary=None, confidence=0.0),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MODERATE,
    )
    analysis.project_path.mkdir(parents=True, exist_ok=True)

    env = analysis.dev_environment
    env.infrastructure_as_code = tools.get("infrastructure_as_code", [])
    env.orchestration_tools = tools.get("orchestration_tools", [])
    env.secrets_management = tools.get("secrets_management", [])
    env.observability = tools.get("observability", [])
    env.ci_cd_systems = tools.get("ci_cd_systems", [])
    env.data_pipeline = tools.get("data_pipeline", [])
    env.mlops_tools = tools.get("mlops_tools", [])
    env.security_tools = tools.get("security_tools", [])

    for slug, meta in metadata.items():
        env.tool_details[slug] = meta
    return analysis


def regenerate() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    snapshot_dir = repo_root / "tests" / "unit" / "templates" / "__snapshots__"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    mgr = ModernTemplateManager()
    tmp_root = repo_root / "tests" / ".tmp_snapshot_project"
    tmp_root.mkdir(parents=True, exist_ok=True)

    # DevOps snapshot
    metadata = {
        "terraform": _metadata(
            "terraform",
            category="infrastructure",
            recommendations=[
                "Introduce workspaces per environment.",
                "Enable remote state locking.",
            ],
        ),
        "kubernetes": _metadata(
            "kubernetes", category="orchestration_tools", files=["k8s/deployment.yaml"]
        ),
        "helm": _metadata(
            "helm", category="orchestration_tools", files=["charts/app/Chart.yaml"]
        ),
        "prometheus": _metadata(
            "prometheus",
            category="observability",
            files=["observability/prometheus.yml"],
        ),
        "grafana": _metadata(
            "grafana", category="observability", files=["grafana/dashboards/app.json"]
        ),
        "vault": _metadata("vault", category="security"),
    }
    tools = {
        "infrastructure_as_code": ["terraform"],
        "orchestration_tools": ["kubernetes", "helm"],
        "observability": ["prometheus", "grafana"],
        "security_tools": ["vault"],
    }
    ctx = mgr._create_environment_context(
        _make_analysis(tmp_root, tools, metadata), agent_definitions=[]
    )
    rendered = mgr._render_domain_sections(ctx)
    (snapshot_dir / "devops_snapshot.md").write_text(rendered, encoding="utf-8")

    # MLOps snapshot
    metadata = {
        "airflow": _metadata(
            "airflow", category="data_pipeline", files=["dags/sample_dag.py"]
        ),
        "prefect": _metadata("prefect", category="data_pipeline"),
        "mlflow": _metadata("mlflow", category="mlops_tools"),
        "feast": _metadata("feast", category="mlops_tools"),
    }
    tools = {
        "data_pipeline": ["airflow", "prefect"],
        "mlops_tools": ["mlflow", "feast"],
    }
    ctx = mgr._create_environment_context(
        _make_analysis(tmp_root, tools, metadata), agent_definitions=[]
    )
    rendered = mgr._render_domain_sections(ctx)
    (snapshot_dir / "mlops_snapshot.md").write_text(rendered, encoding="utf-8")

    # Mixed snapshot
    metadata = {
        "terraform": _metadata("terraform", category="infrastructure"),
        "prometheus": _metadata("prometheus", category="observability"),
        "airflow": _metadata(
            "airflow", category="data_pipeline", files=["dags/sample_dag.py"]
        ),
        "mlflow": _metadata("mlflow", category="mlops_tools"),
    }
    tools = {
        "infrastructure_as_code": ["terraform"],
        "observability": ["prometheus"],
        "data_pipeline": ["airflow"],
        "mlops_tools": ["mlflow"],
    }
    ctx = mgr._create_environment_context(
        _make_analysis(tmp_root, tools, metadata), agent_definitions=[]
    )
    rendered = mgr._render_domain_sections(ctx)
    (snapshot_dir / "mixed_snapshot.md").write_text(rendered, encoding="utf-8")

    print(f"Updated snapshots in {snapshot_dir}")


if __name__ == "__main__":
    regenerate()
