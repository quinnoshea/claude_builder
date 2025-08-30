"""Agent repository management and scanning system for Claude Builder."""

import concurrent.futures
import logging
import re
import threading
import time

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml

from claude_builder.core.models import ProjectAnalysis
from claude_builder.utils.exceptions import ConfigError


# Error constants
REPOSITORY_CONFIG_NOT_FOUND = "Repository configuration file not found"
INVALID_REPOSITORY_CONFIG = "Invalid repository configuration"
REPOSITORY_URL_INVALID = "Repository URL is invalid"
REPOSITORY_NOT_ACCESSIBLE = "Repository is not accessible"
AGENT_DEFINITION_PARSE_ERROR = "Failed to parse agent definition"
CAPABILITY_INDEX_ERROR = "Error in capability indexing"
GITHUB_API_ERROR = "GitHub API error"
AGENT_CACHE_ERROR = "Agent cache error"
PARALLEL_SCAN_ERROR = "Parallel scanning error"
SYNC_OPERATION_ERROR = "Repository synchronization error"

# Magic number constants
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DESCRIPTION_WEIGHT = 0.3
CAPABILITIES_WEIGHT = 0.2
USE_CASES_WEIGHT = 0.2
KEYWORDS_WEIGHT = 0.15
LANGUAGES_WEIGHT = 0.15
NEUTRAL_SCORE = 0.5
HIGH_COMPATIBILITY_SCORE = 0.8
MODERATE_COMPATIBILITY_SCORE = 0.7
LOW_COMPATIBILITY_SCORE = 0.3

# Performance constants
MAX_WORKER_THREADS = 4
AGENT_CACHE_EXPIRY_HOURS = 6
REPOSITORY_SYNC_TIMEOUT_SECONDS = 30
PARSE_TIMEOUT_SECONDS = 5

# Validation error messages
AGENT_NAME_EMPTY = "Agent name cannot be empty"
AGENT_DESCRIPTION_EMPTY = "Agent description cannot be empty"
COMPATIBILITY_SCORE_RANGE = "Compatibility score must be between 0.0 and 1.0"


@dataclass(frozen=True)
class AgentDefinition:
    """Parsed agent definition from repository."""

    name: str
    description: str
    capabilities: Tuple[str, ...] = field(default_factory=tuple)
    use_cases: Tuple[str, ...] = field(default_factory=tuple)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    trigger_keywords: Tuple[str, ...] = field(default_factory=tuple)
    framework_compatibility: Tuple[str, ...] = field(default_factory=tuple)
    language_compatibility: Tuple[str, ...] = field(default_factory=tuple)
    complexity_level: str = "moderate"
    confidence_score: float = 0.0
    source_url: str = ""
    repository_name: str = ""

    def __post_init__(self) -> None:
        """Validate agent definition after creation."""
        if not self.name or not self.name.strip():
            raise ValueError(AGENT_NAME_EMPTY)
        if not self.description or not self.description.strip():
            raise ValueError(AGENT_DESCRIPTION_EMPTY)
        if not self.capabilities:
            # Convert to tuple if needed
            object.__setattr__(
                self, "capabilities", ("General development assistance",)
            )

        # Convert other lists to tuples for immutability
        for field_name in [
            "use_cases",
            "dependencies",
            "trigger_keywords",
            "framework_compatibility",
            "language_compatibility",
        ]:
            field_value = getattr(self, field_name)
            if isinstance(field_value, list):
                object.__setattr__(self, field_name, tuple(field_value))


@dataclass
class CompatibleAgent:
    """Agent with compatibility score for specific project."""

    agent: AgentDefinition
    compatibility_score: float
    matching_criteria: List[str]
    confidence_factors: Dict[str, float]

    def __post_init__(self) -> None:
        """Validate compatibility agent after creation."""
        if not 0.0 <= self.compatibility_score <= 1.0:
            raise ValueError(COMPATIBILITY_SCORE_RANGE)


@dataclass
class ScanResult:
    """Result of repository scanning operation."""

    total_agents: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    repositories_scanned: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SyncResult:
    """Result of repository synchronization."""

    updated_repositories: int = 0
    new_agents: int = 0
    updated_agents: int = 0
    removed_agents: int = 0
    sync_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class AgentCacheEntry:
    """Cached agent definition with metadata."""

    agent: AgentDefinition
    cached_at: float
    source_etag: Optional[str] = None
    source_last_modified: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age_hours = (time.time() - self.cached_at) / 3600
        return age_hours > AGENT_CACHE_EXPIRY_HOURS


