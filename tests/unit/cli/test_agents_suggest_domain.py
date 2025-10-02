from unittest.mock import patch

from click.testing import CliRunner

from claude_builder.cli.agent_commands import agents
from claude_builder.core.models import AgentInfo


def _agents(*names):
    return [AgentInfo(name=n, role="", confidence=0.9) for n in names]


@patch("claude_builder.cli.agent_commands.AgentSelector.select_from_text")
def test_agents_suggest_domain_filters_mlops(mock_select):
    mock_select.return_value = _agents(
        "mlops-engineer", "terraform-specialist", "airflow-orchestrator"
    )
    runner = CliRunner()
    res = runner.invoke(
        agents, ["suggest", "--text", "pipeline", "--domain", "mlops", "--json"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "mlops-engineer" in out
    # DevOps agent should be filtered out
    assert "terraform-specialist" not in out


@patch("claude_builder.cli.agent_commands.AgentSelector.select_from_text")
def test_agents_suggest_domain_infra_maps_to_devops(mock_select):
    mock_select.return_value = _agents(
        "mlops-engineer", "terraform-specialist", "kubernetes-operator"
    )
    runner = CliRunner()
    res = runner.invoke(
        agents, ["suggest", "--text", "k8s", "--domain", "infra", "--json"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "terraform-specialist" in out or "kubernetes-operator" in out
    assert "mlops-engineer" not in out
