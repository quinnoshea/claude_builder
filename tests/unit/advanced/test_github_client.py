"""Tests for GitHub API client functionality."""

import os
import time

from unittest.mock import Mock, patch

import pytest
import requests

from claude_builder.utils.exceptions import ConfigError
from claude_builder.utils.github_client import (
    GITHUB_AUTH_ERROR,
    GITHUB_FILE_NOT_FOUND,
    GITHUB_INVALID_URL,
    GITHUB_NETWORK_ERROR,
    GITHUB_RATE_LIMIT_ERROR,
    GITHUB_REPO_NOT_FOUND,
    CacheEntry,
    GitHubAgentClient,
    GitHubFile,
    RateLimit,
    RepositoryInfo,
)


@pytest.fixture
def mock_session():
    """Mock requests session."""
    session = Mock(spec=requests.Session)
    session.headers = {}
    return session


@pytest.fixture
def github_client(tmp_path):
    """GitHub client with temporary cache directory."""
    cache_dir = tmp_path / "github_cache"
    return GitHubAgentClient(token="test_token", cache_dir=cache_dir)


@pytest.fixture
def mock_response():
    """Mock HTTP response."""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Used": "100",
        "X-RateLimit-Remaining": "4900",
        "X-RateLimit-Reset": str(int(time.time() + 3600)),
        "X-RateLimit-Resource": "core",
        "ETag": '"test-etag"',
    }
    response.json.return_value = {"test": "data"}
    response.text = "test content"
    response.raise_for_status = Mock()
    return response


class TestRateLimit:
    """Test RateLimit dataclass functionality."""

    def test_rate_limit_creation(self):
        """Test RateLimit creation with valid parameters."""
        reset_time = time.time() + 3600
        rate_limit = RateLimit(
            limit=5000, used=100, remaining=4900, reset_time=reset_time
        )

        assert rate_limit.limit == 5000
        assert rate_limit.used == 100
        assert rate_limit.remaining == 4900
        assert rate_limit.reset_time == reset_time
        assert rate_limit.resource == "core"  # default

    def test_reset_in_seconds(self):
        """Test reset_in_seconds property."""
        reset_time = time.time() + 3600
        rate_limit = RateLimit(
            limit=5000, used=100, remaining=4900, reset_time=reset_time
        )

        assert 3590 <= rate_limit.reset_in_seconds <= 3610  # Allow for execution time

    def test_is_near_limit(self):
        """Test is_near_limit property with different remaining values."""
        # Not near limit
        rate_limit = RateLimit(
            limit=5000, used=100, remaining=4900, reset_time=time.time() + 3600
        )
        assert not rate_limit.is_near_limit

        # Near limit
        rate_limit = RateLimit(
            limit=5000, used=4950, remaining=50, reset_time=time.time() + 3600
        )
        assert rate_limit.is_near_limit


class TestCacheEntry:
    """Test CacheEntry functionality."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation with valid data."""
        data = {"test": "data"}
        timestamp = time.time()
        cache_entry = CacheEntry(data=data, timestamp=timestamp, etag="test-etag")

        assert cache_entry.data == data
        assert cache_entry.timestamp == timestamp
        assert cache_entry.etag == "test-etag"

    def test_is_expired_fresh(self):
        """Test is_expired property with fresh entry."""
        cache_entry = CacheEntry(
            data={"test": "data"}, timestamp=time.time(), etag="test-etag"
        )
        assert not cache_entry.is_expired

    def test_is_expired_old(self):
        """Test is_expired property with old entry."""
        old_timestamp = time.time() - (7 * 3600)  # 7 hours ago
        cache_entry = CacheEntry(
            data={"test": "data"}, timestamp=old_timestamp, etag="test-etag"
        )
        assert cache_entry.is_expired

    def test_age_seconds(self):
        """Test age_seconds property."""
        timestamp = time.time() - 3600  # 1 hour ago
        cache_entry = CacheEntry(
            data={"test": "data"}, timestamp=timestamp, etag="test-etag"
        )

        assert 3590 <= cache_entry.age_seconds <= 3610  # Allow for execution time


class TestGitHubFile:
    """Test GitHubFile dataclass."""

    def test_github_file_creation(self):
        """Test GitHubFile creation with required parameters."""
        github_file = GitHubFile(
            name="test.md",
            path="agents/test.md",
            download_url="https://raw.githubusercontent.com/owner/repo/main/agents/test.md",
            sha="abc123",
            size=1024,
        )

        assert github_file.name == "test.md"
        assert github_file.path == "agents/test.md"
        assert github_file.download_url.startswith("https://raw.githubusercontent.com")
        assert github_file.sha == "abc123"
        assert github_file.size == 1024
        assert github_file.type == "file"  # default


