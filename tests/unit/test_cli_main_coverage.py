"""Comprehensive tests for cli.main module to increase coverage."""

import tempfile

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_builder.cli.main import (
    ExitCodes,
    _display_analysis_results,
    _display_summary,
    _get_git_mode,
    _get_output_mode,
    _list_templates,
    _write_generated_files,
)
from claude_builder.core.models import OutputTarget


def test_exit_codes():
    """Test ExitCodes class constants - covers lines 22-35."""
    assert ExitCodes.SUCCESS == 0
    assert ExitCodes.GENERAL_ERROR == 1
    assert ExitCodes.INVALID_ARGUMENTS == 2
    assert ExitCodes.PROJECT_NOT_FOUND == 3
    assert ExitCodes.NOT_A_PROJECT == 4
    assert ExitCodes.ANALYSIS_FAILED == 5
    assert ExitCodes.TEMPLATE_ERROR == 6
    assert ExitCodes.AGENT_ERROR == 7
    assert ExitCodes.GIT_ERROR == 8
    assert ExitCodes.PERMISSION_ERROR == 9
    assert ExitCodes.CONFIG_ERROR == 10
    assert ExitCodes.INTERRUPTED == 128


def test_get_git_mode_disabled():
    """Test _get_git_mode with no_git=True - covers lines 174-175."""
    kwargs = {"no_git": True, "git_exclude": False, "git_track": False}
    result = _get_git_mode(kwargs)
    assert result == "disabled"


def test_get_git_mode_exclude():
    """Test _get_git_mode with git_exclude=True - covers lines 176-177."""
    kwargs = {"no_git": False, "git_exclude": True, "git_track": False}
    result = _get_git_mode(kwargs)
    assert result == "exclude generated files"


def test_get_git_mode_track():
    """Test _get_git_mode with git_track=True - covers lines 178-179."""
    kwargs = {"no_git": False, "git_exclude": False, "git_track": True}
    result = _get_git_mode(kwargs)
    assert result == "track generated files"


def test_get_git_mode_no_changes():
    """Test _get_git_mode with no git options - covers line 180."""
    kwargs = {"no_git": False, "git_exclude": False, "git_track": False}
    result = _get_git_mode(kwargs)
    assert result == "no changes"


def test_get_output_mode_complete_claude():
    """Test _get_output_mode default complete mode for Claude."""
    kwargs = {"agents_only": False, "no_agents": False, "target": "claude"}
    result = _get_output_mode(kwargs)
    assert result == "complete environment (CLAUDE.md + subagents + AGENTS.md)"


def test_get_output_mode_complete_codex():
    """Test _get_output_mode complete mode for Codex."""
    kwargs = {"agents_only": False, "no_agents": False, "target": "codex"}
    result = _get_output_mode(kwargs)
    assert result == "complete environment (AGENTS.md + .agents/skills/*/SKILL.md)"


def test_get_output_mode_complete_gemini():
    """Test _get_output_mode complete mode for Gemini."""
    kwargs = {"agents_only": False, "no_agents": False, "target": "gemini"}
    result = _get_output_mode(kwargs)
    assert (
        result == "complete environment (GEMINI.md + AGENTS.md + .gemini/agents/*.md)"
    )


@patch("claude_builder.cli.main.console")
@patch("claude_builder.cli.main.TemplateManager")
def test_list_templates_success(mock_template_manager, mock_console):
    """Test _list_templates successful execution - covers lines 186-216."""
    # Mock template manager and templates
    mock_template = MagicMock()
    mock_template.installed = True
    mock_template.metadata.name = "test-template"
    mock_template.metadata.version = "1.0.0"
    mock_template.metadata.category = "python"
    mock_template.metadata.description = "A test template"

    mock_manager = MagicMock()
    mock_manager.list_available_templates.return_value = [mock_template]
    mock_template_manager.return_value = mock_manager

    _list_templates()

    # Should create template manager and list templates
    mock_template_manager.assert_called_once()
    mock_manager.list_available_templates.assert_called_once()
    mock_console.print.assert_called()  # Should print the table


@patch("claude_builder.cli.main.console")
@patch("claude_builder.cli.main.TemplateManager")
def test_list_templates_no_templates(mock_template_manager, mock_console):
    """Test _list_templates with no templates - covers lines 190-192."""
    mock_manager = MagicMock()
    mock_manager.list_available_templates.return_value = []
    mock_template_manager.return_value = mock_manager

    _list_templates()

    # Should print "No templates available"
    mock_console.print.assert_called_with("[yellow]No templates available[/yellow]")


