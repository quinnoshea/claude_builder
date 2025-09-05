"""DevOps Agent Registry for Claude Builder (P2.1).

Registers DevOps-domain agents so they are discoverable by the AgentRegistry.
Mapping/selection logic is deferred to P2.3.
"""

from typing import TYPE_CHECKING

from claude_builder.core.agents import AgentRole
from claude_builder.core.models import AgentInfo


if TYPE_CHECKING:  # Imported at type-check time only to avoid cycles
    from claude_builder.core.agents import AgentRegistry


class DevOpsAgents:
    """DevOps agents registration façade."""

    @staticmethod
    def register(registry: "AgentRegistry") -> None:
        """Register DevOps agents into the provided registry."""
        # Infrastructure (domain)
        agents_to_register = [
            AgentInfo(
                name="terraform-specialist",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Infrastructure-as-Code expert for Terraform: modular architecture, "
                    "remote state/backends, workspaces, providers, plan/apply safety, "
                    "policy guardrails, and drift management across environments."
                ),
                use_cases=[
                    "Author reusable modules and root configurations",
                    "Migrate/secure state (remote backends, locking, workspaces)",
                    "Multi-env strategies with variables and workspaces",
                    "Policy-as-code (Sentinel/OPA) and drift detection",
                    "CI pipelines for plan/apply with cost visibility",
                ],
            ),
            AgentInfo(
                name="ansible-automator",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Configuration management and provisioning with Ansible: playbooks, roles, "
                    "inventories, idempotent tasks, and day-2 ops across fleets and clouds."
                ),
                use_cases=[
                    "Harden OS images using CIS-aligned roles",
                    "Provision services idempotently across environments",
                    "Use dynamic inventories for cloud/VM targets",
                    "Zero-downtime rolling updates and handlers",
                    "Author Collections and test with Molecule",
                ],
            ),
            AgentInfo(
                name="kubernetes-operator",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Kubernetes workload and platform operations: manifests, controllers, "
                    "networking, multi-tenancy guardrails, and cluster lifecycle."
                ),
                use_cases=[
                    "Design namespaces, RBAC, and multi-tenant guardrails",
                    "Deployments/StatefulSets/DaemonSets rollout strategies",
                    "Ingress, Gateway API, and service mesh integration",
                    "HPA/VPA resources and reliable autoscaling",
                    "Cluster upgrades and addon lifecycle management",
                ],
            ),
            AgentInfo(
                name="helm-specialist",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Helm chart authoring and release management: templates, values schema, "
                    "chart testing, provenance/signing, and multi-env workflows."
                ),
                use_cases=[
                    "Create reusable charts and library charts",
                    "Values schema, defaults, and validation",
                    "helmfile/helm-secrets promotion workflows",
                    "Environment overrides for staging/production",
                    "Chart-testing and provenance/signing policies",
                ],
            ),
            # Platform (domain)
            AgentInfo(
                name="pulumi-engineer",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Pulumi IaC across clouds/stacks in TypeScript/Python/Go: component "
                    "abstractions, stack refs, secrets, and CI previews with policies."
                ),
                use_cases=[
                    "Define stacks with components and abstractions",
                    "Multi-cloud networking with Crosswalk patterns",
                    "Stack references, config, and encrypted secrets",
                    "Import and manage existing cloud resources",
                    "CI previews, policies, and approvals",
                ],
            ),
            AgentInfo(
                name="cloudformation-specialist",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "AWS CloudFormation/SAM/CDK authoring: nested stacks, change sets, drift "
                    "detection, and deployment guardrails for serverless and infra."
                ),
                use_cases=[
                    "Author nested stacks and StackSets for scale",
                    "Build serverless apps with SAM (APIs/functions)",
                    "Use change sets and drift detection safely",
                    "Design CDK constructs and CI/CD pipelines",
                    "Apply IAM guardrails and hooks for compliance",
                ],
            ),
            AgentInfo(
                name="packer-builder",
                role=AgentRole.DOMAIN.value,
                priority=2,
                description=(
                    "Golden image pipelines with Packer: AMIs, images, multi-builders, "
                    "provisioners (Ansible/Shell), validations, and registry publishing."
                ),
                use_cases=[
                    "Build hardened AMIs with CIS baselines",
                    "Multi-builder images across regions/clouds",
                    "HCL2 templates with Ansible provisioners",
                    "Pre/post validations and smoke tests",
                    "Publish/version images to registries",
                ],
            ),
            # Security (workflow)
            AgentInfo(
                name="security-auditor",
                role=AgentRole.WORKFLOW.value,
                priority=2,
                description=(
                    "Cloud/container/app security assessment: IaC scanning, image scanning, "
                    "benchmarks, secrets detection, SBOMs, and least-privilege reviews."
                ),
                use_cases=[
                    "Scan IaC (tfsec/Checkov) and remediate",
                    "Container image scanning (Trivy/Grype)",
                    "CIS/Kubernetes benchmark hardening",
                    "Secrets detection and SBOM generation",
                    "Identity and least-privilege reviews",
                ],
            ),
            # Operations (workflow)
            AgentInfo(
                name="ci-pipeline-engineer",
                role=AgentRole.WORKFLOW.value,
                priority=2,
                description=(
                    "CI/CD pipeline design across GitHub Actions/GitLab/Jenkins: "
                    "multi-stage, caching, matrix builds, reusable workflows, and "
                    "promotion/approval gates with secure runner operations."
                ),
                use_cases=[
                    "Design multi-stage pipelines with caching",
                    "Matrix builds and reusable workflows",
                    "Artifacts/versioning and SBOM publishing",
                    "Promotions with approvals and environments",
                    "OIDC secrets and scalable runners",
                ],
            ),
            AgentInfo(
                name="observability-engineer",
                role=AgentRole.WORKFLOW.value,
                priority=2,
                description=(
                    "Observability across metrics/logs/traces with Prometheus/Grafana/ELK/"
                    "OpenTelemetry: actionable dashboards, alerting, and on-call readiness."
                ),
                use_cases=[
                    "Define SLIs/SLOs and alert policies",
                    "Distributed tracing instrumentation (OTel)",
                    "Log pipelines, parsing, and retention",
                    "Service dashboards and runbooks",
                    "Alert routing and noise reduction",
                ],
            ),
            AgentInfo(
                name="sre-operator",
                role=AgentRole.WORKFLOW.value,
                priority=2,
                description=(
                    "Site Reliability Engineering: incident response, error budgets, "
                    "capacity planning, progressive delivery, and chaos engineering."
                ),
                use_cases=[
                    "Error budgets and SLO governance",
                    "Incident playbooks and postmortems",
                    "Autoscaling and capacity management",
                    "Blue/green and canary deployments",
                    "Chaos experiments and game days",
                ],
            ),
        ]

        for agent in agents_to_register:
            registry.register_agent(agent)
