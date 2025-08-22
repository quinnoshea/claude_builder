"""Tests for Phase 2 intelligence layer: Agent System.

Tests cover the agent management and coordination system including:
- Agent discovery and selection
- Agent workflow orchestration
- Agent configuration and customization
- Multi-agent coordination
"""

from unittest.mock import Mock, patch

import pytest

from claude_builder.core.agents import (
    Agent,
    AgentCoordinator,
    AgentManager,
    AgentSelector,
    AgentWorkflow,
)
from claude_builder.core.models import ComplexityLevel, ProjectType


@pytest.mark.unit
@pytest.mark.phase2
class TestAgentManager:
    """Test the main AgentManager class."""

    def test_agent_manager_initialization(self):
        """Test agent manager initializes with correct defaults."""
        manager = AgentManager()
        assert manager is not None
        assert hasattr(manager, "agent_selector")
        assert hasattr(manager, "agent_coordinator")

    def test_agent_manager_with_config(self):
        """Test agent manager initializes with custom configuration."""
        config = {
            "install_automatically": False,
            "exclude_agents": ["test-agent"],
            "priority_agents": ["python-pro", "backend-architect"],
            "max_concurrent_agents": 3,
        }
        manager = AgentManager(config=config)
        assert manager.config["install_automatically"] is False
        assert "test-agent" in manager.config["exclude_agents"]
        assert manager.config["max_concurrent_agents"] == 3

    def test_discover_available_agents(self):
        """Test discovery of available agents."""
        manager = AgentManager()
        agents = manager.discover_available_agents()

        assert isinstance(agents, list)
        assert len(agents) > 0

        # Check for core agents that should always be available
        agent_names = [agent.name for agent in agents]
        expected_core_agents = [
            "python-pro",
            "frontend-developer",
            "backend-architect",
            "test-writer-fixer",
            "ui-designer",
            "rapid-prototyper",
        ]

        for expected_agent in expected_core_agents:
            assert expected_agent in agent_names

    def test_select_agents_for_project(self, sample_analysis):
        """Test agent selection for a specific project."""
        manager = AgentManager()

        # Test Python web API project
        sample_analysis.language_info.primary = "python"
        sample_analysis.project_type = ProjectType.API_SERVICE
        sample_analysis.framework_info.primary = "fastapi"

        selected_agents = manager.select_agents_for_project(sample_analysis)

        assert isinstance(selected_agents, list)
        assert len(selected_agents) > 0

        # Should select appropriate agents for Python web API
        agent_names = [agent.name for agent in selected_agents]
        assert any(
            "python" in name.lower() or "backend" in name.lower()
            for name in agent_names
        )

    def test_install_agent(self):
        """Test agent installation functionality."""
        manager = AgentManager()

        # Mock agent installation
        with patch.object(manager, "_download_agent") as mock_download:
            mock_download.return_value = True

            result = manager.install_agent("test-agent")

            assert result is True
            mock_download.assert_called_once_with("test-agent")

    def test_agent_workflow_creation(self, sample_analysis):
        """Test creation of agent workflows."""
        manager = AgentManager()

        workflow = manager.create_workflow_for_project(sample_analysis)

        assert isinstance(workflow, AgentWorkflow)
        assert len(workflow.agents) > 0
        assert workflow.project_analysis == sample_analysis

    def test_agent_exclusion(self, sample_analysis):
        """Test agent exclusion functionality."""
        config = {"exclude_agents": ["ui-designer", "whimsy-injector"]}
        manager = AgentManager(config=config)

        selected_agents = manager.select_agents_for_project(sample_analysis)
        agent_names = [agent.name for agent in selected_agents]

        assert "ui-designer" not in agent_names
        assert "whimsy-injector" not in agent_names

    def test_priority_agent_selection(self, sample_analysis):
        """Test priority agent selection."""
        config = {"priority_agents": ["rapid-prototyper", "test-writer-fixer"]}
        manager = AgentManager(config=config)

        selected_agents = manager.select_agents_for_project(sample_analysis)
        agent_names = [agent.name for agent in selected_agents]

        # Priority agents should be included
        assert "rapid-prototyper" in agent_names
        assert "test-writer-fixer" in agent_names