class TestRepositoryInfo:
    """Test RepositoryInfo dataclass."""

    def test_repository_info_creation(self):
        """Test RepositoryInfo creation with required parameters."""
        repo_info = RepositoryInfo(
            owner="test-owner",
            name="test-repo",
            full_name="test-owner/test-repo",
            description="Test repository",
        )

        assert repo_info.owner == "test-owner"
        assert repo_info.name == "test-repo"
        assert repo_info.full_name == "test-owner/test-repo"
        assert repo_info.description == "Test repository"
        assert repo_info.default_branch == "main"  # default


class TestGitHubAgentClientInit:
    """Test GitHubAgentClient initialization."""

    def test_init_with_token(self, tmp_path):
        """Test client initialization with explicit token."""
        cache_dir = tmp_path / "github_cache"
        client = GitHubAgentClient(token="test_token", cache_dir=cache_dir)

        assert client.token == "test_token"
        assert client.cache_dir == cache_dir
        assert cache_dir.exists()

    def test_init_with_env_token(self, tmp_path, monkeypatch):
        """Test client initialization with environment token."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        cache_dir = tmp_path / "github_cache"
        client = GitHubAgentClient(cache_dir=cache_dir)

        assert client.token == "env_token"

    def test_init_no_token(self, tmp_path, monkeypatch):
        """Test client initialization without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        cache_dir = tmp_path / "github_cache"
        client = GitHubAgentClient(cache_dir=cache_dir)

        assert client.token is None


