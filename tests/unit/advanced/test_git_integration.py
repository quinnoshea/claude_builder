"""
Unit tests for advanced git integration components.

Tests the sophisticated git analysis including:
- Git history analysis and insights
- Branch and merge pattern detection
- Contributor analysis and statistics
- Code evolution tracking
- Advanced git metadata extraction
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from claude_builder.utils.git import (
    AdvancedGitAnalyzer,
    BranchAnalyzer,
    CodeEvolutionTracker,
    ContributorAnalyzer,
    GitHistoryAnalyzer,
    GitInsights,
)


@pytest.mark.skip(reason="Advanced git integration features not yet implemented")
class TestAdvancedGitAnalyzer:
    """Test suite for AdvancedGitAnalyzer class."""

    def test_analyzer_initialization(self, mock_git_repo):
        """Test git analyzer initialization."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        assert analyzer.repo_path == mock_git_repo
        assert analyzer.history_analyzer is not None
        assert analyzer.branch_analyzer is not None
        assert analyzer.contributor_analyzer is not None
        assert analyzer.evolution_tracker is not None

    def test_comprehensive_repository_analysis(self, mock_git_repo):
        """Test comprehensive repository analysis."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        # Mock git command outputs
        with patch("subprocess.run") as mock_run:
            # Mock git log output
            mock_run.side_effect = [
                # git log --oneline
                MagicMock(
                    returncode=0, stdout="abc123 Initial commit\ndef456 Add feature\n"
                ),
                # git branch -a
                MagicMock(
                    returncode=0, stdout="* main\n  feature/new-ui\n  origin/main\n"
                ),
                # git shortlog -sn
                MagicMock(returncode=0, stdout="  10\tJohn Doe\n   5\tJane Smith\n"),
                # git log --stat
                MagicMock(
                    returncode=0,
                    stdout=(
                        "commit abc123\nAuthor: John Doe\nDate: 2024-01-01\n\n"
                        " 2 files changed, 10 insertions(+), 2 deletions(-)\n"
                    ),
                ),
            ]

            analysis = analyzer.analyze_repository()

            assert analysis is not None
            assert analysis.total_commits > 0
            assert len(analysis.branches) > 0
            assert len(analysis.contributors) > 0

    def test_git_metadata_extraction(self, mock_git_repo):
        """Test extraction of detailed git metadata."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock detailed git log output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""commit abc123def456
Author: John Doe <john@example.com>
Date: Mon Jan 1 12:00:00 2024 +0000
Subject: Add new feature

 src/main.py    | 10 ++++++++++
 tests/test.py  |  5 +++++
 README.md      |  2 +-
 3 files changed, 16 insertions(+), 1 deletion(-)

commit def456abc789
Author: Jane Smith <jane@example.com>
Date: Sun Dec 31 15:30:00 2023 +0000
Subject: Fix bug in parser

 src/parser.py  |  3 +--
 1 file changed, 1 insertion(+), 2 deletions(-)
""",
            )

            metadata = analyzer.extract_detailed_metadata()

            assert len(metadata.commits) == 2
            assert metadata.commits[0].hash == "abc123def456"
            assert metadata.commits[0].author == "John Doe <john@example.com>"
            assert metadata.commits[0].files_changed == 3
            assert metadata.commits[0].insertions == 16
            assert metadata.commits[0].deletions == 1

    def test_repository_health_assessment(self, mock_git_repo):
        """Test repository health assessment."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        # Mock various git metrics
        with patch.object(
            analyzer.history_analyzer, "get_commit_frequency"
        ) as mock_freq:
            with patch.object(
                analyzer.branch_analyzer, "analyze_branch_health"
            ) as mock_health:
                with patch.object(
                    analyzer.contributor_analyzer, "get_contributor_distribution"
                ) as mock_contrib:

                    mock_freq.return_value = 5.2  # commits per week
                    mock_health.return_value = {
                        "stale_branches": 2,
                        "active_branches": 3,
                    }
                    mock_contrib.return_value = {
                        "bus_factor": 3,
                        "distribution_score": 0.7,
                    }

                    health = analyzer.assess_repository_health()

                    assert health.commit_frequency == 5.2
                    assert health.stale_branches == 2
                    assert health.bus_factor == 3
                    assert health.overall_score > 0


