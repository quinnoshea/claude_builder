from pathlib import Path

from claude_builder.analysis.detectors.infrastructure import InfrastructureDetector


def test_detect_categories_and_secrets_mapping(tmp_path: Path) -> None:
    # Infra: Terraform and Docker
    (tmp_path / "main.tf").touch()
    (tmp_path / "terraform.tfstate").touch()
    (tmp_path / ".terraform").mkdir()
    (tmp_path / "Dockerfile").touch()

    # Orchestration: Kubernetes + Helm
    (tmp_path / "deployment.yaml").touch()
    (tmp_path / "Chart.yaml").touch()

    # Observability
    (tmp_path / "prometheus.yml").touch()

    # Security + Secrets
    (tmp_path / ".trivyignore").touch()
    (tmp_path / "policy.rego").touch()
    (tmp_path / ".sops.yaml").touch()
    (tmp_path / "vault.hcl").touch()

    detector = InfrastructureDetector(tmp_path)
    categories = detector.detect()

    assert "terraform" in categories["infrastructure_as_code"]
    assert "docker" in (
        categories["orchestration_tools"] + categories["infrastructure_as_code"]
    )  # docker may be classified either way based on sets
    assert (
        "kubernetes" in categories["orchestration_tools"]
        or "helm" in categories["orchestration_tools"]
    )
    assert "prometheus" in categories["observability"]
    assert "trivy" in categories["security_tools"]
    # secrets combined from infra (vault) and security (sops)
    assert "vault" in categories["secrets_management"]
    assert "sops" in categories["secrets_management"]


def test_confidence_bucketing(tmp_path: Path) -> None:
    # High confidence terraform: dir + state + files
    (tmp_path / "main.tf").touch()
    (tmp_path / "variables.tf").touch()
    (tmp_path / "terraform.tfstate").touch()
    (tmp_path / ".terraform").mkdir()

    detector = InfrastructureDetector(tmp_path)
    categories, confidence = detector.detect_with_confidence()

    assert confidence.get("terraform") in {"high", "medium"}

    # Low confidence case: single file
    low_dir = tmp_path / "low"
    low_dir.mkdir()
    (low_dir / "main.tf").touch()

    low_detector = InfrastructureDetector(low_dir)
    _, low_conf = low_detector.detect_with_confidence()
    assert low_conf.get("terraform") == "low"
