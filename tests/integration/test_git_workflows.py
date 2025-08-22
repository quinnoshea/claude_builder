"""
Integration tests for git workflow integration.

Tests the complete git integration including:
- Git repository analysis workflows
- Integration with project analysis
- Git metadata extraction and processing
- Branch analysis and insights
- Git history integration with documentation generation
"""

from unittest.mock import Mock, patch

import pytest

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.generator import DocumentGenerator

# from claude_builder.utils.git import AdvancedGitAnalyzer  # Not yet implemented


class TestGitAnalysisIntegration:
    """Test suite for git analysis integration."""

    def test_git_integrated_project_analysis(self, mock_git_repo):
        """Test project analysis with git integration."""
        # Create test files in the git repository
        (mock_git_repo / "main.py").write_text("print('Hello World')")
        (mock_git_repo / "requirements.txt").write_text("fastapi\nuvicorn")

        # Use current ProjectAnalyzer API
        analyzer = ProjectAnalyzer()
        analysis_result = analyzer.analyze(mock_git_repo)

        # Verify analysis worked on git repository
        assert analysis_result.project_path == mock_git_repo
        assert analysis_result.language_info.primary == "python"
        # Note: Git integration features not yet implemented in current codebase
        # This test verifies analyzer works with git repositories

    @pytest.mark.skip(reason="Git history integration not yet implemented")
    def test_git_history_documentation_generation(self, mock_git_repo):
        """Test documentation generation with git history integration."""
        with patch("subprocess.run") as mock_run:
            # Mock detailed git history
            mock_run.side_effect = [
                # Git log with dates and authors
                Mock(
                    returncode=0,
                    stdout="""commit abc123def456
Author: John Doe <john@example.com>
Date: Mon Jan 15 12:00:00 2024 +0000
Subject: Add new authentication system

 src/auth.py       | 150 +++++++++++++++++++++++++++++++
 tests/test_auth.py | 75 ++++++++++++++++
 README.md         |  5 +++
 3 files changed, 230 insertions(+)

commit def456abc789
Author: Jane Smith <jane@example.com>
Date: Sun Jan 14 15:30:00 2024 +0000
Subject: Initial project setup

 src/main.py       | 25 ++++++++++++++++
 requirements.txt  |  3 +++
 .gitignore       | 10 +++++++
 3 files changed, 38 insertions(+)
""",
                ),
                # Git shortlog for contributors
                Mock(returncode=0, stdout="   2\tJohn Doe\n   1\tJane Smith"),
                # Git tag list
                Mock(returncode=0, stdout="v1.0.0\nv1.1.0"),
            ]

            # Analyze git repository
            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)
            git_analysis = git_analyzer.analyze_repository()

            # Create project analysis with git data
            project_analyzer = ProjectAnalyzer(mock_git_repo)
            analysis_result = project_analyzer.analyze()
            analysis_result.git_analysis = git_analysis

            # Generate documentation with git integration
            generator = DocumentGenerator(analysis_result)

            # Create template that uses git information
            git_template = """# {{ project_name }} - Development History

## Project Overview
Type: {{ project_type }}
Total Commits: {{ git_analysis.total_commits }}

## Contributors
{% for contributor in git_analysis.contributors %}
- {{ contributor.name }}: {{ contributor.commits }} commits
{% endfor %}

## Recent Development
{% for commit in git_analysis.recent_commits %}
- {{ commit.date }}: {{ commit.message }} ({{ commit.author }})
{% endfor %}

## Release History
{% for release in git_analysis.releases %}
- {{ release.tag }}: {{ release.date }}
{% endfor %}
"""

            rendered_content = generator.render_template(
                git_template,
                {
                    "project_name": analysis_result.project_info.name,
                    "project_type": analysis_result.project_info.project_type,
                    "git_analysis": git_analysis,
                },
            )

            # Should include git-derived content
            assert "Development History" in rendered_content
            assert "John Doe" in rendered_content
            assert "Jane Smith" in rendered_content
            assert "authentication system" in rendered_content

    @pytest.mark.skip(reason="Git branch analysis not yet implemented")
    def test_git_branch_analysis_integration(self, mock_git_repo):
        """Test integration of git branch analysis."""
        with patch("subprocess.run") as mock_run:
            # Mock branch analysis commands
            mock_run.side_effect = [
                # Git branch listing with remotes
                Mock(
                    returncode=0,
                    stdout="""* main
  develop
  feature/user-authentication
  feature/api-improvements
  hotfix/security-patch
  origin/main
  origin/develop
  origin/feature/user-authentication
""",
                ),
                # Git log for branch creation dates
                Mock(
                    returncode=0,
                    stdout="""feature/user-authentication 2024-01-10
feature/api-improvements 2024-01-12
hotfix/security-patch 2024-01-15
""",
                ),
                # Git merge information
                Mock(
                    returncode=0,
                    stdout="""abc123 Merge pull request #45 from feature/user-authentication
def456 Merge branch 'hotfix/security-patch' into main
ghi789 Merge pull request #46 from feature/api-improvements
""",
                ),
            ]

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)
            branch_analysis = git_analyzer.branch_analyzer.analyze_branches()

            # Should detect branching strategy
            assert branch_analysis.strategy_type in ["gitflow", "feature_branch"]
            assert len(branch_analysis.feature_branches) >= 2
            assert len(branch_analysis.hotfix_branches) >= 1

            # Should provide branch lifecycle information
            assert len(branch_analysis.branch_lifespans) > 0
            assert branch_analysis.average_lifespan > 0

    @pytest.mark.skip(reason="Git contributor analysis not yet implemented")
    def test_git_contributor_analysis_integration(self, mock_git_repo):
        """Test integration of git contributor analysis."""
        with patch("subprocess.run") as mock_run:
            # Mock contributor analysis commands
            mock_run.side_effect = [
                # Git shortlog for contributor stats
                Mock(
                    returncode=0,
                    stdout="""  150\tJohn Doe <john@example.com>
   75\tJane Smith <jane@example.com>
   25\tBob Johnson <bob@example.com>
   10\tAlice Brown <alice@example.com>
""",
                ),
                # Git log with file changes per author
                Mock(
                    returncode=0,
                    stdout="""John Doe:
  src/auth/: 45 commits
  src/api/: 30 commits
  tests/: 25 commits

Jane Smith:
  frontend/: 35 commits
  docs/: 20 commits
  tests/: 15 commits

Bob Johnson:
  deployment/: 15 commits
  scripts/: 10 commits

Alice Brown:
  docs/: 8 commits
  README.md: 2 commits
""",
                ),
                # Git log for activity timeline
                Mock(
                    returncode=0,
                    stdout="""2024-01-15 John Doe
2024-01-15 Jane Smith
2024-01-14 John Doe
2024-01-14 Bob Johnson
2024-01-13 John Doe
2024-01-12 Jane Smith
""",
                ),
            ]

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)
            contributor_analysis = (
                git_analyzer.contributor_analyzer.analyze_contributors()
            )

            # Should analyze contributor statistics
            assert contributor_analysis.total_contributors == 4
            assert contributor_analysis.top_contributor == "John Doe <john@example.com>"
            assert contributor_analysis.bus_factor >= 2

            # Should identify expertise areas
            assert "auth" in contributor_analysis.expertise_areas["John Doe"]
            assert "frontend" in contributor_analysis.expertise_areas["Jane Smith"]
            assert "deployment" in contributor_analysis.expertise_areas["Bob Johnson"]

    @pytest.mark.skip(reason="Git evolution tracking not yet implemented")
    def test_git_evolution_tracking_integration(self, mock_git_repo):
        """Test integration of git code evolution tracking."""
        with patch("subprocess.run") as mock_run:
            # Mock evolution tracking commands
            mock_run.side_effect = [
                # File evolution for specific file
                Mock(
                    returncode=0,
                    stdout="""commit abc123
Date: 2024-01-15
Author: John Doe
 src/main.py | 25 ++++++++++++++++++++++++-
 1 file changed, 24 insertions(+), 1 deletion(-)

commit def456
Date: 2024-01-10
Author: Jane Smith
 src/main.py | 50 ++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 50 insertions(+)
""",
                ),
                # Architecture evolution
                Mock(
                    returncode=0,
                    stdout="""2024-01-01: src/ tests/ README.md
2024-01-08: src/ src/models/ src/views/ tests/ docs/ README.md
2024-01-15: backend/ frontend/ shared/ tests/ docs/ deployment/ README.md
""",
                ),
                # Dependency changes
                Mock(
                    returncode=0,
                    stdout="""commit abc123 2024-01-15
+fastapi==0.100.0
+uvicorn==0.23.0

commit def456 2024-01-10
+click==8.1.0
+requests==2.31.0

commit ghi789 2024-01-05
+pytest==7.4.0
""",
                ),
            ]

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)
            evolution_tracker = git_analyzer.evolution_tracker

            # Track file evolution
            file_evolution = evolution_tracker.track_file_evolution("src/main.py")
            assert file_evolution.total_changes == 2
            assert file_evolution.total_additions == 74
            assert len(file_evolution.contributors) == 2

            # Track dependency evolution
            deps_evolution = evolution_tracker.track_dependency_evolution()
            assert len(deps_evolution.dependency_additions) >= 5
            assert "fastapi" in deps_evolution.dependency_timeline

    @pytest.mark.skip(reason="Git insights generation not yet implemented")
    def test_git_insights_generation_integration(self, mock_git_repo):
        """Test integration of git insights generation."""
        with patch("subprocess.run") as mock_run:
            # Mock comprehensive git data for insights
            mock_run.side_effect = [
                # Repository overview
                Mock(returncode=0, stdout="125 commits, 3 branches, 4 contributors"),
                # Health indicators
                Mock(
                    returncode=0,
                    stdout="""Stale branches: 2
Average commit frequency: 5.2 per week
Bus factor: 2
Test coverage trend: improving
Recent hotfixes: 1 in last month
""",
                ),
                # Workflow patterns
                Mock(
                    returncode=0,
                    stdout="""Branching strategy: gitflow
Conventional commits: 65%
Average PR merge time: 2.3 days
Code review coverage: 85%
""",
                ),
            ]

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)

            # Generate comprehensive insights
            with patch.object(git_analyzer, "analyze_repository") as mock_analyze:
                mock_analyze.return_value = Mock(
                    total_commits=125,
                    active_contributors=3,
                    stale_branches=2,
                    bus_factor=2,
                    commit_frequency=5.2,
                    follows_conventions=False,
                    test_coverage_trend="improving",
                )

                from claude_builder.utils.git import GitInsights

                insights = GitInsights.generate_insights(git_analyzer)

                # Should provide actionable insights
                assert len(insights.recommendations) > 0
                assert len(insights.warnings) >= 0
                assert 0 <= insights.overall_health_score <= 100

                # Should identify specific issues and suggestions
                recommendations = [r.message.lower() for r in insights.recommendations]
                assert any("stale branch" in r for r in recommendations)
                assert any("bus factor" in r for r in recommendations)


