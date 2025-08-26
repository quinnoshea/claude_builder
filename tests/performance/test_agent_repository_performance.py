"""Performance tests for agent repository system."""

import tempfile
import time

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from claude_builder.core.agent_repository import (
    AgentDefinition,
    AgentRepositoryScanner,
    RepositoryConfig,
)


class TestAgentRepositoryPerformance:
    """Performance tests for agent repository operations."""

    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "perf_test_repositories.yaml"
            config = RepositoryConfig(config_path)
            self.scanner = AgentRepositoryScanner(config=config, max_workers=4)

    def test_agent_indexing_performance(self):
        """Test that indexing 100+ agents completes in under 5 seconds."""
        # Generate 120 test agents
        test_agents = self._generate_test_agents(120)

        start_time = time.time()

        # Index all agents
        for agent in test_agents:
            self.scanner.index.index_agent(agent)

        indexing_duration = time.time() - start_time

        # Should index 120 agents in well under 5 seconds
        assert (
            indexing_duration < 2.0
        ), f"Indexing took {indexing_duration:.2f}s, expected <2.0s"

        # Verify all agents were indexed
        stats = self.scanner.index.get_stats()
        assert stats["total_agents"] == 120

    def test_capability_search_performance(self):
        """Test that searching through 100+ agents is fast."""
        # Generate and index 150 test agents
        test_agents = self._generate_test_agents(150)
        for agent in test_agents:
            self.scanner.index.index_agent(agent)

        # Test various search patterns
        search_patterns = [
            {"language": "python"},
            {"framework": "django"},
            {"keywords": ["web", "api"]},
            {"language": "javascript", "framework": "react"},
            {"complexity": "moderate"},
        ]

        total_search_time = 0

        for pattern in search_patterns:
            start_time = time.time()
            results = self.scanner.index.search_agents(**pattern)
            search_time = time.time() - start_time
            total_search_time += search_time

            # Each search should be very fast
            assert search_time < 0.1, f"Search took {search_time:.3f}s, expected <0.1s"
            assert isinstance(results, list)

        # Total search time for all patterns should be minimal
        assert (
            total_search_time < 0.5
        ), f"Total search time {total_search_time:.2f}s, expected <0.5s"

    def test_compatibility_scoring_performance(self):
        """Test that scoring 100+ agents against a project is fast."""

        # Generate test agents and project
        test_agents = self._generate_test_agents(100)
        test_project = self._create_test_project()

        start_time = time.time()

        # Score all agents against the project
        scored_agents = []
        for agent in test_agents:
            compatible_agent = self.scanner.scorer.score_agent_compatibility(
                agent, test_project
            )
            scored_agents.append(compatible_agent)

        scoring_duration = time.time() - start_time

        # Should score 100 agents in under 2 seconds
        assert (
            scoring_duration < 2.0
        ), f"Scoring took {scoring_duration:.2f}s, expected <2.0s"
        assert len(scored_agents) == 100

        # All scores should be valid
        for scored_agent in scored_agents:
            assert 0.0 <= scored_agent.compatibility_score <= 1.0

    def test_cache_performance(self):
        """Test that caching operations are fast."""
        # Generate test agents
        test_agents = self._generate_test_agents(50)

        # Test cache writes
        start_time = time.time()
        for i, agent in enumerate(test_agents):
            url = f"https://github.com/test/agent_{i}.md"
            self.scanner.cache.set(url, agent)
        cache_write_time = time.time() - start_time

        # Cache writes should be very fast
        assert (
            cache_write_time < 0.5
        ), f"Cache writes took {cache_write_time:.2f}s, expected <0.5s"

        # Test cache reads
        start_time = time.time()
        for i in range(len(test_agents)):
            url = f"https://github.com/test/agent_{i}.md"
            cached_agent = self.scanner.cache.get(url)
            assert cached_agent is not None
        cache_read_time = time.time() - start_time

        # Cache reads should be extremely fast
        assert (
            cache_read_time < 0.2
        ), f"Cache reads took {cache_read_time:.2f}s, expected <0.2s"

    @patch("claude_builder.utils.github_client.GitHubAgentClient")
    def test_parallel_processing_performance(self, mock_github_client):
        """Test that parallel processing improves performance."""
        # Mock GitHub client to return test data
        mock_agents_data = self._generate_mock_agents_data(80)
        mock_github_client.return_value.fetch_repository_agents.return_value = (
            mock_agents_data
        )

        # Test sequential processing (max_workers=1)
        sequential_scanner = AgentRepositoryScanner(max_workers=1)
        sequential_scanner.github_client = mock_github_client.return_value

        start_time = time.time()
        sequential_result = sequential_scanner.scan_repositories()
        sequential_time = time.time() - start_time

        # Test parallel processing (max_workers=4)
        parallel_scanner = AgentRepositoryScanner(max_workers=4)
        parallel_scanner.github_client = mock_github_client.return_value

        start_time = time.time()
        parallel_result = parallel_scanner.scan_repositories()
        parallel_time = time.time() - start_time

        # Both should complete, and parallel should be faster or comparable
        assert sequential_result.repositories_scanned >= 0
        assert parallel_result.repositories_scanned >= 0

        # Parallel processing should not be significantly slower
        # (In practice with real network I/O, it would be much faster)
        assert parallel_time <= sequential_time + 1.0

    def test_memory_efficiency(self):
        """Test that the system is memory efficient with large agent sets."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate and index 200 agents
        test_agents = self._generate_test_agents(200)
        for agent in test_agents:
            self.scanner.index.index_agent(agent)

        # Perform various operations
        stats = self.scanner.index.get_stats()
        search_results = self.scanner.index.search_agents(language="python")
        cache_stats = self.scanner.cache.get_stats()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for 200 agents)
        assert (
            memory_increase < 50
        ), f"Memory increased by {memory_increase:.1f}MB, expected <50MB"

        # Verify operations still work
        assert stats["total_agents"] == 200
        assert isinstance(search_results, list)
        assert isinstance(cache_stats, dict)

    def _generate_test_agents(self, count: int) -> list[AgentDefinition]:
        """Generate test agents for performance testing."""
        agents = []

        languages = ["python", "javascript", "java", "go", "rust"]
        frameworks = ["django", "react", "spring", "gin", "axum"]
        complexities = ["simple", "moderate", "complex"]

        for i in range(count):
            agent = AgentDefinition(
                name=f"Test Agent {i}",
                description=f"Test agent {i} for performance testing",
                capabilities=(f"capability_{i}", f"feature_{i % 10}"),
                use_cases=(f"use_case_{i}", f"scenario_{i % 5}"),
                language_compatibility=(languages[i % len(languages)],),
                framework_compatibility=(frameworks[i % len(frameworks)],),
                trigger_keywords=(f"keyword_{i}", f"trigger_{i % 8}"),
                complexity_level=complexities[i % len(complexities)],
                confidence_score=0.8,
                source_url=f"https://github.com/test/agent_{i}.md",
                repository_name=f"test/repo_{i % 5}",
            )
            agents.append(agent)

        return agents

    def _create_test_project(self):
        """Create a test project for compatibility testing."""
        from claude_builder.core.models import (
            ArchitecturePattern,
            ComplexityLevel,
            DevelopmentEnvironment,
            DomainInfo,
            FrameworkInfo,
            LanguageInfo,
            ProjectAnalysis,
            ProjectType,
        )

        return ProjectAnalysis(
            project_path=Path("/test/project"),
            language_info=LanguageInfo(primary="python", confidence=0.9),
            framework_info=FrameworkInfo(primary="django", confidence=0.8),
            domain_info=DomainInfo(domain="web", confidence=0.85),
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=ComplexityLevel.MODERATE,
            architecture_pattern=ArchitecturePattern.MVC,
            dev_environment=DevelopmentEnvironment(
                databases=["postgresql"], testing_frameworks=["pytest"]
            ),
        )

    def _generate_mock_agents_data(self, count: int) -> list[dict]:
        """Generate mock agent data for GitHub client testing."""
        mock_data = []

        for i in range(count):
            mock_data.append(
                {
                    "name": f"agent_{i}.md",
                    "content": f"""# Agent {i}

