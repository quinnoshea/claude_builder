"""Global test configuration and fixtures for Claude Builder tests."""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

# Add src directory to Python path for src layout
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from claude_builder.core.config import Config, ConfigManager
from claude_builder.core.models import (
    ComplexityLevel,
    DevelopmentEnvironment,
    DomainInfo,
    FileSystemInfo,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_project_dir(temp_dir: Path) -> Path:
    """Create a temporary directory with sample project structure - matches guide expectations."""
    project_path = temp_dir / "test_project"
    project_path.mkdir()
    
    # Create basic Python project structure
    (project_path / "setup.py").write_text("""
from setuptools import setup
setup(name="test-project", version="0.1.0")
""")
    
    (project_path / "requirements.txt").write_text("requests>=2.25.0\n")
    
    src_dir = project_path / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
    
    return str(project_path)


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
def sample_python_project(temp_dir: Path) -> Path:
    """Create a comprehensive Python project for integration testing."""
    project_dir = temp_dir / "python_project"
    project_dir.mkdir()

    # Project metadata files
    (project_dir / "README.md").write_text("""# Python Test Project
A comprehensive test project for integration testing.

## Features
- CLI interface with Click
- Web API with FastAPI
- Database integration
- Testing with pytest
""")
    
    (project_dir / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project for integration testing"
dependencies = [
    "click>=8.0.0",
    "fastapi>=0.95.0",
    "uvicorn>=0.20.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
""")

    (project_dir / "requirements.txt").write_text("""click>=8.0.0
fastapi>=0.95.0
uvicorn>=0.20.0
pydantic>=2.0.0
requests>=2.25.0
""")

    # Main source structure
    src_dir = project_dir / "src" / "testproject"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test project package."""\n__version__ = "0.1.0"')
    
    # CLI module
    (src_dir / "cli.py").write_text("""#!/usr/bin/env python3
\"\"\"Command line interface for test project.\"\"\"
import click

@click.group()
def main():
    \"\"\"Test project CLI.\"\"\"
    pass

@main.command()
@click.option('--name', default='World', help='Name to greet')
def hello(name):
    \"\"\"Say hello.\"\"\"
    click.echo(f'Hello, {name}!')

if __name__ == '__main__':
    main()
""")

    # Core business logic
    (src_dir / "core.py").write_text("""\"\"\"Core business logic for test project.\"\"\"
from typing import List, Dict, Any

class ProjectManager:
    \"\"\"Manages project operations.\"\"\"
    
    def __init__(self):
        self.projects: List[Dict[str, Any]] = []
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        \"\"\"Create a new project.\"\"\"
        project = {
            "id": len(self.projects) + 1,
            "name": name,
            "description": description,
            "status": "active"
        }
        self.projects.append(project)
        return project
    
    def get_project(self, project_id: int) -> Dict[str, Any]:
        \"\"\"Get project by ID.\"\"\"
        for project in self.projects:
            if project["id"] == project_id:
                return project
        raise ValueError(f"Project {project_id} not found")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        \"\"\"List all projects.\"\"\"
        return self.projects.copy()
""")

    # API module
    (src_dir / "api.py").write_text("""\"\"\"FastAPI web application.\"\"\"
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from .core import ProjectManager

app = FastAPI(title="Test Project API", version="0.1.0")
manager = ProjectManager()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class Project(BaseModel):
    id: int
    name: str
    description: str
    status: str

@app.get("/")
async def root():
    return {"message": "Test Project API"}

@app.post("/projects/", response_model=Project)
async def create_project(project: ProjectCreate):
    return manager.create_project(project.name, project.description)

@app.get("/projects/", response_model=List[Project])
async def list_projects():
    return manager.list_projects()

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    try:
        return manager.get_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
""")

    # Configuration module
    (src_dir / "config.py").write_text("""\"\"\"Configuration management.\"\"\"
import os
from pathlib import Path
from typing import Optional

class Config:
    \"\"\"Application configuration.\"\"\"
    
    def __init__(self):
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.api_key = os.getenv("API_KEY")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def is_development(self) -> bool:
        return self.debug
    
    def get_data_dir(self) -> Path:
        return Path.home() / ".testproject"
""")

    # Tests structure
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    
    (tests_dir / "conftest.py").write_text("""\"\"\"Test configuration.\"\"\"
import pytest
from pathlib import Path
from src.testproject.core import ProjectManager

@pytest.fixture
def project_manager():
    return ProjectManager()

@pytest.fixture
def sample_project_data():
    return {
        "name": "Test Project",
        "description": "A test project for testing"
    }
""")

    (tests_dir / "test_core.py").write_text("""\"\"\"Tests for core module.\"\"\"
import pytest
from src.testproject.core import ProjectManager

def test_create_project(project_manager):
    project = project_manager.create_project("Test", "Description")
    assert project["name"] == "Test"
    assert project["description"] == "Description"
    assert project["status"] == "active"

def test_get_project(project_manager):
    project = project_manager.create_project("Test", "Description")
    retrieved = project_manager.get_project(project["id"])
    assert retrieved == project

def test_list_projects(project_manager):
    project1 = project_manager.create_project("Test1", "Desc1")
    project2 = project_manager.create_project("Test2", "Desc2")
    projects = project_manager.list_projects()
    assert len(projects) == 2
    assert project1 in projects
    assert project2 in projects
""")

    (tests_dir / "test_api.py").write_text("""\"\"\"Tests for API module.\"\"\"
import pytest
from fastapi.testclient import TestClient
from src.testproject.api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Test Project API"}

def test_create_project(client):
    response = client.post("/projects/", json={"name": "Test", "description": "Desc"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test"
    assert data["description"] == "Desc"
""")

    # Documentation
    docs_dir = project_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("""# Documentation

This is the documentation directory for the test project.
""")

    # Configuration files
    (project_dir / ".gitignore").write_text("""__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

.coverage
htmlcov/
.pytest_cache/
""")

    return project_dir


@pytest.fixture
def sample_rust_project(temp_dir: Path) -> Path:
    """Create a sample Rust project for testing."""
    project_dir = temp_dir / "rust_project"
    project_dir.mkdir()
    
    # Create Cargo.toml
    (project_dir / "Cargo.toml").write_text("""[package]
name = "test-rust-project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
""")
    
    # Create src directory and main.rs
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.rs").write_text("""fn main() {
    println!("Hello, world!");
}
""")
    
    return project_dir


@pytest.fixture
def sample_javascript_project(temp_dir: Path) -> Path:
    """Create a sample JavaScript project for testing."""
    project_dir = temp_dir / "javascript_project"
    project_dir.mkdir()
    
    # Create package.json
    (project_dir / "package.json").write_text("""{
  "name": "test-javascript-project",
  "version": "1.0.0",
  "description": "A test JavaScript project",
  "main": "src/index.js",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  }
}""")
    
    # Create src directory and index.js
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "index.js").write_text("""const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
""")
    
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
            file_counts={"python": 10, "yaml": 2, "markdown": 1}
        ),
        framework_info=FrameworkInfo(
            primary="fastapi",
            secondary=["pydantic"],
            confidence=85.0,
            version="0.95.0"
        ),
        project_type=ProjectType.API_SERVICE,
        complexity_level=ComplexityLevel.MEDIUM,
        filesystem_info=FileSystemInfo(
            total_files=42,
            source_files=25,
            test_files=8,
            config_files=5,
            documentation_files=4
        ),
        domain_info=DomainInfo(
            domain="web_api",
            confidence=90.0,
            indicators=["rest_api", "authentication", "database"]
        ),
        analysis_confidence=90.0,
        dev_environment=DevelopmentEnvironment(
            package_managers=["pip"],
            testing_frameworks=["pytest"],
            databases=["postgresql"]
        )
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
def mock_git_repo(git_repo: Path) -> Path:
    """Alias for git_repo fixture for backward compatibility."""
    return git_repo


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
            return json.dumps(self.json_data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def mock_urlopen(request, timeout=None):
        url = request.get_full_url() if hasattr(request, "get_full_url") else str(request)
        if url in responses:
            return MockResponse(responses[url])
        raise Exception(f"Mock URL not found: {url}")

    return mock_urlopen


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files after each test."""
    return
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
        (src_dir / "main.rs").write_text('fn main() {\n    println!("Hello, world!");\n}')

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
