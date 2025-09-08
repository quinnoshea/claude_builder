"""Unit tests for the MLOps Agent Registry (P2.2)."""

from claude_builder.core.agents import AgentRegistry, AgentRole


MLOPS_AGENT_NAMES = [
    "mlops-engineer",
    "data-pipeline-engineer",
    "mlflow-ops",
    "airflow-orchestrator",
    "prefect-orchestrator",
    "dbt-analyst",
    "data-quality-engineer",
    "dvc-ops",
    "kubeflow-operator",
]


def test_mlops_agents_are_registered() -> None:
    """Test that all MLOps agents are registered with correct role/metadata."""
    registry = AgentRegistry()

    expected_roles = {
        # Platform agents (domain)
        "mlops-engineer": AgentRole.DOMAIN.value,
        "data-pipeline-engineer": AgentRole.DOMAIN.value,
        "mlflow-ops": AgentRole.DOMAIN.value,
        # Orchestration and quality (workflow)
        "airflow-orchestrator": AgentRole.WORKFLOW.value,
        "prefect-orchestrator": AgentRole.WORKFLOW.value,
        "dbt-analyst": AgentRole.WORKFLOW.value,
        "data-quality-engineer": AgentRole.WORKFLOW.value,
        # Specialized ML (domain)
        "dvc-ops": AgentRole.DOMAIN.value,
        "kubeflow-operator": AgentRole.DOMAIN.value,
    }

    for name, role in expected_roles.items():
        agent = registry.get_agent(name)
        assert agent is not None, f"Agent '{name}' should be registered"
        assert agent.role == role, f"Agent '{name}' should have role {role}"
        assert agent.priority == 2, f"Agent '{name}' should have priority 2"
        assert isinstance(agent.use_cases, list) and len(agent.use_cases) >= 3
        assert isinstance(agent.description, str) and len(agent.description) > 20


def test_registry_loading_is_idempotent() -> None:
    """Loading the registry multiple times should not create duplicates."""
    r1 = AgentRegistry()
    r2 = AgentRegistry()
    assert len(r1._agents) == len(r2._agents)
    assert r1._agents.keys() == r2._agents.keys()


def test_mlops_and_devops_coexist() -> None:
    """Ensure both registries are loaded and co-exist."""
    registry = AgentRegistry()

    # A few well-known DevOps agents
    for devops_name in [
        "terraform-specialist",
        "kubernetes-operator",
        "ci-pipeline-engineer",
    ]:
        assert registry.get_agent(devops_name) is not None

    # A few MLOps agents
    for mlops_name in [
        "mlops-engineer",
        "data-pipeline-engineer",
        "airflow-orchestrator",
    ]:
        assert registry.get_agent(mlops_name) is not None


def test_mlops_role_distribution() -> None:
    """Validate expected domain/workflow distribution for MLOps agents."""
    registry = AgentRegistry()
    domain = 0
    workflow = 0
    for name in MLOPS_AGENT_NAMES:
        agent = registry.get_agent(name)
        assert agent is not None
        if agent.role == AgentRole.DOMAIN.value:
            domain += 1
        elif agent.role == AgentRole.WORKFLOW.value:
            workflow += 1
    assert domain == 5
    assert workflow == 4
