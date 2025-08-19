"""
Unit tests for file pattern matching utilities.

Tests the file pattern matching and recognition including:
- File type detection
- Pattern matching algorithms
- Configuration file recognition
- Project structure patterns
- Language-specific patterns
"""

import pytest
from pathlib import Path
from claude_builder.utils.file_patterns import (
    FilePatternMatcher, LanguageDetector, ConfigFileDetector,
    ProjectTypeDetector, PatternRule
)


class TestFilePatternMatcher:
    """Test suite for FilePatternMatcher class."""
    
    def test_pattern_matcher_initialization(self):
        """Test pattern matcher initialization."""
        matcher = FilePatternMatcher()
        
        assert matcher.patterns is not None
        assert len(matcher.patterns) > 0
    
    def test_file_extension_matching(self, temp_dir):
        """Test file extension pattern matching."""
        matcher = FilePatternMatcher()
        
        # Create test files with different extensions
        (temp_dir / "script.py").touch()
        (temp_dir / "main.rs").touch()
        (temp_dir / "app.js").touch()
        (temp_dir / "style.css").touch()
        (temp_dir / "README.md").touch()
        
        assert matcher.matches_extension(temp_dir / "script.py", [".py"])
        assert matcher.matches_extension(temp_dir / "main.rs", [".rs"])
        assert matcher.matches_extension(temp_dir / "app.js", [".js", ".jsx"])
        assert not matcher.matches_extension(temp_dir / "script.py", [".rs"])
    
    def test_filename_pattern_matching(self, temp_dir):
        """Test filename pattern matching."""
        matcher = FilePatternMatcher()
        
        # Create test files with specific names
        (temp_dir / "Dockerfile").touch()
        (temp_dir / "docker-compose.yml").touch()
        (temp_dir / "requirements.txt").touch()
        (temp_dir / "package.json").touch()
        (temp_dir / "Cargo.toml").touch()
        
        assert matcher.matches_filename(temp_dir / "Dockerfile", ["Dockerfile"])
        assert matcher.matches_filename(temp_dir / "docker-compose.yml", ["docker-compose.*"])
        assert matcher.matches_filename(temp_dir / "requirements.txt", ["requirements.txt"])
        assert not matcher.matches_filename(temp_dir / "Dockerfile", ["package.json"])
    
    def test_glob_pattern_matching(self, temp_dir):
        """Test glob pattern matching."""
        matcher = FilePatternMatcher()
        
        # Create directory structure
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "main.py").touch()
        (temp_dir / "src" / "utils.py").touch()
        (temp_dir / "tests").mkdir()
        (temp_dir / "tests" / "test_main.py").touch()
        
        python_files = list(matcher.find_files(temp_dir, "**/*.py"))
        test_files = list(matcher.find_files(temp_dir, "**/test_*.py"))
        
        assert len(python_files) == 3
        assert len(test_files) == 1
        assert any(f.name == "main.py" for f in python_files)
        assert any(f.name == "test_main.py" for f in test_files)
    
    def test_content_pattern_matching(self, temp_dir):
        """Test content-based pattern matching."""
        matcher = FilePatternMatcher()
        
        # Create files with specific content patterns
        dockerfile = temp_dir / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nRUN pip install requirements.txt")
        
        python_file = temp_dir / "script.py"
        python_file.write_text("#!/usr/bin/env python3\nimport os\nprint('Hello')")
        
        assert matcher.matches_content_pattern(dockerfile, r"FROM\s+\w+")
        assert matcher.matches_content_pattern(python_file, r"import\s+\w+")
        assert not matcher.matches_content_pattern(dockerfile, r"import\s+\w+")


