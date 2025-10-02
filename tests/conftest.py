from pathlib import Path

import pytest

# Types used by fixtures
from claude_builder.core.analyzer import (
    DomainInfo,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
)
from claude_builder.core.models import (
    ArchitecturePattern,
    ComplexityLevel,
    DevelopmentEnvironment,
    FileSystemInfo,
    ProjectType,
)


def create_test_project(base_dir: Path, language: str) -> Path:
    """Create a minimal test project structure for the given language.

    Supports: "python", "rust", "javascript".
    Returns the project path.
    """
    project = base_dir / f"sample_{language}_project"
    project.mkdir(parents=True, exist_ok=True)

    if language == "python":
        (project / "pyproject.toml").write_text(
            """
[project]
name = "sample"
version = "0.1.0"
""".strip()
        )
        (project / "sample.py").write_text("print('hello')\n")
        # Add a main module to satisfy CLI/tool heuristics
        (project / "main.py").write_text(
            "if __name__ == '__main__':\n    print('hi')\n"
        )
        (project / "tests").mkdir(exist_ok=True)
    elif language == "rust":
        (project / "Cargo.toml").write_text(
            """
[package]
name = "sample"
version = "0.1.0"
edition = "2021"
""".strip()
        )
        (project / "src").mkdir(exist_ok=True)
        (project / "src" / "main.rs").write_text('fn main() { println!("hi"); }\n')
    elif language == "javascript":
        (project / "package.json").write_text('{"name": "sample", "version": "0.1.0"}')
        (project / "index.js").write_text("console.log('hi');\n")
    else:
        # Fallback empty project
        (project / "README.md").write_text("# sample\n")

    return project


# Removed pytest_collection_modifyitems - test_project_command_yaml_output_no_yaml
# is now fixed by patching sys.modules in addition to __import__


# --- Common fixtures used across the test suite ---


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory as a Path.

    Many tests reference a `temp_dir` fixture; map it to pytest's `tmp_path`.
    """
    return tmp_path


@pytest.fixture
def sample_python_project(temp_dir: Path) -> Path:
    """Create a minimal sample Python project and return its path."""
    return create_test_project(temp_dir, "python")


@pytest.fixture
def sample_rust_project(temp_dir: Path) -> Path:
    """Create a minimal sample Rust project (when needed)."""
    return create_test_project(temp_dir, "rust")


@pytest.fixture
def sample_javascript_project(temp_dir: Path) -> Path:
    """Create a minimal sample JavaScript project (when needed)."""
    return create_test_project(temp_dir, "javascript")


# --- Additional shared fixtures required by multiple suites ---


@pytest.fixture
def sample_project_path(sample_python_project: Path) -> Path:
    """Alias fixture expected by some tests."""
    return sample_python_project


@pytest.fixture
def sample_analysis(sample_python_project: Path) -> ProjectAnalysis:
    """Provide a realistic ProjectAnalysis structure for tests.

    Mirrors the structure used in CLI tests so intelligence/config
    suites can consume consistent data without hitting the analyzer.
    """
    return ProjectAnalysis(
        project_path=sample_python_project,
        analysis_confidence=85.5,
        analysis_timestamp="2025-01-01T00:00:00",
        analyzer_version="1.0.0",
        language_info=LanguageInfo(
            primary="python",
            secondary=["javascript"],
            confidence=90.0,
            file_counts={"python": 10, "javascript": 2},
            total_lines=1000,
        ),
        framework_info=FrameworkInfo(
            primary="fastapi",
            secondary=["pytest"],
            confidence=80.0,
            version="0.100.0",
            config_files=["requirements.txt"],
        ),
        domain_info=DomainInfo(
            domain="web_development",
            confidence=75.0,
            indicators=["REST API", "web framework"],
            specialized_patterns=["microservice"],
        ),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MODERATE,
        architecture_pattern=ArchitecturePattern.MVC,
        dev_environment=DevelopmentEnvironment(
            package_managers=["pip"],
            testing_frameworks=["pytest"],
            ci_cd_systems=["github-actions"],
            containerization=["docker"],
            databases=["postgresql"],
            # include newer fields used in tables
            infrastructure_as_code=["terraform"],
            orchestration_tools=["kubernetes"],
            secrets_management=["vault"],
            observability=["prometheus"],
            security_tools=["bandit"],
            data_pipeline=["airflow"],
            mlops_tools=["mlflow"],
        ),
        filesystem_info=FileSystemInfo(
            total_files=50,
            total_directories=10,
            source_files=30,
            test_files=10,
            config_files=5,
            documentation_files=5,
            asset_files=0,
            ignore_patterns=[],
            root_files=["README.md"],
        ),
        warnings=["Missing test coverage"],
        suggestions=["Add more unit tests"],
    )


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """Provide a temporary path representing a git repo.

    Current tests only verify analyzer works with a repo path; advanced
    git operations are skipped. We return a clean temp directory and let
    tests populate files as needed.
    """
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Provide a real initialized git repository for integration tests.

    This fixture creates a temporary directory with an initialized git repository,
    complete with initial commit. Useful for tests that require actual git
    operations (commits, branches, etc.).
    """
    import subprocess

    repo_path = tmp_path / "test_repo"
    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repository
    subprocess.run(
        ["git", "init"], cwd=repo_path, check=True, capture_output=True, text=True
    )

    # Configure git for the test environment
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )

    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(
        ["git", "add", "."], cwd=repo_path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )

    return repo_path