@pytest.mark.skip(reason="Git history analysis features not yet implemented")
class TestGitHistoryAnalyzer:
    """Test suite for GitHistoryAnalyzer class."""

    def test_commit_frequency_analysis(self, mock_git_repo):
        """Test commit frequency analysis."""
        analyzer = GitHistoryAnalyzer(mock_git_repo)

        # Mock git log with dates
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""2024-01-15 abc123 Commit 1
2024-01-14 def456 Commit 2
2024-01-14 ghi789 Commit 3
2024-01-10 jkl012 Commit 4
2024-01-08 mno345 Commit 5
2024-01-01 pqr678 Commit 6
""",
            )

            frequency = analyzer.analyze_commit_frequency()

            assert frequency.total_commits == 6
            assert frequency.commits_per_day > 0
            assert frequency.commits_per_week > 0
            assert len(frequency.daily_distribution) > 0

    def test_commit_pattern_detection(self, mock_git_repo):
        """Test detection of commit patterns."""
        analyzer = GitHistoryAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock commit messages with patterns
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""feat: add new user authentication
fix: resolve login issue
docs: update README
feat: implement user dashboard
fix: correct typo in validation
test: add unit tests for auth
feat: add password reset
refactor: clean up auth module
""",
            )

            patterns = analyzer.detect_commit_patterns()

            assert "feat" in patterns.conventional_commits
            assert "fix" in patterns.conventional_commits
            assert "docs" in patterns.conventional_commits
            assert patterns.conventional_commits["feat"] == 3
            assert patterns.conventional_commits["fix"] == 2
            assert patterns.follows_convention is True

    def test_release_cycle_analysis(self, mock_git_repo):
        """Test release cycle analysis."""
        analyzer = GitHistoryAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git tag output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""v1.0.0 2024-01-01
v1.1.0 2024-02-01
v1.2.0 2024-03-01
v2.0.0 2024-04-01
""",
            )

            releases = analyzer.analyze_release_cycles()

            assert len(releases.versions) == 4
            assert releases.average_cycle_days > 0
            assert releases.version_pattern == "semantic"

    def test_hotfix_analysis(self, mock_git_repo):
        """Test hotfix and emergency commit analysis."""
        analyzer = GitHistoryAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock commit data with hotfix patterns
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""abc123 2024-01-15T10:00:00 hotfix: critical security patch
def456 2024-01-14T14:30:00 feat: add new feature
ghi789 2024-01-14T16:45:00 fix: urgent production fix
jkl012 2024-01-13T09:15:00 docs: update docs
mno345 2024-01-12T23:55:00 hotfix: fix payment processing
""",
            )

            hotfix_analysis = analyzer.analyze_hotfixes()

            assert hotfix_analysis.total_hotfixes == 2
            assert hotfix_analysis.hotfix_frequency > 0
            assert len(hotfix_analysis.hotfix_times) > 0

    def test_code_churn_analysis(self, mock_git_repo):
        """Test code churn analysis."""
        analyzer = GitHistoryAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git log --stat output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""commit abc123
Date: 2024-01-15
 src/main.py     | 25 +++++++++++++++++++++++++
 src/utils.py    | 10 ++++++++++
 tests/test.py   | 15 +++++++++++++++
 3 files changed, 50 insertions(+)

commit def456
Date: 2024-01-14
 src/main.py     | 5 +++--
 src/parser.py   | 20 --------------------
 2 files changed, 3 insertions(+), 22 deletions(-)
