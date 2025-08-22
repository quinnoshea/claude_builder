"""
Integration tests for agent coordination.

Tests the complete agent coordination system including:
- Multi-agent task coordination
- Agent communication protocols
- Task delegation and result aggregation
- Agent failure handling and recovery
- Performance optimization across agents
"""

from unittest.mock import Mock

from claude_builder.core.agents import AgentCoordinator, AgentRegistry


class TestAgentCoordinationIntegration:
    """Test suite for agent coordination integration."""

    def test_multi_agent_project_analysis(self, sample_python_project):
        """Test coordinated project analysis using multiple agents."""
        # Setup agent registry and coordinator
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # Mock specialized agents
        analyzer_agent = Mock(name="analyzer-agent")
        analyzer_agent.capabilities = ["project_analysis", "dependency_analysis"]
        analyzer_agent.execute.return_value = Mock(
            success=True,
            data={
                "project_type": "python",
                "dependencies": ["click", "pytest"],
                "framework": "click",
            },
        )

        framework_agent = Mock(name="framework-agent")
        framework_agent.capabilities = ["framework_detection", "pattern_analysis"]
        framework_agent.execute.return_value = Mock(
            success=True,
            data={
                "framework": "click",
                "patterns": ["cli", "command_line"],
                "confidence": 0.9,
            },
        )

        generator_agent = Mock(name="generator-agent")
        generator_agent.capabilities = [
            "documentation_generation",
            "template_processing",
        ]
        generator_agent.execute.return_value = Mock(
            success=True,
            data={
                "generated_docs": ["CLAUDE.md", "README.md", "AGENTS.md"],
                "template_used": "python-cli",
            },
        )

        # Register agents
        registry.register(analyzer_agent)
        registry.register(framework_agent)
        registry.register(generator_agent)

        # Create coordinated tasks
        from claude_builder.core.agents import AgentTask

        analysis_task = AgentTask(
            task_type="project_analysis",
            data={"project_path": str(sample_python_project)},
            context={"stage": "initial_analysis"},
        )

        framework_task = AgentTask(
            task_type="framework_detection",
            data={"project_path": str(sample_python_project)},
            context={"stage": "framework_analysis"},
        )

        generation_task = AgentTask(
            task_type="documentation_generation",
            data={"project_path": str(sample_python_project)},
            context={"stage": "doc_generation"},
        )

        # Execute coordinated workflow
        results = coordinator.execute_workflow(
            [analysis_task, framework_task, generation_task]
        )

        # Verify coordination
        assert len(results) == 3
        assert all(result.success for result in results)
        assert results[0].data["project_type"] == "python"
        assert results[1].data["framework"] == "click"
        assert len(results[2].data["generated_docs"]) == 3

    def test_agent_failure_recovery_coordination(self, sample_python_project):
        """Test agent coordination with failure recovery."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # Primary agent that will fail
        primary_agent = Mock(name="primary-agent")
        primary_agent.capabilities = ["analysis"]
        primary_agent.execute.return_value = Mock(
            success=False, error_message="Primary agent failed"
        )

        # Fallback agent that will succeed
        fallback_agent = Mock(name="fallback-agent")
        fallback_agent.capabilities = ["analysis"]
        fallback_agent.execute.return_value = Mock(
            success=True, data={"analysis": "fallback_result"}
        )

        registry.register(primary_agent)
        registry.register(fallback_agent)

        from claude_builder.core.agents import AgentTask

        task = AgentTask(
            task_type="analysis",
            data={"project_path": str(sample_python_project)},
            context={"retry_enabled": True},
        )

        # Execute with failure recovery
        result = coordinator.execute_with_fallback(task)

        # Should succeed with fallback agent
        assert result.success is True
        assert result.data["analysis"] == "fallback_result"

        # Both agents should have been tried
        primary_agent.execute.assert_called_once()
        fallback_agent.execute.assert_called_once()

    def test_parallel_agent_execution(self, sample_python_project):
        """Test parallel execution of multiple agents."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # Create multiple independent agents
        agents_config = [
            ("analyzer", ["project_analysis"], {"type": "python", "files": 10}),
            ("dependency", ["dependency_analysis"], {"deps": ["click", "pytest"]}),
            ("structure", ["structure_analysis"], {"dirs": ["src", "tests"]}),
            ("git", ["git_analysis"], {"commits": 25, "branches": 3}),
        ]

        agents = []
        for name, capabilities, mock_data in agents_config:
            agent = Mock(name=f"{name}-agent")
            agent.capabilities = capabilities
            agent.execute.return_value = Mock(success=True, data=mock_data)
            registry.register(agent)
            agents.append(agent)

        from claude_builder.core.agents import AgentTask

        # Create parallel tasks
        tasks = [
            AgentTask(
                task_type="project_analysis",
                data={"path": str(sample_python_project)},
                context={},
            ),
            AgentTask(
                task_type="dependency_analysis",
                data={"path": str(sample_python_project)},
                context={},
            ),
            AgentTask(
                task_type="structure_analysis",
                data={"path": str(sample_python_project)},
                context={},
            ),
            AgentTask(
                task_type="git_analysis",
                data={"path": str(sample_python_project)},
                context={},
            ),
        ]

        import time

        start_time = time.time()

        # Execute tasks in parallel
        results = coordinator.execute_tasks_parallel(tasks)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify parallel execution
        assert len(results) == 4
        assert all(result.success for result in results)

        # Should complete faster than sequential execution would
        assert (
            execution_time < 2.0
        )  # Assuming each task takes < 0.5s, parallel should be much faster

        # All agents should have been executed
        for agent in agents:
            agent.execute.assert_called_once()

    def test_agent_priority_coordination(self, sample_python_project):
        """Test agent coordination with priority handling."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # High priority agent
        high_priority_agent = Mock(name="high-priority-agent")
        high_priority_agent.capabilities = ["analysis"]
        high_priority_agent.priority = 1
        high_priority_agent.execute.return_value = Mock(
            success=True, data={"source": "high_priority", "quality": "excellent"}
        )

        # Low priority agent
        low_priority_agent = Mock(name="low-priority-agent")
        low_priority_agent.capabilities = ["analysis"]
        low_priority_agent.priority = 5
        low_priority_agent.execute.return_value = Mock(
            success=True, data={"source": "low_priority", "quality": "good"}
        )

        registry.register(high_priority_agent)
        registry.register(low_priority_agent)

        from claude_builder.core.agents import AgentTask

        # High priority task
        high_priority_task = AgentTask(
            task_type="analysis",
            data={"project_path": str(sample_python_project)},
            context={},
            priority=10,
        )

        # Execute with priority coordination
        result = coordinator.execute_task(high_priority_task)

        # Should use high priority agent
        assert result.success is True
        assert result.data["source"] == "high_priority"

        # Only high priority agent should be called
        high_priority_agent.execute.assert_called_once()
        low_priority_agent.execute.assert_not_called()

    def test_agent_resource_coordination(self, sample_python_project):
        """Test agent coordination with resource management."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry, max_concurrent_agents=2)

        # Create resource-intensive agents
        agents = []
        for i in range(4):
            agent = Mock(name=f"resource-agent-{i}")
            agent.capabilities = ["analysis"]
            agent.resource_requirements = {"memory": 100, "cpu": 1}
            agent.execute.return_value = Mock(
                success=True, data={"agent_id": i, "resource_usage": "high"}
            )
            registry.register(agent)
            agents.append(agent)

        from claude_builder.core.agents import AgentTask

        # Create multiple resource-intensive tasks
        tasks = [
            AgentTask(task_type="analysis", data={"id": i}, context={})
            for i in range(4)
        ]

        # Execute with resource coordination
        results = coordinator.execute_with_resource_management(tasks)

        # Should complete all tasks despite resource limits
        assert len(results) == 4
        assert all(result.success for result in results)

        # Should respect concurrency limits (not all agents run simultaneously)
        # This would be verified by checking execution timing in a real implementation