@pytest.mark.unit
@pytest.mark.phase2
class TestAgentSelector:
    """Test the AgentSelector component."""

    def test_agent_selector_initialization(self):
        """Test agent selector initializes correctly."""
        selector = AgentSelector()
        assert selector is not None
        assert hasattr(selector, "selection_algorithm")

    def test_select_for_python_project(self, sample_analysis):
        """Test agent selection for Python project."""
        sample_analysis.language_info.primary = "python"
        sample_analysis.project_type = ProjectType.CLI_TOOL

        selector = AgentSelector()
        agents = selector.select_agents(sample_analysis)

        assert len(agents) > 0

        # Should include Python-specific agents
        agent_names = [agent.name for agent in agents]
        assert any("python" in name.lower() for name in agent_names)

    def test_select_for_rust_project(self, sample_analysis):
        """Test agent selection for Rust project."""
        sample_analysis.language_info.primary = "rust"
        sample_analysis.project_type = ProjectType.CLI_TOOL
        sample_analysis.build_system = "cargo"

        selector = AgentSelector()
        agents = selector.select_agents(sample_analysis)

        # Should include appropriate agents for Rust CLI
        agent_names = [agent.name for agent in agents]
        expected_agents = ["rapid-prototyper", "test-writer-fixer"]

        for expected in expected_agents:
            assert expected in agent_names

    def test_select_for_web_frontend_project(self, sample_analysis):
        """Test agent selection for web frontend project."""
        sample_analysis.language_info.primary = "javascript"
        sample_analysis.project_type = ProjectType.WEB_FRONTEND
        sample_analysis.framework_info.primary = "react"

        selector = AgentSelector()
        agents = selector.select_agents(sample_analysis)

        # Should include frontend-specific agents
        agent_names = [agent.name for agent in agents]
        expected_agents = ["frontend-developer", "ui-designer"]

        for expected in expected_agents:
            assert expected in agent_names

    def test_select_for_complex_project(self, sample_analysis):
        """Test agent selection adapts to project complexity."""
        sample_analysis.complexity_level = ComplexityLevel.HIGH
        sample_analysis.project_type = ProjectType.API_SERVICE

        selector = AgentSelector()
        high_complexity_agents = selector.select_agents(sample_analysis)

        # High complexity should select more agents
        sample_analysis.complexity_level = ComplexityLevel.SIMPLE
        simple_complexity_agents = selector.select_agents(sample_analysis)

        assert len(high_complexity_agents) >= len(simple_complexity_agents)

    def test_confidence_based_selection(self, sample_analysis):
        """Test that agent selection considers analysis confidence."""
        # High confidence analysis
        sample_analysis.language_info.confidence = 95.0
        sample_analysis.framework_info.confidence = 90.0

        selector = AgentSelector()
        high_confidence_agents = selector.select_agents(sample_analysis)

        # Low confidence analysis
        sample_analysis.language_info.confidence = 60.0
        sample_analysis.framework_info.confidence = 50.0

        low_confidence_agents = selector.select_agents(sample_analysis)

        # High confidence should lead to more specific agent selection
        assert len(high_confidence_agents) >= len(low_confidence_agents)

    def test_domain_specific_selection(self, sample_analysis):
        """Test domain-specific agent selection."""
        sample_analysis.domain_info.domain = "e_commerce"
        sample_analysis.domain_info.features = ["payment_processing", "inventory"]

        selector = AgentSelector()
        agents = selector.select_agents(sample_analysis)

        # Should include appropriate agents for e-commerce domain
        agent_names = [agent.name for agent in agents]
        expected_agents = ["backend-architect", "api-designer"]

        for expected in expected_agents:
            assert expected in agent_names

    def test_selection_algorithm_configuration(self, sample_analysis):
        """Test different selection algorithms."""
        # Test intelligent algorithm
        selector_intelligent = AgentSelector(algorithm="intelligent")
        intelligent_agents = selector_intelligent.select_agents(sample_analysis)

        # Test strict algorithm
        selector_strict = AgentSelector(algorithm="strict")
        strict_agents = selector_strict.select_agents(sample_analysis)

        # Test permissive algorithm
        selector_permissive = AgentSelector(algorithm="permissive")
        permissive_agents = selector_permissive.select_agents(sample_analysis)

        # Different algorithms should produce different results
        assert len(permissive_agents) >= len(intelligent_agents) >= len(strict_agents)


