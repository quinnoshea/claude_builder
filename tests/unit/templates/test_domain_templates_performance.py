import time

from pathlib import Path

import pytest

from claude_builder.core.models import (
    ComplexityLevel,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
)
from claude_builder.core.template_manager import ModernTemplateManager


def _make_basic_analysis(tmp_path: Path) -> ProjectAnalysis:
    analysis = ProjectAnalysis(
        project_path=tmp_path / "sample",
        language_info=LanguageInfo(primary="python", confidence=95.0),
        framework_info=FrameworkInfo(primary=None, confidence=0.0),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MODERATE,
    )
    analysis.project_path.mkdir(parents=True, exist_ok=True)
    env = analysis.dev_environment
    env.infrastructure_as_code = ["terraform"]
    env.orchestration_tools = ["kubernetes", "helm"]
    env.observability = ["prometheus", "grafana", "opentelemetry"]
    env.security_tools = ["trivy"]
    env.data_pipeline = ["airflow", "prefect"]
    env.mlops_tools = ["mlflow"]
    return analysis


@pytest.mark.performance
def test_domain_section_rendering_time(tmp_path: Path) -> None:
    """Render domain sections within a generous threshold to avoid flakiness.

    This is a spot check to guard against accidental quadratic behavior in the
    lightweight Jinja-style renderer used in legacy paths.
    """
    mgr = ModernTemplateManager()
    analysis = _make_basic_analysis(tmp_path)
    ctx = mgr._create_environment_context(analysis, agent_definitions=[])

    start = time.perf_counter()
    result = mgr._render_domain_sections(ctx)
    elapsed = time.perf_counter() - start

    # Basic sanity
    assert "DevOps" in result or "MLOps" in result

    # Generous threshold: keep under 1s locally to catch egregious regressions
    assert elapsed < 1.0, f"Domain rendering took {elapsed:.3f}s (>1.0s)"
