"""Tests for CLI git commands."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.git_commands import git


class TestGitCommands:
    """Test git CLI commands."""

    def test_git_command_group(self):
        """Test git command group exists."""
        runner = CliRunner()
        result = runner.invoke(git, ["--help"])
        assert result.exit_code == 0
        assert "Manage git integration features" in result.output

    @patch("claude_builder.cli.git_commands.ConfigManager")
    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_setup_exclude_command(self, mock_git_manager_class, mock_config_manager_class, sample_python_project):
        """Test git exclude command."""
        # Create actual .git directory structure for test
        git_dir = sample_python_project / ".git"
        git_info_dir = git_dir / "info"
        git_info_dir.mkdir(parents=True, exist_ok=True)

        # Mock config manager
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.git_integration.files_to_exclude = ["CLAUDE.md", "AGENTS.md"]
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager

        # Mock git manager
        mock_git_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.operations_performed = ["Added CLAUDE.md to .git/info/exclude"]
        mock_git_manager.exclude_manager.add_excludes.return_value = mock_result
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, ["exclude", str(sample_python_project)])
        assert result.exit_code == 0
        assert "Files added to .git/info/exclude" in result.output

    @patch("claude_builder.cli.git_commands.ConfigManager")
    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    @patch("pathlib.Path.exists")
    def test_setup_exclude_command_with_patterns(self, mock_path_exists, mock_git_manager_class, mock_config_manager_class, sample_python_project):
        """Test git setup-exclude command with custom patterns."""
        # Mock .git directory exists
        mock_path_exists.return_value = True

        # Mock config manager
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.git_integration.files_to_exclude = ["CLAUDE.md"]
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager

        # Mock git manager
        mock_git_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.operations_performed = ["Added CLAUDE.md to .git/info/exclude"]
        mock_git_manager.exclude_manager.add_excludes.return_value = mock_result
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "exclude",
            str(sample_python_project),
            "--force"
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.ConfigManager")
    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_setup_exclude_command_dry_run(self, mock_git_manager_class, mock_config_manager_class, sample_python_project):
        """Test git setup-exclude command with dry run."""
        # Create actual .git directory structure for test
        git_dir = sample_python_project / ".git"
        git_info_dir = git_dir / "info"
        git_info_dir.mkdir(parents=True, exist_ok=True)

        # Mock config manager
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.git_integration.files_to_exclude = ["CLAUDE.md", "AGENTS.md"]
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager

        # Mock git manager
        mock_git_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.operations_performed = ["Would add CLAUDE.md to .git/info/exclude"]
        mock_git_manager.exclude_manager.add_excludes.return_value = mock_result
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "exclude",
            str(sample_python_project)
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_remove_exclude_command(self, mock_git_manager_class, sample_python_project):
        """Test git remove-exclude command."""
        mock_git_manager = Mock()
        mock_git_manager.remove_git_exclude.return_value = Mock(
            success=True,
            files_removed=["CLAUDE.md", "AGENTS.md"],
            backup_created="exclude.backup"
        )
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, ["unexclude", str(sample_python_project)])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_remove_exclude_command_with_backup(self, mock_git_manager_class, sample_python_project):
        """Test git remove-exclude command with backup."""
        mock_git_manager = Mock()
        mock_git_manager.remove_git_exclude.return_value = Mock(
            success=True,
            files_removed=["CLAUDE.md"],
            backup_created="exclude.backup"
        )
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "unexclude",
            str(sample_python_project)
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_git_status_command(self, mock_git_manager_class, sample_python_project):
        """Test git status command."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=True,
            exclude_file_exists=True,
            exclude_patterns=["CLAUDE.md", "AGENTS.md"],
            tracked_files=["src/main.py"],
            untracked_files=["temp.txt"]
        )
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, ["status", str(sample_python_project)])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_git_status_command_non_git_repo(self, mock_git_manager_class, sample_python_project):
        """Test git status command for non-git repository."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=False,
            error_message="Not a git repository"
        )
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, ["status", str(sample_python_project)])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitBackupManager")
    def test_backup_command(self, mock_backup_manager_class, sample_python_project):
        """Test git list-backups command."""
        mock_backup_manager = Mock()
        mock_backup_manager.list_backups.return_value = [
            {"id": "backup1", "timestamp": "2025-01-19 12:00:00"},
            {"id": "backup2", "timestamp": "2025-01-18 12:00:00"}
        ]
        mock_backup_manager_class.return_value = mock_backup_manager

        runner = CliRunner()
        result = runner.invoke(git, ["list-backups", str(sample_python_project)])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitBackupManager")
    def test_backup_command_with_name(self, mock_backup_manager_class, sample_python_project):
        """Test git list-backups command with JSON format."""
        mock_backup_manager = Mock()
        mock_backup_manager.list_backups.return_value = [
            {"id": "backup1", "timestamp": "2025-01-19 12:00:00"}
        ]
        mock_backup_manager_class.return_value = mock_backup_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "list-backups",
            str(sample_python_project),
            "--format", "json"
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitBackupManager")
    def test_restore_command(self, mock_backup_manager_class, sample_python_project):
        """Test git rollback command."""
        mock_backup_manager = Mock()
        mock_backup_manager.restore_backup.return_value = Mock(
            success=True,
            files_restored=["CLAUDE.md", ".git/info/exclude"],
            restore_path=str(sample_python_project)
        )
        mock_backup_manager_class.return_value = mock_backup_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "rollback",
            "backup1",
            str(sample_python_project)
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitBackupManager")
    def test_restore_command_with_confirmation(self, mock_backup_manager_class, sample_python_project):
        """Test git cleanup-backups command."""
        mock_backup_manager = Mock()
        mock_backup_manager.cleanup_backups.return_value = Mock(
            success=True,
            backups_removed=2
        )
        mock_backup_manager_class.return_value = mock_backup_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "cleanup-backups",
            str(sample_python_project),
            "--keep", "3"
        ])
        assert result.exit_code == 0

    def test_setup_exclude_invalid_path(self):
        """Test git exclude command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(git, ["exclude", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_git_status_invalid_path(self):
        """Test git status command with invalid path."""
        runner = CliRunner()
        result = runner.invoke(git, ["status", "/nonexistent/path"])
        assert result.exit_code != 0

    @patch("claude_builder.cli.git_commands.ConfigManager")
    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    @patch("pathlib.Path.exists")
    def test_setup_exclude_command_failure(self, mock_path_exists, mock_git_manager_class, mock_config_manager_class, sample_python_project):
        """Test git setup-exclude command when operation fails."""
        # Mock .git directory exists
        mock_path_exists.return_value = True

        # Mock config manager
        mock_config_manager = Mock()
        mock_config = Mock()
        mock_config.git_integration.files_to_exclude = ["CLAUDE.md"]
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager

        # Mock git manager with failure
        mock_git_manager = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.errors = ["Permission denied accessing .git/info/exclude"]
        mock_git_manager.exclude_manager.add_excludes.return_value = mock_result
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, ["exclude", str(sample_python_project)])
        assert result.exit_code != 0

    @patch("pathlib.Path.exists")
    def test_git_command_exception_handling(self, mock_path_exists, sample_python_project):
        """Test git command exception handling."""
        # Mock .git directory exists but then cause an exception
        mock_path_exists.return_value = True

        # Mock the file open to cause an exception
        with patch("builtins.open", side_effect=Exception("File access failed")):
            runner = CliRunner()
            result = runner.invoke(git, ["status", str(sample_python_project)])
            assert result.exit_code != 0

    @patch("claude_builder.cli.git_commands.GitIntegrationManager")
    def test_git_status_verbose(self, mock_git_manager_class, sample_python_project):
        """Test git status command with verbose output."""
        mock_git_manager = Mock()
        mock_git_manager.get_git_status.return_value = Mock(
            is_git_repo=True,
            exclude_file_exists=True,
            exclude_patterns=["CLAUDE.md"],
            recent_commits=[{"hash": "abc123", "message": "Initial commit"}],
            branch_info={"current": "main", "upstream": "origin/main"}
        )
        mock_git_manager_class.return_value = mock_git_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "status",
            str(sample_python_project)
        ])
        assert result.exit_code == 0

    @patch("claude_builder.cli.git_commands.GitBackupManager")
    @patch("pathlib.Path.exists")
    def test_restore_command_missing_backup_file(self, mock_path_exists, mock_backup_manager_class, sample_python_project):
        """Test git rollback command with missing backup ID."""
        # Mock .git directory exists
        mock_path_exists.return_value = True

        # Mock backup manager to fail restoration
        mock_backup_manager = Mock()
        mock_backup_manager.restore_backup.return_value = False
        mock_backup_manager_class.return_value = mock_backup_manager

        runner = CliRunner()
        result = runner.invoke(git, [
            "rollback",
            "nonexistent-backup",
            str(sample_python_project),
            "--force"
        ])
        assert result.exit_code != 0