class AgentCache:
    """High-performance agent cache with intelligent invalidation."""

    def __init__(self) -> None:
        """Initialize the agent cache."""
        self._cache: Dict[str, AgentCacheEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

    def get(self, source_url: str) -> Optional[AgentDefinition]:
        """Get cached agent by source URL."""
        with self._lock:
            entry = self._cache.get(source_url)
            if entry and not entry.is_expired():
                self._logger.debug(f"Cache hit for {source_url}")
                return entry.agent
            if entry and entry.is_expired():
                self._logger.debug(f"Cache expired for {source_url}")
                del self._cache[source_url]
            return None

    def set(
        self,
        source_url: str,
        agent: AgentDefinition,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> None:
        """Cache an agent with metadata."""
        with self._lock:
            entry = AgentCacheEntry(
                agent=agent,
                cached_at=time.time(),
                source_etag=etag,
                source_last_modified=last_modified,
            )
            self._cache[source_url] = entry
            self._logger.debug(f"Cached agent {agent.name} from {source_url}")

    def invalidate(self, source_url: str) -> bool:
        """Invalidate cached agent."""
        with self._lock:
            if source_url in self._cache:
                del self._cache[source_url]
                self._logger.debug(f"Invalidated cache for {source_url}")
                return True
            return False

    def clear(self) -> int:
        """Clear all cached agents."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._logger.info(f"Cleared {count} cached agents")
            return count

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        with self._lock:
            expired_urls = [
                url for url, entry in self._cache.items() if entry.is_expired()
            ]
            for url in expired_urls:
                del self._cache[url]

            if expired_urls:
                self._logger.info(
                    f"Cleaned up {len(expired_urls)} expired cache entries"
                )
            return len(expired_urls)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(
                1 for entry in self._cache.values() if entry.is_expired()
            )

            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count,
                "cache_hit_ratio": getattr(self, "_hit_ratio", 0.0),
            }


class RepositoryConfig:
    """Configuration for agent repositories."""

    DEFAULT_REPOSITORIES: ClassVar[List[Dict[str, Any]]] = [
        {
            "name": "claude-code-community",
            "url": "https://github.com/anthropics/claude-code-agents",
            "priority": 1,
            "enabled": True,
            "description": "Official Claude Code community agents",
        },
        {
            "name": "universal-agents",
            "url": "https://github.com/claude-builder/universal-agents",
            "priority": 2,
            "enabled": True,
            "description": "Universal agents for common development tasks",
        },
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize repository configuration."""
        self.config_path = (
            config_path or Path.home() / ".claude" / "agent_repositories.yaml"
        )
        self.repositories = self._load_repositories()

    def _load_repositories(self) -> List[Dict[str, Any]]:
        """Load repository configurations from YAML."""
        try:
            if not self.config_path.exists():
                # Create default configuration if none exists
                self._create_default_config()
                return self.DEFAULT_REPOSITORIES.copy()

            with self.config_path.open(encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            repositories = config_data.get("repositories", [])

            # Validate repository configurations
            validated_repos = []
            for repo in repositories:
                if self._validate_repository_config(repo):
                    validated_repos.append(repo)

            return (
                validated_repos if validated_repos else self.DEFAULT_REPOSITORIES.copy()
            )

        except yaml.YAMLError as e:
            msg = f"{INVALID_REPOSITORY_CONFIG}: YAML parse error: {e}"
            raise ConfigError(msg) from e
        except Exception as e:
            msg = f"{REPOSITORY_CONFIG_NOT_FOUND}: {e}"
            raise ConfigError(msg) from e

    def _validate_repository_config(self, repo_config: Dict[str, Any]) -> bool:
        """Validate a single repository configuration."""
        required_fields = ["name", "url"]

        # Check required fields
        for required_field in required_fields:
            if required_field not in repo_config or not repo_config[required_field]:
                return False

        # Validate URL format
        if not self._is_valid_url(repo_config["url"]):
            return False

        # Set defaults for optional fields
        repo_config.setdefault("priority", 1)
        repo_config.setdefault("enabled", True)
        repo_config.setdefault("description", "")

        return True

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]
        except (ValueError, TypeError):
            return False

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            default_config = {
                "version": "1.0",
                "repositories": self.DEFAULT_REPOSITORIES,
            }

            with self.config_path.open("w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)

        except Exception as e:
            msg = f"Failed to create default configuration: {e}"
            raise ConfigError(msg) from e

    def add_repository(
        self,
        url: str,
        name: str,
        priority: int = 1,
        description: str = "",
        *,
        enabled: bool = True,
    ) -> None:
        """Add a new repository to configuration."""
        # Validate URL format
        if not self._is_valid_url(url):
            msg = f"{REPOSITORY_URL_INVALID}: {url}"
            raise ValueError(msg)

        # Check if repository already exists
        for repo in self.repositories:
            if repo["name"] == name or repo["url"] == url:
                msg = f"Repository already exists: {name} ({url})"
                raise ValueError(msg)

        # Create new repository configuration
        new_repo = {
            "name": name,
            "url": url,
            "priority": priority,
            "enabled": enabled,
            "description": description,
        }

        self.repositories.append(new_repo)
        self._save_config()

    def remove_repository(self, name: str) -> bool:
        """Remove a repository from configuration."""
        original_length = len(self.repositories)
        self.repositories = [repo for repo in self.repositories if repo["name"] != name]

        if len(self.repositories) < original_length:
            self._save_config()
            return True
        return False

    def update_repository(self, name: str, **updates: Any) -> bool:
        """Update repository configuration."""
        for repo in self.repositories:
            if repo["name"] == name:
                # Validate URL if being updated
                if "url" in updates and not self._is_valid_url(updates["url"]):
                    msg = f"{REPOSITORY_URL_INVALID}: {updates['url']}"
                    raise ValueError(msg)

                repo.update(updates)
                self._save_config()
                return True
        return False

    def get_enabled_repositories(self) -> List[Dict[str, Any]]:
        """Get list of enabled repositories sorted by priority."""
        enabled_repos = [
            repo for repo in self.repositories if repo.get("enabled", True)
        ]
        return sorted(enabled_repos, key=lambda x: x.get("priority", 1))

    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            config_data = {"version": "1.0", "repositories": self.repositories}

            with self.config_path.open("w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

        except Exception as e:
            msg = f"Failed to save configuration: {e}"
            raise ConfigError(msg) from e


class AgentDefinitionParser:
    """Parse agent definitions from markdown files."""

    # Common patterns for parsing agent metadata
    NAME_PATTERN = re.compile(r"^#\s+(.+?)(?:\s*-.*)?$", re.MULTILINE)
    DESCRIPTION_PATTERN = re.compile(
        r"(?:##?\s*)?(?:Description|About)[:\s]*(.+?)(?:\n\n|\n#|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    CAPABILITIES_PATTERN = re.compile(
        r"(?:##?\s*)?(?:Capabilities|Features|Can do)[:\s]*\n((?:[-*]\s*.+\n?)+)",
        re.IGNORECASE,
    )
    USE_CASES_PATTERN = re.compile(
        r"(?:##?\s*)?(?:Use cases|Usage|When to use)[:\s]*\n((?:[-*]\s*.+\n?)+)",
        re.IGNORECASE,
    )
    KEYWORDS_PATTERN = re.compile(
        r"##?\s*(?:Keywords|Tags|Triggers)[:\s]*\n?(.+?)(?:\n\n|\n##|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    LANGUAGES_PATTERN = re.compile(
        r"##?\s*(?:Languages|Lang|Programming languages)[:\s]*\n?(.+?)(?:\n\n|\n##|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    FRAMEWORKS_PATTERN = re.compile(
        r"##?\s*(?:Frameworks|Framework|Stack)[:\s]*\n?(.+?)(?:\n\n|\n##|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    COMPLEXITY_PATTERN = re.compile(
        r"(?:##?\s*)?(?:Complexity|Level|Difficulty)[:\s]*(\w+)", re.IGNORECASE
    )

    def parse_agent_file(
        self, content: str, source_url: str
    ) -> Optional[AgentDefinition]:
        """Parse agent definition from markdown content."""
        try:
            # Extract agent name (from first header)
            name_match = self.NAME_PATTERN.search(content)
            if not name_match:
                return None

            name = name_match.group(1).strip()

            # Extract description
            description = self._extract_description(content)
            if not description:
                return None

            # Extract capabilities
            capabilities = self._extract_list_items(content, self.CAPABILITIES_PATTERN)
            if not capabilities:
                # Try to infer from content or provide default
                capabilities = ["General development assistance"]

            # Extract use cases
            use_cases = self._extract_list_items(content, self.USE_CASES_PATTERN)

            # Extract trigger keywords
            trigger_keywords = self._extract_keywords(content, self.KEYWORDS_PATTERN)

            # Extract language compatibility
            language_compatibility = self._extract_keywords(
                content, self.LANGUAGES_PATTERN
            )

            # Extract framework compatibility
            framework_compatibility = self._extract_keywords(
                content, self.FRAMEWORKS_PATTERN
            )

            # Extract complexity level
            complexity_level = self._extract_complexity(content)

            # Calculate confidence score based on available metadata
            confidence_score = self._calculate_confidence_score(
                has_description=bool(description),
                capabilities_count=len(capabilities),
                use_cases_count=len(use_cases),
                keywords_count=len(trigger_keywords),
                languages_count=len(language_compatibility),
            )

            # Extract repository name from URL
            repository_name = self._extract_repository_name(source_url)

            return AgentDefinition(
                name=name,
                description=description,
                capabilities=(
                    tuple(capabilities)
                    if capabilities
                    else ("General development assistance",)
                ),
                use_cases=tuple(use_cases),
                trigger_keywords=tuple(trigger_keywords),
                language_compatibility=tuple(language_compatibility),
                framework_compatibility=tuple(framework_compatibility),
                complexity_level=complexity_level,
                confidence_score=confidence_score,
                source_url=source_url,
                repository_name=repository_name,
            )

        except Exception as e:
            msg = f"{AGENT_DEFINITION_PARSE_ERROR}: {e}"
            raise ValueError(msg) from e

    def _extract_description(self, content: str) -> str:
        """Extract agent description from content."""
        desc_match = self.DESCRIPTION_PATTERN.search(content)
        if desc_match:
            return desc_match.group(1).strip()

        # Fallback: try to get first paragraph after title
        lines = content.split("\n")
        in_description = False
        description_lines = []

        for original_line in lines:
            line = original_line.strip()
            if line.startswith("#") and not in_description:
                in_description = True
                continue
            if line.startswith("#") and in_description:
                break
            if in_description and line:
                if line.startswith(("-", "*")):
                    break
                description_lines.append(line)
            elif in_description and not line and description_lines:
                break

        return " ".join(description_lines) if description_lines else ""

    def _extract_list_items(self, content: str, pattern: re.Pattern) -> List[str]:
        """Extract list items from content using pattern."""
        match = pattern.search(content)
        if not match:
            return []

        items = []
        for original_line in match.group(1).split("\n"):
            line = original_line.strip()
            if line.startswith(("-", "*")):
                item = line[1:].strip()
                if item:
                    items.append(item)

        return items

    def _extract_keywords(self, content: str, pattern: re.Pattern) -> List[str]:
        """Extract keywords from content using pattern."""
        match = pattern.search(content)
        if not match:
            return []

        keywords_text = match.group(1).strip()
        # Split by common delimiters
        keywords = re.split(r"[,;|]+", keywords_text)
        return [kw.strip() for kw in keywords if kw.strip()]

    def _extract_complexity(self, content: str) -> str:
        """Extract complexity level from content."""
        match = self.COMPLEXITY_PATTERN.search(content)
        if match:
            complexity = match.group(1).lower()
            valid_levels = ["simple", "moderate", "complex", "enterprise"]
            if complexity in valid_levels:
                return complexity

        return "moderate"  # Default

    def _calculate_confidence_score(
        self,
        *,
        has_description: bool,
        capabilities_count: int,
        use_cases_count: int,
        keywords_count: int,
        languages_count: int,
    ) -> float:
        """Calculate confidence score based on available metadata."""
        score = 0.0

        if has_description:
            score += DESCRIPTION_WEIGHT
        if capabilities_count > 0:
            score += CAPABILITIES_WEIGHT
        if use_cases_count > 0:
            score += USE_CASES_WEIGHT
        if keywords_count > 0:
            score += KEYWORDS_WEIGHT
        if languages_count > 0:
            score += LANGUAGES_WEIGHT

        return min(score, 1.0)

    def _extract_repository_name(self, source_url: str) -> str:
        """Extract repository name from URL."""
        try:
            parsed = urlparse(source_url)
            if "github.com" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                # Minimum path parts for owner/repo structure
                min_path_parts = 2
                if len(path_parts) >= min_path_parts:
                    return f"{path_parts[0]}/{path_parts[1]}"
        except (ValueError, TypeError, AttributeError):
            return "unknown"
        else:
            return parsed.netloc


class CapabilityIndex:
    """Searchable index of agent capabilities."""

    def __init__(self) -> None:
        """Initialize the capability index."""
        self.agents_by_language: Dict[str, List[AgentDefinition]] = defaultdict(list)
        self.agents_by_framework: Dict[str, List[AgentDefinition]] = defaultdict(list)
        self.agents_by_domain: Dict[str, List[AgentDefinition]] = defaultdict(list)
        self.agents_by_complexity: Dict[str, List[AgentDefinition]] = defaultdict(list)
        self.keyword_to_agents: Dict[str, List[AgentDefinition]] = defaultdict(list)
        self.all_agents: List[AgentDefinition] = []

    def index_agent(self, agent: AgentDefinition) -> None:
        """Index an agent by its capabilities."""
        try:
            # Add to master list
            self.all_agents.append(agent)

            # Index by language compatibility
            for language in agent.language_compatibility:
                normalized_lang = language.lower().strip()
                self.agents_by_language[normalized_lang].append(agent)

            # Index by framework compatibility
            for framework in agent.framework_compatibility:
                normalized_framework = framework.lower().strip()
                self.agents_by_framework[normalized_framework].append(agent)

            # Index by complexity level
            self.agents_by_complexity[agent.complexity_level].append(agent)

            # Index by trigger keywords
            for keyword in agent.trigger_keywords:
                normalized_keyword = keyword.lower().strip()
                self.keyword_to_agents[normalized_keyword].append(agent)

            # Index by capabilities (treat as domain keywords)
            for capability in agent.capabilities:
                # Extract domain keywords from capabilities
                domain_keywords = self._extract_domain_keywords(capability)
                for keyword in domain_keywords:
                    self.agents_by_domain[keyword].append(agent)
                    self.keyword_to_agents[keyword].append(agent)

        except Exception as e:
            msg = f"{CAPABILITY_INDEX_ERROR}: {e}"
            raise ValueError(msg) from e

    def search_agents(
        self,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        domain: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        complexity: Optional[str] = None,
    ) -> List[AgentDefinition]:
        """Search for compatible agents using multiple criteria."""
        if not any([language, framework, domain, keywords, complexity]):
            return self.all_agents.copy()

        # Start with all agents, then apply filters
        candidate_agents = self.all_agents.copy()

        # Apply each filter
        return self._filter_by_keywords(
            self._filter_by_complexity(
                self._filter_by_domain(
                    self._filter_by_framework(
                        self._filter_by_language(candidate_agents, language), framework
                    ),
                    domain,
                ),
                complexity,
            ),
            keywords,
        )

    def _filter_by_language(
        self, agents: List[AgentDefinition], language: Optional[str]
    ) -> List[AgentDefinition]:
        """Filter agents by language compatibility."""
        if not language:
            return agents

        lang_agents = self.agents_by_language.get(language.lower(), [])
        return [a for a in agents if a in lang_agents] if lang_agents else []

    def _filter_by_framework(
        self, agents: List[AgentDefinition], framework: Optional[str]
    ) -> List[AgentDefinition]:
        """Filter agents by framework compatibility."""
        if not framework:
            return agents

        framework_agents = self.agents_by_framework.get(framework.lower(), [])
        return [a for a in agents if a in framework_agents] if framework_agents else []

    def _filter_by_domain(
        self, agents: List[AgentDefinition], domain: Optional[str]
    ) -> List[AgentDefinition]:
        """Filter agents by domain compatibility."""
        if not domain:
            return agents

        domain_agents = self.agents_by_domain.get(domain.lower(), [])
        return [a for a in agents if a in domain_agents] if domain_agents else []

    def _filter_by_complexity(
        self, agents: List[AgentDefinition], complexity: Optional[str]
    ) -> List[AgentDefinition]:
        """Filter agents by complexity level."""
        if not complexity:
            return agents

        complexity_agents = self.agents_by_complexity.get(complexity.lower(), [])
        return (
            [a for a in agents if a in complexity_agents] if complexity_agents else []
        )

    def _filter_by_keywords(
        self, agents: List[AgentDefinition], keywords: Optional[List[str]]
    ) -> List[AgentDefinition]:
        """Filter agents by keyword compatibility."""
        if not keywords:
            return agents

        keyword_agents = set()
        for keyword in keywords:
            keyword_agents.update(self.keyword_to_agents.get(keyword.lower(), []))
        return [a for a in agents if a in keyword_agents] if keyword_agents else []

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_agents": len(self.all_agents),
            "languages": len(self.agents_by_language),
            "frameworks": len(self.agents_by_framework),
            "complexity_levels": len(self.agents_by_complexity),
            "keywords": len(self.keyword_to_agents),
            "domains": len(self.agents_by_domain),
        }

    def _extract_domain_keywords(self, capability: str) -> List[str]:
        """Extract domain keywords from capability description."""
        # Common domain keywords that might appear in capabilities
        domain_keywords = []
        capability_lower = capability.lower()

        # Development domains
        if any(
            word in capability_lower
            for word in ["web", "frontend", "backend", "full-stack"]
        ):
            domain_keywords.append("web development")
        if any(word in capability_lower for word in ["api", "rest", "graphql"]):
            domain_keywords.append("api development")
        if any(word in capability_lower for word in ["test", "testing", "qa"]):
            domain_keywords.append("testing")
        if any(
            word in capability_lower
            for word in ["deploy", "deployment", "devops", "ci/cd"]
        ):
            domain_keywords.append("deployment")
        if any(word in capability_lower for word in ["database", "sql", "nosql"]):
            domain_keywords.append("database")
        if any(word in capability_lower for word in ["mobile", "ios", "android"]):
            domain_keywords.append("mobile development")
        if any(word in capability_lower for word in ["data", "analytics", "ml", "ai"]):
            domain_keywords.append("data science")

        return domain_keywords


class AgentCompatibilityScorer:
    """Score agent compatibility with projects."""

    # Scoring weights for different compatibility factors
    LANGUAGE_WEIGHT = 0.3
    FRAMEWORK_WEIGHT = 0.25
    DOMAIN_WEIGHT = 0.2
    COMPLEXITY_WEIGHT = 0.15
    KEYWORD_WEIGHT = 0.1

    def score_agent_compatibility(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> CompatibleAgent:
        """Calculate compatibility score for agent-project pair."""
        scores = {}
        matching_criteria = []

        # Calculate individual compatibility scores
        scores["language"] = self._calculate_language_score(agent, project)
        scores["framework"] = self._calculate_framework_score(agent, project)
        scores["domain"] = self._calculate_domain_score(agent, project)
        scores["complexity"] = self._calculate_complexity_score(agent, project)
        scores["keywords"] = self._calculate_keyword_score(agent, project)

        # Determine matching criteria
        if scores["language"] > DEFAULT_CONFIDENCE_THRESHOLD:
            matching_criteria.append(f"Language: {project.language}")
        if scores["framework"] > DEFAULT_CONFIDENCE_THRESHOLD:
            matching_criteria.append(f"Framework: {project.framework}")
        if scores["domain"] > DEFAULT_CONFIDENCE_THRESHOLD:
            matching_criteria.append(f"Domain: {project.domain_info.domain}")
        if scores["complexity"] > DEFAULT_CONFIDENCE_THRESHOLD:
            matching_criteria.append(f"Complexity: {project.complexity_level.value}")

        # Calculate weighted final score
        final_score = (
            scores["language"] * self.LANGUAGE_WEIGHT
            + scores["framework"] * self.FRAMEWORK_WEIGHT
            + scores["domain"] * self.DOMAIN_WEIGHT
            + scores["complexity"] * self.COMPLEXITY_WEIGHT
            + scores["keywords"] * self.KEYWORD_WEIGHT
        )

        # Apply agent confidence as a modifier
        final_score *= agent.confidence_score

        return CompatibleAgent(
            agent=agent,
            compatibility_score=min(final_score, 1.0),
            matching_criteria=matching_criteria,
            confidence_factors=scores,
        )

    def _calculate_language_score(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> float:
        """Calculate language-specific compatibility."""
        if not project.language or not agent.language_compatibility:
            return NEUTRAL_SCORE  # Neutral score if no language info

        project_lang = project.language.lower()

        # Check for exact match
        for agent_lang in agent.language_compatibility:
            if agent_lang.lower() == project_lang:
                return 1.0

        # Check for compatible languages (e.g., TypeScript <-> JavaScript)
        compatible_languages = {
            "typescript": ["javascript", "js", "ts"],
            "javascript": ["typescript", "js", "ts"],
            "python": ["py"],
            "c++": ["cpp", "cxx", "cc"],
            "c#": ["csharp", "cs"],
        }

        for agent_lang in agent.language_compatibility:
            agent_lang_lower = agent_lang.lower()
            if project_lang in compatible_languages.get(agent_lang_lower, []):
                return HIGH_COMPATIBILITY_SCORE
            if agent_lang_lower in compatible_languages.get(project_lang, []):
                return HIGH_COMPATIBILITY_SCORE

        return 0.0  # No match

    def _calculate_framework_score(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> float:
        """Calculate framework-specific compatibility."""
        if not project.framework or not agent.framework_compatibility:
            return NEUTRAL_SCORE  # Neutral score if no framework info

        project_framework = project.framework.lower()

        # Check for exact match
        for agent_framework in agent.framework_compatibility:
            if agent_framework.lower() == project_framework:
                return 1.0

        # Check for related frameworks
        framework_families = {
            "react": ["nextjs", "gatsby", "create-react-app"],
            "vue": ["nuxtjs", "vuetify"],
            "angular": ["angular-cli"],
            "django": ["django-rest-framework", "drf"],
            "fastapi": ["starlette"],
            "express": ["nestjs", "koa"],
        }

        for agent_framework in agent.framework_compatibility:
            agent_framework_lower = agent_framework.lower()
            if project_framework in framework_families.get(agent_framework_lower, []):
                return MODERATE_COMPATIBILITY_SCORE
            if agent_framework_lower in framework_families.get(project_framework, []):
                return MODERATE_COMPATIBILITY_SCORE

        return 0.0  # No match

    def _calculate_domain_score(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> float:
        """Calculate domain relevance compatibility."""
        if not project.domain_info.domain:
            return NEUTRAL_SCORE  # Neutral if no domain detected

        project_domain = project.domain_info.domain.lower()

        # Check agent capabilities for domain relevance
        domain_score = 0.0
        capability_text = " ".join(agent.capabilities + agent.use_cases).lower()

        # Domain mapping
        domain_keywords = {
            "web": ["web", "frontend", "backend", "http", "api", "browser"],
            "api": ["api", "rest", "graphql", "endpoint", "service"],
            "cli": ["cli", "command", "terminal", "console", "script"],
            "data": ["data", "analytics", "ml", "ai", "science", "pipeline"],
            "mobile": ["mobile", "ios", "android", "app"],
            "game": ["game", "gaming", "engine", "graphics"],
        }

        if project_domain in domain_keywords:
            keywords = domain_keywords[project_domain]
            matches = sum(1 for keyword in keywords if keyword in capability_text)
            domain_score = min(matches / len(keywords), 1.0)

        return domain_score

    def _calculate_complexity_score(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> float:
        """Calculate complexity level matching."""
        complexity_levels = {"simple": 1, "moderate": 2, "complex": 3, "enterprise": 4}

        agent_level = complexity_levels.get(agent.complexity_level, 2)
        project_level = complexity_levels.get(project.complexity_level.value, 2)

        # Perfect match
        if agent_level == project_level:
            return 1.0

        # Adjacent levels get partial score
        if abs(agent_level - project_level) == 1:
            return MODERATE_COMPATIBILITY_SCORE

        # More than 1 level apart
        return LOW_COMPATIBILITY_SCORE

    def _calculate_keyword_score(
        self, agent: AgentDefinition, project: ProjectAnalysis
    ) -> float:
        """Calculate keyword-based compatibility."""
        if not agent.trigger_keywords:
            return NEUTRAL_SCORE  # Neutral if no keywords

        # Create project keyword context from various sources
        project_context = []

        if project.framework:
            project_context.append(project.framework.lower())
        if project.language:
            project_context.append(project.language.lower())
        if project.domain_info.domain:
            project_context.append(project.domain_info.domain.lower())

        # Add project type and architecture pattern
        project_context.append(project.project_type.value)
        project_context.append(project.architecture_pattern.value)

        # Add development environment keywords
        project_context.extend([db.lower() for db in project.dev_environment.databases])
        project_context.extend(
            [tool.lower() for tool in project.dev_environment.testing_frameworks]
        )

        # Calculate keyword overlap
        agent_keywords = [kw.lower() for kw in agent.trigger_keywords]
        matches = sum(
            1
            for keyword in agent_keywords
            if any(keyword in ctx for ctx in project_context)
        )

        if not agent_keywords:
            return NEUTRAL_SCORE

        return matches / len(agent_keywords)


# Configure logging for the module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class AgentRepositoryScanner:
    """Main orchestrator for agent repository operations."""

    def __init__(
        self,
        config: Optional[RepositoryConfig] = None,
        github_token: Optional[str] = None,
        max_workers: int = MAX_WORKER_THREADS,
    ):
        """Initialize the agent repository scanner."""
        self.config = config or RepositoryConfig()
        self.parser = AgentDefinitionParser()
        self.scorer = AgentCompatibilityScorer()
        self.index = CapabilityIndex()
        self.cache = AgentCache()
        self.max_workers = max_workers
        self._logger = logging.getLogger(__name__)
        self._scan_lock = threading.RLock()

        # Initialize GitHub client - import here to avoid circular imports
        try:
            from claude_builder.utils.github_client import GitHubAgentClient

            self.github_client: Optional[GitHubAgentClient] = GitHubAgentClient(
                token=github_token
            )
        except ImportError:
            # Fallback if github_client is not available
            self.github_client = None
            self._logger.warning(
                "GitHub client not available - repository scanning disabled"
            )

    def scan_repositories(self, force_refresh: bool = False) -> ScanResult:
        """Scan all configured repositories for agents with parallel processing."""
        start_time = time.time()

        with self._scan_lock:
            result = ScanResult()

            if not self.github_client:
                result.errors.append("GitHub client not available - check dependencies")
                return result

            # Clean up expired cache entries
            expired_cleaned = self.cache.cleanup_expired()
            if expired_cleaned > 0:
                self._logger.info(f"Cleaned up {expired_cleaned} expired cache entries")

            enabled_repos = self.config.get_enabled_repositories()
            result.repositories_scanned = len(enabled_repos)

            if not enabled_repos:
                self._logger.warning("No enabled repositories found for scanning")
                result.scan_duration = time.time() - start_time
                return result

            # Parallel repository scanning
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:
                # Submit repository scan tasks
                future_to_repo = {
                    executor.submit(
                        self._scan_single_repository, repo_config, force_refresh
                    ): repo_config
                    for repo_config in enabled_repos
                }

                # Collect results
                for future in concurrent.futures.as_completed(
                    future_to_repo, timeout=REPOSITORY_SYNC_TIMEOUT_SECONDS
                ):
                    repo_config = future_to_repo[future]
                    try:
                        repo_result = future.result()
                        # Merge repository result into overall result
                        result.total_agents += repo_result.total_agents
                        result.successful_parses += repo_result.successful_parses
                        result.failed_parses += repo_result.failed_parses
                        result.errors.extend(repo_result.errors)
                        result.warnings.extend(repo_result.warnings)

                    except concurrent.futures.TimeoutError:
                        error_msg = f"Repository scan timeout for {repo_config['name']}"
                        result.errors.append(error_msg)
                        self._logger.error(error_msg)
                    except Exception as e:
                        error_msg = (
                            f"Failed to scan repository {repo_config['name']}: {e}"
                        )
                        result.errors.append(error_msg)
                        self._logger.error(error_msg)

            result.scan_duration = time.time() - start_time
            self._logger.info(
                f"Scan completed in {result.scan_duration:.2f}s: "
                f"{result.successful_parses} successful, {result.failed_parses} failed"
            )

            return result

    def _scan_single_repository(
        self, repo_config: Dict[str, Any], force_refresh: bool
    ) -> ScanResult:
        """Scan a single repository for agents."""
        result = ScanResult()
        repo_name = repo_config["name"]
        repo_url = repo_config["url"]

        try:
            self._logger.info(f"Scanning repository: {repo_name}")

            # Fetch agents from repository
            if self.github_client is None:
                raise RuntimeError("GitHub client not available")
            agents_data = self.github_client.fetch_repository_agents(repo_url)
            result.total_agents = len(agents_data)

            if not agents_data:
                result.warnings.append(
                    f"No agent files found in repository {repo_name}"
                )
                return result

            # Process agents in parallel batches
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_to_agent = {
                    executor.submit(
                        self._process_single_agent, agent_data, force_refresh
                    ): agent_data
                    for agent_data in agents_data
                }

                for future in concurrent.futures.as_completed(
                    future_to_agent, timeout=PARSE_TIMEOUT_SECONDS
                ):
                    agent_data = future_to_agent[future]
                    try:
                        agent = future.result()
                        if agent:
                            # Index the agent
                            self.index.index_agent(agent)
                            result.successful_parses += 1
                        else:
                            result.failed_parses += 1

                    except concurrent.futures.TimeoutError:
                        result.failed_parses += 1
                        result.errors.append(f"Parse timeout for {agent_data['name']}")
                    except Exception as e:
                        result.failed_parses += 1
                        result.errors.append(
                            f"Failed to parse {agent_data['name']}: {e}"
                        )

        except Exception as e:
            result.errors.append(f"Repository scan failed for {repo_name}: {e}")
            self._logger.error(f"Repository scan failed for {repo_name}: {e}")

        return result

    def _process_single_agent(
        self, agent_data: Dict[str, Any], force_refresh: bool
    ) -> Optional[AgentDefinition]:
        """Process a single agent definition with caching."""
        source_url = agent_data["source_url"]

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_agent = self.cache.get(source_url)
            if cached_agent:
                return cached_agent

        # Parse agent definition
        agent = self.parser.parse_agent_file(agent_data["content"], source_url)

        # Cache the result if successful
        if agent:
            self.cache.set(
                source_url,
                agent,
                etag=agent_data.get("etag"),
                last_modified=agent_data.get("last_modified"),
            )

        return agent

    def find_compatible_agents(
        self, project: ProjectAnalysis, limit: int = 10
    ) -> List[CompatibleAgent]:
        """Find most compatible agents for a project."""
        # Search for agents using the capability index
        candidate_agents = self.index.search_agents(
            language=project.language,
            framework=project.framework,
            domain=project.domain_info.domain if project.domain_info else None,
            complexity=(
                project.complexity_level.value if project.complexity_level else None
            ),
        )

        # If no specific matches, get all agents
        if not candidate_agents:
            candidate_agents = self.index.all_agents

        # Score each candidate agent
        scored_agents = []
        for agent in candidate_agents:
            try:
                compatible_agent = self.scorer.score_agent_compatibility(agent, project)
                scored_agents.append(compatible_agent)
            except Exception:
                # Skip agents that fail scoring
                continue

        # Sort by compatibility score (descending) and return top matches
        scored_agents.sort(key=lambda x: x.compatibility_score, reverse=True)
        return scored_agents[:limit]

    def sync_repositories(self) -> SyncResult:
        """Synchronize with remote repositories for updates."""
        start_time = time.time()

        with self._scan_lock:
            result = SyncResult()

            if not self.github_client:
                result.errors.append("GitHub client not available - sync disabled")
                return result

            self._logger.info("Starting repository synchronization")

            enabled_repos = self.config.get_enabled_repositories()

            for repo_config in enabled_repos:
                try:
                    repo_name = repo_config["name"]
                    repo_url = repo_config["url"]

                    self._logger.info(f"Syncing repository: {repo_name}")

                    # Get current repository information
                    repo_info = self.github_client.get_repository_info(repo_url)

                    if not repo_info:
                        result.errors.append(
                            f"Could not fetch repository info for {repo_name}"
                        )
                        continue

                    # Check if repository has been updated since last scan
                    # This is a simplified check - in production, you'd want to compare
                    # with stored metadata about last sync time

                    # Force refresh agents from this repository
                    repo_scan_result = self._scan_single_repository(
                        repo_config, force_refresh=True
                    )

                    # Update sync statistics
                    result.updated_repositories += 1
                    result.new_agents += repo_scan_result.successful_parses

                    if repo_scan_result.errors:
                        result.errors.extend(repo_scan_result.errors)

                except Exception as e:
                    error_msg = f"Failed to sync repository {repo_config['name']}: {e}"
                    result.errors.append(error_msg)
                    self._logger.error(error_msg)

            result.sync_duration = time.time() - start_time

            self._logger.info(
                f"Sync completed in {result.sync_duration:.2f}s: "
                f"{result.updated_repositories} repos, {result.new_agents} agents"
            )

            return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        cache_stats = self.cache.get_stats()
        index_stats = self.index.get_stats()

        return {
            "cache": cache_stats,
            "index": index_stats,
            "scanner": {
                "max_workers": self.max_workers,
                "github_client_available": self.github_client is not None,
            },
        }

    def clear_caches(self) -> Dict[str, int]:
        """Clear all caches and return counts."""
        agent_cache_cleared = self.cache.clear()

        # Note: Index is not cleared as it contains actively used data
        # In production, you might want to add index.clear() method

        return {"agent_cache_cleared": agent_cache_cleared}
