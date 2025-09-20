from pathlib import Path

import pytest


pytestmark = pytest.mark.failing

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


def _normalise_markdown(content: str) -> str:
    lines: list[str] = []
    previous_blank = False
    for raw in content.strip().splitlines():
        line = raw.rstrip()
        if not line:
            if previous_blank:
                continue
            previous_blank = True
            lines.append("")
        else:
            previous_blank = False
            lines.append(line)
    return "\n".join(lines)


def _make_analysis(
    tmp_path: Path,
    *,
    tools: dict[str, list[str]],
    metadata: dict[str, ToolMetadata] | None = None,
) -> ProjectAnalysis:
    analysis = ProjectAnalysis(
        project_path=tmp_path / "sample",
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

    for slug, meta in (metadata or {}).items():
        env.tool_details[slug] = meta
    return analysis


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


def _render_sections(
    tmp_path: Path, *, tools: dict[str, list[str]], metadata: dict[str, ToolMetadata]
) -> str:
    analysis = _make_analysis(tmp_path, tools=tools, metadata=metadata)
    mgr = ModernTemplateManager()
    ctx = mgr._create_environment_context(analysis, agent_definitions=[])
    return mgr._render_domain_sections(ctx)


def test_devops_and_mlops_sections_render(tmp_path: Path) -> None:
    tools = {
        "infrastructure_as_code": ["terraform"],
        "orchestration_tools": ["kubernetes", "helm"],
        "observability": ["prometheus", "grafana", "opentelemetry"],
        "security_tools": ["tfsec", "trivy"],
        "data_pipeline": ["airflow", "dvc"],
        "mlops_tools": ["mlflow"],
    }
    metadata = {
        "terraform": _metadata("terraform", category="infrastructure"),
        "kubernetes": _metadata(
            "kubernetes", category="orchestration_tools", files=["k8s/deployment.yaml"]
        ),
        "helm": _metadata(
            "helm", category="orchestration_tools", files=["charts/my-chart/Chart.yaml"]
        ),
        "prometheus": _metadata(
            "prometheus",
            category="observability",
            files=["observability/prometheus.yml"],
        ),
        "grafana": _metadata(
            "grafana", category="observability", files=["grafana/dashboards/app.json"]
        ),
        "opentelemetry": _metadata("opentelemetry", category="observability"),
        "tfsec": _metadata("tfsec", category="security"),
        "trivy": _metadata("trivy", category="security"),
        "airflow": _metadata(
            "airflow", category="data_pipeline", files=["dags/sample_dag.py"]
        ),
        "dvc": _metadata("dvc", category="data_pipeline", files=["data.dvc"]),
        "mlflow": _metadata(
            "mlflow", category="mlops_tools", files=["mlruns/0/meta.yaml"]
        ),
    }
    sections = _render_sections(tmp_path, tools=tools, metadata=metadata)

    # DevOps bits
    assert "Infrastructure as Code" in sections
    assert "Kubernetes Deployments" in sections
    assert "Helm Chart" in sections
    assert "Prometheus" in sections
    assert "Grafana" in sections
    assert "OpenTelemetry" in sections
    assert "tfsec" in sections
    assert "Trivy" in sections

    # MLOps bits
    assert "MLflow" in sections
    assert "Airflow" in sections
    assert get_display_name("dvc") in sections


def test_no_domain_tools_renders_no_sections(tmp_path: Path) -> None:
    sections = _render_sections(tmp_path, tools={}, metadata={})
    assert sections == ""


def test_mlops_only_sections(tmp_path: Path) -> None:
    tools = {
        "mlops_tools": ["mlflow"],
        "data_pipeline": ["airflow"],
    }
    metadata = {
        "mlflow": _metadata("mlflow", category="mlops_tools"),
        "airflow": _metadata("airflow", category="data_pipeline"),
    }
    sections = _render_sections(tmp_path, tools=tools, metadata=metadata)

    assert "MLflow" in sections
    assert "Airflow" in sections
    # Should not include unrelated DevOps content
    assert "Kubernetes Deployments" not in sections
    assert "Infrastructure as Code" not in sections


def test_devops_snapshot(tmp_path: Path) -> None:
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
    rendered = _render_sections(tmp_path, tools=tools, metadata=metadata)
    snapshot_path = Path(__file__).parent / "__snapshots__" / "devops_snapshot.md"
    expected = snapshot_path.read_text(encoding="utf-8").replace(
        "<!-- markdownlint-disable MD025 -->", ""
    )
    assert _normalise_markdown(rendered) == _normalise_markdown(expected)


def test_mlops_snapshot(tmp_path: Path) -> None:
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
    rendered = _render_sections(tmp_path, tools=tools, metadata=metadata)
    snapshot_path = Path(__file__).parent / "__snapshots__" / "mlops_snapshot.md"
    expected = snapshot_path.read_text(encoding="utf-8").replace(
        "<!-- markdownlint-disable MD025 -->", ""
    )
    assert _normalise_markdown(rendered) == _normalise_markdown(expected)


def test_mixed_snapshot(tmp_path: Path) -> None:
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
    rendered = _render_sections(tmp_path, tools=tools, metadata=metadata)
    snapshot_path = Path(__file__).parent / "__snapshots__" / "mixed_snapshot.md"
    expected = snapshot_path.read_text(encoding="utf-8").replace(
        "<!-- markdownlint-disable MD025 -->", ""
    )
    assert _normalise_markdown(rendered) == _normalise_markdown(expected)