""",
            )

            churn = analyzer.analyze_code_churn()

            assert churn.total_additions > 0
            assert churn.total_deletions > 0
            assert "src/main.py" in churn.file_churn
            assert churn.churn_rate > 0


@pytest.mark.skip(reason="Git branch analysis features not yet implemented")
class TestBranchAnalyzer:
    """Test suite for BranchAnalyzer class."""

    def test_branch_strategy_detection(self, mock_git_repo):
        """Test detection of branching strategy."""
        analyzer = BranchAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock branch listing
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""* main
  develop
  feature/user-auth
  feature/payment-integration
  hotfix/security-patch
  release/v2.0.0
  origin/main
  origin/develop
""",
            )

            strategy = analyzer.detect_branching_strategy()

            assert strategy.strategy_type == "gitflow"
            assert "main" in strategy.permanent_branches
            assert "develop" in strategy.permanent_branches
            assert len(strategy.feature_branches) == 2
            assert len(strategy.release_branches) == 1
            assert len(strategy.hotfix_branches) == 1

    def test_merge_pattern_analysis(self, mock_git_repo):
        """Test merge pattern analysis."""
        analyzer = BranchAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git log with merge commits
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""abc123 Merge pull request #45 from feature/user-auth
def456 Regular commit
ghi789 Merge branch 'hotfix/security-fix' into main
jkl012 Another regular commit
mno345 Merge pull request #46 from feature/dashboard
""",
            )

            patterns = analyzer.analyze_merge_patterns()

            assert patterns.total_merges == 3
            assert patterns.pull_request_merges == 2
            assert patterns.direct_merges == 1
            assert patterns.merge_frequency > 0

    def test_branch_lifecycle_analysis(self, mock_git_repo):
        """Test branch lifecycle analysis."""
        analyzer = BranchAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock branch creation and merge data
            mock_run.side_effect = [
                # Branch creation dates
                MagicMock(
                    returncode=0,
                    stdout="feature/auth 2024-01-10\nfeature/dashboard 2024-01-15\n",
                ),
                # Branch merge dates
                MagicMock(
                    returncode=0,
                    stdout="feature/auth 2024-01-20\nfeature/dashboard 2024-01-25\n",
                ),
            ]

            lifecycle = analyzer.analyze_branch_lifecycle()

            assert "feature/auth" in lifecycle.branch_lifespans
            assert "feature/dashboard" in lifecycle.branch_lifespans
            assert lifecycle.branch_lifespans["feature/auth"] == 10  # days
            assert lifecycle.average_lifespan > 0

    def test_stale_branch_detection(self, mock_git_repo):
        """Test detection of stale branches."""
        analyzer = BranchAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock branch last activity
            current_date = datetime.now()
            old_date = current_date - timedelta(days=90)
            recent_date = current_date - timedelta(days=5)

            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=f"""feature/old-feature {old_date.strftime('%Y-%m-%d')}