class TestLanguageDetector:
    """Test suite for LanguageDetector class."""
    
    def test_language_detection_by_extension(self, temp_dir):
        """Test language detection by file extension."""
        detector = LanguageDetector()
        
        files = {
            "main.py": "python",
            "app.js": "javascript", 
            "component.tsx": "typescript",
            "main.rs": "rust",
            "app.go": "go",
            "Main.java": "java",
            "script.rb": "ruby",
            "app.php": "php"
        }
        
        for filename, expected_lang in files.items():
            test_file = temp_dir / filename
            test_file.touch()
            
            detected = detector.detect_language(test_file)
            assert detected == expected_lang
    
    def test_language_detection_by_shebang(self, temp_dir):
        """Test language detection by shebang line."""
        detector = LanguageDetector()
        
        # Python script with shebang
        python_script = temp_dir / "script"
        python_script.write_text("#!/usr/bin/env python3\nprint('Hello')")
        
        # Bash script with shebang
        bash_script = temp_dir / "script.sh"
        bash_script.write_text("#!/bin/bash\necho 'Hello'")
        
        # Node.js script
        node_script = temp_dir / "script.js"
        node_script.write_text("#!/usr/bin/env node\nconsole.log('Hello')")
        
        assert detector.detect_language(python_script) == "python"
        assert detector.detect_language(bash_script) == "bash"
        assert detector.detect_language(node_script) == "javascript"
    
    def test_language_detection_by_content(self, temp_dir):
        """Test language detection by content analysis."""
        detector = LanguageDetector()
        
        # Python-like content without extension
        python_file = temp_dir / "unknown_file"
        python_file.write_text("""
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
""")
        
        # JavaScript-like content
        js_file = temp_dir / "another_file"
        js_file.write_text("""
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

module.exports = helloWorld;
""")
        
        assert detector.detect_language(python_file) == "python"
        assert detector.detect_language(js_file) == "javascript"
    
    def test_multi_language_project_analysis(self, temp_dir):
        """Test analysis of multi-language projects."""
        detector = LanguageDetector()
        
        # Create multi-language project structure
        files = {
            "backend/main.py": "python",
            "backend/models.py": "python",
            "frontend/App.js": "javascript",
            "frontend/Component.tsx": "typescript",
            "scripts/build.sh": "bash",
            "automation/deploy.rs": "rust"
        }
        
        for file_path, content in files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
        
        languages = detector.analyze_project_languages(temp_dir)
        
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "bash" in languages
        assert "rust" in languages
        assert languages["python"]["file_count"] == 2
        assert languages["javascript"]["file_count"] == 1