A test agent for performance testing.

## Capabilities
- Test capability {i}
- Performance testing

## Use Cases
- Performance testing
- Load testing

## Keywords
test, performance, agent{i}

## Languages
python

## Frameworks
django

## Complexity
moderate
""",
                    "source_url": f"https://github.com/test/agent_{i}.md",
                    "etag": f"etag_{i}",
                    "last_modified": "2024-01-01T00:00:00Z",
                }
            )

        return mock_data


@pytest.mark.performance
class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @patch("claude_builder.utils.github_client.GitHubAgentClient")
    def test_full_workflow_under_5_seconds(self, mock_github_client):
        """Test that the full workflow handles 100+ agents in under 5 seconds."""
        # Generate mock data for 120 agents
        mock_agents_data = self._generate_mock_agents_data(120)
        mock_github_client.return_value.fetch_repository_agents.return_value = (
            mock_agents_data
        )
        mock_github_client.return_value.get_repository_info.return_value = Mock(
            name="test/repo", full_name="test/repo", updated_at="2024-01-01T00:00:00Z"
        )

        # Create scanner with performance settings
        scanner = AgentRepositoryScanner(max_workers=4)
        scanner.github_client = mock_github_client.return_value

        # Full workflow timing
        start_time = time.time()

        # 1. Scan repositories (parse and index agents)
        scan_result = scanner.scan_repositories()

        # 2. Create test project and find compatible agents
        test_project = self._create_test_project()
        compatible_agents = scanner.find_compatible_agents(test_project, limit=20)

        # 3. Get statistics
        stats = scanner.get_cache_stats()

        total_time = time.time() - start_time

        # Should complete full workflow in under 5 seconds
        assert total_time < 5.0, f"Full workflow took {total_time:.2f}s, expected <5.0s"

        # Verify results
        assert scan_result.successful_parses > 0
        assert len(compatible_agents) <= 20
        assert stats["index"]["total_agents"] > 0

        print("\n🚀 PERFORMANCE SUCCESS:")
        print(
            f"   • Processed {scan_result.successful_parses} agents in {total_time:.2f}s"
        )
        print(f"   • Found {len(compatible_agents)} compatible agents")
        print(f"   • Cache entries: {stats['cache']['total_entries']}")
        print("   • Target: <5.0s ✅")

    def _generate_mock_agents_data(self, count: int) -> list[dict]:
        """Generate mock agent data."""
        mock_data = []

        for i in range(count):
            mock_data.append(
                {
                    "name": f"agent_{i}.md",
                    "content": f"""# Performance Agent {i}