@patch("claude_builder.cli.main.console")
@patch("claude_builder.cli.main.TemplateManager")
def test_list_templates_many_templates(mock_template_manager, mock_console):
    """Test _list_templates with more than 10 templates - covers lines 215-216."""
    # Create 15 mock templates
    templates = []
    for i in range(15):
        mock_template = MagicMock()
        mock_template.installed = i % 2 == 0  # Alternating installed status
        mock_template.metadata.name = f"template-{i}"
        mock_template.metadata.version = "1.0.0"
        mock_template.metadata.category = "test"
        mock_template.metadata.description = f"Test template {i}"
        templates.append(mock_template)

    mock_manager = MagicMock()
    mock_manager.list_available_templates.return_value = templates
    mock_template_manager.return_value = mock_manager

    _list_templates()

    # Should print the "... and X more" message
    expected_call = (
        "\n[dim]... and 5 more. Use 'claude-builder templates list' for full list[/dim]"
    )
    mock_console.print.assert_any_call(expected_call)


@patch("claude_builder.cli.main.console")
@patch("claude_builder.cli.main.TemplateManager")
def test_list_templates_long_description(mock_template_manager, mock_console):
    """Test _list_templates with long description truncation - covers lines 209."""
    mock_template = MagicMock()
    mock_template.installed = True
    mock_template.metadata.name = "test-template"
    mock_template.metadata.version = "1.0.0"
    mock_template.metadata.category = "python"
    # Long description that should be truncated
    mock_template.metadata.description = (
        "This is a very long description that exceeds the 50 character "
        "limit and should be truncated"
    )

    mock_manager = MagicMock()
    mock_manager.list_available_templates.return_value = [mock_template]
    mock_template_manager.return_value = mock_manager

    _list_templates()

    mock_template_manager.assert_called_once()


@patch("claude_builder.cli.main.console")
@patch("claude_builder.cli.main.TemplateManager")
def test_list_templates_exception_fallback(mock_template_manager, mock_console):
    """Test _list_templates exception fallback - covers lines 218-238."""
    mock_template_manager.side_effect = Exception("Template manager failed")

    _list_templates()

    # Should print error message
    mock_console.print.assert_any_call(
        "[red]Error listing templates: Template manager failed[/red]"
    )

    # Should fall back to built-in templates table
    # The fallback creates a table with built-in templates
    assert mock_console.print.call_count > 1  # Multiple print calls for error + table


@patch("claude_builder.cli.main.console")
def test_display_analysis_results_basic(mock_console):
    """Test _display_analysis_results with basic analysis - covers lines 242-253."""
    # Create mock analysis object
    analysis = MagicMock()
    analysis.language_info.primary = "python"
    analysis.language_info.confidence = 95.5
    analysis.language_info.secondary = ["javascript", "html"]
    analysis.framework_info.primary = "django"
    analysis.framework_info.confidence = 88.2
    analysis.project_type.value = "web_application"
    analysis.complexity_level.value = "moderate"
    analysis.filesystem_info.total_files = 150
    analysis.filesystem_info.source_files = 85
    analysis.domain_info.domain = "web_development"
    analysis.domain_info.confidence = 72.3
    analysis.analysis_confidence = 91.7

    _display_analysis_results(analysis)

    # Should make multiple print calls for different analysis aspects
    assert mock_console.print.call_count >= 7


@patch("claude_builder.cli.main.console")
def test_display_analysis_results_minimal(mock_console):
    """Test _display_analysis_results with minimal data - covers edge cases."""
    # Create mock analysis with minimal data
    analysis = MagicMock()
    analysis.language_info.primary = None
    analysis.language_info.confidence = 0.0
    analysis.language_info.secondary = []
    analysis.framework_info.primary = None
    analysis.framework_info.confidence = 0.0
    analysis.project_type.value = "unknown"
    analysis.complexity_level.value = "simple"
    analysis.filesystem_info.total_files = 5
    analysis.filesystem_info.source_files = 2
    analysis.domain_info = None  # No domain info
    analysis.analysis_confidence = 45.0

    _display_analysis_results(analysis)

    # Should handle None values gracefully
    mock_console.print.assert_called()


def test_write_generated_files_basic(temp_dir):
    """Test _write_generated_files basic functionality - covers lines 259-285."""
    # Create mock generated content
    generated_content = MagicMock()
    generated_content.files = {
        "CLAUDE.md": "# Claude Builder Project\\nContent here",
        "AGENTS.md": "# Agent Configuration\\nAgents here",
        "docs/guide.md": "# Documentation\\nGuide content",
    }

    kwargs = {
        "output_dir": None,  # Will use project_path
        "backup_existing": False,
        "quiet": True,
    }

    with patch("claude_builder.cli.main.console") as mock_console:
        _write_generated_files(generated_content, temp_dir, kwargs)
        mock_console.print.assert_called()  # Verify console output

    # Check that files were created
    assert (temp_dir / "CLAUDE.md").exists()
    assert (temp_dir / "AGENTS.md").exists()
    assert (temp_dir / "docs" / "guide.md").exists()

    # Check file contents
    with open(temp_dir / "CLAUDE.md") as f:
        assert "Claude Builder Project" in f.read()


