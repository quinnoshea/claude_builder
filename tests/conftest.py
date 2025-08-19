"""Global test configuration and fixtures for Claude Builder tests."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock

import pytest

from claude_builder.core.models import (
    ProjectAnalysis, LanguageInfo, FrameworkInfo, DomainInfo, 
    FilesystemInfo, ProjectType, ComplexityLevel
)
from claude_builder.core.config import Config, ConfigManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_project_path(temp_dir: Path) -> Path:
    """Create a sample project directory structure."""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir()
    
    # Create basic files
    (project_dir / "README.md").write_text("# Sample Project\nA test project.")
    (project_dir / "main.py").write_text("#!/usr/bin/env python3\nprint('Hello, World!')")
    (project_dir / "requirements.txt").write_text("requests>=2.25.0\nclick>=8.0.0")
    (project_dir / "setup.py").write_text("from setuptools import setup\nsetup(name='sample')")
    
    # Create source directory
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "core.py").write_text("def main():\n    pass")
    
    # Create tests directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_core.py").write_text("def test_main():\n    assert True")
    
    return project_dir


@pytest.fixture
def sample_analysis() -> ProjectAnalysis:
    """Create a sample project analysis for testing."""
    return ProjectAnalysis(
        project_path=Path("/test/project"),
        language_info=LanguageInfo(
            primary="python",
            secondary=["yaml", "markdown"],
            confidence=95.0,
            version_info={"python": "3.11"}
        ),
        framework_info=FrameworkInfo(
            primary="fastapi",
            secondary=["pydantic"],
            confidence=85.0,
            details={"web_framework": True}
        ),
        project_type=ProjectType.WEB_API,
        complexity_level=ComplexityLevel.MEDIUM,
        filesystem_info=FilesystemInfo(
            total_files=42,
            source_files=25,
            test_files=8,
            config_files=5,
            doc_files=4,
            largest_files=["main.py", "models.py", "api.py"]
        ),
        domain_info=DomainInfo(
            domain="web_api",
            confidence=90.0,
            features=["rest_api", "authentication", "database"]
        ),
        analysis_confidence=90.0,
        dependencies={"requests": "2.28.0", "fastapi": "0.95.0"},
        build_system="pip",
        metadata={"license": "MIT", "author": "Test Author"}
    )


@pytest.fixture
def default_config() -> Config:
    """Create a default configuration for testing."""
    return Config()


@pytest.fixture
def config_manager() -> ConfigManager:
    """Create a config manager for testing."""
    return ConfigManager()


@pytest.fixture
def git_repo(temp_dir: Path) -> Path:
    """Create a git repository for testing."""
    repo_dir = temp_dir / "git_repo"
    repo_dir.mkdir()
    
    # Initialize git repository
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    
    # Create initial commit
    (repo_dir / "README.md").write_text("# Test Repository")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    return repo_dir


@pytest.fixture
def sample_template_metadata() -> Dict[str, Any]:
    """Create sample template metadata for testing."""
    return {
        "name": "test-template",
        "version": "1.0.0",
        "description": "A test template",
        "author": "test-author",
        "category": "testing",
        "languages": ["python"],
        "frameworks": ["fastapi"],
        "project_types": ["web_api"],
        "min_builder_version": "0.1.0",
        "license": "MIT",
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for template marketplace testing."""
    responses = {
        "https://raw.githubusercontent.com/claude-builder/templates/main/index.json": {
            "templates": [
                {
                    "name": "python-web",
                    "version": "1.0.0",
                    "description": "Python web application template",
                    "author": "official",
                    "category": "web",
                    "languages": ["python"],
                    "frameworks": ["fastapi", "django"],
                    "project_types": ["web_api"]
                }
            ]
        }
    }
    
    class MockResponse:
        def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
            self.json_data = json_data
            self.status_code = status_code
        
        def read(self) -> bytes:
            return json.dumps(self.json_data).encode('utf-8')
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    def mock_urlopen(request, timeout=None):
        url = request.get_full_url() if hasattr(request, 'get_full_url') else str(request)
        if url in responses:
            return MockResponse(responses[url])
        raise Exception(f"Mock URL not found: {url}")
    
    return mock_urlopen


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files after each test."""
    yield
    # Cleanup happens automatically with temp_dir fixture


# Test utilities
def create_test_project(base_path: Path, project_type: str = "python") -> Path:
    """Create a test project of specified type."""
    project_path = base_path / f"test_{project_type}_project"
    project_path.mkdir(exist_ok=True)
    
    if project_type == "python":
        # Python project structure
        (project_path / "main.py").write_text("#!/usr/bin/env python3\nprint('Hello')")
        (project_path / "requirements.txt").write_text("requests>=2.25.0")
        (project_path / "setup.py").write_text("from setuptools import setup\nsetup(name='test')")
        
    elif project_type == "rust":
        # Rust project structure
        (project_path / "Cargo.toml").write_text("""[package]
name = "test-project"
version = "0.1.0"
edition = "2021"

[dependencies]
""")
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("fn main() {\n    println!(\"Hello, world!\");\n}")
        
    elif project_type == "javascript":
        # JavaScript/Node.js project structure
        (project_path / "package.json").write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test project",
            "main": "index.js",
            "dependencies": {
                "express": "^4.18.0"
            }
        }, indent=2))
        (project_path / "index.js").write_text("console.log('Hello, world!');")
        
    return project_path


def assert_file_exists(file_path: Path, content_contains: str = None):
    """Assert that a file exists and optionally contains specific content."""
    assert file_path.exists(), f"File does not exist: {file_path}"
    if content_contains:
        content = file_path.read_text()
        assert content_contains in content, f"Content '{content_contains}' not found in {file_path}"


def assert_directory_structure(base_path: Path, expected_structure: Dict[str, Any]):
    """Assert that directory structure matches expected layout."""
    for item_name, item_spec in expected_structure.items():
        item_path = base_path / item_name
        
        if isinstance(item_spec, dict):
            # It's a directory
            assert item_path.is_dir(), f"Expected directory: {item_path}"
            assert_directory_structure(item_path, item_spec)
        else:
            # It's a file
            assert item_path.is_file(), f"Expected file: {item_path}"
            if item_spec and isinstance(item_spec, str):
                content = item_path.read_text()
                assert item_spec in content, f"Content '{item_spec}' not found in {item_path}"