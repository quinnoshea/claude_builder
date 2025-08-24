"""Tests for agent repository management system."""

import tempfile
from pathlib import Path

import pytest

from claude_builder.core.agent_repository import (
    AgentCompatibilityScorer,
    AgentDefinition,
    AgentDefinitionParser,
    AgentRepositoryScanner,
    CapabilityIndex,
    CompatibleAgent,
    RepositoryConfig,
    ScanResult,
    SyncResult,
)
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


class TestRepositoryConfig:
    """Test the repository configuration system."""

    def test_repository_config_initialization(self):
        """Test repository configuration initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            assert config.config_path == config_path
            assert len(config.repositories) >= 2  # Should have default repositories
            assert all("name" in repo for repo in config.repositories)
            assert all("url" in repo for repo in config.repositories)

    def test_default_config_creation(self):
        """Test creation of default configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Config file should be created
            assert config_path.exists()

            # Should contain default repositories
            assert len(config.repositories) >= 2
            claude_repo = next(
                (r for r in config.repositories if "claude-code" in r["name"]), None
            )
            assert claude_repo is not None
            assert claude_repo["priority"] == 1
            assert claude_repo["enabled"] is True

    def test_add_repository(self):
        """Test adding a new repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            initial_count = len(config.repositories)

            config.add_repository(
                url="https://github.com/test/test-agents",
                name="test-repo",
                priority=3,
                description="Test repository",
            )

            assert len(config.repositories) == initial_count + 1

            # Find the added repository
            test_repo = next(
                (r for r in config.repositories if r["name"] == "test-repo"), None
            )
            assert test_repo is not None
            assert test_repo["url"] == "https://github.com/test/test-agents"
            assert test_repo["priority"] == 3
            assert test_repo["description"] == "Test repository"

    def test_add_duplicate_repository(self):
        """Test adding a duplicate repository raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Add a repository
            config.add_repository(
                url="https://github.com/test/unique", name="unique-repo"
            )

            # Try to add same name - should raise error
            with pytest.raises(ValueError, match="Repository already exists"):
                config.add_repository(
                    url="https://github.com/test/different", name="unique-repo"
                )

            # Try to add same URL - should raise error
            with pytest.raises(ValueError, match="Repository already exists"):
                config.add_repository(
                    url="https://github.com/test/unique", name="different-name"
                )

    def test_invalid_url_validation(self):
        """Test invalid URL validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Test invalid URLs
            invalid_urls = [
                "not-a-url",
                "ftp://invalid-scheme.com",
                "http://",
                "",
                "just-text",
            ]

            for invalid_url in invalid_urls:
                with pytest.raises(ValueError, match="Repository URL is invalid"):
                    config.add_repository(
                        url=invalid_url, name=f"test-{invalid_url[:5]}"
                    )

    def test_remove_repository(self):
        """Test removing a repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Add a test repository
            config.add_repository(
                url="https://github.com/test/remove-me", name="remove-me"
            )

            initial_count = len(config.repositories)

            # Remove the repository
            result = config.remove_repository("remove-me")

            assert result is True
            assert len(config.repositories) == initial_count - 1

            # Verify it's gone
            test_repo = next(
                (r for r in config.repositories if r["name"] == "remove-me"), None
            )
            assert test_repo is None

    def test_remove_nonexistent_repository(self):
        """Test removing a nonexistent repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            result = config.remove_repository("nonexistent")
            assert result is False

    def test_update_repository(self):
        """Test updating repository configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Add a test repository
            config.add_repository(
                url="https://github.com/test/original", name="update-me", priority=5
            )

            # Update the repository
            result = config.update_repository(
                "update-me",
                url="https://github.com/test/updated",
                priority=1,
                description="Updated description",
            )

            assert result is True

            # Verify updates
            updated_repo = next(
                (r for r in config.repositories if r["name"] == "update-me"), None
            )
            assert updated_repo is not None
            assert updated_repo["url"] == "https://github.com/test/updated"
            assert updated_repo["priority"] == 1
            assert updated_repo["description"] == "Updated description"

    def test_get_enabled_repositories(self):
        """Test getting enabled repositories sorted by priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent_repositories.yaml"
            config = RepositoryConfig(config_path)

            # Add repositories with different priorities and enabled states
            config.add_repository(
                "https://github.com/test/high", "high-priority", priority=1
            )
            config.add_repository(
                "https://github.com/test/low", "low-priority", priority=5
            )
            config.add_repository(
                "https://github.com/test/disabled", "disabled", enabled=False
            )

            enabled_repos = config.get_enabled_repositories()

            # Should exclude disabled repository
            repo_names = [repo["name"] for repo in enabled_repos]
            assert "disabled" not in repo_names

            # Should be sorted by priority (lower numbers first)
            priorities = [repo["priority"] for repo in enabled_repos]
            assert priorities == sorted(priorities)


class TestAgentDefinition:
    """Test the agent definition model."""

    def test_agent_definition_creation(self):
        """Test creating a valid agent definition."""
        agent = AgentDefinition(
            name="test-agent",
            description="A test agent for testing",
            capabilities=["testing", "validation"],
            use_cases=["unit testing", "integration testing"],
        )

        assert agent.name == "test-agent"
        assert agent.description == "A test agent for testing"
        assert len(agent.capabilities) == 2
        assert len(agent.use_cases) == 2
        assert agent.complexity_level == "moderate"  # default
        assert agent.confidence_score == 0.0  # default

    def test_agent_definition_validation(self):
        """Test agent definition validation."""
        # Empty name should raise error
        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            AgentDefinition(name="", description="test", capabilities=("test",))

        # Empty description should raise error
        with pytest.raises(ValueError, match="Agent description cannot be empty"):
            AgentDefinition(name="test", description="", capabilities=("test",))

        # Empty capabilities should get default value
        agent = AgentDefinition(name="test", description="test", capabilities=())
        assert len(agent.capabilities) == 1
        assert agent.capabilities[0] == "General development assistance"


class TestAgentDefinitionParser:
    """Test the agent definition parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AgentDefinitionParser()

        self.sample_markdown = """
# Test Agent - Development Assistant

A comprehensive agent for testing and development tasks.

## Capabilities
- Write unit tests
- Perform integration testing
- Code quality analysis
- Bug detection and fixing

## Use Cases
- Testing new features
- Validating existing code
- Code review assistance

## Keywords
testing, qa, quality, validation, bugs

## Languages
Python, JavaScript, TypeScript

## Frameworks
pytest, jest, cypress

## Complexity
moderate
"""

    def test_parse_agent_file_success(self):
        """Test successful parsing of agent definition."""
        result = self.parser.parse_agent_file(
            self.sample_markdown, "https://github.com/test/agents/test-agent.md"
        )

        assert result is not None
        assert result.name == "Test Agent"
        assert "comprehensive agent" in result.description.lower()
        assert len(result.capabilities) == 4
        assert "Write unit tests" in result.capabilities
        assert len(result.use_cases) == 3
        assert "testing" in [kw.lower() for kw in result.trigger_keywords]
        assert "python" in [lang.lower() for lang in result.language_compatibility]
        assert "pytest" in [fw.lower() for fw in result.framework_compatibility]
        assert result.complexity_level == "moderate"
        assert result.confidence_score > 0.8  # Should be high due to complete info

    def test_parse_minimal_agent_file(self):
        """Test parsing minimal agent definition."""
        minimal_markdown = """
# Minimal Agent

Basic agent for simple tasks.
"""

        result = self.parser.parse_agent_file(
            minimal_markdown, "https://github.com/test/minimal.md"
        )

        assert result is not None
        assert result.name == "Minimal Agent"
        assert result.description == "Basic agent for simple tasks."
        assert len(result.capabilities) == 1  # Should get default capability
        assert result.confidence_score <= 0.5  # Lower due to missing info

    def test_parse_invalid_agent_file(self):
        """Test parsing invalid agent definition."""
        # No title/name
        invalid_markdown = """
This is just text without a proper title.

Some description here.
"""

        result = self.parser.parse_agent_file(
            invalid_markdown, "https://github.com/test/invalid.md"
        )
        assert result is None

    def test_extract_list_items(self):
        """Test extraction of list items from markdown."""
        # We need to adjust this test since the pattern looks for specific headers
        content_with_capabilities = """
## Capabilities
- First capability
- Second capability
* Third capability
- Fourth capability
"""
        pattern = self.parser.CAPABILITIES_PATTERN

        items = self.parser._extract_list_items(content_with_capabilities, pattern)
        assert len(items) == 4
        assert "First capability" in items
        assert "Third capability" in items

    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        # High confidence - all fields present
        high_score = self.parser._calculate_confidence_score(  # noqa: SLF001
            has_description=True,
            capabilities_count=5,
            use_cases_count=3,
            keywords_count=4,
            languages_count=2,
        )
        assert high_score >= 0.9

        # Low confidence - minimal fields
        low_score = self.parser._calculate_confidence_score(  # noqa: SLF001
            has_description=False,
            capabilities_count=0,
            use_cases_count=0,
            keywords_count=0,
            languages_count=0,
        )
        assert low_score == 0.0


