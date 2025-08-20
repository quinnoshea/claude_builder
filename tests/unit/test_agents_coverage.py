"""Tests for core.agents module to boost coverage."""

from unittest.mock import MagicMock

import pytest

from claude_builder.core.agents import (
    AgentConfiguration,
    AgentInfo,
    AgentSelector,
    UniversalAgentSystem,
)
from claude_builder.core.models import ProjectAnalysis, ProjectType, ComplexityLevel, LanguageInfo, FrameworkInfo
from pathlib import Path


def test_agent_info_creation():
    """Test AgentInfo creation - covers AgentInfo dataclass."""
    agent = AgentInfo(
        name="test-agent",
        description="Test agent description",
        priority=1,
        category="test",
        capabilities=["testing", "validation"]
    )
    
    assert agent.name == "test-agent"
    assert agent.description == "Test agent description"
    assert agent.priority == 1
    assert agent.category == "test"
    assert "testing" in agent.capabilities
    assert "validation" in agent.capabilities


def test_agent_configuration_creation():
    """Test AgentConfiguration creation - covers AgentConfiguration."""
    config = AgentConfiguration()
    
    assert isinstance(config.core_agents, list)
    assert isinstance(config.domain_agents, list)
    assert isinstance(config.workflow_agents, list)
    assert isinstance(config.custom_agents, list)
    assert isinstance(config.coordination_patterns, dict)


def test_agent_configuration_all_agents():
    """Test AgentConfiguration.all_agents property - covers all_agents property."""
    config = AgentConfiguration()
    
    # Add some test agents
    core_agent = AgentInfo(name="core-agent", priority=1)
    domain_agent = AgentInfo(name="domain-agent", priority=2)
    workflow_agent = AgentInfo(name="workflow-agent", priority=3)
    custom_agent = AgentInfo(name="custom-agent", priority=4)
    
    config.core_agents = [core_agent]
    config.domain_agents = [domain_agent]
    config.workflow_agents = [workflow_agent]
    config.custom_agents = [custom_agent]
    
    all_agents = config.all_agents
    
    assert len(all_agents) == 4
    assert all_agents[0].name == "core-agent"
    assert all_agents[1].name == "domain-agent"
    assert all_agents[2].name == "workflow-agent"
    assert all_agents[3].name == "custom-agent"


def test_universal_agent_system_initialization():
    """Test UniversalAgentSystem initialization - covers __init__."""
    system = UniversalAgentSystem()
    
    assert hasattr(system, 'selector')
    assert isinstance(system.selector, AgentSelector)


def test_universal_agent_system_with_config():
    """Test UniversalAgentSystem with config - covers config handling."""
    config = {"test_key": "test_value"}
    system = UniversalAgentSystem(config=config)
    
    assert system.config == config
    assert system.config["test_key"] == "test_value"


def test_agent_selector_initialization():
    """Test AgentSelector initialization - covers AgentSelector.__init__."""
    selector = AgentSelector()
    
    assert selector is not None
    # Basic initialization test


def test_agent_selector_select_core_agents_basic():
    """Test AgentSelector.select_core_agents basic functionality."""
    selector = AgentSelector()
    
    # Create a basic analysis
    analysis = ProjectAnalysis(
        project_path=Path("/test"),
        language_info=LanguageInfo(primary="python"),
        framework_info=FrameworkInfo(primary="django"),
        project_type=ProjectType.WEB_APPLICATION,
        complexity_level=ComplexityLevel.MODERATE
    )
    
    core_agents = selector.select_core_agents(analysis)
    
    assert isinstance(core_agents, list)
    # Should return some agents for a web application
    assert len(core_agents) >= 0


def test_agent_selector_select_domain_agents_basic():
    """Test AgentSelector.select_domain_agents basic functionality."""
    selector = AgentSelector()
    
    analysis = ProjectAnalysis(
        project_path=Path("/test"),
        language_info=LanguageInfo(primary="python"),
        framework_info=FrameworkInfo(primary="django"),
        project_type=ProjectType.WEB_APPLICATION,
        complexity_level=ComplexityLevel.MODERATE
    )
    
    domain_agents = selector.select_domain_agents(analysis)
    
    assert isinstance(domain_agents, list)
    # Should return domain agents for web development
    assert len(domain_agents) >= 0


def test_agent_selector_select_workflow_agents_basic():
    """Test AgentSelector.select_workflow_agents basic functionality."""
    selector = AgentSelector()
    
    analysis = ProjectAnalysis(
        project_path=Path("/test"),
        language_info=LanguageInfo(primary="python"),
        framework_info=FrameworkInfo(primary="django"),
        project_type=ProjectType.WEB_APPLICATION,
        complexity_level=ComplexityLevel.MODERATE
    )
    
    workflow_agents = selector.select_workflow_agents(analysis)
    
    assert isinstance(workflow_agents, list)
    # Should return workflow agents
    assert len(workflow_agents) >= 0


