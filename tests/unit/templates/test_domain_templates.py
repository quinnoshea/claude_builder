from pathlib import Path

from claude_builder.core.models import (
    ComplexityLevel,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
)
from claude_builder.core.template_manager import ModernTemplateManager


def _make_analysis(tmp_path: Path, *, tools: dict[str, list[str]]) -> ProjectAnalysis:
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
    return analysis


def test_devops_and_mlops_sections_render(tmp_path: Path) -> None:
    tools = {
        "infrastructure_as_code": ["terraform"],
        "orchestration_tools": ["kubernetes", "helm"],
        "observability": ["prometheus", "grafana", "opentelemetry"],
        "security_tools": ["tfsec", "trivy"],
        "data_pipeline": ["airflow", "dvc"],
        "mlops_tools": ["mlflow"],
    }
    analysis = _make_analysis(tmp_path, tools=tools)

    mgr = ModernTemplateManager()
    ctx = mgr._create_environment_context(analysis, agent_definitions=[])
    sections = mgr._render_domain_sections(ctx)

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
    assert "DVC" in sections


def test_no_domain_tools_renders_no_sections(tmp_path: Path) -> None:
    analysis = _make_analysis(tmp_path, tools={})
    mgr = ModernTemplateManager()
    ctx = mgr._create_environment_context(analysis, agent_definitions=[])
    sections = mgr._render_domain_sections(ctx)
    assert sections == ""


def test_mlops_only_sections(tmp_path: Path) -> None:
    tools = {
        "mlops_tools": ["mlflow"],
        "data_pipeline": ["airflow"],
    }
    analysis = _make_analysis(tmp_path, tools=tools)
    mgr = ModernTemplateManager()
    ctx = mgr._create_environment_context(analysis, agent_definitions=[])
    sections = mgr._render_domain_sections(ctx)

    assert "MLflow" in sections
    assert "Airflow" in sections
    # Should not include unrelated DevOps content
    assert "Kubernetes Deployments" not in sections
    assert "Infrastructure as Code" not in sections