class TestCapabilityIndex:
    """Test the capability indexing system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.index = CapabilityIndex()

        # Create test agents
        self.python_web_agent = AgentDefinition(
            name="Python Web Agent",
            description="Web development with Python",
            capabilities=("web development", "API creation"),
            use_cases=("building web apps",),
            language_compatibility=("python",),
            framework_compatibility=("django", "fastapi"),
            trigger_keywords=("web", "api", "backend"),
            complexity_level="moderate",
        )

        self.js_frontend_agent = AgentDefinition(
            name="JavaScript Frontend Agent",
            description="Frontend development with JavaScript",
            capabilities=("frontend development", "UI components"),
            use_cases=("user interfaces",),
            language_compatibility=("javascript", "typescript"),
            framework_compatibility=("react", "vue"),
            trigger_keywords=("frontend", "ui", "components"),
            complexity_level="simple",
        )

        self.testing_agent = AgentDefinition(
            name="Testing Agent",
            description="Comprehensive testing solutions",
            capabilities=("test automation", "quality assurance"),
            use_cases=("unit testing", "integration testing"),
            language_compatibility=("python", "javascript"),
            framework_compatibility=("pytest", "jest"),
            trigger_keywords=("test", "qa", "quality"),
            complexity_level="complex",
        )

    def test_index_agent(self):
        """Test indexing an agent."""
        self.index.index_agent(self.python_web_agent)

        assert len(self.index.all_agents) == 1
        assert len(self.index.agents_by_language["python"]) == 1
        assert len(self.index.agents_by_framework["django"]) == 1
        assert len(self.index.agents_by_complexity["moderate"]) == 1
        assert len(self.index.keyword_to_agents["web"]) == 1

    def test_search_by_language(self):
        """Test searching agents by language."""
        self.index.index_agent(self.python_web_agent)
        self.index.index_agent(self.js_frontend_agent)
        self.index.index_agent(self.testing_agent)

        # Search for Python agents
        python_agents = self.index.search_agents(language="python")
        assert len(python_agents) == 2  # python_web_agent and testing_agent

        # Search for JavaScript agents
        js_agents = self.index.search_agents(language="javascript")
        assert len(js_agents) == 2  # js_frontend_agent and testing_agent

    def test_search_by_framework(self):
        """Test searching agents by framework."""
        self.index.index_agent(self.python_web_agent)
        self.index.index_agent(self.js_frontend_agent)

        # Search for Django agents
        django_agents = self.index.search_agents(framework="django")
        assert len(django_agents) == 1
        assert django_agents[0].name == "Python Web Agent"

        # Search for React agents
        react_agents = self.index.search_agents(framework="react")
        assert len(react_agents) == 1
        assert react_agents[0].name == "JavaScript Frontend Agent"

    def test_search_by_keywords(self):
        """Test searching agents by keywords."""
        self.index.index_agent(self.python_web_agent)
        self.index.index_agent(self.testing_agent)

        # Search by single keyword
        web_agents = self.index.search_agents(keywords=["web"])
        assert len(web_agents) == 1
        assert web_agents[0].name == "Python Web Agent"

        # Search by multiple keywords
        test_agents = self.index.search_agents(keywords=["test", "qa"])
        assert len(test_agents) == 1
        assert test_agents[0].name == "Testing Agent"

    def test_search_multiple_criteria(self):
        """Test searching with multiple criteria."""
        self.index.index_agent(self.python_web_agent)
        self.index.index_agent(self.js_frontend_agent)
        self.index.index_agent(self.testing_agent)

        # Search for Python web agents
        results = self.index.search_agents(language="python", keywords=["web"])
        assert len(results) == 1
        assert results[0].name == "Python Web Agent"

        # Search with no matches
        results = self.index.search_agents(language="rust", framework="django")
        assert len(results) == 0

    def test_get_stats(self):
        """Test getting index statistics."""
        self.index.index_agent(self.python_web_agent)
        self.index.index_agent(self.js_frontend_agent)

        stats = self.index.get_stats()

        assert stats["total_agents"] == 2
        assert stats["languages"] >= 2  # python, javascript, typescript
        assert stats["frameworks"] >= 4  # django, fastapi, react, vue
        assert stats["keywords"] > 0


class TestAgentCompatibilityScorer:
    """Test the agent compatibility scoring system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = AgentCompatibilityScorer()

        # Create test project analysis
        self.python_web_project = ProjectAnalysis(
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

        # Create test agent
        self.python_web_agent = AgentDefinition(
            name="Django Expert",
            description="Expert in Django web development",
            capabilities=("web development", "Django applications", "REST APIs"),
            use_cases=("building web applications", "API development"),
            language_compatibility=("python",),
            framework_compatibility=("django",),
            trigger_keywords=("web", "django", "api"),
            complexity_level="moderate",
            confidence_score=0.9,
        )

    def test_score_perfect_match(self):
        """Test scoring a perfect agent-project match."""
        compatible_agent = self.scorer.score_agent_compatibility(
            self.python_web_agent, self.python_web_project
        )

        assert isinstance(compatible_agent, CompatibleAgent)
        assert compatible_agent.compatibility_score > 0.7
        assert "Language: python" in compatible_agent.matching_criteria
        assert "Framework: django" in compatible_agent.matching_criteria
        assert compatible_agent.confidence_factors["language"] == 1.0
        assert compatible_agent.confidence_factors["framework"] == 1.0

    def test_score_partial_match(self):
        """Test scoring a partial agent-project match."""
        # Create agent that matches language but not framework
        python_flask_agent = AgentDefinition(
            name="Flask Expert",
            description="Expert in Flask web development",
            capabilities=("web development",),
            use_cases=("building web apps",),
            language_compatibility=("python",),
            framework_compatibility=("flask",),
            complexity_level="moderate",
            confidence_score=0.8,
        )

        compatible_agent = self.scorer.score_agent_compatibility(
            python_flask_agent, self.python_web_project
        )

        assert 0.3 < compatible_agent.compatibility_score < 0.8
        assert "Language: python" in compatible_agent.matching_criteria
        assert "Framework: django" not in compatible_agent.matching_criteria

    def test_score_no_match(self):
        """Test scoring agent with no match."""
        # Create agent for completely different stack
        java_agent = AgentDefinition(
            name="Java Spring Expert",
            description="Expert in Java Spring development",
            capabilities=("enterprise development",),
            use_cases=("building enterprise apps",),
            language_compatibility=("java",),
            framework_compatibility=("spring",),
            complexity_level="enterprise",
            confidence_score=0.9,
        )

        compatible_agent = self.scorer.score_agent_compatibility(
            java_agent, self.python_web_project
        )

        assert compatible_agent.compatibility_score < 0.5

    def test_language_compatibility_scoring(self):
        """Test language compatibility scoring specifics."""
        # Test exact match
        score = self.scorer._calculate_language_score(  # noqa: SLF001
            self.python_web_agent, self.python_web_project
        )
        assert score == 1.0

        # Test compatible languages (TypeScript <-> JavaScript)
        ts_agent = AgentDefinition(
            name="TS Agent",
            description="TypeScript agent",
            capabilities=("web dev",),
            use_cases=("apps",),
            language_compatibility=("typescript",),
        )

        js_project = ProjectAnalysis(
            project_path=Path("/test"), language_info=LanguageInfo(primary="javascript")
        )

        score = self.scorer._calculate_language_score(ts_agent, js_project)
        assert score == 0.8  # Compatible but not exact

    def test_complexity_matching(self):
        """Test complexity level matching."""
        # Perfect complexity match
        score = self.scorer._calculate_complexity_score(  # noqa: SLF001
            self.python_web_agent, self.python_web_project
        )
        assert score == 1.0

        # Adjacent complexity levels
        simple_agent = AgentDefinition(
            name="Simple Agent",
            description="Simple tasks",
            capabilities=("basic tasks",),
            use_cases=("simple projects",),
            complexity_level="simple",
        )

        score = self.scorer._calculate_complexity_score(  # noqa: SLF001
            simple_agent, self.python_web_project
        )
        assert score == 0.7  # Adjacent level

        # Distant complexity levels
        enterprise_agent = AgentDefinition(
            name="Enterprise Agent",
            description="Enterprise solutions",
            capabilities=("complex systems",),
            use_cases=("enterprise projects",),
            complexity_level="enterprise",
        )

        score = self.scorer._calculate_complexity_score(  # noqa: SLF001
            enterprise_agent, self.python_web_project
        )
        assert score == 0.3  # Two levels apart


class TestCompatibleAgent:
    """Test the CompatibleAgent model."""

    def test_compatible_agent_creation(self):
        """Test creating a CompatibleAgent."""
        agent = AgentDefinition(
            name="Test Agent",
            description="Test description",
            capabilities=("testing",),
            use_cases=("test cases",),
        )

        compatible = CompatibleAgent(
            agent=agent,
            compatibility_score=0.85,
            matching_criteria=["Language: python"],
            confidence_factors={"language": 1.0, "framework": 0.7},
        )

        assert compatible.agent == agent
        assert compatible.compatibility_score == 0.85
        assert len(compatible.matching_criteria) == 1
        assert compatible.confidence_factors["language"] == 1.0

    def test_compatibility_score_validation(self):
        """Test compatibility score validation."""
        agent = AgentDefinition(
            name="Test", description="Test", capabilities=("test",), use_cases=("test",)
        )

        # Invalid score > 1.0
        with pytest.raises(
            ValueError, match="Compatibility score must be between 0.0 and 1.0"
        ):
            CompatibleAgent(
                agent=agent,
                compatibility_score=1.5,
                matching_criteria=[],
                confidence_factors={},
            )

        # Invalid score < 0.0
        with pytest.raises(
            ValueError, match="Compatibility score must be between 0.0 and 1.0"
        ):
            CompatibleAgent(
                agent=agent,
                compatibility_score=-0.1,
                matching_criteria=[],
                confidence_factors={},
            )


class TestAgentRepositoryScanner:
    """Test the main agent repository scanner."""

    def test_scanner_initialization(self):
        """Test scanner initialization."""
        scanner = AgentRepositoryScanner()

        assert scanner.config is not None
        assert scanner.parser is not None
        assert scanner.scorer is not None
        assert scanner.index is not None

    def test_scan_repositories_placeholder(self):
        """Test scan repositories placeholder implementation."""
        scanner = AgentRepositoryScanner()
        result = scanner.scan_repositories()

        assert isinstance(result, ScanResult)
        assert result.total_agents == 0
        assert "Implementation pending" in result.errors[0]

    def test_find_compatible_agents_placeholder(self):
        """Test find compatible agents placeholder implementation."""
        scanner = AgentRepositoryScanner()

        project = ProjectAnalysis(project_path=Path("/test"))
        results = scanner.find_compatible_agents(project)

        assert isinstance(results, list)
        assert len(results) == 0  # Placeholder returns empty list

    def test_sync_repositories_placeholder(self):
        """Test sync repositories placeholder implementation."""
        scanner = AgentRepositoryScanner()
        result = scanner.sync_repositories()

        assert isinstance(result, SyncResult)
        assert result.updated_repositories == 0
        assert "Implementation pending" in result.errors[0]


@pytest.mark.advanced
class TestIntegrationAgentRepository:
    """Integration tests for agent repository system."""

    def test_end_to_end_configuration_workflow(self):
        """Test complete configuration management workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"

            # Initialize config
            config = RepositoryConfig(config_path)

            # Add custom repository
            config.add_repository(
                url="https://github.com/custom/agents",
                name="custom-agents",
                priority=2,
                description="Custom development agents",
            )

            # Update repository
            config.update_repository("custom-agents", priority=1)

            # Get enabled repositories
            enabled = config.get_enabled_repositories()
            custom_repo = next(
                (r for r in enabled if r["name"] == "custom-agents"), None
            )

            assert custom_repo is not None
            assert custom_repo["priority"] == 1

            # Remove repository
            result = config.remove_repository("custom-agents")
            assert result is True

            # Verify removal
            final_enabled = config.get_enabled_repositories()
            custom_repo_final = next(
                (r for r in final_enabled if r["name"] == "custom-agents"), None
            )
            assert custom_repo_final is None

    def test_agent_parsing_and_indexing_workflow(self):
        """Test parsing agent definitions and indexing them."""
        # Create sample agent content
        agent_content = """
# Web Development Assistant

Expert agent for modern web development with Python and JavaScript.

## Capabilities
- Full-stack web development
- REST API design and implementation
- Database integration
- Frontend component development

## Use Cases
- Building web applications
- Creating API services
- Developing single-page applications

## Keywords
web, fullstack, api, rest, database

## Languages
Python, JavaScript, TypeScript

## Frameworks
Django, FastAPI, React, Vue

## Complexity
moderate
"""

        # Parse agent definition
        parser = AgentDefinitionParser()
        agent = parser.parse_agent_file(
            agent_content, "https://github.com/test/web-agent.md"
        )

        assert agent is not None
        assert agent.name == "Web Development Assistant"
        assert len(agent.capabilities) == 4
        assert "python" in [lang.lower() for lang in agent.language_compatibility]

        assert "django" in [fw.lower() for fw in agent.framework_compatibility]

        # Index the agent
        index = CapabilityIndex()
        index.index_agent(agent)

        # Search for the agent
        web_agents = index.search_agents(keywords=["web"])
        assert len(web_agents) == 1
        assert web_agents[0].name == "Web Development Assistant"

        python_agents = index.search_agents(language="python")
        assert len(python_agents) == 1

        django_agents = index.search_agents(framework="django")
        assert len(django_agents) == 1

    def test_compatibility_scoring_workflow(self):
        """Test complete compatibility scoring workflow."""
        # Create test project
        project = ProjectAnalysis(
            project_path=Path("/test/django-project"),
            language_info=LanguageInfo(primary="python", confidence=0.95),
            framework_info=FrameworkInfo(primary="django", confidence=0.90),
            domain_info=DomainInfo(domain="web", confidence=0.85),
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=ComplexityLevel.MODERATE,
        )

        # Create matching agent
        perfect_agent = AgentDefinition(
            name="Django Web Expert",
            description="Specialized Django web development agent",
            capabilities=("Django development", "web applications", "REST APIs"),
            use_cases=("building Django apps", "creating web services"),
            language_compatibility=("python",),
            framework_compatibility=("django",),
            trigger_keywords=("django", "web", "python"),
            complexity_level="moderate",
            confidence_score=0.95,
        )

        # Create partial match agent
        partial_agent = AgentDefinition(
            name="Python General Expert",
            description="General Python development agent",
            capabilities=("Python programming", "general development"),
            use_cases=("Python projects",),
            language_compatibility=("python",),
            framework_compatibility=("flask", "fastapi"),
            trigger_keywords=("python", "development"),
            complexity_level="simple",
            confidence_score=0.80,
        )

        # Score compatibility
        scorer = AgentCompatibilityScorer()

        perfect_match = scorer.score_agent_compatibility(perfect_agent, project)
        partial_match = scorer.score_agent_compatibility(partial_agent, project)

        # Perfect match should score higher
        assert perfect_match.compatibility_score > partial_match.compatibility_score
        assert perfect_match.compatibility_score > 0.8
        assert "Language: python" in perfect_match.matching_criteria
        assert "Framework: django" in perfect_match.matching_criteria

        # Partial match should still have reasonable score
        assert partial_match.compatibility_score > 0.3
        assert "Language: python" in partial_match.matching_criteria
        assert "Framework: django" not in partial_match.matching_criteria