class TestConfigFileDetector:
    """Test suite for ConfigFileDetector class."""
    
    def test_python_config_detection(self, temp_dir):
        """Test detection of Python configuration files."""
        detector = ConfigFileDetector()
        
        # Create Python config files
        (temp_dir / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'")
        (temp_dir / "requirements.txt").write_text("requests==2.31.0")
        (temp_dir / "setup.py").write_text("from setuptools import setup")
        (temp_dir / "pytest.ini").write_text("[tool:pytest]")
        
        configs = detector.detect_config_files(temp_dir)
        
        assert "python" in configs
        assert "pyproject.toml" in configs["python"]
        assert "requirements.txt" in configs["python"]
        assert "setup.py" in configs["python"]
        assert "pytest.ini" in configs["python"]
    
    def test_javascript_config_detection(self, temp_dir):
        """Test detection of JavaScript configuration files."""
        detector = ConfigFileDetector()
        
        # Create JavaScript config files
        (temp_dir / "package.json").write_text('{"name": "test"}')
        (temp_dir / "package-lock.json").write_text('{"name": "test"}')
        (temp_dir / "webpack.config.js").write_text("module.exports = {}")
        (temp_dir / "babel.config.js").write_text("module.exports = {}")
        (temp_dir / "tsconfig.json").write_text('{"compilerOptions": {}}')
        
        configs = detector.detect_config_files(temp_dir)
        
        assert "javascript" in configs
        assert "package.json" in configs["javascript"]
        assert "webpack.config.js" in configs["javascript"]
        assert "typescript" in configs
        assert "tsconfig.json" in configs["typescript"]
    
    def test_rust_config_detection(self, temp_dir):
        """Test detection of Rust configuration files."""
        detector = ConfigFileDetector()
        
        # Create Rust config files
        (temp_dir / "Cargo.toml").write_text("[package]\nname = 'test'")
        (temp_dir / "Cargo.lock").write_text("# Cargo lock file")
        (temp_dir / "rust-toolchain.toml").write_text("[toolchain]")
        
        configs = detector.detect_config_files(temp_dir)
        
        assert "rust" in configs
        assert "Cargo.toml" in configs["rust"]
        assert "Cargo.lock" in configs["rust"]
        assert "rust-toolchain.toml" in configs["rust"]
    
    def test_docker_config_detection(self, temp_dir):
        """Test detection of Docker configuration files."""
        detector = ConfigFileDetector()
        
        # Create Docker config files
        (temp_dir / "Dockerfile").write_text("FROM python:3.9")
        (temp_dir / "docker-compose.yml").write_text("version: '3'")
        (temp_dir / ".dockerignore").write_text("node_modules/")
        
        configs = detector.detect_config_files(temp_dir)
        
        assert "docker" in configs
        assert "Dockerfile" in configs["docker"]
        assert "docker-compose.yml" in configs["docker"]
        assert ".dockerignore" in configs["docker"]


class TestProjectTypeDetector:
    """Test suite for ProjectTypeDetector class."""
    
    def test_python_project_detection(self, sample_python_project):
        """Test detection of Python projects."""
        detector = ProjectTypeDetector()
        
        project_type = detector.detect_project_type(sample_python_project)
        assert project_type == "python"
        
        details = detector.get_detection_details(sample_python_project)
        assert details["confidence"] > 0.8
        assert "pyproject.toml" in details["indicators"]
    
    def test_rust_project_detection(self, sample_rust_project):
        """Test detection of Rust projects."""
        detector = ProjectTypeDetector()
        
        project_type = detector.detect_project_type(sample_rust_project)
        assert project_type == "rust"
        
        details = detector.get_detection_details(sample_rust_project)
        assert details["confidence"] > 0.8
        assert "Cargo.toml" in details["indicators"]
    
    def test_javascript_project_detection(self, sample_javascript_project):
        """Test detection of JavaScript projects."""
        detector = ProjectTypeDetector()
        
        project_type = detector.detect_project_type(sample_javascript_project)
        assert project_type == "javascript"
        
        details = detector.get_detection_details(sample_javascript_project)
        assert details["confidence"] > 0.8
        assert "package.json" in details["indicators"]
    
    def test_multi_language_project_detection(self, temp_dir):
        """Test detection of multi-language projects."""
        detector = ProjectTypeDetector()
        
        # Create multi-language project
        (temp_dir / "backend").mkdir()
        (temp_dir / "backend" / "Cargo.toml").write_text("[package]\nname = 'backend'")
        (temp_dir / "frontend").mkdir()
        (temp_dir / "frontend" / "package.json").write_text('{"name": "frontend"}')
        
        project_type = detector.detect_project_type(temp_dir)
        assert project_type == "multi_language"
        
        details = detector.get_detection_details(temp_dir)
        assert "rust" in details["languages"]
        assert "javascript" in details["languages"]
    
    def test_unknown_project_handling(self, temp_dir):
        """Test handling of unknown project types."""
        detector = ProjectTypeDetector()
        
        # Create project with no recognizable patterns
        (temp_dir / "random.txt").write_text("Random content")
        (temp_dir / "data.csv").write_text("col1,col2\n1,2")
        
        project_type = detector.detect_project_type(temp_dir)
        assert project_type == "unknown"
        
        details = detector.get_detection_details(temp_dir)
        assert details["confidence"] < 0.5


class TestPatternRule:
    """Test suite for PatternRule class."""
    
    def test_pattern_rule_creation(self):
        """Test pattern rule creation."""
        rule = PatternRule(
            name="python_project",
            description="Detects Python projects",
            patterns=["*.py", "requirements.txt", "pyproject.toml"],
            priority=1.0,
            required_patterns=["*.py"]
        )
        
        assert rule.name == "python_project"
        assert rule.description == "Detects Python projects"
        assert len(rule.patterns) == 3
        assert rule.priority == 1.0
        assert len(rule.required_patterns) == 1
    
    def test_pattern_rule_matching(self, temp_dir):
        """Test pattern rule matching logic."""
        rule = PatternRule(
            name="web_project",
            patterns=["*.html", "*.css", "*.js"],
            required_patterns=["*.html"],
            weight_factors={"*.html": 2.0, "*.css": 1.5, "*.js": 1.0}
        )
        
        # Create matching files
        (temp_dir / "index.html").touch()
        (temp_dir / "style.css").touch()
        (temp_dir / "script.js").touch()
        
        match_result = rule.evaluate_match(temp_dir)
        
        assert match_result.matches is True
        assert match_result.confidence > 0.5
        assert match_result.matched_patterns == ["*.html", "*.css", "*.js"]
    
    def test_pattern_rule_scoring(self, temp_dir):
        """Test pattern rule scoring system."""
        rule = PatternRule(
            name="scoring_test",
            patterns=["file1.txt", "file2.txt", "file3.txt"],
            weight_factors={"file1.txt": 3.0, "file2.txt": 2.0, "file3.txt": 1.0}
        )
        
        # Create subset of files
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file3.txt").touch()
        
        match_result = rule.evaluate_match(temp_dir)
        
        assert match_result.matches is True
        assert match_result.score == 4.0  # 3.0 + 1.0
        assert "file1.txt" in match_result.matched_patterns
        assert "file3.txt" in match_result.matched_patterns
        assert "file2.txt" not in match_result.matched_patterns