class TestURLParsing:
    """Test repository URL parsing functionality."""

    def test_parse_https_url(self, github_client):
        """Test parsing HTTPS GitHub URLs."""
        url = "https://github.com/owner/repo"
        owner, repo = github_client.parse_repository_url(url)

        assert owner == "owner"
        assert repo == "repo"

    def test_parse_git_url(self, github_client):
        """Test parsing git URLs."""
        url = "https://github.com/owner/repo.git"
        owner, repo = github_client.parse_repository_url(url)

        assert owner == "owner"
        assert repo == "repo"

    def test_parse_owner_repo_format(self, github_client):
        """Test parsing owner/repo format."""
        url = "owner/repo"
        owner, repo = github_client.parse_repository_url(url)

        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_url(self, github_client):
        """Test parsing invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "https://example.com/path",
            "owner",
            "",
            "https://github.com",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match=GITHUB_INVALID_URL):
                github_client.parse_repository_url(url)


class TestCaching:
    """Test caching functionality."""

    def test_cache_save_and_load(self, github_client):
        """Test saving and loading cache."""
        # Add data to cache
        cache_key = "test_key"
        test_data = {"test": "data"}
        github_client.cache[cache_key] = CacheEntry(
            data=test_data, timestamp=time.time(), etag="test-etag"
        )

        # Save cache
        github_client._save_cache()

        # Create new client and verify cache is loaded
        new_client = GitHubAgentClient(
            token="test_token", cache_dir=github_client.cache_dir
        )

        assert cache_key in new_client.cache
        assert new_client.cache[cache_key].data == test_data

    def test_cache_expiration_cleanup(self, github_client):
        """Test that expired entries are cleaned up on save."""
        # Add fresh and expired entries
        fresh_key = "fresh_key"
        expired_key = "expired_key"

        github_client.cache[fresh_key] = CacheEntry(
            data={"fresh": "data"}, timestamp=time.time(), etag="fresh-etag"
        )
        github_client.cache[expired_key] = CacheEntry(
            data={"expired": "data"},
            timestamp=time.time() - (8 * 3600),  # 8 hours ago
            etag="expired-etag",
        )

        # Save cache
        github_client._save_cache()

        # Load in new client
        new_client = GitHubAgentClient(
            token="test_token", cache_dir=github_client.cache_dir
        )

        assert fresh_key in new_client.cache
        assert expired_key not in new_client.cache

    def test_clear_cache(self, github_client):
        """Test clearing cache."""
        # Add data to cache
        github_client.cache["test_key"] = CacheEntry(
            data={"test": "data"}, timestamp=time.time()
        )
        github_client._save_cache()

        # Clear cache
        github_client.clear_cache()

        assert len(github_client.cache) == 0
        assert not (github_client.cache_dir / "api_cache.json").exists()


@pytest.mark.advanced
class TestMakeRequest:
    """Test _make_request functionality with mocking."""

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_successful_request(
        self, mock_create_session, github_client, mock_response
    ):
        """Test successful API request."""
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session
        github_client.session = mock_session

        url = "https://api.github.com/repos/owner/repo"
        data, from_cache = github_client._make_request(url)

        assert data == {"test": "data"}
        assert not from_cache
        mock_session.get.assert_called_once()

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_request_with_cache_hit(self, mock_create_session, github_client):
        """Test request with cache hit."""
        # Add cached data
        cache_key = "https://api.github.com/repos/owner/repo?{}"
        cached_data = {"cached": "data"}
        github_client.cache[cache_key] = CacheEntry(
            data=cached_data, timestamp=time.time()
        )

        url = "https://api.github.com/repos/owner/repo"
        data, from_cache = github_client._make_request(url)

        assert data == cached_data
        assert from_cache

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_request_auth_error(self, mock_create_session, github_client):
        """Test request with authentication error."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session
        github_client.session = mock_session

        url = "https://api.github.com/repos/owner/repo"

        with pytest.raises(ConfigError, match=GITHUB_AUTH_ERROR):
            github_client._make_request(url)

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_request_rate_limit_error(self, mock_create_session, github_client):
        """Test request with rate limit error."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "rate limit exceeded"
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session
        github_client.session = mock_session

        url = "https://api.github.com/repos/owner/repo"

        with pytest.raises(ConfigError, match=GITHUB_RATE_LIMIT_ERROR):
            github_client._make_request(url)

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_request_not_found(self, mock_create_session, github_client):
        """Test request with 404 error."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session
        github_client.session = mock_session

        url = "https://api.github.com/repos/owner/repo"

        with pytest.raises(ConfigError, match=GITHUB_REPO_NOT_FOUND):
            github_client._make_request(url)

    @patch("claude_builder.utils.github_client.GitHubAgentClient._create_session")
    def test_request_network_timeout(self, mock_create_session, github_client):
        """Test request with network timeout."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.Timeout()
        mock_create_session.return_value = mock_session
        github_client.session = mock_session

        url = "https://api.github.com/repos/owner/repo"

        with pytest.raises(ConfigError, match=GITHUB_NETWORK_ERROR):
            github_client._make_request(url)


@pytest.mark.advanced
class TestRepositoryOperations:
    """Test repository operations with mocking."""

    @patch("claude_builder.utils.github_client.GitHubAgentClient._make_request")
    def test_get_repository_info(self, mock_make_request, github_client):
        """Test getting repository information."""
        mock_data = {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
            "full_name": "test-owner/test-repo",
            "description": "Test repository",
            "default_branch": "main",
            "updated_at": "2023-01-01T00:00:00Z",
            "size": 1024,
            "language": "Python",
        }
        mock_make_request.return_value = (mock_data, False)

        repo_info = github_client.get_repository_info("test-owner/test-repo")

        assert isinstance(repo_info, RepositoryInfo)
        assert repo_info.owner == "test-owner"
        assert repo_info.name == "test-repo"
        assert repo_info.full_name == "test-owner/test-repo"
        assert repo_info.description == "Test repository"
        assert repo_info.language == "Python"

    @patch("claude_builder.utils.github_client.GitHubAgentClient.get_repository_info")
    @patch("claude_builder.utils.github_client.GitHubAgentClient._make_request")
    def test_list_repository_files(
        self, mock_make_request, mock_get_repo_info, github_client
    ):
        """Test listing repository files."""
        # Mock repository info
        mock_get_repo_info.return_value = RepositoryInfo(
            owner="test-owner", name="test-repo", full_name="test-owner/test-repo"
        )

        # Mock file listing response
        mock_files_data = [
            {
                "name": "agent1.md",
                "path": "agents/agent1.md",
                "type": "file",
                "download_url": "https://raw.githubusercontent.com/test-owner/test-repo/main/agents/agent1.md",
                "sha": "abc123",
                "size": 1024,
            },
            {
                "name": "agent2.md",
                "path": "agents/agent2.md",
                "type": "file",
                "download_url": "https://raw.githubusercontent.com/test-owner/test-repo/main/agents/agent2.md",
                "sha": "def456",
                "size": 2048,
            },
        ]
        mock_make_request.return_value = (mock_files_data, False)

        files = github_client.list_repository_files("test-owner/test-repo", "*.md")

        assert len(files) == 2
        assert all(isinstance(f, GitHubFile) for f in files)
        assert files[0].name == "agent1.md"
        assert files[1].name == "agent2.md"

    @patch("claude_builder.utils.github_client.GitHubAgentClient.get_repository_info")
    @patch("claude_builder.utils.github_client.requests.Session.get")
    def test_get_file_content(self, mock_get, mock_get_repo_info, github_client):
        """Test getting file content."""
        # Mock repository info
        mock_get_repo_info.return_value = RepositoryInfo(
            owner="test-owner", name="test-repo", full_name="test-owner/test-repo"
        )

        # Mock file content response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "# Agent Definition\nThis is an agent definition file."
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        content = github_client.get_file_content(
            "test-owner/test-repo", "agents/test.md"
        )

        assert "# Agent Definition" in content
        assert "This is an agent definition file." in content

    @patch("claude_builder.utils.github_client.GitHubAgentClient.get_repository_info")
    @patch("claude_builder.utils.github_client.requests.Session.get")
    def test_get_file_content_not_found(
        self, mock_get, mock_get_repo_info, github_client
    ):
        """Test getting file content for non-existent file."""
        # Mock repository info
        mock_get_repo_info.return_value = RepositoryInfo(
            owner="test-owner", name="test-repo", full_name="test-owner/test-repo"
        )

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ConfigError, match=GITHUB_FILE_NOT_FOUND):
            github_client.get_file_content("test-owner/test-repo", "nonexistent.md")


@pytest.mark.advanced
class TestIntegrationGitHubClient:
    """Integration tests for GitHub client functionality."""

    @patch("claude_builder.utils.github_client.GitHubAgentClient.list_repository_files")
    @patch("claude_builder.utils.github_client.GitHubAgentClient.get_file_content")
    def test_fetch_repository_agents_workflow(
        self, mock_get_content, mock_list_files, github_client
    ):
        """Test complete workflow of fetching repository agents."""
        # Mock file listing
        mock_files = [
            GitHubFile(
                name="frontend-developer.md",
                path="agents/frontend-developer.md",
                download_url="https://raw.githubusercontent.com/test/repo/main/agents/frontend-developer.md",
                sha="abc123",
                size=1024,
            ),
            GitHubFile(
                name="backend-architect.md",
                path="agents/backend-architect.md",
                download_url="https://raw.githubusercontent.com/test/repo/main/agents/backend-architect.md",
                sha="def456",
                size=2048,
            ),
        ]
        mock_list_files.return_value = mock_files

        # Mock file content
        mock_get_content.side_effect = [
            "# Frontend Developer\nSpecializes in React and Vue.js development.",
            "# Backend Architect\nDesigns scalable backend systems.",
        ]

        agents = github_client.fetch_repository_agents("test/repo")

        assert len(agents) == 2
        assert agents[0]["name"] == "frontend-developer.md"
        assert agents[1]["name"] == "backend-architect.md"
        assert "React and Vue.js" in agents[0]["content"]
        assert "scalable backend" in agents[1]["content"]

    def test_rate_limit_status_without_request(self, github_client):
        """Test getting rate limit status without making requests."""
        # Set github_client rate_limit to None to simulate no prior requests
        github_client.rate_limit = None

        with patch.object(github_client, "_make_request") as mock_request:
            mock_request.side_effect = ConfigError("Mock error")
            status = github_client.get_rate_limit_status()
            assert "error" in status

    def test_cache_stats(self, github_client):
        """Test getting cache statistics."""
        # Add some cache entries
        github_client.cache["test1"] = CacheEntry(
            data={"test": "data1"}, timestamp=time.time()
        )
        github_client.cache["test2"] = CacheEntry(
            data={"test": "data2"}, timestamp=time.time() - (8 * 3600)  # expired
        )

        stats = github_client.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 1
        assert "cache_directory" in stats
        assert "request_count" in stats


@pytest.mark.requires_network
class TestGitHubClientLive:
    """Live tests against GitHub API (requires network and token)."""

    @pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
    def test_live_repository_info(self, github_client):
        """Test getting real repository information."""
        # Test with a known public repository
        repo_info = github_client.get_repository_info("octocat/Hello-World")

        assert repo_info.owner == "octocat"
        assert repo_info.name == "Hello-World"
        assert repo_info.full_name == "octocat/Hello-World"

    @pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
    def test_live_rate_limit(self, github_client):
        """Test getting rate limit status."""
        # Make a request to populate rate limit info
        try:
            github_client.get_repository_info("octocat/Hello-World")
            status = github_client.get_rate_limit_status()

            assert "limit" in status
            assert "remaining" in status
            assert status["limit"] > 0
        except ConfigError:
            # Skip if we hit rate limits or auth issues
            pytest.skip("Rate limit or authentication issue")