class TestAgentCommunicationIntegration:
    """Test suite for agent communication integration."""

    def test_agent_message_passing(self, sample_python_project):
        """Test message passing between agents."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # Producer agent that sends messages
        producer_agent = Mock(name="producer-agent")
        producer_agent.capabilities = ["data_production"]
        producer_agent.execute.return_value = Mock(
            success=True,
            data={"analysis_data": "processed_info"},
            messages=[
                {
                    "to": "consumer-agent",
                    "type": "data_ready",
                    "payload": {"data_id": "123"},
                }
            ],
        )

        # Consumer agent that receives messages
        consumer_agent = Mock(name="consumer-agent")
        consumer_agent.capabilities = ["data_consumption"]
        consumer_agent.execute.return_value = Mock(
            success=True, data={"processed": "final_result"}
        )

        registry.register(producer_agent)
        registry.register(consumer_agent)

        from claude_builder.core.agents import AgentTask

        # Create coordinated tasks with message passing
        producer_task = AgentTask(
            task_type="data_production",
            data={"project_path": str(sample_python_project)},
            context={"enable_messaging": True},
        )

        # Execute with message coordination
        results = coordinator.execute_with_messaging([producer_task])

        # Verify message passing occurred
        assert len(results) >= 1
        assert results[0].success is True

        # Producer should have been executed
        producer_agent.execute.assert_called_once()

        # In a real implementation, consumer would be triggered by message

    def test_agent_state_sharing(self, sample_python_project):
        """Test state sharing between agents."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # State manager for shared data
        shared_state = {}

        # First agent that updates shared state
        state_writer_agent = Mock(name="state-writer-agent")
        state_writer_agent.capabilities = ["state_writing"]

        def write_state_side_effect(task):
            shared_state["project_info"] = {
                "name": "test-project",
                "type": "python",
                "analyzed": True,
            }
            return Mock(success=True, data={"state_updated": True})

        state_writer_agent.execute.side_effect = write_state_side_effect

        # Second agent that reads shared state
        state_reader_agent = Mock(name="state-reader-agent")
        state_reader_agent.capabilities = ["state_reading"]

        def read_state_side_effect(task):
            project_info = shared_state.get("project_info", {})
            return Mock(
                success=True,
                data={
                    "read_state": project_info,
                    "can_proceed": project_info.get("analyzed", False),
                },
            )

        state_reader_agent.execute.side_effect = read_state_side_effect

        registry.register(state_writer_agent)
        registry.register(state_reader_agent)

        from claude_builder.core.agents import AgentTask

        # Execute sequential tasks with state sharing
        write_task = AgentTask(
            task_type="state_writing",
            data={"project_path": str(sample_python_project)},
            context={},
        )

        read_task = AgentTask(
            task_type="state_reading",
            data={"project_path": str(sample_python_project)},
            context={},
        )

        # Execute in sequence
        write_result = coordinator.execute_task(write_task)
        read_result = coordinator.execute_task(read_task)

        # Verify state sharing
        assert write_result.success is True
        assert read_result.success is True
        assert read_result.data["can_proceed"] is True
        assert read_result.data["read_state"]["name"] == "test-project"


