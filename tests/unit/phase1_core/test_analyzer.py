"""Tests for Phase 1 core functionality: Project Analyzer.

Tests cover the fundamental project analysis capabilities including:
- Language detection and confidence scoring
- Framework identification
- Project type classification
- Complexity assessment
- Filesystem analysis
- Domain detection
"""


import pytest

from claude_builder.core.analyzer import (
    FrameworkDetector,
    LanguageDetector,
    ProjectAnalyzer,
)
from claude_builder.core.models import ComplexityLevel, ProjectType
from tests.conftest import create_test_project


@pytest.mark.unit
@pytest.mark.phase1
class TestProjectAnalyzer:
    """Test the main ProjectAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initializes with correct defaults."""
        analyzer = ProjectAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "language_detector")
        assert hasattr(analyzer, "framework_detector")

    def test_analyzer_with_config(self):
        """Test analyzer initializes with custom configuration."""
        config = {
            "confidence_threshold": 70,
            "parallel_processing": False,
            "cache_enabled": False
        }
        analyzer = ProjectAnalyzer(config=config)
        assert analyzer.config["confidence_threshold"] == 70
        assert analyzer.config["parallel_processing"] is False

    def test_analyze_python_project(self, temp_dir):
        """Test analysis of a Python project."""
        project_path = create_test_project(temp_dir, "python")
        analyzer = ProjectAnalyzer()

        result = analyzer.analyze(project_path)

        assert result.project_path == project_path
        assert result.language_info.primary == "python"
        assert result.language_info.confidence >= 80
        assert result.project_type in [ProjectType.CLI_TOOL, ProjectType.LIBRARY]
        assert result.complexity_level in [ComplexityLevel.SIMPLE, ComplexityLevel.MEDIUM]
        assert result.analysis_confidence >= 70

    def test_analyze_rust_project(self, temp_dir):
        """Test analysis of a Rust project."""
        project_path = create_test_project(temp_dir, "rust")
        analyzer = ProjectAnalyzer()

        result = analyzer.analyze(project_path)

        assert result.language_info.primary == "rust"
        assert result.language_info.confidence >= 90  # Cargo.toml is a strong indicator
        assert result.project_type == ProjectType.CLI_TOOL
        assert result.build_system == "cargo"

    def test_analyze_javascript_project(self, temp_dir):
        """Test analysis of a JavaScript/Node.js project."""
        project_path = create_test_project(temp_dir, "javascript")
        analyzer = ProjectAnalyzer()

        result = analyzer.analyze(project_path)

        assert result.language_info.primary == "javascript"
        assert result.language_info.confidence >= 80
        assert result.build_system == "npm"
        assert "express" in result.dependencies

    def test_analyze_nonexistent_project(self, temp_dir):
        """Test analysis of non-existent project raises appropriate error."""
        nonexistent_path = temp_dir / "does_not_exist"
        analyzer = ProjectAnalyzer()

        with pytest.raises(FileNotFoundError):
            analyzer.analyze(nonexistent_path)

    def test_analyze_empty_directory(self, temp_dir):
        """Test analysis of empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        analyzer = ProjectAnalyzer()

        result = analyzer.analyze(empty_dir)

        assert result.language_info.primary is None
        assert result.project_type == ProjectType.UNKNOWN
        assert result.complexity_level == ComplexityLevel.SIMPLE
        assert result.analysis_confidence < 50

    def test_analyze_mixed_language_project(self, temp_dir):
        """Test analysis of project with multiple languages."""
        project_path = temp_dir / "mixed_project"
        project_path.mkdir()

        # Create files in multiple languages
        (project_path / "main.py").write_text("print('Python')")
        (project_path / "script.js").write_text("console.log('JavaScript');")
        (project_path / "style.css").write_text("body { margin: 0; }")
        (project_path / "README.md").write_text("# Mixed Project")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.language_info.primary in ["python", "javascript"]
        assert len(result.language_info.secondary) >= 1
        assert result.filesystem_info.total_files >= 4

    @pytest.mark.slow
    def test_analyze_large_project(self, temp_dir):
        """Test analysis performance on larger project structure."""
        project_path = temp_dir / "large_project"
        project_path.mkdir()

        # Create many files to test performance
        for i in range(100):
            (project_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")

        # Create nested directories
        for depth in range(5):
            nested_dir = project_path
            for level in range(depth):
                nested_dir = nested_dir / f"level_{level}"
                nested_dir.mkdir(exist_ok=True)
            (nested_dir / f"nested_{depth}.py").write_text(f"# Nested file {depth}")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.language_info.primary == "python"
        assert result.filesystem_info.total_files >= 100
        assert result.complexity_level == ComplexityLevel.HIGH

    def test_analyze_with_cache_enabled(self, temp_dir):
        """Test analyzer caching functionality."""
        project_path = create_test_project(temp_dir, "python")
        analyzer = ProjectAnalyzer(config={"cache_enabled": True})

        # First analysis
        result1 = analyzer.analyze(project_path)

        # Second analysis should use cache
        result2 = analyzer.analyze(project_path)

        assert result1.language_info.primary == result2.language_info.primary
        assert result1.project_type == result2.project_type

    def test_analyze_with_overrides(self, temp_dir):
        """Test analyzer with language/framework overrides."""
        project_path = create_test_project(temp_dir, "python")
        config = {
            "overrides": {
                "language": "typescript",
                "framework": "react"
            }
        }
        analyzer = ProjectAnalyzer(config=config)

        result = analyzer.analyze(project_path)

        # Overrides should be applied
        assert result.language_info.primary == "typescript"
        assert result.framework_info.primary == "react"


@pytest.mark.unit
@pytest.mark.phase1
class TestLanguageDetector:
    """Test the LanguageDetector component."""

    def test_detect_python_files(self, temp_dir):
        """Test Python language detection."""
        project_path = temp_dir / "python_project"
        project_path.mkdir()
        (project_path / "main.py").write_text("#!/usr/bin/env python3\nprint('Hello')")
        (project_path / "utils.py").write_text("def helper(): pass")
        (project_path / "requirements.txt").write_text("requests")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary == "python"
        assert result.confidence >= 80
        assert "python" in result.version_info

    def test_detect_rust_files(self, temp_dir):
        """Test Rust language detection."""
        project_path = temp_dir / "rust_project"
        project_path.mkdir()
        (project_path / "Cargo.toml").write_text("[package]\nname = 'test'")
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("fn main() {}")
        (src_dir / "lib.rs").write_text("pub fn hello() {}")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary == "rust"
        assert result.confidence >= 90  # Cargo.toml is strong indicator

    def test_detect_javascript_files(self, temp_dir):
        """Test JavaScript language detection."""
        project_path = temp_dir / "js_project"
        project_path.mkdir()
        (project_path / "package.json").write_text('{"name": "test"}')
        (project_path / "index.js").write_text("console.log('test');")
        (project_path / "utils.js").write_text("module.exports = {};")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary == "javascript"
        assert result.confidence >= 80

    def test_detect_mixed_languages(self, temp_dir):
        """Test detection with multiple languages present."""
        project_path = temp_dir / "mixed_project"
        project_path.mkdir()
        (project_path / "script.py").write_text("print('python')")
        (project_path / "app.js").write_text("console.log('js');")
        (project_path / "style.css").write_text("body {}")
        (project_path / "README.md").write_text("# Docs")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary in ["python", "javascript"]
        assert len(result.secondary) >= 1
        assert "css" in result.secondary or "markdown" in result.secondary

    def test_confidence_scoring(self, temp_dir):
        """Test confidence scoring accuracy."""
        project_path = temp_dir / "confidence_test"
        project_path.mkdir()

        # Strong Python indicators
        (project_path / "setup.py").write_text("from setuptools import setup")
        (project_path / "requirements.txt").write_text("django")
        (project_path / "main.py").write_text("#!/usr/bin/env python3")
        (project_path / "utils.py").write_text("def func(): pass")
        (project_path / "__init__.py").write_text("")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary == "python"
        assert result.confidence >= 95  # Should be very confident

    def test_no_recognizable_files(self, temp_dir):
        """Test detection with no recognizable programming files."""
        project_path = temp_dir / "no_code"
        project_path.mkdir()
        (project_path / "README.txt").write_text("Documentation")
        (project_path / "data.csv").write_text("col1,col2\n1,2")
        (project_path / "image.jpg").write_bytes(b"fake image data")

        detector = LanguageDetector()
        result = detector.detect_primary_language(project_path)

        assert result.primary is None
        assert result.confidence < 50


@pytest.mark.unit
@pytest.mark.phase1
class TestFrameworkDetector:
    """Test the FrameworkDetector component."""

    def test_detect_fastapi_framework(self, temp_dir):
        """Test FastAPI framework detection."""
        project_path = temp_dir / "fastapi_project"
        project_path.mkdir()
        (project_path / "requirements.txt").write_text("fastapi>=0.95.0\nuvicorn")
        (project_path / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "python")

        assert result.primary == "fastapi"
        assert result.confidence >= 80
        assert result.details.get("web_framework") is True

    def test_detect_django_framework(self, temp_dir):
        """Test Django framework detection."""
        project_path = temp_dir / "django_project"
        project_path.mkdir()
        (project_path / "requirements.txt").write_text("Django>=4.0.0")
        (project_path / "manage.py").write_text("#!/usr/bin/env python\nfrom django.core.management import execute_from_command_line")
        (project_path / "settings.py").write_text("INSTALLED_APPS = ['django.contrib.admin']")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "python")

        assert result.primary == "django"
        assert result.confidence >= 90

    def test_detect_react_framework(self, temp_dir):
        """Test React framework detection."""
        project_path = temp_dir / "react_project"
        project_path.mkdir()
        (project_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}')
        (project_path / "App.jsx").write_text("""
