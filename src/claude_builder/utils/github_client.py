"""GitHub API client for agent repositories."""

import contextlib
import json
import os
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from claude_builder.utils.exceptions import ConfigError


# Error constants
GITHUB_API_ERROR = "GitHub API error"
GITHUB_RATE_LIMIT_ERROR = "GitHub API rate limit exceeded"
GITHUB_AUTH_ERROR = "GitHub authentication error"
GITHUB_REPO_NOT_FOUND = "Repository not found"
GITHUB_INVALID_URL = "Invalid GitHub repository URL"
GITHUB_FILE_NOT_FOUND = "File not found in repository"
GITHUB_NETWORK_ERROR = "Network error accessing GitHub API"

# API configuration constants
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.3
RATE_LIMIT_BUFFER = 100  # Reserve 100 requests for other operations
CACHE_DURATION_HOURS = 6  # Cache API responses for 6 hours


@dataclass
class GitHubFile:
    """Represents a file in a GitHub repository."""

    name: str
    path: str
    download_url: str
    sha: str
    size: int
    type: str = "file"


@dataclass
class RepositoryInfo:
    """Repository metadata from GitHub API."""

    owner: str
    name: str
    full_name: str
    description: str = ""
    default_branch: str = "main"
    updated_at: str = ""
    size: int = 0
    language: str = ""


@dataclass
class RateLimit:
    """GitHub API rate limit information."""

    limit: int
    used: int
    remaining: int
    reset_time: float
    resource: str = "core"

    @property
    def reset_in_seconds(self) -> float:
        """Time until rate limit resets."""
        return max(0, self.reset_time - time.time())

    @property
    def is_near_limit(self) -> bool:
        """Check if we're approaching the rate limit."""
        return self.remaining < RATE_LIMIT_BUFFER


@dataclass
class CacheEntry:
    """Cache entry for GitHub API responses."""

    data: Any
    timestamp: float
    etag: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > CACHE_DURATION_HOURS * 3600

    @property
    def age_seconds(self) -> float:
        """Age of cache entry in seconds."""
        return time.time() - self.timestamp


