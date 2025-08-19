"""Tests for CLI git commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch

from claude_builder.cli.git_commands import git, setup_exclude, remove_exclude, status, backup, restore


class TestGitCommands:
    """Test git CLI commands."""

    def test_git_command_group(self):
        """Test git command group exists."""
        runner = CliRunner()
        result = runner.invoke(git, ["--help"])
        assert result.exit_code == 0
        assert "Git integration management" in result.output

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_setup_exclude_command(self, mock_git_manager_class, sample_python_project):
        """Test git setup-exclude command."""
        mock_git_manager = Mock()
        mock_git_manager.setup_git_exclude.return_value = Mock(
            success=True,
            files_added=['CLAUDE.md', 'AGENTS.md'],
            exclude_file_path='.git/info/exclude'
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(setup_exclude, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Git exclude configured" in result.output or "configured" in result.output.lower()

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_setup_exclude_command_with_patterns(self, mock_git_manager_class, sample_python_project):
        """Test git setup-exclude command with custom patterns."""
        mock_git_manager = Mock()
        mock_git_manager.setup_git_exclude.return_value = Mock(success=True, files_added=['CLAUDE.md'])
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(setup_exclude, [
            str(sample_python_project),
            "--patterns", "CLAUDE.md,AGENTS.md,*.claude"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_setup_exclude_command_dry_run(self, mock_git_manager_class, sample_python_project):
        """Test git setup-exclude command with dry run."""
        mock_git_manager = Mock()
        mock_git_manager.setup_git_exclude.return_value = Mock(
            success=True,
            dry_run=True,
            files_would_add=['CLAUDE.md', 'AGENTS.md']
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(setup_exclude, [
            str(sample_python_project),
            "--dry-run"
        ])
        assert result.exit_code == 0
        assert "would add" in result.output.lower() or "dry run" in result.output.lower()

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_remove_exclude_command(self, mock_git_manager_class, sample_python_project):
        """Test git remove-exclude command."""
        mock_git_manager = Mock()
        mock_git_manager.remove_git_exclude.return_value = Mock(
            success=True,
            files_removed=['CLAUDE.md', 'AGENTS.md'],
            backup_created='exclude.backup'
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(remove_exclude, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Git exclude entries removed" in result.output or "removed" in result.output.lower()

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_remove_exclude_command_with_backup(self, mock_git_manager_class, sample_python_project):
        """Test git remove-exclude command with backup."""
        mock_git_manager = Mock()
        mock_git_manager.remove_git_exclude.return_value = Mock(
            success=True,
            files_removed=['CLAUDE.md'],
            backup_created='exclude.backup'
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(remove_exclude, [
            str(sample_python_project),
            "--create-backup"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_git_status_command(self, mock_git_manager_class, sample_python_project):
        """Test git status command."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=True,
            exclude_file_exists=True,
            exclude_patterns=['CLAUDE.md', 'AGENTS.md'],
            tracked_files=['src/main.py'],
            untracked_files=['temp.txt']
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(status, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Git Status" in result.output or "Repository Status" in result.output

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_git_status_command_non_git_repo(self, mock_git_manager_class, sample_python_project):
        """Test git status command for non-git repository."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=False,
            error_message="Not a git repository"
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(status, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "not a git repository" in result.output.lower() or "Not a git" in result.output

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_backup_command(self, mock_git_manager_class, sample_python_project):
        """Test git backup command."""
        mock_git_manager = Mock()
        mock_git_manager.create_backup.return_value = Mock(
            success=True,
            backup_path='backup-20250119-120000.tar.gz',
            files_backed_up=['CLAUDE.md', 'AGENTS.md', '.git/info/exclude']
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(backup, [str(sample_python_project)])
        assert result.exit_code == 0
        assert "Backup created" in result.output or "backup" in result.output.lower()

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_backup_command_with_name(self, mock_git_manager_class, sample_python_project):
        """Test git backup command with custom name."""
        mock_git_manager = Mock()
        mock_git_manager.create_backup.return_value = Mock(
            success=True,
            backup_path='custom-backup.tar.gz'
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(backup, [
            str(sample_python_project),
            "--name", "custom-backup"
        ])
        assert result.exit_code == 0

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_restore_command(self, mock_git_manager_class, sample_python_project, tmp_path):
        """Test git restore command."""
        backup_file = tmp_path / "backup.tar.gz"
        backup_file.write_text("mock backup content")
        
        mock_git_manager = Mock()
        mock_git_manager.restore_backup.return_value = Mock(
            success=True,
            files_restored=['CLAUDE.md', '.git/info/exclude'],
            restore_path=str(sample_python_project)
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(restore, [
            str(sample_python_project),
            str(backup_file)
        ])
        assert result.exit_code == 0
        assert "Backup restored" in result.output or "restored" in result.output.lower()

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_restore_command_with_confirmation(self, mock_git_manager_class, sample_python_project, tmp_path):
        """Test git restore command with confirmation prompt."""
        backup_file = tmp_path / "backup.tar.gz"
        backup_file.write_text("mock backup content")
        
        mock_git_manager = Mock()
        mock_git_manager.restore_backup.return_value = Mock(success=True, files_restored=['CLAUDE.md'])
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(restore, [
            str(sample_python_project),
            str(backup_file),
            "--force"
        ])
        assert result.exit_code == 0

    def test_setup_exclude_invalid_path(self):
        """Test git setup-exclude command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(setup_exclude, ["/nonexistent/path"])
        assert result.exit_code != 0

    def test_git_status_invalid_path(self):
        """Test git status command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(status, ["/nonexistent/path"])
        assert result.exit_code != 0

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_setup_exclude_command_failure(self, mock_git_manager_class, sample_python_project):
        """Test git setup-exclude command when operation fails."""
        mock_git_manager = Mock()
        mock_git_manager.setup_git_exclude.return_value = Mock(
            success=False,
            error_message="Permission denied accessing .git/info/exclude"
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(setup_exclude, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Failed to setup" in result.output or "Permission denied" in result.output

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_git_command_exception_handling(self, mock_git_manager_class, sample_python_project):
        """Test git command exception handling."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.side_effect = Exception("Git operation failed")
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(status, [str(sample_python_project)])
        assert result.exit_code != 0
        assert "Error" in result.output or "Git operation failed" in result.output

    @patch('claude_builder.cli.git_commands.GitIntegrationManager')
    def test_git_status_verbose(self, mock_git_manager_class, sample_python_project):
        """Test git status command with verbose output."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=True,
            exclude_file_exists=True,
            exclude_patterns=['CLAUDE.md'],
            recent_commits=[{'hash': 'abc123', 'message': 'Initial commit'}],
            branch_info={'current': 'main', 'upstream': 'origin/main'}
        )
        mock_git_manager_class.return_value = mock_git_manager
        
        runner = CliRunner()
        result = runner.invoke(status, [
            str(sample_python_project),
            "--verbose"
        ])
        assert result.exit_code == 0

    def test_restore_command_missing_backup_file(self, sample_python_project):
        """Test git restore command with missing backup file."""
        runner = CliRunner()
        result = runner.invoke(restore, [
            str(sample_python_project),
            "/nonexistent/backup.tar.gz"
        ])
        assert result.exit_code != 0