import React from 'react';

function App() {
  return <div>Hello React</div>;
}

export default App;
""")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "javascript")

        assert result.primary == "react"
        assert result.confidence >= 80

    def test_detect_axum_framework(self, temp_dir):
        """Test Axum framework detection for Rust."""
        project_path = temp_dir / "axum_project"
        project_path.mkdir()
        (project_path / "Cargo.toml").write_text("""
[package]
name = "test-api"
version = "0.1.0"

[dependencies]
axum = "0.6"
tokio = { version = "1.0", features = ["full"] }
""")
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text("""
use axum::{routing::get, Router};

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(|| async { "Hello, World!" }));
}
""")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "rust")

        assert result.primary == "axum"
        assert result.confidence >= 80

    def test_no_framework_detected(self, temp_dir):
        """Test when no framework is detected."""
        project_path = temp_dir / "simple_script"
        project_path.mkdir()
        (project_path / "simple.py").write_text("print('Hello, World!')")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "python")

        assert result.primary is None
        assert result.confidence < 50

    def test_multiple_frameworks(self, temp_dir):
        """Test detection when multiple frameworks are present."""
        project_path = temp_dir / "multi_framework"
        project_path.mkdir()
        (project_path / "requirements.txt").write_text("fastapi\nflask\ndjango")
        (project_path / "fastapi_app.py").write_text("from fastapi import FastAPI")
        (project_path / "flask_app.py").write_text("from flask import Flask")

        detector = FrameworkDetector()
        result = detector.detect_framework(project_path, "python")

        assert result.primary in ["fastapi", "flask", "django"]
        assert len(result.secondary) >= 1


@pytest.mark.unit
@pytest.mark.phase1
class TestProjectTypeClassification:
    """Test project type classification logic."""

    def test_classify_web_api_project(self, temp_dir):
        """Test classification of web API project."""
        project_path = temp_dir / "api_project"
        project_path.mkdir()
        (project_path / "requirements.txt").write_text("fastapi\nuvicorn\npydantic")
        (project_path / "main.py").write_text("""
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/users")
def get_users():
    return []