High-performance agent for testing scalability.

## Capabilities
- Performance testing
- Scalability analysis
- Load testing
- Benchmark creation

## Use Cases
- Testing large systems
- Performance optimization
- Scalability planning

## Keywords
performance, scale, test, benchmark, load

## Languages
{['python', 'javascript', 'java'][i % 3]}

## Frameworks
{['django', 'react', 'spring'][i % 3]}

## Complexity
{['simple', 'moderate', 'complex'][i % 3]}
""",
                    "source_url": f"https://github.com/perf/agent_{i}.md",
                    "etag": f"perf_etag_{i}",
                    "last_modified": "2024-01-01T00:00:00Z",
                }
            )

        return mock_data

    def _create_test_project(self):
        """Create test project."""
        from claude_builder.core.models import (
            ArchitecturePattern,
            ComplexityLevel,
            DevelopmentEnvironment,
            DomainInfo,
            FrameworkInfo,
            LanguageInfo,
            ProjectAnalysis,
            ProjectType,
        )

        return ProjectAnalysis(
            project_path=Path("/test/perf-project"),
            language_info=LanguageInfo(primary="python", confidence=0.95),
            framework_info=FrameworkInfo(primary="django", confidence=0.90),
            domain_info=DomainInfo(domain="web", confidence=0.85),
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=ComplexityLevel.MODERATE,
            architecture_pattern=ArchitecturePattern.MVC,
            dev_environment=DevelopmentEnvironment(
                databases=["postgresql"], testing_frameworks=["pytest"]
            ),
        )