class GitHubAgentClient:
    """GitHub API client for agent repositories with rate limiting and caching."""

    def __init__(self, token: Optional[str] = None, cache_dir: Optional[Path] = None):
        """Initialize GitHub client with authentication and caching."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.cache_dir = cache_dir or Path.home() / ".claude" / "github_cache"

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize session with retry strategy
        self.session = self._create_session()

        # Rate limiting and caching
        self.rate_limit: Optional[RateLimit] = None
        self.cache: Dict[str, CacheEntry] = {}
        self._load_cache()

        # Request tracking
        self.request_count = 0
        self.last_request_time = 0.0

    def _create_session(self) -> requests.Session:
        """Create configured requests session with retry strategy."""
        session = requests.Session()

        # Configure headers
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Claude-Builder/1.0",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        session.headers.update(headers)

        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=BACKOFF_FACTOR,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "api_cache.json"

        try:
            if cache_file.exists():
                with cache_file.open(encoding="utf-8") as f:
                    cache_data = json.load(f)

                for key, data in cache_data.items():
                    self.cache[key] = CacheEntry(
                        data=data["data"],
                        timestamp=data["timestamp"],
                        etag=data.get("etag"),
                    )

        except (json.JSONDecodeError, KeyError, OSError):
            # If cache is corrupted, start fresh
            self.cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self.cache_dir / "api_cache.json"

        try:
            # Clean expired entries before saving
            valid_cache = {
                key: {
                    "data": entry.data,
                    "timestamp": entry.timestamp,
                    "etag": entry.etag,
                }
                for key, entry in self.cache.items()
                if not entry.is_expired
            }

            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(valid_cache, f, indent=2)

        except OSError:
            # Cache saving failure is not critical
            pass

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Tuple[Dict[str, Any], bool]:
        """Make GitHub API request with rate limiting and caching."""
        # Check cache first
        cache_key = f"{url}?{json.dumps(params or {}, sort_keys=True)}"

        if use_cache and cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired:
                return entry.data, True

        # Check rate limits
        self._check_rate_limits()

        try:
            # Add conditional request headers if we have cached data
            headers = {}
            if use_cache and cache_key in self.cache:
                entry = self.cache[cache_key]
                if entry.etag:
                    headers["If-None-Match"] = entry.etag

            response = self.session.get(
                url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT
            )

            # Update request tracking
            self.request_count += 1
            self.last_request_time = time.time()

            # Update rate limit information
            self._update_rate_limit(response)

            # Handle 304 Not Modified
            if response.status_code == 304 and cache_key in self.cache:
                return self.cache[cache_key].data, True

            # Handle errors
            if response.status_code == 401:
                msg = f"{GITHUB_AUTH_ERROR}: Invalid or missing token"
                raise ConfigError(msg)
            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    msg = f"{GITHUB_RATE_LIMIT_ERROR}: {response.json().get('message', 'Unknown')}"
                    raise ConfigError(msg)
                msg = f"{GITHUB_API_ERROR}: Forbidden - {response.status_code}"
                raise ConfigError(msg)
            if response.status_code == 404:
                msg = f"{GITHUB_REPO_NOT_FOUND}: {url}"
                raise ConfigError(msg)
            if response.status_code >= 400:
                msg = f"{GITHUB_API_ERROR}: HTTP {response.status_code} - {response.text[:200]}"
                raise ConfigError(msg)

            response.raise_for_status()
            data = response.json()

            # Cache successful responses
            if use_cache:
                self.cache[cache_key] = CacheEntry(
                    data=data,
                    timestamp=time.time(),
                    etag=response.headers.get("ETag"),
                )
                # Save cache periodically
                if len(self.cache) % 10 == 0:
                    self._save_cache()

            return data, False

        except requests.exceptions.Timeout:
            msg = f"{GITHUB_NETWORK_ERROR}: Request timeout"
            raise ConfigError(msg)
        except requests.exceptions.ConnectionError:
            msg = f"{GITHUB_NETWORK_ERROR}: Connection error"
            raise ConfigError(msg)
        except requests.exceptions.RequestException as e:
            msg = f"{GITHUB_API_ERROR}: {e}"
            raise ConfigError(msg)

    def _update_rate_limit(self, response: requests.Response) -> None:
        """Update rate limit information from response headers."""
        try:
            self.rate_limit = RateLimit(
                limit=int(response.headers.get("X-RateLimit-Limit", 5000)),
                used=int(response.headers.get("X-RateLimit-Used", 0)),
                remaining=int(response.headers.get("X-RateLimit-Remaining", 5000)),
                reset_time=float(
                    response.headers.get("X-RateLimit-Reset", time.time() + 3600)
                ),
                resource=response.headers.get("X-RateLimit-Resource", "core"),
            )
        except (ValueError, TypeError):
            # If headers are malformed, use conservative defaults
            self.rate_limit = RateLimit(
                limit=5000, used=0, remaining=5000, reset_time=time.time() + 3600
            )

    def _check_rate_limits(self) -> None:
        """Check and handle rate limits."""
        if self.rate_limit and self.rate_limit.is_near_limit:
            # If we're near the limit, wait until reset
            if self.rate_limit.reset_in_seconds > 0:
                sleep_time = min(self.rate_limit.reset_in_seconds + 1, 60)
                time.sleep(sleep_time)

    def parse_repository_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name."""
        try:
            parsed = urlparse(repo_url)

            # Handle both github.com URLs and direct owner/repo format
            if parsed.netloc and "github.com" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo = path_parts[1].replace(".git", "")
                    return owner, repo
            elif "/" in repo_url and not parsed.netloc:
                # Direct owner/repo format
                parts = repo_url.strip("/").split("/")
                if len(parts) >= 2:
                    return parts[0], parts[1]

            msg = f"{GITHUB_INVALID_URL}: {repo_url}"
            raise ValueError(msg)

        except (AttributeError, IndexError) as e:
            msg = f"{GITHUB_INVALID_URL}: {repo_url} - {e}"
            raise ValueError(msg) from e

    def get_repository_info(self, repo_url: str) -> RepositoryInfo:
        """Get repository information from GitHub API."""
        owner, repo = self.parse_repository_url(repo_url)
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

        data, _ = self._make_request(url)

        return RepositoryInfo(
            owner=data["owner"]["login"],
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description", ""),
            default_branch=data.get("default_branch", "main"),
            updated_at=data.get("updated_at", ""),
            size=data.get("size", 0),
            language=data.get("language", ""),
        )

    def list_repository_files(
        self,
        repo_url: str,
        file_pattern: str = "*.md",
        path: str = "",
        branch: Optional[str] = None,
    ) -> List[GitHubFile]:
        """List files in repository matching pattern."""
        owner, repo = self.parse_repository_url(repo_url)

        # Get repository info to determine default branch if not specified
        if not branch:
            repo_info = self.get_repository_info(repo_url)
            branch = repo_info.default_branch

        # Build API URL for repository contents
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents"
        if path:
            url = f"{url}/{path.strip('/')}"

        params = {"ref": branch}

        try:
            data, _ = self._make_request(url, params)
        except ConfigError as e:
            if GITHUB_REPO_NOT_FOUND in str(e):
                return []  # Return empty list for missing directories
            raise

        files = []

        # Handle both file and directory responses
        if isinstance(data, dict):
            # Single file response
            if data.get("type") == "file":
                files.append(self._create_github_file(data))
        else:
            # Directory listing
            for item in data:  # type: ignore[unreachable]
                if item.get("type") == "file":
                    # Simple pattern matching (only *.md for now)
                    if file_pattern == "*.md" and item["name"].endswith(".md"):
                        files.append(self._create_github_file(item))
                elif item.get("type") == "dir":
                    # Recursively search subdirectories
                    subpath = f"{path}/{item['name']}".strip("/")
                    try:
                        subfiles = self.list_repository_files(
                            repo_url, file_pattern, subpath, branch
                        )
                        files.extend(subfiles)
                    except ConfigError:
                        # Skip directories that can't be accessed
                        continue

        return files

    def _create_github_file(self, file_data: Dict[str, Any]) -> GitHubFile:
        """Create GitHubFile from API response data."""
        return GitHubFile(
            name=file_data["name"],
            path=file_data["path"],
            download_url=file_data.get("download_url", ""),
            sha=file_data["sha"],
            size=file_data.get("size", 0),
            type=file_data.get("type", "file"),
        )

    def get_file_content(
        self,
        repo_url: str,
        file_path: str,
        branch: Optional[str] = None,
    ) -> str:
        """Get content of specific file from repository."""
        owner, repo = self.parse_repository_url(repo_url)

        if not branch:
            repo_info = self.get_repository_info(repo_url)
            branch = repo_info.default_branch

        # Use raw.githubusercontent.com for direct file access (faster)
        raw_url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{file_path}"

        try:
            response = self.session.get(raw_url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 404:
                msg = f"{GITHUB_FILE_NOT_FOUND}: {file_path} in {repo_url}"
                raise ConfigError(msg)

            response.raise_for_status()
            return str(response.text)

        except requests.exceptions.RequestException as e:
            msg = f"{GITHUB_API_ERROR}: Failed to fetch {file_path} - {e}"
            raise ConfigError(msg) from e

    def fetch_repository_agents(self, repo_url: str) -> List[Dict[str, Any]]:
        """Fetch all agent files from a GitHub repository."""
        try:
            # List all markdown files in the repository
            files = self.list_repository_files(repo_url, "*.md")

            agents = []

            for file in files:
                try:
                    # Get file content
                    content = self.get_file_content(repo_url, file.path)

                    agents.append(
                        {
                            "name": file.name,
                            "path": file.path,
                            "content": content,
                            "source_url": f"{repo_url}/blob/main/{file.path}",
                            "sha": file.sha,
                            "size": file.size,
                        }
                    )

                except ConfigError:
                    # Skip files that can't be accessed
                    continue

            return agents

        except ConfigError:
            # If repository can't be accessed, return empty list
            return []

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        if not self.rate_limit:
            # Make a test request to get rate limit info
            with contextlib.suppress(ConfigError):
                self._make_request(f"{GITHUB_API_BASE}/rate_limit", use_cache=False)

        if self.rate_limit:
            return {
                "limit": self.rate_limit.limit,
                "used": self.rate_limit.used,
                "remaining": self.rate_limit.remaining,
                "reset_time": self.rate_limit.reset_time,
                "reset_in_seconds": self.rate_limit.reset_in_seconds,
                "is_near_limit": self.rate_limit.is_near_limit,
            }

        return {"error": "Rate limit information not available"}

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache = {}
        cache_file = self.cache_dir / "api_cache.json"
        if cache_file.exists():
            cache_file.unlink()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired)

        return {
            "total_entries": total_entries,
            "valid_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_directory": str(self.cache_dir),
            "request_count": self.request_count,
        }

    def __del__(self) -> None:
        """Cleanup: save cache on destruction."""
        try:
            self._save_cache()
        except Exception:
            # Ignore cleanup errors
            pass