""")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.project_type == ProjectType.API_SERVICE

    def test_classify_cli_tool_project(self, temp_dir):
        """Test classification of CLI tool project."""
        project_path = temp_dir / "cli_project"
        project_path.mkdir()
        (project_path / "requirements.txt").write_text("click\nargparse")
        (project_path / "cli.py").write_text("""
import click

@click.command()
@click.option('--count', default=1)
def hello(count):
    click.echo('Hello!')

if __name__ == '__main__':
    hello()
""")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.project_type == ProjectType.CLI_TOOL

    def test_classify_library_project(self, temp_dir):
        """Test classification of library project."""
        project_path = temp_dir / "lib_project"
        project_path.mkdir()
        (project_path / "setup.py").write_text("""
from setuptools import setup, find_packages

setup(
    name="mylib",
    packages=find_packages(),
)
""")
        lib_dir = project_path / "mylib"
        lib_dir.mkdir()
        (lib_dir / "__init__.py").write_text("__version__ = '1.0.0'")
        (lib_dir / "core.py").write_text("def public_function(): pass")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.project_type == ProjectType.LIBRARY

    def test_classify_web_frontend_project(self, temp_dir):
        """Test classification of web frontend project."""
        project_path = temp_dir / "frontend_project"
        project_path.mkdir()
        (project_path / "package.json").write_text("""
{
  "name": "frontend-app",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
""")
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "App.js").write_text("import React from 'react';")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.project_type == ProjectType.WEB_FRONTEND


@pytest.mark.unit
@pytest.mark.phase1
class TestComplexityAssessment:
    """Test complexity level assessment."""

    def test_simple_complexity(self, temp_dir):
        """Test simple complexity assessment."""
        project_path = temp_dir / "simple_project"
        project_path.mkdir()
        (project_path / "main.py").write_text("print('Hello, World!')")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.complexity_level == ComplexityLevel.SIMPLE

    def test_medium_complexity(self, temp_dir):
        """Test medium complexity assessment."""
        project_path = temp_dir / "medium_project"
        project_path.mkdir()

        # Create moderate number of files with some structure
        (project_path / "main.py").write_text("from utils import helper")
        (project_path / "utils.py").write_text("def helper(): pass")
        (project_path / "config.py").write_text("CONFIG = {}")
        (project_path / "requirements.txt").write_text("requests\nclick")

        tests_dir = project_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test_main(): pass")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.complexity_level in [ComplexityLevel.SIMPLE, ComplexityLevel.MEDIUM]

    def test_high_complexity(self, temp_dir):
        """Test high complexity assessment."""
        project_path = temp_dir / "complex_project"
        project_path.mkdir()

        # Create many files and directories
        for i in range(20):
            (project_path / f"module_{i}.py").write_text(f"# Module {i}")

        for subdir in ["api", "models", "utils", "tests", "docs"]:
            sub_path = project_path / subdir
            sub_path.mkdir()
            for i in range(5):
                (sub_path / f"file_{i}.py").write_text(f"# {subdir} file {i}")

        # Add configuration files
        (project_path / "requirements.txt").write_text("django\ncelery\nredis\npostgresql")
        (project_path / "docker-compose.yml").write_text("version: '3'")
        (project_path / "Dockerfile").write_text("FROM python:3.11")

        analyzer = ProjectAnalyzer()
        result = analyzer.analyze(project_path)

        assert result.complexity_level == ComplexityLevel.HIGH
