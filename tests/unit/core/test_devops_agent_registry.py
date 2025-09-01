"""Smoke tests for the DevOps Agent Registry (P2.1)."""

from claude_builder.core.agents import AgentRegistry, AgentRole


def test_devops_agents_are_registered() -> None:
    registry = AgentRegistry()

    expected = {
        # Infrastructure (domain)
        "terraform-specialist": AgentRole.DOMAIN.value,
        "ansible-automator": AgentRole.DOMAIN.value,
        "kubernetes-operator": AgentRole.DOMAIN.value,
        "helm-specialist": AgentRole.DOMAIN.value,
        # Platform/Security
        "pulumi-engineer": AgentRole.DOMAIN.value,
        "cloudformation-specialist": AgentRole.DOMAIN.value,
        "packer-builder": AgentRole.DOMAIN.value,
        # Operations/Security (workflow)
        "security-auditor": AgentRole.WORKFLOW.value,
        "ci-pipeline-engineer": AgentRole.WORKFLOW.value,
        "observability-engineer": AgentRole.WORKFLOW.value,
        "sre-operator": AgentRole.WORKFLOW.value,
    }

    # Ensure at least these agents exist and have correct role/priority/use_cases
    for name, role in expected.items():
        agent = registry.get_agent(name)
        assert agent is not None, f"Agent '{name}' should be registered"
        assert agent.role == role
        assert agent.priority == 2
        assert isinstance(agent.use_cases, list) and len(agent.use_cases) >= 3