class TestGitProjectIntegration:
    """Test suite for git integration with project analysis."""

    @pytest.mark.skip(reason="Git-aware classification not yet implemented")
    def test_git_aware_project_classification(self, mock_git_repo):
        """Test project classification with git history awareness."""
        with patch("subprocess.run") as mock_run:
            # Mock git log showing project evolution
            mock_run.side_effect = [
                Mock(
                    returncode=0,
                    stdout="""commit abc123
Date: 2024-01-15
Files: package.json src/App.js src/components/

commit def456
Date: 2024-01-10
Files: requirements.txt src/main.py

commit ghi789
Date: 2024-01-05
Files: Cargo.toml src/main.rs
""",
                ),
                # Current project state
                Mock(returncode=0, stdout="On branch main"),
            ]

            # Create project analyzer with git integration
            analyzer = ProjectAnalyzer(mock_git_repo, include_git=True)

            # Mock file discovery to show current state
            with patch.object(analyzer, "_discover_project_files") as mock_discover:
                mock_discover.return_value = {
                    "package.json": {"type": "config", "language": "javascript"},
                    "src/App.js": {"type": "source", "language": "javascript"},
                    "src/components/Header.js": {
                        "type": "source",
                        "language": "javascript",
                    },
                }

                analysis_result = analyzer.analyze()

                # Should detect current project type
                assert analysis_result.project_info.project_type == "javascript"

                # Should include git-based insights about project evolution
                if hasattr(analysis_result, "git_insights"):
                    assert "evolution" in analysis_result.git_insights

    @pytest.mark.skip(reason="Git-based documentation context not yet implemented")
    def test_git_based_documentation_context(self, mock_git_repo):
        """Test documentation generation with git-based context."""
        with patch("subprocess.run") as mock_run:
            # Mock git information for documentation context
            mock_run.side_effect = [
                # Recent commits for changelog
                Mock(
                    returncode=0,
                    stdout="""v2.0.0 abc123 2024-01-15 Add user authentication
v1.1.0 def456 2024-01-10 Improve API performance
v1.0.0 ghi789 2024-01-05 Initial release
""",
                ),
                # Contributors for acknowledgments
                Mock(
                    returncode=0,
                    stdout="  50\tJohn Doe\n  25\tJane Smith\n  10\tBob Johnson",
                ),
                # Branch info for development status
                Mock(returncode=0, stdout="* main\n  develop\n  feature/new-ui"),
            ]

            # Analyze project with git context
            analyzer = ProjectAnalyzer(mock_git_repo, include_git=True)
            analysis_result = analyzer.analyze()

            # Add mock git analysis
            analysis_result.git_analysis = Mock(
                recent_releases=[
                    {
                        "tag": "v2.0.0",
                        "date": "2024-01-15",
                        "description": "Add user authentication",
                    },
                    {
                        "tag": "v1.1.0",
                        "date": "2024-01-10",
                        "description": "Improve API performance",
                    },
                    {
                        "tag": "v1.0.0",
                        "date": "2024-01-05",
                        "description": "Initial release",
                    },
                ],
                contributors=[
                    {"name": "John Doe", "commits": 50},
                    {"name": "Jane Smith", "commits": 25},
                    {"name": "Bob Johnson", "commits": 10},
                ],
                active_branches=["main", "develop", "feature/new-ui"],
            )

            # Generate documentation with git context
            generator = DocumentGenerator(analysis_result)

            # Template using git information
            git_aware_template = """# {{ project_name }}

## Recent Changes
{% for release in git_analysis.recent_releases %}
- **{{ release.tag }}** ({{ release.date }}): {{ release.description }}
{% endfor %}

## Contributors
{% for contributor in git_analysis.contributors %}
- {{ contributor.name }} ({{ contributor.commits }} commits)
{% endfor %}

## Development Status
Active branches: {{ git_analysis.active_branches | join(', ') }}

## Getting Started
This {{ project_type }} project can be set up by following these steps...
"""

            rendered_content = generator.render_template(
                git_aware_template,
                {
                    "project_name": analysis_result.project_info.name,
                    "project_type": analysis_result.project_info.project_type,
                    "git_analysis": analysis_result.git_analysis,
                },
            )

            # Should include git-derived content
            assert "Recent Changes" in rendered_content
            assert "v2.0.0" in rendered_content
            assert "John Doe" in rendered_content
            assert "feature/new-ui" in rendered_content

    @pytest.mark.skip(reason="Git workflow recommendations not yet implemented")
    def test_git_workflow_recommendations(self, mock_git_repo):
        """Test git workflow recommendations integration."""
        with patch("subprocess.run") as mock_run:
            # Mock git workflow analysis
            mock_run.side_effect = [
                # Branch patterns showing inconsistent workflow
                Mock(
                    returncode=0,
                    stdout="""main
feature/new-ui
feature-api-update
fix-bug-123
urgent-hotfix
random-branch-name
""",
                ),
                # Commit message patterns
                Mock(
                    returncode=0,
                    stdout="""feat: add user authentication
fix: resolve login issue
update readme
random commit message
WIP: working on feature
Fix bug
""",
                ),
                # Merge patterns
                Mock(
                    returncode=0,
                    stdout="""Merge pull request #45
Merge branch 'feature/new-ui'
Direct merge from fix-bug-123
""",
                ),
            ]

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo)

            # Mock workflow analysis results
            with patch.object(
                git_analyzer.branch_analyzer, "detect_branching_strategy"
            ) as mock_strategy:
                with patch.object(
                    git_analyzer.history_analyzer, "detect_commit_patterns"
                ) as mock_patterns:

                    mock_strategy.return_value = Mock(
                        strategy_type="inconsistent",
                        follows_convention=False,
                        recommended_strategy="gitflow",
                    )

                    mock_patterns.return_value = Mock(
                        follows_convention=False,
                        conventional_commits={"feat": 1, "fix": 2, "random": 3},
                        recommended_format="conventional_commits",
                    )

                    # Generate workflow insights
                    from claude_builder.utils.git import GitInsights

                    insights = GitInsights(git_analyzer)
                    workflow_insights = insights.analyze_workflow_patterns()

                    # Should provide specific recommendations
                    assert len(workflow_insights.suggestions) > 0
                    suggestions = [s.lower() for s in workflow_insights.suggestions]
                    assert any("branching" in s for s in suggestions)
                    assert any("commit message" in s for s in suggestions)


