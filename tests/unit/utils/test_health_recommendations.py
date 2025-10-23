"""Tests for health recommendations module."""

from unittest.mock import patch

from claude_builder.utils.health_recommendations import (
    RecommendationProvider,
    format_recommendation,
    get_recommendation_for_tool,
)


class TestRecommendationProvider:
    """Test RecommendationProvider functionality."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = RecommendationProvider()
        assert provider.platform in ["linux", "darwin", "windows"]

    def test_get_tool_recommendation_git(self):
        """Test Git recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("git")

        assert "message" in rec
        assert rec["message"]  # Not empty
        # Should have command or fallback URL
        assert rec.get("command") is not None or "git-scm.com" in rec["message"]

    def test_get_tool_recommendation_terraform(self):
        """Test Terraform recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("terraform")

        assert "message" in rec
        assert "terraform" in rec["message"].lower()

    def test_get_tool_recommendation_kubectl(self):
        """Test kubectl recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("kubectl")

        assert "message" in rec
        assert "kubectl" in rec["message"].lower()

    def test_get_tool_recommendation_docker(self):
        """Test Docker recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("docker")

        assert "message" in rec
        assert "docker" in rec["message"].lower()

    def test_get_tool_recommendation_helm(self):
        """Test Helm recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("helm")

        assert "message" in rec
        assert "helm" in rec["message"].lower()

    def test_get_tool_recommendation_ansible(self):
        """Test Ansible recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("ansible")

        assert "message" in rec
        assert "ansible" in rec["message"].lower()
        assert "pip install ansible" in rec.get("command", "")

    def test_get_tool_recommendation_aws_cli(self):
        """Test AWS CLI recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("aws")

        assert "message" in rec
        assert "aws" in rec["message"].lower()

    def test_get_tool_recommendation_gcloud(self):
        """Test Google Cloud CLI recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("gcloud")

        assert "message" in rec
        assert "cloud" in rec["message"].lower()

    def test_get_tool_recommendation_azure_cli(self):
        """Test Azure CLI recommendation retrieval."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("az")

        assert "message" in rec
        assert "azure" in rec["message"].lower()

    def test_get_tool_recommendation_unknown_tool(self):
        """Test recommendation for unknown tool."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("unknown_tool_xyz")

        assert "message" in rec
        assert "unknown_tool_xyz" in rec["message"]
        assert rec.get("command") is None

    def test_get_multiple_tools_summary_empty(self):
        """Test summary for no missing tools."""
        provider = RecommendationProvider()
        summary = provider.get_multiple_tools_summary([])

        assert "all tools" in summary.lower()

    def test_get_multiple_tools_summary_single(self):
        """Test summary for single missing tool."""
        provider = RecommendationProvider()
        summary = provider.get_multiple_tools_summary(["terraform"])

        assert "missing tool" in summary.lower()
        assert "terraform" in summary

    def test_get_multiple_tools_summary_multiple(self):
        """Test summary for multiple missing tools."""
        provider = RecommendationProvider()
        summary = provider.get_multiple_tools_summary(
            ["terraform", "kubectl", "docker"]
        )

        assert "missing 3 tools" in summary.lower()
        assert "terraform" in summary
        assert "kubectl" in summary
        assert "docker" in summary

    @patch("platform.system", return_value="Linux")
    def test_platform_specific_recommendations_linux(self, _mock_platform):
        """Test that Linux-specific recommendations are provided."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("terraform")

        assert "message" in rec
        # Linux should have apt-get or similar
        if rec.get("command"):
            assert "apt" in rec["command"] or "wget" in rec["command"]

    @patch("platform.system", return_value="Darwin")
    def test_platform_specific_recommendations_macos(self, _mock_platform):
        """Test that macOS-specific recommendations are provided."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("terraform")

        assert "message" in rec
        # macOS should mention brew
        if rec.get("command"):
            assert "brew" in rec["command"]

    @patch("platform.system", return_value="Windows")
    def test_platform_specific_recommendations_windows(self, _mock_platform):
        """Test that Windows-specific recommendations are provided."""
        provider = RecommendationProvider()
        rec = provider.get_tool_recommendation("terraform")

        assert "message" in rec
        # Windows should mention choco or winget
        if rec.get("command"):
            assert "choco" in rec["command"] or "winget" in rec["command"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_recommendation_for_tool(self):
        """Test get_recommendation_for_tool function."""
        rec = get_recommendation_for_tool("git")

        assert "message" in rec
        assert isinstance(rec, dict)

    def test_format_recommendation_with_command(self):
        """Test format_recommendation with command."""
        rec = {"message": "Install tool", "command": "apt-get install tool"}
        formatted = format_recommendation("tool", rec)

        assert "Install tool" in formatted
        assert "apt-get install tool" in formatted

    def test_format_recommendation_without_command(self):
        """Test format_recommendation without command."""
        rec = {"message": "Visit website to install"}
        formatted = format_recommendation("tool", rec)

        assert "Visit website to install" in formatted
        assert "Command:" not in formatted

    def test_format_recommendation_fetch_if_not_provided(self):
        """Test that format_recommendation fetches recommendation if not provided."""
        formatted = format_recommendation("git")

        assert len(formatted) > 0
        assert "git" in formatted.lower() or "install" in formatted.lower()