feature/recent-feature {recent_date.strftime('%Y-%m-%d')}
main {recent_date.strftime('%Y-%m-%d')}
""",
            )

            stale_branches = analyzer.detect_stale_branches(threshold_days=30)

            assert "feature/old-feature" in stale_branches.stale_branches
            assert "feature/recent-feature" not in stale_branches.stale_branches
            assert "main" not in stale_branches.stale_branches
            assert stale_branches.stale_count == 1


@pytest.mark.skip(reason="Git contributor analysis features not yet implemented")
class TestContributorAnalyzer:
    """Test suite for ContributorAnalyzer class."""

    def test_contributor_statistics(self, mock_git_repo):
        """Test contributor statistics analysis."""
        analyzer = ContributorAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git shortlog output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""   50\tJohn Doe <john@example.com>
   30\tJane Smith <jane@example.com>
   15\tBob Johnson <bob@example.com>
    5\tAlice Brown <alice@example.com>
""",
            )

            stats = analyzer.analyze_contributor_statistics()

            assert stats.total_contributors == 4
            assert stats.total_commits == 100
            assert stats.top_contributor == "John Doe <john@example.com>"
            assert stats.contribution_distribution["John Doe <john@example.com>"] == 50

    def test_bus_factor_calculation(self, mock_git_repo):
        """Test bus factor calculation."""
        analyzer = ContributorAnalyzer(mock_git_repo)

        # Mock contributor distribution
        with patch.object(analyzer, "analyze_contributor_statistics") as mock_stats:
            mock_stats.return_value = MagicMock(
                contribution_distribution={
                    "John Doe": 60,  # 60% of commits
                    "Jane Smith": 25,  # 25% of commits
                    "Bob Johnson": 10,  # 10% of commits
                    "Alice Brown": 5,  # 5% of commits
                },
                total_commits=100,
            )

            bus_factor = analyzer.calculate_bus_factor()

            # Bus factor should be 2 (John + Jane > 50% of commits)
            assert bus_factor.factor == 2
            assert bus_factor.risk_level == "medium"

    def test_contributor_activity_timeline(self, mock_git_repo):
        """Test contributor activity timeline analysis."""
        analyzer = ContributorAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git log with author and date
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""2024-01-15 John Doe
2024-01-14 Jane Smith
2024-01-14 John Doe
2024-01-10 Bob Johnson
2024-01-08 John Doe
2024-01-05 Jane Smith
""",
            )

            timeline = analyzer.analyze_activity_timeline()

            assert "John Doe" in timeline.contributor_activity
            assert "Jane Smith" in timeline.contributor_activity
            assert "Bob Johnson" in timeline.contributor_activity
            assert len(timeline.contributor_activity["John Doe"]) == 3
            assert len(timeline.contributor_activity["Jane Smith"]) == 2

    def test_expertise_areas_analysis(self, mock_git_repo):
        """Test analysis of contributor expertise areas."""
        analyzer = ContributorAnalyzer(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git log with file changes per author
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""John Doe:
  src/backend/auth.py: 25 commits
  src/backend/models.py: 15 commits
  tests/test_auth.py: 10 commits

Jane Smith:
  src/frontend/components/: 30 commits
  src/frontend/styles/: 20 commits
  docs/: 15 commits

Bob Johnson:
  deployment/docker/: 20 commits
  deployment/k8s/: 15 commits
  scripts/: 10 commits
""",
            )

            expertise = analyzer.analyze_expertise_areas()

            assert "backend" in expertise["John Doe"]
            assert "frontend" in expertise["Jane Smith"]
            assert "deployment" in expertise["Bob Johnson"]


@pytest.mark.skip(reason="Code evolution tracking features not yet implemented")
class TestCodeEvolutionTracker:
    """Test suite for CodeEvolutionTracker class."""

    def test_file_evolution_tracking(self, mock_git_repo):
        """Test tracking of individual file evolution."""
        tracker = CodeEvolutionTracker(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock git log for specific file
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""commit abc123
Date: 2024-01-15
Author: John Doe
 10 insertions(+), 5 deletions(-)

commit def456
Date: 2024-01-10
Author: Jane Smith
 25 insertions(+), 2 deletions(-)

commit ghi789
Date: 2024-01-05
Author: John Doe
 50 insertions(+), 0 deletions(-)
""",
            )

            evolution = tracker.track_file_evolution("src/main.py")

            assert len(evolution.commits) == 3
            assert evolution.total_changes == 3
            assert evolution.total_additions == 85
            assert evolution.total_deletions == 7
            assert len(evolution.contributors) == 2

    def test_architecture_evolution_analysis(self, mock_git_repo):
        """Test analysis of architecture evolution over time."""
        tracker = CodeEvolutionTracker(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock directory structure changes over time
            mock_run.side_effect = [
                # Initial structure
                MagicMock(returncode=0, stdout="src/\ntests/\nREADME.md\n"),
                # After 6 months
                MagicMock(
                    returncode=0,
                    stdout="src/\nsrc/models/\nsrc/views/\ntests/\ndocs/\nREADME.md\n",
                ),
                # After 1 year
                MagicMock(
                    returncode=0,
                    stdout="backend/\nfrontend/\nshared/\ntests/\ndocs/\ndeployment/\nREADME.md\n",
                ),
            ]

            evolution = tracker.analyze_architecture_evolution()

            assert len(evolution.snapshots) == 3
            assert evolution.complexity_trend == "increasing"
            assert evolution.major_restructures > 0

    def test_dependency_evolution_tracking(self, mock_git_repo):
        """Test tracking of dependency changes over time."""
        tracker = CodeEvolutionTracker(mock_git_repo)

        with patch("subprocess.run") as mock_run:
            # Mock requirements.txt changes
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""commit abc123 2024-01-15
+fastapi==0.100.0
+uvicorn==0.23.0

commit def456 2024-01-10
+requests==2.31.0
+pydantic==2.0.0

commit ghi789 2024-01-05
+click==8.1.0
""",
            )

            deps_evolution = tracker.track_dependency_evolution()

            assert len(deps_evolution.dependency_additions) == 5
            assert "fastapi" in deps_evolution.dependency_timeline
            assert (
                deps_evolution.dependency_timeline["fastapi"]["added"] == "2024-01-15"
            )

    def test_code_quality_trends(self, mock_git_repo):
        """Test tracking of code quality trends over time."""
        tracker = CodeEvolutionTracker(mock_git_repo)

        # Mock quality metrics over time
        with patch.object(tracker, "_extract_quality_metrics") as mock_metrics:
            mock_metrics.side_effect = [
                {
                    "complexity": 15,
                    "test_coverage": 60,
                    "documentation": 40,
                },  # 3 months ago
                {
                    "complexity": 18,
                    "test_coverage": 75,
                    "documentation": 55,
                },  # 2 months ago
                {"complexity": 22, "test_coverage": 85, "documentation": 70},  # current
            ]

            trends = tracker.analyze_quality_trends()

            assert trends.complexity_trend == "increasing"
            assert trends.test_coverage_trend == "improving"
            assert trends.documentation_trend == "improving"
            assert trends.overall_quality_trend == "mixed"


