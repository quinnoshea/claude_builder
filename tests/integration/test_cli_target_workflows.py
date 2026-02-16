"""Integration tests for top-level CLI target profile workflows."""

from click.testing import CliRunner

from claude_builder.cli.main import cli


class TestCLITargetWorkflows:
    """Integration coverage for target-aware top-level CLI execution."""

    def test_top_level_codex_target_generates_skill_artifacts(
        self, sample_python_project
    ):
        """Top-level CLI should generate Codex artifacts when --target codex is set."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["--target", "codex", "--no-git", str(sample_python_project)],
        )

        assert result.exit_code == 0, result.output
        assert (sample_python_project / "AGENTS.md").exists()
        assert not (sample_python_project / "CLAUDE.md").exists()

        skills_root = sample_python_project / ".agents" / "skills"
        if skills_root.exists():
            skill_files = list(skills_root.glob("*/SKILL.md"))
            assert skill_files