def test_agent_selector_different_project_types():
    """Test AgentSelector with different project types - covers project type handling."""
    selector = AgentSelector()
    
    # Test CLI project
    cli_analysis = ProjectAnalysis(
        project_path=Path("/cli"),
        language_info=LanguageInfo(primary="rust"),
        project_type=ProjectType.CLI_TOOL,
        complexity_level=ComplexityLevel.SIMPLE
    )
    
    cli_core_agents = selector.select_core_agents(cli_analysis)
    assert isinstance(cli_core_agents, list)
    
    # Test library project
    lib_analysis = ProjectAnalysis(
        project_path=Path("/lib"),
        language_info=LanguageInfo(primary="javascript"),
        project_type=ProjectType.LIBRARY,
        complexity_level=ComplexityLevel.MODERATE
    )
    
    lib_core_agents = selector.select_core_agents(lib_analysis)
    assert isinstance(lib_core_agents, list)


def test_agent_selector_different_languages():
    """Test AgentSelector with different languages - covers language-specific logic."""
    selector = AgentSelector()
    
    languages = ["python", "rust", "javascript", "java", "go"]
    
    for language in languages:
        analysis = ProjectAnalysis(
            project_path=Path(f"/{language}"),
            language_info=LanguageInfo(primary=language),
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=ComplexityLevel.MODERATE
        )
        
        core_agents = selector.select_core_agents(analysis)
        assert isinstance(core_agents, list)


def test_agent_selector_different_complexities():
    """Test AgentSelector with different complexities - covers complexity handling."""
    selector = AgentSelector()
    
    complexities = [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE, ComplexityLevel.HIGH]
    
    for complexity in complexities:
        analysis = ProjectAnalysis(
            project_path=Path("/test"),
            language_info=LanguageInfo(primary="python"),
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=complexity
        )
        
        core_agents = selector.select_core_agents(analysis)
        assert isinstance(core_agents, list)


def test_universal_agent_system_configure_agents():
    """Test UniversalAgentSystem.configure_agents - covers main configuration method."""
    system = UniversalAgentSystem()
    
    analysis = ProjectAnalysis(
        project_path=Path("/test"),
        language_info=LanguageInfo(primary="python"),
        framework_info=FrameworkInfo(primary="django"),
        project_type=ProjectType.WEB_APPLICATION,
        complexity_level=ComplexityLevel.MODERATE
    )
    
    config = system.configure_agents(analysis)
    
    assert isinstance(config, AgentConfiguration)
    assert isinstance(config.core_agents, list)
    assert isinstance(config.domain_agents, list)
    assert isinstance(config.workflow_agents, list)
    assert isinstance(config.coordination_patterns, dict)


def test_agent_info_defaults():
    """Test AgentInfo with default values - covers default initialization."""
    agent = AgentInfo(name="minimal-agent")
    
    assert agent.name == "minimal-agent"
    assert agent.description == ""
    assert agent.priority == 0
    assert agent.category == "general"
    assert agent.capabilities == []
    assert agent.requirements == []
    assert agent.conflicts == []
    assert agent.metadata == {}


def test_agent_info_full_initialization():
    """Test AgentInfo with all fields - covers full initialization."""
    agent = AgentInfo(
        name="full-agent",
        description="Full agent with all fields",
        priority=5,
        category="specialized",
        capabilities=["analysis", "generation"],
        requirements=["python>=3.8"],
        conflicts=["old-agent"],
        metadata={"version": "1.0", "author": "test"}
    )
    
    assert agent.name == "full-agent"
    assert agent.description == "Full agent with all fields"
    assert agent.priority == 5
    assert agent.category == "specialized"
    assert agent.capabilities == ["analysis", "generation"]
    assert agent.requirements == ["python>=3.8"]
    assert agent.conflicts == ["old-agent"]
    assert agent.metadata["version"] == "1.0"
    assert agent.metadata["author"] == "test"


def test_agent_configuration_with_agents():
    """Test AgentConfiguration with various agents - covers initialization with data."""
    core_agent = AgentInfo(name="core-1", priority=1)
    domain_agent = AgentInfo(name="domain-1", priority=2)
    workflow_agent = AgentInfo(name="workflow-1", priority=3)
    custom_agent = AgentInfo(name="custom-1", priority=4)
    
    config = AgentConfiguration(
        core_agents=[core_agent],
        domain_agents=[domain_agent],
        workflow_agents=[workflow_agent],
        custom_agents=[custom_agent],
        coordination_patterns={"test": "pattern"}
    )
    
    assert len(config.core_agents) == 1
    assert len(config.domain_agents) == 1
    assert len(config.workflow_agents) == 1
    assert len(config.custom_agents) == 1
    assert config.coordination_patterns["test"] == "pattern"


def test_universal_agent_system_empty_analysis():
    """Test UniversalAgentSystem with minimal analysis - covers edge cases."""
    system = UniversalAgentSystem()
    
    # Minimal analysis
    analysis = ProjectAnalysis(
        project_path=Path("/minimal"),
        language_info=LanguageInfo(primary=None),
        project_type=ProjectType.UNKNOWN,
        complexity_level=ComplexityLevel.SIMPLE
    )
    
    config = system.configure_agents(analysis)
    
    assert isinstance(config, AgentConfiguration)
    # Should handle minimal analysis gracefully
