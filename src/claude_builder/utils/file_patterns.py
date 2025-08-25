"""File pattern utilities for project analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class FilePatterns:
    """Utilities for file pattern recognition."""

    # Common source file extensions by language
    LANGUAGE_EXTENSIONS = {
        "python": {".py", ".pyx", ".pyi", ".pyw"},
        "rust": {".rs"},
        "javascript": {".js", ".mjs", ".cjs"},
        "typescript": {".ts", ".tsx"},
        "java": {".java"},
        "go": {".go"},
        "c": {".c", ".h"},
        "cpp": {".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh"},
        "csharp": {".cs"},
        "php": {".php", ".phtml"},
        "ruby": {".rb", ".rbw"},
        "scala": {".scala", ".sc"},
        "kotlin": {".kt", ".kts"},
        "swift": {".swift"},
        "dart": {".dart"},
        "elixir": {".ex", ".exs"},
        "erlang": {".erl", ".hrl"},
        "haskell": {".hs", ".lhs"},
        "clojure": {".clj", ".cljs", ".cljc", ".edn"},
        "r": {".r", ".R", ".rmd", ".Rmd"},
        "julia": {".jl"},
        "matlab": {".m"},
        "perl": {".pl", ".pm", ".t"},
        "lua": {".lua"},
        "bash": {".sh", ".bash", ".zsh", ".fish"},
        "powershell": {".ps1", ".psm1", ".psd1"},
        "sql": {".sql"},
        "html": {".html", ".htm"},
        "css": {".css", ".scss", ".sass", ".less"},
        "xml": {".xml", ".xsl", ".xslt"},
        "json": {".json"},
        "yaml": {".yaml", ".yml"},
        "toml": {".toml"},
        "ini": {".ini", ".cfg", ".conf"},
        "markdown": {".md", ".markdown", ".mdown", ".mkd"},
        "tex": {".tex", ".latex"},
    }

    # Configuration file patterns
    CONFIG_FILES = {
        "package.json",  # Node.js
        "yarn.lock",  # Yarn
        "package-lock.json",  # npm
        "Cargo.toml",  # Rust
        "Cargo.lock",  # Rust
        "pyproject.toml",  # Python (modern)
        "setup.py",  # Python
        "setup.cfg",  # Python
        "requirements.txt",  # Python
        "requirements-dev.txt",  # Python
        "Pipfile",  # Python (pipenv)
        "Pipfile.lock",  # Python (pipenv)
        "poetry.lock",  # Python (poetry)
        "go.mod",  # Go
        "go.sum",  # Go
        "pom.xml",  # Java (Maven)
        "build.gradle",  # Java/Kotlin (Gradle)
        "gradle.properties",  # Gradle
        "settings.gradle",  # Gradle
        "composer.json",  # PHP
        "composer.lock",  # PHP
        "Gemfile",  # Ruby
        "Gemfile.lock",  # Ruby
        "mix.exs",  # Elixir
        "mix.lock",  # Elixir
        "pubspec.yaml",  # Dart/Flutter
        "pubspec.lock",  # Dart/Flutter
        "dub.json",  # D
        "cabal.project",  # Haskell
        "stack.yaml",  # Haskell
        "project.clj",  # Clojure
        "deps.edn",  # Clojure
        "build.sbt",  # Scala
        "CMakeLists.txt",  # C/C++
        "Makefile",  # Make
        "configure.ac",  # Autotools
        "configure.in",  # Autotools
        "meson.build",  # Meson
        "conanfile.txt",  # Conan
        "vcpkg.json",  # vcpkg
    }

    # Build and deployment files
    BUILD_FILES = {
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "Makefile",
        "CMakeLists.txt",
        "build.gradle",
        "pom.xml",
        "setup.py",
        "build.xml",
        "webpack.config.js",
        "rollup.config.js",
        "vite.config.js",
        "tsconfig.json",
        "babel.config.js",
        ".babelrc",
        "gulpfile.js",
        "gruntfile.js",
    }

    # CI/CD configuration files
    CI_CD_FILES = {
        ".github/workflows",  # GitHub Actions (directory)
        ".gitlab-ci.yml",  # GitLab CI
        "Jenkinsfile",  # Jenkins
        ".travis.yml",  # Travis CI
        "appveyor.yml",  # AppVeyor
        ".circleci/config.yml",  # CircleCI
        "azure-pipelines.yml",  # Azure Pipelines
        "bitbucket-pipelines.yml",  # Bitbucket Pipelines
        ".buildkite/pipeline.yml",  # Buildkite
        "wercker.yml",  # Wercker
        "drone.yml",  # Drone CI
        ".drone.yml",  # Drone CI
        "tox.ini",  # Python tox
        "noxfile.py",  # Python nox
    }

    # Documentation file patterns
    DOCUMENTATION_FILES = {
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "CHANGELOG.md",
        "CHANGELOG.rst",
        "CHANGELOG.txt",
        "CHANGELOG",
        "HISTORY.md",
        "HISTORY.rst",
        "HISTORY.txt",
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "CONTRIBUTING.md",
        "CONTRIBUTING.rst",
        "CONTRIBUTING.txt",
        "CODE_OF_CONDUCT.md",
        "CODE_OF_CONDUCT.rst",
        "CODE_OF_CONDUCT.txt",
        "SECURITY.md",
        "SECURITY.rst",
        "SECURITY.txt",
        "AUTHORS.md",
        "AUTHORS.rst",
        "AUTHORS.txt",
        "AUTHORS",
        "CREDITS.md",
        "CREDITS.rst",
        "CREDITS.txt",
        "CREDITS",
        "MAINTAINERS.md",
        "MAINTAINERS.rst",
        "MAINTAINERS.txt",
        "docs/",
        "doc/",
        "documentation/",  # Common doc directories
    }

    # Test file patterns
    TEST_PATTERNS = {
        "test_*.py",
        "*_test.py",
        "tests.py",  # Python
        "test_*.rs",
        "*_test.rs",
        "tests.rs",  # Rust
        "*.test.js",
        "*.spec.js",
        "test.js",  # JavaScript
        "*.test.ts",
        "*.spec.ts",
        "test.ts",  # TypeScript
        "*Test.java",
        "*Tests.java",  # Java
        "*_test.go",
        "*Test.go",  # Go
        "test_*.cpp",
        "*_test.cpp",  # C++
        "*Test.cs",
        "*Tests.cs",  # C#
        "*_test.rb",
        "*Test.rb",  # Ruby
        "*Test.scala",
        "*Spec.scala",  # Scala
        "*Test.kt",
        "*Tests.kt",  # Kotlin
        "*Tests.swift",
        "*Test.swift",  # Swift
    }

    # Ignore patterns (common directories/files to skip)
    IGNORE_PATTERNS = {
        # Version control
        ".git/",
        ".svn/",
        ".hg/",
        ".bzr/",
        # Dependencies
        "node_modules/",
        "vendor/",
        "lib/",
        "libs/",
        # Build outputs
        "target/",
        "build/",
        "dist/",
        "out/",
        "bin/",
        # Python
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".tox/",
        "venv/",
        ".venv/",
        # Rust
        # Java
        ".gradle/",
        # .NET
        "obj/",
        # IDE files
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        "Thumbs.db",
        # Logs and temps
        "*.log",
        "logs/",
        "tmp/",
        "temp/",
        ".tmp/",
        # Coverage
        "coverage/",
        ".coverage",
        ".nyc_output/",
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "django": {"manage.py", "django/", "settings.py"},
        "flask": {"app.py", "flask/", "wsgi.py"},
        "fastapi": {"main.py", "fastapi/", "uvicorn"},
        "express": {"app.js", "server.js", "express"},
        "react": {"src/App.js", "src/App.tsx", "public/index.html", "react"},
        "vue": {"src/App.vue", "vue.config.js", "vue"},
        "angular": {"src/app/", "angular.json", "@angular"},
        "nextjs": {"pages/", "next.config.js", "next"},
        "nuxt": {"nuxt.config.js", "pages/", "nuxt"},
        "svelte": {"src/App.svelte", "svelte.config.js", "svelte"},
        "spring": {"src/main/java/", "pom.xml", "@SpringBootApplication"},
        "springboot": {"application.properties", "application.yml"},
        "rails": {"Gemfile", "config/application.rb", "app/"},
        "laravel": {"artisan", "composer.json", "app/Http/"},
        "symfony": {"symfony.lock", "config/", "src/"},
        "dotnet": {"*.csproj", "*.sln", "Program.cs"},
        "gin": {"main.go", "gin"},
        "echo": {"main.go", "echo"},
        "axum": {"Cargo.toml", "axum"},
        "actix": {"Cargo.toml", "actix-web"},
        "warp": {"Cargo.toml", "warp"},
    }

    @classmethod
    def get_language_from_extension(cls, file_path: Path) -> str:
        """Get programming language from file extension."""
        extension = file_path.suffix.lower()

        for language, extensions in cls.LANGUAGE_EXTENSIONS.items():
            if extension in extensions:
                return language

        return "unknown"

    @classmethod
    def is_source_file(cls, file_path: Path) -> bool:
        """Check if file is a source code file."""
        extension = file_path.suffix.lower()

        for extensions in cls.LANGUAGE_EXTENSIONS.values():
            if extension in extensions:
                return True

        return False

    @classmethod
    def is_test_file(cls, file_path: Path) -> bool:
        """Check if file appears to be a test file."""
        filename = file_path.name.lower()

        # Check for test patterns
        test_indicators = ["test", "spec", "tests", "__test__", "__tests__"]

        return any(indicator in filename for indicator in test_indicators)

    @classmethod
    def is_config_file(cls, file_path: Path) -> bool:
        """Check if file is a configuration file."""
        filename = file_path.name

        return (
            filename in cls.CONFIG_FILES
            or filename in cls.BUILD_FILES
            or file_path.suffix.lower()
            in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
        )

    @classmethod
    def is_documentation_file(cls, file_path: Path) -> bool:
        """Check if file is documentation."""
        filename = file_path.name
        extension = file_path.suffix.lower()

        return filename.upper() in {
            f.upper() for f in cls.DOCUMENTATION_FILES
        } or extension in {".md", ".rst", ".txt", ".pdf", ".doc", ".docx"}

    @classmethod
    def should_ignore(cls, file_path: Path, project_root: Path) -> bool:
        """Check if file should be ignored during analysis."""
        relative_path = file_path.relative_to(project_root)
        path_str = str(relative_path).lower()

        for pattern in cls.IGNORE_PATTERNS:
            if pattern.endswith("/"):
                # Directory pattern
                if (
                    path_str.startswith(pattern[:-1])
                    or f"/{pattern[:-1]}/" in f"/{path_str}"
                ):
                    return True
            # File pattern
            elif pattern.replace("*", "") in path_str:
                return True

        return False

    @classmethod
    def detect_frameworks(cls, project_path: Path) -> Dict[str, float]:
        """Detect frameworks based on file patterns."""
        detected: Dict[str, float] = {}

        for framework, patterns in cls.FRAMEWORK_PATTERNS.items():
            score = 0.0

            for pattern in patterns:
                if "/" in pattern:
                    # Directory or specific path pattern
                    if (project_path / pattern).exists():
                        score += 5.0
                # File pattern or content pattern
                elif any(
                    f.name == pattern for f in project_path.rglob("*") if f.is_file()
                ):
                    score += 3.0

            if score > 0:
                detected[framework] = score

        return detected


# Placeholder classes for test compatibility
class ConfigFileDetector:
    """Configuration file detection system."""

    def __init__(self, project_path: str | Path | None = None) -> None:
        self.project_path = Path(project_path) if project_path else None

    def detect_config_files(
        self, project_path: str | Path | None = None
    ) -> Dict[str, List[str]]:
        """Detect configuration files in project grouped by language/category."""
        target_path = Path(project_path) if project_path else self.project_path
        if not target_path or not target_path.exists():
            return {}

        config_files: dict[str, list[str]] = {
            "python": [],
            "javascript": [],
            "rust": [],
            "docker": [],
            "general": [],
        }

        for file_path in target_path.rglob("*"):
            if file_path.is_file() and (
                FilePatterns.is_config_file(file_path)
                or file_path.name.startswith(".docker")
            ):
                filename = file_path.name
                relative_path = str(file_path.relative_to(target_path))

                # Categorize by language/type
                if filename in {
                    "pyproject.toml",
                    "setup.py",
                    "requirements.txt",
                    "pytest.ini",
                    "Pipfile",
                    "setup.cfg",
                }:
                    config_files["python"].append(relative_path)
                elif filename in {
                    "package.json",
                    "package-lock.json",
                    "webpack.config.js",
                    "babel.config.js",
                }:
                    config_files["javascript"].append(relative_path)
                elif filename in {"tsconfig.json"}:
                    if "typescript" not in config_files:
                        config_files["typescript"] = []
                    config_files["typescript"].append(relative_path)
                elif filename in {"Cargo.toml", "Cargo.lock", "rust-toolchain.toml"}:
                    config_files["rust"].append(relative_path)
                elif filename in {
                    "Dockerfile",
                    "docker-compose.yml",
                    "docker-compose.yaml",
                } or filename.startswith(".docker"):
                    config_files["docker"].append(relative_path)
                else:
                    config_files["general"].append(relative_path)

        # Remove empty categories and return
        return {k: v for k, v in config_files.items() if v}

    def analyze_config_patterns(self) -> dict:
        """Analyze configuration patterns in project."""
        if self.project_path is None:
            return {"config_types": [], "config_count": 0, "has_secrets": False}

        config_files = self.detect_config_files()
        config_types = set()
        has_secrets = False

        for config_file in config_files:
            file_path = self.project_path / config_file
            ext = file_path.suffix.lower()

            if ext in {".yaml", ".yml"}:
                config_types.add("yaml")
            elif ext == ".json":
                config_types.add("json")
            elif ext == ".toml":
                config_types.add("toml")
            elif ext in {".ini", ".cfg", ".conf"}:
                config_types.add("ini")
            elif file_path.name.startswith(".env"):
                config_types.add("env")
                has_secrets = True

        return {
            "config_types": list(config_types),
            "config_count": len(config_files),
            "has_secrets": has_secrets,
        }


class FilePatternMatcher:
    """Advanced file pattern matching system."""

    def __init__(self, patterns: Optional[List[str]] = None):
        # Default patterns cover common file types
        self.patterns = patterns or [
            "*.py",
            "*.js",
            "*.ts",
            "*.rs",
            "*.go",
            "*.java",
            "*.cpp",
            "*.c",
            "*.h",
            "*.css",
            "*.html",
            "*.md",
            "*.json",
            "*.yaml",
            "*.toml",
            "Dockerfile",
        ]

    def match(self, filepath: str) -> bool:
        """Basic pattern matching."""
        return any(pattern in filepath for pattern in self.patterns)

    def matches_extension(self, file_path: Path, extensions: List[str]) -> bool:
        """Check if file matches any of the given extensions."""
        return file_path.suffix.lower() in [ext.lower() for ext in extensions]

    def matches_filename(self, file_path: Path, patterns: List[str]) -> bool:
        """Check if filename matches any of the given patterns."""
        filename = file_path.name
        for pattern in patterns:
            if "*" in pattern:
                # Simple glob-like matching
                import fnmatch

                if fnmatch.fnmatch(filename, pattern):
                    return True
            elif pattern == filename:
                return True
        return False

    def find_files(self, root_path: Path, pattern: str) -> Any:
        """Find files matching glob pattern."""
        return root_path.glob(pattern)

    def matches_content_pattern(self, file_path: Path, regex_pattern: str) -> bool:
        """Check if file content matches regex pattern."""
        try:
            import re

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return bool(re.search(regex_pattern, content))
        except Exception:
            return False


class LanguageDetector:
    """Advanced language detection system."""

    def __init__(self) -> None:
        self.language_patterns = {
            "python": [r"def\s+\w+\(.*\):", r"import\s+\w+", r"from\s+\w+\s+import"],
            "javascript": [
                r"function\s+\w+\(.*\)",
                r"const\s+\w+\s*=",
                r"console\.log",
            ],
            "rust": [r"fn\s+\w+\(.*\)", r"use\s+\w+", r"let\s+\w+\s*="],
            "go": [r"func\s+\w+\(.*\)", r"package\s+\w+", r"import\s+\("],
            "java": [r"public\s+class\s+\w+", r"public\s+static\s+void\s+main"],
            "bash": [r"#!/bin/bash", r"#!/bin/sh"],
        }

    def detect_language(self, file_path: Any) -> str:
        """Detect language from file path or content."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # First try extension-based detection
        extension = file_path.suffix.lower()
        for language, extensions in FilePatterns.LANGUAGE_EXTENSIONS.items():
            if extension in extensions:
                return language

        # Try shebang detection
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                first_line = content.split("\n")[0] if content else ""

                if first_line.startswith("#!"):
                    if "python" in first_line:
                        return "python"
                    if "node" in first_line:
                        return "javascript"
                    if (
                        "bash" in first_line
                        or "/bin/sh" in first_line
                        or "/usr/bin/sh" in first_line
                    ):
                        return "bash"

                # Try content pattern matching
                for language, patterns in self.language_patterns.items():
                    import re

                    for pattern in patterns:
                        if re.search(pattern, content):
                            return language

            except Exception:
                pass

        return "unknown"

    def detect_primary_language(self, project_path: str) -> str:
        """Detect the primary language of a project."""
        stats = self.get_language_stats(project_path)
        if stats:
            return max(stats.keys(), key=lambda x: stats[x])
        return "unknown"

    def get_language_stats(self, project_path: str) -> Dict[str, int]:
        """Get language statistics for a project."""
        path = Path(project_path)
        stats: dict[str, int] = {}

        for file_path in path.rglob("*"):
            if file_path.is_file() and not FilePatterns.should_ignore(file_path, path):
                language = self.detect_language(file_path)
                if language != "unknown":
                    stats[language] = stats.get(language, 0) + 1

        return stats

    def analyze_project_languages(self, project_path: Path) -> Dict[str, Any]:
        """Analyze languages in project with detailed statistics."""

        stats = self.get_language_stats(str(project_path))
        total_files = sum(stats.values())

        # Return format expected by tests: language -> {"file_count": count}
        result = {}
        for language, count in stats.items():
            result[language] = {"file_count": count}

        return result