@pytest.mark.skip(reason="Git insights features not yet implemented")
class TestGitInsights:
    """Test suite for GitInsights class."""

    def test_insights_generation(self, mock_git_repo):
        """Test generation of actionable git insights."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        # Mock analysis results
        with patch.object(analyzer, "analyze_repository") as mock_analyze:
            mock_analyze.return_value = MagicMock(
                total_commits=150,
                active_contributors=3,
                stale_branches=5,
                bus_factor=2,
                test_coverage_trend="declining",
                hotfix_frequency=0.2,  # per week
            )

            insights = GitInsights.generate_insights(analyzer)

            assert len(insights.recommendations) > 0
            assert len(insights.warnings) > 0
            assert insights.overall_health_score > 0

            # Check for specific insights
            recommendations = [r.message for r in insights.recommendations]
            assert any("stale branch" in r.lower() for r in recommendations)
            assert any("bus factor" in r.lower() for r in recommendations)

    def test_development_workflow_insights(self, mock_git_repo):
        """Test insights about development workflow."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)

        insights = GitInsights(analyzer)

        with patch.object(
            analyzer.branch_analyzer, "detect_branching_strategy"
        ) as mock_strategy:
            with patch.object(
                analyzer.history_analyzer, "detect_commit_patterns"
            ) as mock_patterns:

                mock_strategy.return_value = MagicMock(
                    strategy_type="feature_branch", follows_convention=False
                )

                mock_patterns.return_value = MagicMock(
                    follows_convention=False,
                    conventional_commits={"feat": 5, "fix": 3, "random": 10},
                )

                workflow_insights = insights.analyze_workflow_patterns()

                assert len(workflow_insights.suggestions) > 0
                suggestions = [s.lower() for s in workflow_insights.suggestions]
                assert any("conventional commit" in s for s in suggestions)
                assert any("branching strategy" in s for s in suggestions)

    def test_performance_insights(self, mock_git_repo):
        """Test insights about repository performance."""
        analyzer = AdvancedGitAnalyzer(mock_git_repo)
        insights = GitInsights(analyzer)

        with patch.object(
            analyzer.evolution_tracker, "analyze_quality_trends"
        ) as mock_trends:
            mock_trends.return_value = MagicMock(
                complexity_trend="increasing",
                performance_trend="declining",
                large_files=["data/large_dataset.csv", "assets/video.mp4"],
            )

            perf_insights = insights.analyze_performance_indicators()

            assert len(perf_insights.optimizations) > 0
            optimizations = [o.lower() for o in perf_insights.optimizations]
            assert any("large file" in o for o in optimizations)
            assert any("complexity" in o for o in optimizations)