@pytest.mark.unit
@pytest.mark.phase2
class TestAgentCoordinator:
    """Test the AgentCoordinator component."""

    def test_agent_coordinator_initialization(self):
        """Test agent coordinator initializes correctly."""
        coordinator = AgentCoordinator()
        assert coordinator is not None
        assert hasattr(coordinator, "max_concurrent_agents")

    def test_create_workflow(self, sample_analysis):
        """Test workflow creation."""
        coordinator = AgentCoordinator()

        # Create mock agents
        agents = [
            Mock(name="agent1", capabilities=["analysis"], priority=1),
            Mock(name="agent2", capabilities=["generation"], priority=2),
            Mock(name="agent3", capabilities=["validation"], priority=3),
        ]

        workflow = coordinator.create_workflow(agents, sample_analysis)

        assert isinstance(workflow, AgentWorkflow)
        assert len(workflow.agents) == 3
        assert workflow.project_analysis == sample_analysis

    def test_workflow_execution_order(self):
        """Test that workflow execution follows proper order."""
        coordinator = AgentCoordinator()

        # Create agents with different priorities
        agent1 = Mock(name="low-priority", priority=3)
        agent2 = Mock(name="high-priority", priority=1)
        agent3 = Mock(name="medium-priority", priority=2)

        agents = [agent1, agent2, agent3]

        workflow = coordinator.create_workflow(agents, Mock())
        execution_order = coordinator.determine_execution_order(workflow)

        # Should be ordered by priority (1, 2, 3)
        assert execution_order[0].name == "high-priority"
        assert execution_order[1].name == "medium-priority"
        assert execution_order[2].name == "low-priority"

    def test_parallel_execution_grouping(self):
        """Test parallel execution grouping."""
        coordinator = AgentCoordinator(max_concurrent_agents=2)

        # Create agents that can run in parallel
        agents = [
            Mock(name="agent1", capabilities=["analysis"], dependencies=[]),
            Mock(name="agent2", capabilities=["research"], dependencies=[]),
            Mock(name="agent3", capabilities=["generation"], dependencies=["analysis"]),
        ]

        workflow = coordinator.create_workflow(agents, Mock())
        execution_groups = coordinator.group_for_parallel_execution(workflow)

        # First group should have agents without dependencies
        # Second group should have agents that depend on first group
        assert len(execution_groups) >= 2
        assert len(execution_groups[0]) <= 2  # Max concurrent limit

    def test_dependency_resolution(self):
        """Test agent dependency resolution."""
        coordinator = AgentCoordinator()

        # Create agents with dependencies
        agent1 = Mock(name="analyzer", capabilities=["analysis"], dependencies=[])
        agent2 = Mock(
            name="generator", capabilities=["generation"], dependencies=["analysis"]
        )
        agent3 = Mock(
            name="validator", capabilities=["validation"], dependencies=["generation"]
        )

        agents = [agent3, agent1, agent2]  # Intentionally out of order

        workflow = coordinator.create_workflow(agents, Mock())
        resolved_order = coordinator.resolve_dependencies(workflow)

        # Should be reordered based on dependencies
        names = [agent.name for agent in resolved_order]
        analyzer_idx = names.index("analyzer")
        generator_idx = names.index("generator")
        validator_idx = names.index("validator")

        assert analyzer_idx < generator_idx < validator_idx

    def test_workflow_validation(self, sample_analysis):
        """Test workflow validation."""
        coordinator = AgentCoordinator()

        # Valid workflow
        valid_agents = [
            Mock(name="agent1", capabilities=["analysis"], dependencies=[]),
            Mock(name="agent2", capabilities=["generation"], dependencies=["analysis"]),
        ]

        valid_workflow = coordinator.create_workflow(valid_agents, sample_analysis)
        assert coordinator.validate_workflow(valid_workflow) is True

        # Invalid workflow (circular dependency)
        invalid_agents = [
            Mock(name="agent1", capabilities=["analysis"], dependencies=["generation"]),
            Mock(name="agent2", capabilities=["generation"], dependencies=["analysis"]),
        ]

        invalid_workflow = coordinator.create_workflow(invalid_agents, sample_analysis)
        assert coordinator.validate_workflow(invalid_workflow) is False

    def test_agent_communication(self):
        """Test agent communication mechanisms."""
        coordinator = AgentCoordinator()

        agent1 = Mock(name="producer")
        agent2 = Mock(name="consumer")

        # Test message passing
        message = {"type": "analysis_result", "data": {"language": "python"}}
        coordinator.send_message(agent1, agent2, message)

        # Verify message was received
        received_messages = coordinator.get_messages_for_agent(agent2)
        assert len(received_messages) == 1
        assert received_messages[0]["data"]["language"] == "python"