@dataclass
class AdvancedPatternRule:
    """Advanced pattern rule configuration."""

    name: Optional[str] = None
    description: Optional[str] = None
    patterns: Optional[List[str]] = None
    priority: float = 1.0
    required_patterns: Optional[List[str]] = None
    weight_factors: Optional[Dict[str, float]] = None
    pattern: Optional[str] = None
    action: str = "include"


class PatternRule:
    """Advanced pattern rule for project detection."""

    def __init__(
        self, config: Optional[AdvancedPatternRule] = None, **kwargs: Any
    ) -> None:
        # Support both config object and individual parameters
        if config:
            self.name = config.name or "unnamed_rule"
            self.description = config.description or ""
            self.patterns = config.patterns or []
            self.priority = config.priority
            self.required_patterns = config.required_patterns or []
            self.weight_factors = config.weight_factors or {}
            self.action = config.action
            # Handle legacy pattern parameter
            if config.pattern and not self.patterns:
                self.pattern = config.pattern
                self.patterns = [config.pattern]
            else:
                self.pattern = self.patterns[0] if self.patterns else ""
        else:
            # Legacy constructor support
            self.name = kwargs.get("name", "unnamed_rule")
            self.description = kwargs.get("description", "")
            self.patterns = kwargs.get("patterns", [])
            self.priority = kwargs.get("priority", 1.0)
            self.required_patterns = kwargs.get("required_patterns", [])
            self.weight_factors = kwargs.get("weight_factors", {})
            self.action = kwargs.get("action", "include")
            pattern = kwargs.get("pattern")
            if pattern and not self.patterns:
                self.pattern = pattern
                self.patterns = [pattern]
            else:
                self.pattern = self.patterns[0] if self.patterns else ""
        # Constructor handled above

    def matches(self, file_path: str) -> bool:
        """Legacy compatibility method."""
        return self.pattern in file_path

    def apply(self, file_path: str) -> bool:
        """Legacy compatibility method."""
        return self.action == "include"

    def evaluate_match(self, project_path: Path) -> Any:
        """Evaluate pattern rule against project."""
        from collections import namedtuple

        MatchResult = namedtuple(
            "MatchResult", ["matches", "confidence", "matched_patterns", "score"]
        )

        matched_patterns = []
        total_score = 0.0

        # Check each pattern
        for pattern in self.patterns:
            if self._pattern_exists(project_path, pattern):
                matched_patterns.append(pattern)
                weight = self.weight_factors.get(pattern, 1.0)
                total_score += weight

        # Check required patterns
        required_satisfied = all(
            self._pattern_exists(project_path, req_pattern)
            for req_pattern in self.required_patterns
        )

        matches = required_satisfied and len(matched_patterns) > 0
        confidence = min(total_score / max(len(self.patterns), 1), 1.0)

        return MatchResult(
            matches=matches,
            confidence=confidence,
            matched_patterns=matched_patterns,
            score=total_score,
        )

    def _pattern_exists(self, project_path: Path, pattern: str) -> bool:
        """Check if pattern exists in project."""
        if "*" in pattern:
            # Glob pattern
            return len(list(project_path.glob(pattern))) > 0
        # Exact file/directory match
        return (project_path / pattern).exists()


