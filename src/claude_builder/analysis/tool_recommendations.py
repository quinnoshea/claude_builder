"""Lookup tables for tool display names and actionable recommendations.

This module centralises the human-friendly metadata that templates use when
rendering DevOps and MLOps guidance. Keeping it here avoids hard-coding copy in
multiple templates while making it easy to evolve recommendations over time.
"""

from __future__ import annotations

from typing import Dict, List


DISPLAY_NAMES: Dict[str, str] = {
    # Infrastructure-as-code
    "terraform": "Terraform",
    "pulumi": "Pulumi",
    "ansible": "Ansible",
    "cloudformation": "AWS CloudFormation",
    "chef": "Chef",
    "saltstack": "SaltStack",
    "packer": "HashiCorp Packer",
    "waypoint": "HashiCorp Waypoint",
    "boundary": "HashiCorp Boundary",
    # Orchestration / containerisation
    "kubernetes": "Kubernetes",
    "helm": "Helm",
    "nomad": "HashiCorp Nomad",
    "docker": "Docker",
    "compose": "Docker Compose",
    # Secrets / security
    "vault": "HashiCorp Vault",
    "sops": "Mozilla SOPS",
    "trivy": "Trivy",
    "grype": "Grype",
    # Observability
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "opentelemetry": "OpenTelemetry",
    "jaeger": "Jaeger",
    "elastic_stack": "Elastic Stack",
    "loki": "Grafana Loki",
    # MLOps / data pipeline
    "airflow": "Apache Airflow",
    "prefect": "Prefect",
    "dagster": "Dagster",
    "dbt": "dbt",
    "dvc": "Data Version Control",
    "great_expectations": "Great Expectations",
    "mlflow": "MLflow",
    "feast": "Feast",
    "kubeflow": "Kubeflow",
    "bentoml": "BentoML",
    "notebooks": "Jupyter Notebooks",
}

RECOMMENDATIONS: Dict[str, List[str]] = {
    "terraform": [
        "Introduce separate workspaces or state files per environment (dev/staging/prod).",
        "Enable state locking via Terraform Cloud, S3 + DynamoDB, or another backend.",
        "Add mandatory `terraform fmt`/`terraform validate` to CI before apply stages.",
    ],
    "pulumi": [
        "Adopt stack configuration secrets for credentials and sensitive values.",
        "Automate preview + deployment flows through Pulumi Cloud or GitOps triggers.",
    ],
    "ansible": [
        "Group inventory by environment and use `group_vars` for shared defaults.",
        "Lint playbooks with `ansible-lint` and enforce idempotent roles in CI.",
    ],
    "kubernetes": [
        "Document cluster access policies and RBAC roles for each service.",
        "Add readiness/liveness probes and resource requests to every deployment.",
        "Consider applying Pod Security Standards or admission policies for hardening.",
    ],
    "helm": [
        "Template chart values per environment and store them alongside release docs.",
        "Enable chart testing/linting (`helm lint`) in CI to prevent misconfigured releases.",
    ],
    "docker": [
        "Adopt multi-stage builds to minimise final image size and surface vulnerabilities.",
        "Pin base images and configure automated CVE scanning (e.g. Trivy) in CI.",
    ],
    "prometheus": [
        "Define service-level SLIs/SLOs and track them via recording rules.",
        "Back up `prometheus.yml` and alert rules alongside infrastructure code.",
    ],
    "grafana": [
        "Manage dashboards as code (JSON/YAML) and ship via GitOps for repeatability.",
        "Leverage folders + permissions to segment dashboards for teams.",
    ],
    "opentelemetry": [
        "Roll out consistent resource attributes and sampling policies across services.",
        "Ship traces to a durable backend (e.g. Tempo, Jaeger, XRay) with retention rules.",
    ],
    "jaeger": [
        "Enable adaptive sampling to balance cost vs. visibility per service tier.",
        "Instrument baggage propagation for critical transaction identifiers.",
    ],
    "vault": [
        "Rotate root tokens and seal keys; rely on AppRole or OIDC for workloads.",
        "Integrate Vault audit logging with your security monitoring pipeline.",
    ],
    "sops": [
        "Store AES/GCP/KMS key references in repository documentation for onboarding.",
        "Automate SOPS decryption through CI with fine-grained IAM permissions.",
    ],
    "airflow": [
        "Version DAGs alongside code and validate with `airflow dags test` in CI.",
        "Monitor task duration trends to catch regressions and tune worker autoscaling.",
    ],
    "prefect": [
        "Promote flows via Prefect Deployments and tag runs for observability.",
        "Leverage Prefect Blocks for secrets and infrastructure to avoid hard-coded config.",
    ],
    "dagster": [
        "Document ops/assets metadata to power Dagster's asset catalog effectively.",
        "Schedule regular backfills and asset checks for critical pipelines.",
    ],
    "dbt": [
        "Enforce `dbt test` (data quality) and `dbt docs generate` in CI before deploys.",
        "Adopt exposures + freshness checks to track downstream data contracts.",
    ],
    "dvc": [
        "Store `.dvc` remotes in cloud object storage with versioned lifecycle policies.",
        "Use `dvc exp` to iterate on experiments and capture parameters reproducibly.",
    ],
    "great_expectations": [
        "Schedule expectation suites in orchestrators and surface failures via alerting.",
        "Version expectation YAMLs to track schema drift over time.",
    ],
    "mlflow": [
        "Promote models via MLflow Model Registry stages (staging/production).",
        "Capture environment markers (`conda.yaml`/`pip requirements.txt`) for reproducibility.",
    ],
    "feast": [
        "Document feature ownership and TTLs to manage production staleness.",
        "Automate feast materialisation jobs and monitor for import latency.",
    ],
    "kubeflow": [
        "Secure Kubeflow Pipelines with authentication (Dex/OIDC) and namespace isolation.",
        "Version pipeline components and track lineage via ML Metadata.",
    ],
    "bentoml": [
        "Build runners with GPU/CPU annotations and allocate appropriate resource limits.",
        "Publish Bento bundles to an OCI registry for deployment traceability.",
    ],
    "notebooks": [
        "Convert exploratory notebooks into reproducible pipelines (Papermill/dbt).",
        "Run parameterised notebooks via CI to detect breaking changes early.",
    ],
}


def get_display_name(slug: str) -> str:
    """Return a human-friendly display name for a tool slug."""

    return DISPLAY_NAMES.get(slug, slug.replace("_", " ").title())


def get_recommendations(slug: str) -> List[str]:
    """Return curated recommendations for a tool, falling back to generic advice."""

    return RECOMMENDATIONS.get(slug, [])