@pytest.mark.unit
@pytest.mark.phase2
class TestAgent:
    """Test the Agent base class and specific agent implementations."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = Agent(
            name="test-agent",
            capabilities=["analysis", "generation"],
            description="A test agent",
        )

        assert agent.name == "test-agent"
        assert "analysis" in agent.capabilities
        assert agent.description == "A test agent"

    def test_agent_capability_checking(self):
        """Test agent capability checking."""
        agent = Agent(
            name="specialized-agent", capabilities=["python", "web-api", "testing"]
        )

        assert agent.has_capability("python")
        assert agent.has_capability("web-api")
        assert not agent.has_capability("rust")

    def test_agent_compatibility_scoring(self, sample_analysis):
        """Test agent compatibility scoring with project analysis."""
        python_agent = Agent(
            name="python-expert",
            capabilities=["python", "web-development"],
            languages=["python"],
            frameworks=["fastapi", "django"],
        )

        # Test with Python FastAPI project
        sample_analysis.language_info.primary = "python"
        sample_analysis.framework_info.primary = "fastapi"

        compatibility = python_agent.calculate_compatibility(sample_analysis)

        assert compatibility > 0.8  # Should be highly compatible

    def test_agent_execution_context(self):
        """Test agent execution context management."""
        agent = Agent(name="context-agent")

        context = {
            "project_path": "/test/path",
            "analysis_result": {"language": "python"},
            "previous_agent_outputs": [],
        }

        agent.set_execution_context(context)

        assert agent.get_context("project_path") == "/test/path"
        assert agent.get_context("analysis_result")["language"] == "python"

    def test_agent_configuration_validation(self):
        """Test agent configuration validation."""
        # Valid configuration
        valid_config = {
            "timeout": 300,
            "max_retries": 3,
            "custom_params": {"style": "verbose"},
        }

        agent = Agent(name="configurable-agent", config=valid_config)
        assert agent.config["timeout"] == 300

        # Invalid configuration should raise error
        invalid_config = {
            "timeout": -1,  # Invalid negative timeout
            "max_retries": "invalid",  # Invalid type
        }

        with pytest.raises(ValueError):
            Agent(name="invalid-agent", config=invalid_config)

    def test_agent_state_management(self):
        """Test agent state management."""
        agent = Agent(name="stateful-agent")

        # Test state transitions
        assert agent.state == "initialized"

        agent.prepare()
        assert agent.state == "ready"

        agent.start_execution()
        assert agent.state == "running"

        agent.complete_execution()
        assert agent.state == "completed"

    def test_agent_error_handling(self):
        """Test agent error handling."""
        agent = Agent(name="error-prone-agent")

        # Simulate execution error
        with patch.object(agent, "execute") as mock_execute:
            mock_execute.side_effect = Exception("Execution failed")

            try:
                agent.run()
            except Exception:
                pass

            assert agent.state == "failed"
            assert agent.last_error is not None


@pytest.mark.unit
@pytest.mark.phase2
class TestAgentWorkflow:
    """Test the AgentWorkflow class."""

    def test_workflow_initialization(self, sample_analysis):
        """Test workflow initialization."""
        agents = [Mock(name="agent1"), Mock(name="agent2")]

        workflow = AgentWorkflow(agents, sample_analysis)

        assert len(workflow.agents) == 2
        assert workflow.project_analysis == sample_analysis
        assert workflow.status == "initialized"

    def test_workflow_execution(self, sample_analysis):
        """Test workflow execution."""
        # Create mock agents
        agent1 = Mock(name="agent1")
        agent1.execute.return_value = {"result": "success"}
        agent2 = Mock(name="agent2")
        agent2.execute.return_value = {"result": "success"}

        workflow = AgentWorkflow([agent1, agent2], sample_analysis)

        results = workflow.execute()

        assert workflow.status == "completed"
        assert len(results) == 2
        agent1.execute.assert_called_once()
        agent2.execute.assert_called_once()

    def test_workflow_failure_handling(self, sample_analysis):
        """Test workflow failure handling."""
        # Create agents where one fails
        agent1 = Mock(name="success-agent")
        agent1.execute.return_value = {"result": "success"}

        agent2 = Mock(name="failure-agent")
        agent2.execute.side_effect = Exception("Agent failed")

        workflow = AgentWorkflow([agent1, agent2], sample_analysis)

        with pytest.raises(Exception):
            workflow.execute()

        assert workflow.status == "failed"

    def test_workflow_progress_tracking(self, sample_analysis):
        """Test workflow progress tracking."""
        agents = [Mock(name=f"agent{i}") for i in range(5)]
        for agent in agents:
            agent.execute.return_value = {"result": "success"}

        workflow = AgentWorkflow(agents, sample_analysis)

        progress_updates = []

        def progress_callback(current, total):
            progress_updates.append((current, total))

        workflow.set_progress_callback(progress_callback)
        workflow.execute()

        # Should have received progress updates
        assert len(progress_updates) > 0
        assert progress_updates[-1] == (5, 5)  # Final update should be complete

    def test_workflow_cancellation(self, sample_analysis):
        """Test workflow cancellation."""
        # Create long-running mock agents
        agents = [Mock(name=f"agent{i}") for i in range(3)]

        workflow = AgentWorkflow(agents, sample_analysis)

        # Cancel workflow after starting
        workflow.start_async()
        workflow.cancel()

        assert workflow.status == "cancelled"

    def test_workflow_result_aggregation(self, sample_analysis):
        """Test workflow result aggregation."""
        # Create agents with different result types
        agent1 = Mock(name="analyzer")
        agent1.execute.return_value = {
            "type": "analysis",
            "data": {"language": "python"},
        }

        agent2 = Mock(name="generator")
        agent2.execute.return_value = {
            "type": "files",
            "data": {"CLAUDE.md": "content"},
        }

        workflow = AgentWorkflow([agent1, agent2], sample_analysis)
        results = workflow.execute()

        # Test result aggregation
        aggregated = workflow.aggregate_results(results)

        assert "analysis" in aggregated
        assert "files" in aggregated
        assert aggregated["analysis"]["language"] == "python"
        assert "CLAUDE.md" in aggregated["files"]


@pytest.mark.unit
@pytest.mark.phase2
class TestAgentIntegration:
    """Test agent system integration with other components."""

    def test_agent_with_template_system(self, sample_analysis, temp_dir):
        """Test agent integration with template system."""
        # Mock template-aware agent
        template_agent = Mock(name="template-agent")
        template_agent.requires_templates = True
        template_agent.template_dependencies = ["python-web", "fastapi"]

        manager = AgentManager()

        # Should verify template availability before agent execution
        with patch.object(manager, "_check_template_availability") as mock_check:
            mock_check.return_value = True

            result = manager.execute_agent_with_templates(
                template_agent, sample_analysis
            )

            mock_check.assert_called_once_with(template_agent.template_dependencies)

    def test_agent_with_git_integration(self, sample_analysis, git_repo):
        """Test agent integration with git system."""
        git_aware_agent = Mock(name="git-agent")
        git_aware_agent.modifies_git = True

        manager = AgentManager()

        # Should handle git operations properly
        with patch("claude_builder.utils.git.GitIntegrationManager") as mock_git:
            mock_git_instance = mock_git.return_value
            mock_git_instance.integrate.return_value.success = True

            manager.execute_agent_with_git(git_aware_agent, sample_analysis, git_repo)

            mock_git_instance.integrate.assert_called_once()

    def test_agent_configuration_from_project_config(self, sample_analysis, temp_dir):
        """Test agent configuration from project configuration."""
        # Create project config with agent settings
        config_data = {
            "agents": {
                "priority_agents": ["rapid-prototyper"],
                "exclude_agents": ["whimsy-injector"],
                "agent_preferences": {
                    "python-pro": {"style": "verbose", "include_examples": True}
                },
            }
        }

        import json

        config_file = temp_dir / "claude-builder.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        manager = AgentManager()

        # Load configuration and create agents
        with patch.object(manager, "load_project_config") as mock_load:
            mock_load.return_value = config_data

            agents = manager.select_agents_for_project(sample_analysis)

            # Should respect configuration preferences
            agent_names = [agent.name for agent in agents]
            assert "rapid-prototyper" in agent_names
            assert "whimsy-injector" not in agent_names

    def test_multi_agent_collaboration(self, sample_analysis):
        """Test multi-agent collaboration scenarios."""
        # Create agents that need to collaborate
        analyzer_agent = Mock(name="analyzer")
        analyzer_agent.execute.return_value = {
            "type": "analysis",
            "data": {"complexity": "high", "patterns": ["mvc", "api"]},
        }

        generator_agent = Mock(name="generator")
        generator_agent.execute.return_value = {
            "type": "files",
            "data": {"CLAUDE.md": "generated content"},
        }

        coordinator = AgentCoordinator()
        workflow = coordinator.create_workflow(
            [analyzer_agent, generator_agent], sample_analysis
        )

        results = workflow.execute()

        # Generator should have access to analyzer results
        assert len(results) == 2
        assert any(r["type"] == "analysis" for r in results)
        assert any(r["type"] == "files" for r in results)

    def test_agent_performance_monitoring(self, sample_analysis):
        """Test agent performance monitoring."""
        manager = AgentManager()

        # Create agents with different performance characteristics
        fast_agent = Mock(name="fast-agent")
        slow_agent = Mock(name="slow-agent")

        # Mock execution times
        import time

        def fast_execute(*args, **kwargs):
            time.sleep(0.1)
            return {"result": "fast"}

        def slow_execute(*args, **kwargs):
            time.sleep(0.5)
            return {"result": "slow"}

        fast_agent.execute = fast_execute
        slow_agent.execute = slow_execute

        # Execute and monitor performance
        workflow = AgentWorkflow([fast_agent, slow_agent], sample_analysis)

        start_time = time.time()
        results = workflow.execute()
        total_time = time.time() - start_time

        # Should track execution times
        assert hasattr(workflow, "execution_times")
        assert len(workflow.execution_times) == 2
        assert total_time >= 0.6  # At least sum of individual times