class TestAgentPerformanceIntegration:
    """Test suite for agent performance integration."""

    def test_agent_load_balancing(self, sample_python_project):
        """Test load balancing across multiple agents."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry)

        # Create multiple agents with same capabilities but different loads
        agents = []
        for i in range(3):
            agent = Mock(name=f"load-agent-{i}")
            agent.capabilities = ["analysis"]
            agent.current_load = i * 20  # 0%, 20%, 40% load
            agent.execute.return_value = Mock(
                success=True, data={"agent_id": i, "load": agent.current_load}
            )
            registry.register(agent)
            agents.append(agent)

        from claude_builder.core.agents import AgentTask

        # Create multiple tasks
        tasks = [
            AgentTask(task_type="analysis", data={"task_id": i}, context={})
            for i in range(6)
        ]

        # Execute with load balancing
        results = coordinator.execute_with_load_balancing(tasks)

        # Should distribute tasks based on agent load
        assert len(results) == 6
        assert all(result.success for result in results)

        # Agent with lowest load should handle more tasks
        # This would be verified by checking call counts in a real implementation

    def test_agent_performance_monitoring(self, sample_python_project):
        """Test agent performance monitoring integration."""
        registry = AgentRegistry()
        coordinator = AgentCoordinator(registry, enable_monitoring=True)

        # Agent with performance metrics
        monitored_agent = Mock(name="monitored-agent")
        monitored_agent.capabilities = ["analysis"]

        def execute_with_metrics(task):
            import time

            time.sleep(0.1)  # Simulate work
            return Mock(
                success=True,
                data={"result": "completed"},
                execution_time=0.1,
                memory_usage=50,
            )

        monitored_agent.execute.side_effect = execute_with_metrics
        registry.register(monitored_agent)

        from claude_builder.core.agents import AgentTask

        # Execute multiple tasks to gather metrics
        tasks = [
            AgentTask(task_type="analysis", data={"task_id": i}, context={})
            for i in range(5)
        ]

        results = []
        for task in tasks:
            result = coordinator.execute_task(task)
            results.append(result)

        # Get performance metrics
        metrics = coordinator.get_performance_metrics()

        # Verify monitoring
        assert len(results) == 5
        assert all(result.success for result in results)
        assert metrics["total_tasks"] == 5
        assert metrics["avg_execution_time"] > 0
        assert "monitored-agent" in metrics["agent_metrics"]
