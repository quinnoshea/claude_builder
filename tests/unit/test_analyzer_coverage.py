"""Comprehensive tests for core.analyzer module to boost coverage."""

import tempfile
from pathlib import Path

import pytest

from claude_builder.core.analyzer import (
    FrameworkDetector,
    LanguageDetector,
    ProjectAnalyzer,
)
from claude_builder.core.models import ComplexityLevel, ProjectType
from tests.conftest import create_test_project


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_project_analyzer_initialization():
    """Test analyzer initializes with correct defaults - covers initialization."""
    analyzer = ProjectAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, "language_detector")
    assert hasattr(analyzer, "framework_detector")


def test_project_analyzer_with_config():
    """Test analyzer initializes with custom configuration - covers config setup."""
    config = {
        "confidence_threshold": 70,
        "parallel_processing": False,
        "cache_enabled": False
    }
    analyzer = ProjectAnalyzer(config=config)
    assert analyzer.config["confidence_threshold"] == 70
    assert analyzer.config["parallel_processing"] is False


def test_analyze_python_project(temp_dir):
    """Test analysis of a Python project - covers Python detection logic."""
    project_path = create_test_project(temp_dir, "python")
    analyzer = ProjectAnalyzer()

    result = analyzer.analyze(project_path)

    assert result.project_path == project_path
    assert result.language_info.primary == "python"
    assert result.language_info.confidence >= 80
    assert result.project_type in [ProjectType.CLI_TOOL, ProjectType.LIBRARY]
    assert result.complexity_level in [ComplexityLevel.SIMPLE, ComplexityLevel.MEDIUM]
    assert result.analysis_confidence >= 70


def test_analyze_rust_project(temp_dir):
    """Test analysis of a Rust project - covers Rust detection logic."""
    project_path = create_test_project(temp_dir, "rust")
    analyzer = ProjectAnalyzer()

    result = analyzer.analyze(project_path)

    assert result.language_info.primary == "rust"
    assert result.language_info.confidence >= 90  # Cargo.toml is a strong indicator
    assert result.project_type in [ProjectType.CLI_TOOL, ProjectType.LIBRARY]
    assert "cargo" in result.dev_environment.package_managers


def test_analyze_javascript_project(temp_dir):
    """Test analysis of a JavaScript/Node.js project - covers JS detection."""
    project_path = create_test_project(temp_dir, "javascript")
    analyzer = ProjectAnalyzer()

    result = analyzer.analyze(project_path)

    assert result.language_info.primary == "javascript"
    assert result.language_info.confidence >= 80
    assert "npm" in result.dev_environment.package_managers


def test_analyze_empty_directory(temp_dir):
    """Test analysis of empty directory - covers edge case handling."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()
    analyzer = ProjectAnalyzer()

    result = analyzer.analyze(empty_dir)

    assert result.language_info.primary is None
    assert result.project_type == ProjectType.UNKNOWN
    assert result.complexity_level == ComplexityLevel.SIMPLE
    assert result.analysis_confidence < 50


def test_analyze_mixed_language_project(temp_dir):
    """Test analysis of project with multiple languages - covers multi-language detection."""
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


def test_analyze_with_cache_enabled(temp_dir):
    """Test analyzer caching functionality - covers caching logic."""
    project_path = create_test_project(temp_dir, "python")
    analyzer = ProjectAnalyzer(config={"cache_enabled": True})

    # First analysis
    result1 = analyzer.analyze(project_path)

    # Second analysis should use cache
    result2 = analyzer.analyze(project_path)

    assert result1.language_info.primary == result2.language_info.primary
    assert result1.project_type == result2.project_type


def test_analyze_with_overrides(temp_dir):
    """Test analyzer with configuration overrides - covers config handling logic."""
    project_path = create_test_project(temp_dir, "python")
    config = {
        "overrides": {
            "language": "typescript",
            "framework": "react"
        }
    }
    analyzer = ProjectAnalyzer(config=config)

    result = analyzer.analyze(project_path)

    # Should still analyze the project successfully with config
    assert result.language_info.primary == "python"  # Actual detected language
    assert result.analysis_confidence >= 50


def test_language_detector_python_files(temp_dir):
    """Test Python language detection - covers Python detection."""
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


def test_language_detector_rust_files(temp_dir):
    """Test Rust language detection - covers Rust detection."""
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


def test_language_detector_javascript_files(temp_dir):
    """Test JavaScript language detection - covers JS detection."""
    project_path = temp_dir / "js_project"
    project_path.mkdir()
    (project_path / "package.json").write_text('{"name": "test"}')
    (project_path / "index.js").write_text("console.log('test');")
    (project_path / "utils.js").write_text("module.exports = {};")

    detector = LanguageDetector()
    result = detector.detect_primary_language(project_path)

    assert result.primary == "javascript"
    assert result.confidence >= 80


def test_language_detector_mixed_languages(temp_dir):
    """Test detection with multiple languages present - covers multi-language logic."""
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


def test_language_detector_confidence_scoring(temp_dir):
    """Test confidence scoring accuracy - covers confidence algorithm."""
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


def test_language_detector_no_recognizable_files(temp_dir):
    """Test detection with no recognizable programming files - covers edge case."""
    project_path = temp_dir / "no_code"
    project_path.mkdir()
    (project_path / "README.txt").write_text("Documentation")
    (project_path / "data.csv").write_text("col1,col2\n1,2")
    (project_path / "image.jpg").write_bytes(b"fake image data")

    detector = LanguageDetector()
    result = detector.detect_primary_language(project_path)

    assert result.primary is None
    assert result.confidence < 50


def test_framework_detector_fastapi(temp_dir):
    """Test FastAPI framework detection - covers FastAPI detection."""
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


def test_framework_detector_django(temp_dir):
    """Test Django framework detection - covers Django detection."""
    project_path = temp_dir / "django_project"
    project_path.mkdir()
    (project_path / "requirements.txt").write_text("Django>=4.0.0")
    (project_path / "manage.py").write_text("#!/usr/bin/env python\nfrom django.core.management import execute_from_command_line")
    (project_path / "settings.py").write_text("INSTALLED_APPS = ['django.contrib.admin']")

    detector = FrameworkDetector()
    result = detector.detect_framework(project_path, "python")

    assert result.primary == "django"
    assert result.confidence >= 90


def test_framework_detector_react(temp_dir):
    """Test React framework detection - covers React detection."""
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


def test_framework_detector_no_framework(temp_dir):
    """Test when no framework is detected - covers no-framework case."""
    project_path = temp_dir / "simple_script"
    project_path.mkdir()
    (project_path / "simple.py").write_text("print('Hello, World!')")

    detector = FrameworkDetector()
    result = detector.detect_framework(project_path, "python")

    assert result.primary is None
    assert result.confidence < 50


def test_framework_detector_multiple_frameworks(temp_dir):
    """Test detection when multiple frameworks are present - covers multiple framework logic."""
    project_path = temp_dir / "multi_framework"
    project_path.mkdir()
    (project_path / "requirements.txt").write_text("fastapi\nflask\ndjango")
    (project_path / "fastapi_app.py").write_text("from fastapi import FastAPI")
    (project_path / "flask_app.py").write_text("from flask import Flask")

    detector = FrameworkDetector()
    result = detector.detect_framework(project_path, "python")

    assert result.primary in ["fastapi", "flask", "django"]
    assert len(result.secondary) >= 1
