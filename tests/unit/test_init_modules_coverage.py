"""Tests for __init__.py modules and imports to boost coverage."""


def test_main_package_imports():
    """Test main package imports and constants."""
    import claude_builder

    # Test version and metadata
    assert claude_builder.__version__ == "0.1.0"
    assert claude_builder.__author__ == "Claude Builder Team"
    assert (
        claude_builder.__description__ == "Universal Claude Code Environment Generator"
    )

    # Test __all__ exports
    assert "Config" in claude_builder.__all__
    assert "ConfigManager" in claude_builder.__all__
    assert "DocumentGenerator" in claude_builder.__all__
    assert "ProjectAnalyzer" in claude_builder.__all__
    assert "main" in claude_builder.__all__

    # Test actual imports work
    assert claude_builder.Config is not None
    assert claude_builder.ConfigManager is not None
    assert claude_builder.DocumentGenerator is not None
    assert claude_builder.ProjectAnalyzer is not None
    assert claude_builder.main is not None


def test_models_package_imports():
    """Test models package backward compatibility imports."""
    from claude_builder.models import (
        ArchitecturePattern,
        ComplexityLevel,
        ProjectAnalysis,
        ProjectType,
    )

    # Test that enums are accessible
    assert ProjectType.WEB_APPLICATION is not None
    assert ComplexityLevel.MODERATE is not None
    assert ArchitecturePattern.MVC is not None
    assert ProjectAnalysis is not None


def test_models_enums_imports():
    """Test models.enums backward compatibility imports."""
    from claude_builder.models.enums import (
        ArchitecturePattern,
        ClaudeMentionPolicy,
        ComplexityLevel,
        GitIntegrationMode,
        ProjectType,
    )

    # Test enum values
    assert ProjectType.API_SERVICE.value == "api_service"
    assert ComplexityLevel.SIMPLE.value == "simple"
    assert ArchitecturePattern.MONOLITH.value == "monolith"
    assert GitIntegrationMode.NO_INTEGRATION.value == "no_integration"
    assert ClaudeMentionPolicy.MINIMAL.value == "minimal"


def test_cli_package_init():
    """Test CLI package init import."""
    from claude_builder.cli import main

    # Should be able to import main
    assert main is not None


def test_core_package_init():
    """Test core package init import."""
    # Just test that core package can be imported
    import claude_builder.core

    assert claude_builder.core is not None


def test_utils_package_init():
    """Test utils package init import."""
    # Just test that utils package can be imported
    import claude_builder.utils

    assert claude_builder.utils is not None