def test_write_generated_files_custom_output_dir(temp_dir):
    """Test _write_generated_files with custom output directory.

    Covers lines 261-264.
    """
    output_dir = temp_dir / "custom_output"

    generated_content = MagicMock()
    generated_content.files = {"test.md": "Test content"}

    kwargs = {"output_dir": str(output_dir), "backup_existing": False, "quiet": True}

    with patch("claude_builder.cli.main.console"):
        _write_generated_files(generated_content, temp_dir, kwargs)

    # Should create file in custom output directory
    assert (output_dir / "test.md").exists()


def test_write_generated_files_backup_existing(temp_dir):
    """Test _write_generated_files with backup - covers lines 274-276."""
    # Create existing file
    existing_file = temp_dir / "existing.md"
    existing_file.write_text("Original content")

    generated_content = MagicMock()
    generated_content.files = {"existing.md": "New content"}

    kwargs = {"output_dir": None, "backup_existing": True, "quiet": True}

    with patch("claude_builder.cli.main.console"):
        _write_generated_files(generated_content, temp_dir, kwargs)

    # Should create backup file
    backup_file = temp_dir / "existing.md.bak"
    assert backup_file.exists()
    assert backup_file.read_text() == "Original content"

    # New file should have new content
    assert existing_file.read_text() == "New content"


def test_write_generated_files_project_path_none():
    """Test _write_generated_files with None project_path - covers lines 259-260."""
    generated_content = MagicMock()
    generated_content.files = {}
    kwargs = {"quiet": True}

    with pytest.raises(ValueError, match="project_path is None"):
        _write_generated_files(generated_content, None, kwargs)


@patch("claude_builder.cli.main.console")
def test_write_generated_files_not_quiet(mock_console, temp_dir):
    """Test _write_generated_files verbose output - covers lines 284-285."""
    generated_content = MagicMock()
    generated_content.files = {"test1.md": "content1", "test2.md": "content2"}

    kwargs = {
        "output_dir": None,
        "backup_existing": False,
        "quiet": False,  # Not quiet, should print summary
    }

    _write_generated_files(generated_content, temp_dir, kwargs)

    # Should print summary with file count
    expected_call = f"\n[green]✓ Wrote 2 files to {temp_dir}[/green]"
    mock_console.print.assert_called_with(expected_call)


@patch("claude_builder.cli.main.console")
def test_display_summary_dry_run(mock_console):
    """Test _display_summary with dry_run=True - covers lines 290-291."""
    project_path = Path("/test/project")

    _display_summary(project_path, dry_run=True)

    mock_console.print.assert_any_call("\n[bold green]✓ Complete![/bold green]")
    mock_console.print.assert_any_call(
        "Would generate Claude environment for [cyan]/test/project[/cyan]"
    )


@patch("claude_builder.cli.main.console")
def test_display_summary_actual_run(mock_console):
    """Test _display_summary with dry_run=False - covers lines 294-299."""
    project_path = Path("/test/project")

    _display_summary(project_path, dry_run=False)

    mock_console.print.assert_any_call("\n[bold green]✓ Complete![/bold green]")
    mock_console.print.assert_any_call(
        "Generated Claude environment for [cyan]/test/project[/cyan]"
    )

    # Should print next steps
    mock_console.print.assert_any_call("1. Review generated CLAUDE.md file")
    mock_console.print.assert_any_call("2. Review specialist files in .claude/agents/")
    mock_console.print.assert_any_call(
        "3. Start using Claude Code with your optimized environment!"
    )


@patch("claude_builder.cli.main.console")
def test_display_summary_codex_actual_run(mock_console):
    """Test _display_summary codex messaging for target-aware workflow."""
    project_path = Path("/test/project")

    _display_summary(project_path, dry_run=False, target=OutputTarget.CODEX)

    mock_console.print.assert_any_call("\n[bold green]✓ Complete![/bold green]")
    mock_console.print.assert_any_call(
        "Generated Codex environment for [cyan]/test/project[/cyan]"
    )
    mock_console.print.assert_any_call("1. Review generated AGENTS.md file")
    mock_console.print.assert_any_call("2. Review specialist files in .agents/skills/")
    mock_console.print.assert_any_call(
        "3. Start using Codex CLI with your optimized environment!"
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