class ProjectTypeDetector:
    """Project type detection system."""

    def __init__(self) -> None:
        self.detection_rules: List[Dict[str, Any]] = []
        self.language_detector = LanguageDetector()

    def detect_project_type(self, project_path: str) -> str:
        """Detect the primary project type."""
        path = Path(project_path)
        if not path.exists():
            return "unknown"

        # Fall back to primary language
        primary_lang = self.language_detector.detect_primary_language(project_path)
        lang_stats = self.language_detector.get_language_stats(project_path)

        # Special handling for really empty projects
        if not lang_stats:
            return "unknown"

        # Check for specific project indicators across all subdirectories
        all_files = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                all_files.append(file_path.name)

        # Count different project type indicators
        project_indicators = {
            "python": {"setup.py", "pyproject.toml", "requirements.txt", "Pipfile"},
            "rust": {"Cargo.toml"},
            "javascript": {"package.json"},
            "go": {"go.mod"},
            "java": {"pom.xml", "build.gradle", "gradle.properties"},
        }

        detected_types = []
        for project_type, indicators in project_indicators.items():
            if any(indicator in all_files for indicator in indicators):
                detected_types.append(project_type)

        # Multi-language project if multiple types detected
        if len(detected_types) > 1:
            return "multi_language"

        # Single language project
        if detected_types:
            return detected_types[0]

        return primary_lang if primary_lang != "unknown" else "unknown"

    def get_project_metadata(self, project_path: str) -> Dict[str, Any]:
        """Get comprehensive project metadata."""
        project_type = self.detect_project_type(project_path)
        frameworks = FilePatterns.detect_frameworks(Path(project_path))

        # Determine build system
        build_system = "unknown"
        path = Path(project_path)
        if (path / "setup.py").exists():
            build_system = "setuptools"
        elif (path / "pyproject.toml").exists():
            build_system = "pyproject"
        elif (path / "Cargo.toml").exists():
            build_system = "cargo"
        elif (path / "package.json").exists():
            build_system = "npm"
        elif (path / "pom.xml").exists():
            build_system = "maven"
        elif (path / "build.gradle").exists():
            build_system = "gradle"

        primary_framework = (
            max(frameworks.keys(), key=lambda x: frameworks[x])
            if frameworks
            else "none"
        )

        return {
            "type": project_type,
            "framework": primary_framework,
            "build_system": build_system,
            "frameworks": frameworks,
            "language_stats": self.language_detector.get_language_stats(project_path),
        }

    def add_detection_rule(self, rule: Any) -> None:
        """Add custom detection rule."""
        self.detection_rules.append(rule)

    def get_detection_details(self, project_path: str) -> Dict[str, Any]:
        """Get detailed detection information."""
        path = Path(project_path)
        project_type = self.detect_project_type(project_path)
        metadata = self.get_project_metadata(project_path)

        # Additional details
        project_files = [f.name for f in path.iterdir() if f.is_file()]
        indicators = []

        # Re-run detection logic to get detected_types
        all_files = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                all_files.append(file_path.name)

        project_indicators = {
            "python": {"setup.py", "pyproject.toml", "requirements.txt", "Pipfile"},
            "rust": {"Cargo.toml"},
            "javascript": {"package.json"},
            "go": {"go.mod"},
            "java": {"pom.xml", "build.gradle", "gradle.properties"},
        }

        detected_types = []
        for ptype, pindicators in project_indicators.items():
            if any(indicator in all_files for indicator in pindicators):
                detected_types.append(ptype)

        # Project type indicators
        if project_type == "python":
            indicators = [
                f
                for f in project_files
                if f in {"setup.py", "pyproject.toml", "requirements.txt", "Pipfile"}
            ]
        elif project_type == "rust":
            indicators = [f for f in project_files if f == "Cargo.toml"]
        elif project_type == "javascript":
            indicators = [f for f in project_files if f == "package.json"]

        confidence = 0.9 if indicators else (0.3 if project_type == "unknown" else 0.5)

        # Add languages list for multi-language projects
        languages = []
        if project_type == "multi_language":
            languages = detected_types
        elif project_type != "unknown":
            languages = [project_type]

        return {
            "project_type": project_type,
            "confidence": confidence,
            "indicators": indicators,
            "metadata": metadata,
            "languages": languages,
            "all_files": project_files[:10],  # Limit for readability
        }
