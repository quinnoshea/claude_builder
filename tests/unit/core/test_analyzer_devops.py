from pathlib import Path

from claude_builder.core.analyzer import ProjectAnalyzer


def test_analyze_devops_environment(tmp_path: Path) -> None:
    project = tmp_path / "devops_project"
    project.mkdir()

    # Infra
    (project / "main.tf").touch()
    (project / "Dockerfile").touch()
    (project / "docker-compose.yml").touch()

    # Orchestration
    (project / "deployment.yaml").touch()
    (project / "Chart.yaml").touch()

    # Observability
    (project / "prometheus.yml").touch()

    # Security + Secrets
    (project / ".trivyignore").touch()
    (project / ".sops.yaml").touch()
    (project / "vault.hcl").touch()

    analyzer = ProjectAnalyzer()
    result = analyzer.analyze(project)
    env = result.dev_environment

    assert "terraform" in env.infrastructure_as_code
    assert ("kubernetes" in env.orchestration_tools) or (
        "helm" in env.orchestration_tools
    )
    assert "prometheus" in env.observability
    assert "trivy" in env.security_tools
    assert "sops" in env.secrets_management and "vault" in env.secrets_management