class TestGitPerformanceIntegration:
    """Test suite for git performance integration."""

    @pytest.mark.skip(reason="AdvancedGitAnalyzer not yet implemented")
    def test_large_repository_analysis_performance(self, temp_dir):
        """Test git analysis performance with large repositories."""
        # Create mock large repository
        large_repo = temp_dir / "large_repo"
        large_repo.mkdir()
        (large_repo / ".git").mkdir()
        (large_repo / ".git" / "config").write_text(
            "[core]\nrepositoryformatversion = 0"
        )

        with patch("subprocess.run") as mock_run:
            # Mock large repository data
            mock_run.side_effect = [
                # Large commit history
                Mock(
                    returncode=0,
                    stdout="\n".join(
                        [f"commit{i} Author{i % 10} Message{i}" for i in range(1000)]
                    ),
                ),
                # Many branches
                Mock(
                    returncode=0, stdout="\n".join([f"branch-{i}" for i in range(50)])
                ),
                # Many contributors
                Mock(
                    returncode=0,
                    stdout="\n".join([f"  {100-i}\tContributor{i}" for i in range(20)]),
                ),
            ]

            import time

            start_time = time.time()

            git_analyzer = AdvancedGitAnalyzer(large_repo)
            analysis_result = git_analyzer.analyze_repository()

            end_time = time.time()
            analysis_time = end_time - start_time

            # Should complete within reasonable time
            assert analysis_time < 10.0  # Less than 10 seconds for large repo
            assert analysis_result is not None

    @pytest.mark.skip(reason="Git analysis caching not yet implemented")
    def test_git_analysis_caching_integration(self, mock_git_repo):
        """Test git analysis caching for performance."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="commit abc123\ncommit def456\ncommit ghi789"
            )

            git_analyzer = AdvancedGitAnalyzer(mock_git_repo, enable_cache=True)

            # First analysis
            start_time = time.time()
            result1 = git_analyzer.analyze_repository()
            first_analysis_time = time.time() - start_time

            # Second analysis (should use cache)
            start_time = time.time()
            result2 = git_analyzer.analyze_repository()
            second_analysis_time = time.time() - start_time

            # Cached analysis should be significantly faster
            assert second_analysis_time < first_analysis_time * 0.5
            assert result1.total_commits == result2.total_commits
