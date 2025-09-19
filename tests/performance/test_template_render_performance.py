import pytest

from claude_builder.core.models import (
    ComplexityLevel,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
    ToolMetadata,
)
from claude_builder.core.template_manager import ModernTemplateManager


def _analysis(tmp_path, tools, metadata):
    project_path = tmp_path / "perf_project"
    project_path.mkdir(parents=True, exist_ok=True)
    analysis = ProjectAnalysis(
        project_path=project_path,
        language_info=LanguageInfo(primary="python", confidence=95.0),
        framework_info=FrameworkInfo(primary=None, confidence=0.0),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MODERATE,
    )
    env = analysis.dev_environment
    env.infrastructure_as_code = tools.get("infrastructure_as_code", [])
    env.orchestration_tools = tools.get("orchestration_tools", [])
    env.secrets_management = tools.get("secrets_management", [])
    env.observability = tools.get("observability", [])
    env.ci_cd_systems = tools.get("ci_cd_systems", [])
    env.data_pipeline = tools.get("data_pipeline", [])
    env.mlops_tools = tools.get("mlops_tools", [])
    env.security_tools = tools.get("security_tools", [])
    env.tool_details.update(metadata)
    return analysis


def _meta(slug: str, category: str) -> ToolMetadata:
    return ToolMetadata(
        name=slug.replace("_", " ").title(),
        slug=slug,
        category=category,
        confidence="high",
        score=15.0,
        files=[f"{slug}/config.yaml"],
        recommendations=[f"Apply best practices for {slug} across environments."],
    )


@pytest.mark.benchmark(group="template-render")
def test_template_rendering_under_200ms(benchmark, tmp_path):
    tools = {
        "infrastructure_as_code": ["terraform", "pulumi", "ansible", "cloudformation"],
        "orchestration_tools": ["kubernetes", "helm", "nomad"],
        "observability": ["prometheus", "grafana", "opentelemetry", "loki"],
        "security_tools": ["vault", "trivy", "grype"],
        "data_pipeline": ["airflow", "prefect", "dagster"],
        "mlops_tools": ["mlflow", "feast", "kubeflow"],
    }

    metadata = {
        slug: _meta(slug, category)
        for category, slugs in tools.items()
        for slug in slugs
    }

    analysis = _analysis(tmp_path, tools=tools, metadata=metadata)
    mgr = ModernTemplateManager()

    def _render() -> str:
        context = mgr._create_environment_context(analysis, agent_definitions=[])
        return mgr._render_domain_sections(context)

    result = benchmark(_render)

    # Ensure the rendering still produces content and remains performant.
    assert "DevOps" in result or "MLOps" in result
    mean_runtime = benchmark.stats.get("mean")
    assert (
        mean_runtime < 0.2
    ), f"Template rendering took {mean_runtime:.3f}s which exceeds the 200 ms budget"
