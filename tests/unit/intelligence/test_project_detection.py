"""
Unit tests for advanced project detection components.

Tests the intelligent project analysis including:
- Advanced pattern recognition
- Multi-language project detection
- Framework-specific analysis
- Architecture pattern identification
- Technology stack inference
"""

from claude_builder.core.analyzer import (
    AdvancedProjectDetector,
    ArchitectureAnalyzer,
    FrameworkDetector,
    PatternMatcher,
    TechnologyStackAnalyzer,
)


class TestPatternMatcher:
    """Test suite for PatternMatcher class."""

    def test_pattern_matcher_initialization(self):
        """Test pattern matcher initialization."""
        matcher = PatternMatcher()

        assert matcher.patterns is not None
        assert len(matcher.patterns) >= 0

    def test_file_pattern_matching(self, temp_dir):
        """Test file pattern matching capabilities."""
        # Create test files
        (temp_dir / "package.json").write_text('{"name": "test"}')
        (temp_dir / "Cargo.toml").write_text('[package]\nname = "test"')
        (temp_dir / "pyproject.toml").write_text('[tool.poetry]\nname = "test"')
        (temp_dir / "requirements.txt").write_text("requests==2.31.0")

        matcher = PatternMatcher()

        # Test individual pattern matches
        assert matcher.matches_pattern(temp_dir / "package.json", "nodejs_project")
        assert matcher.matches_pattern(temp_dir / "Cargo.toml", "rust_project")
        assert matcher.matches_pattern(temp_dir / "pyproject.toml", "python_project")
        assert matcher.matches_pattern(
            temp_dir / "requirements.txt", "python_requirements"
        )

    def test_content_pattern_matching(self, temp_dir):
        """Test content-based pattern matching."""
        # Create file with specific content patterns
        dockerfile = temp_dir / "Dockerfile"
        dockerfile.write_text(
            """
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
        )

        matcher = PatternMatcher()

        # Should detect Docker and Python patterns
        assert matcher.matches_content_pattern(dockerfile, "docker_python")
        assert matcher.matches_content_pattern(dockerfile, "docker_file")

    def test_directory_structure_patterns(self, temp_dir):
        """Test directory structure pattern recognition."""
        # Create typical React project structure
        react_structure = [
            "src/",
            "src/components/",
            "src/components/App.js",
            "src/components/Header.js",
            "public/",
            "public/index.html",
            "package.json",
        ]

        for path in react_structure:
            full_path = temp_dir / path
            if path.endswith("/"):
                full_path.mkdir(parents=True, exist_ok=True)
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()

        matcher = PatternMatcher()

        # Should recognize React project structure
        assert matcher.matches_structure_pattern(temp_dir, "react_project")

    def test_custom_pattern_registration(self):
        """Test registering custom patterns."""
        matcher = PatternMatcher()

        # Register custom pattern
        custom_pattern = {
            "name": "custom_framework",
            "file_patterns": ["custom.config"],
            "content_patterns": ["custom_framework_marker"],
            "structure_patterns": ["custom/", "custom/lib/"],
        }

        matcher.register_pattern(custom_pattern)

        assert "custom_framework" in matcher.patterns
        assert matcher.patterns["custom_framework"] == custom_pattern

    def test_pattern_priority_and_scoring(self, temp_dir):
        """Test pattern matching with priority and confidence scoring."""
        # Create ambiguous project structure
        (temp_dir / "package.json").write_text(
            '{"name": "test", "dependencies": {"react": "^18.0.0"}}'
        )
        (temp_dir / "tsconfig.json").write_text('{"compilerOptions": {}}')
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "App.tsx").touch()

        matcher = PatternMatcher()

        # Should return multiple matches with confidence scores
        matches = matcher.get_all_matches(temp_dir)

        assert len(matches) > 0
        assert all("confidence" in match for match in matches)
        assert all(0 <= match["confidence"] <= 1 for match in matches)

        # React+TypeScript should score higher than plain JavaScript
        react_match = next((m for m in matches if "react" in m["pattern_name"]), None)
        js_match = next(
            (m for m in matches if m["pattern_name"] == "javascript_project"), None
        )

        if react_match and js_match:
            assert react_match["confidence"] > js_match["confidence"]


class TestFrameworkDetector:
    """Test suite for FrameworkDetector class."""

    def test_python_framework_detection(self, temp_dir):
        """Test Python framework detection."""
        detector = FrameworkDetector()

        # Test FastAPI detection
        requirements = temp_dir / "requirements.txt"
        requirements.write_text("fastapi==0.100.0\nuvicorn==0.23.0")

        main_py = temp_dir / "main.py"
        main_py.write_text(
            """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
        )

        frameworks = detector.detect_frameworks(temp_dir)

        fastapi_framework = next((f for f in frameworks if f.name == "fastapi"), None)
        assert fastapi_framework is not None
        assert fastapi_framework.category == "web"
        assert fastapi_framework.confidence > 0.8

    def test_javascript_framework_detection(self, temp_dir):
        """Test JavaScript framework detection."""
        detector = FrameworkDetector()

        # Test React detection
        package_json = temp_dir / "package.json"
        package_json.write_text(
            """
{
  "name": "react-app",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "scripts": {
    "start": "react-scripts start"
  }
}
"""
        )

        app_js = temp_dir / "src" / "App.js"
        app_js.parent.mkdir()
        app_js.write_text(
            """
import React from 'react';

function App() {
  return <div>Hello React</div>;
}

export default App;
"""
        )

        frameworks = detector.detect_frameworks(temp_dir)

        react_framework = next((f for f in frameworks if f.name == "react"), None)
        assert react_framework is not None
        assert react_framework.category == "frontend"
        assert react_framework.confidence > 0.8

    def test_rust_framework_detection(self, temp_dir):
        """Test Rust framework detection."""
        detector = FrameworkDetector()

        # Test Axum detection
        cargo_toml = temp_dir / "Cargo.toml"
        cargo_toml.write_text(
            """
[package]
name = "axum-app"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.6"
tokio = { version = "1", features = ["full"] }
tower = "0.4"
"""
        )

        main_rs = temp_dir / "src" / "main.rs"
        main_rs.parent.mkdir()
        main_rs.write_text(
            """
use axum::{response::Html, routing::get, Router};

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(handler));
    // ...
}

async fn handler() -> Html<&'static str> {
    Html("<h1>Hello, World!</h1>")
}
"""
        )

        frameworks = detector.detect_frameworks(temp_dir)

        axum_framework = next((f for f in frameworks if f.name == "axum"), None)
        assert axum_framework is not None
        assert axum_framework.category == "web"
        assert axum_framework.confidence > 0.8

    def test_multi_framework_detection(self, temp_dir):
        """Test detection of multiple frameworks in one project."""
        detector = FrameworkDetector()

        # Create project with multiple frameworks
        # Backend: FastAPI
        (temp_dir / "backend").mkdir()
        (temp_dir / "backend" / "requirements.txt").write_text("fastapi==0.100.0")
        (temp_dir / "backend" / "main.py").write_text("from fastapi import FastAPI")

        # Frontend: React
        (temp_dir / "frontend").mkdir()
        (temp_dir / "frontend" / "package.json").write_text(
            '{"dependencies": {"react": "^18.0.0"}}'
        )
        (temp_dir / "frontend" / "src").mkdir()
        (temp_dir / "frontend" / "src" / "App.js").write_text(
            "import React from 'react';"
        )

        frameworks = detector.detect_frameworks(temp_dir)

        framework_names = [f.name for f in frameworks]
        assert "fastapi" in framework_names
        assert "react" in framework_names
        assert len(frameworks) >= 2

    def test_framework_version_detection(self, temp_dir):
        """Test framework version detection."""
        detector = FrameworkDetector()

        # Create package.json with specific versions
        package_json = temp_dir / "package.json"
        package_json.write_text(
            """
{
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "7.0.3"
  }
}
"""
        )

        frameworks = detector.detect_frameworks(temp_dir)

        express_framework = next((f for f in frameworks if f.name == "express"), None)
        if express_framework:
            assert express_framework.version == "^4.18.2"


class TestArchitectureAnalyzer:
    """Test suite for ArchitectureAnalyzer class."""

    def test_monolith_architecture_detection(self, temp_dir):
        """Test monolithic architecture detection."""
        analyzer = ArchitectureAnalyzer()

        # Create monolithic structure
        structure = [
            "src/main.py",
            "src/models.py",
            "src/views.py",
            "src/utils.py",
            "tests/test_main.py",
        ]

        for path in structure:
            full_path = temp_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()

        architecture = analyzer.analyze_architecture(temp_dir)

        assert architecture.pattern == "monolith"
        assert architecture.confidence > 0.7

    def test_microservice_architecture_detection(self, temp_dir):
        """Test microservice architecture detection."""
        analyzer = ArchitectureAnalyzer()

        # Create microservice structure
        services = ["auth-service", "user-service", "order-service", "payment-service"]

        for service in services:
            service_dir = temp_dir / service
            service_dir.mkdir()
            (service_dir / "Dockerfile").touch()
            (service_dir / "main.py").touch()
            (service_dir / "requirements.txt").touch()

        # Add docker-compose.yml
        (temp_dir / "docker-compose.yml").write_text(
            """
version: '3'
services:
  auth-service:
    build: ./auth-service
  user-service:
    build: ./user-service
"""
        )

        architecture = analyzer.analyze_architecture(temp_dir)

        assert architecture.pattern == "microservices"
        assert architecture.confidence > 0.8
        assert len(architecture.services) == 4

    def test_layered_architecture_detection(self, temp_dir):
        """Test layered architecture detection."""
        analyzer = ArchitectureAnalyzer()

        # Create layered structure
        layers = [
            "src/presentation/controllers/",
            "src/presentation/views/",
            "src/business/services/",
            "src/business/models/",
            "src/data/repositories/",
            "src/data/entities/",
        ]

        for layer in layers:
            layer_dir = temp_dir / layer
            layer_dir.mkdir(parents=True)
            (layer_dir / "example.py").touch()

        architecture = analyzer.analyze_architecture(temp_dir)

        assert architecture.pattern in ["layered", "n-tier"]
        assert len(architecture.layers) >= 3

    def test_mvc_pattern_detection(self, temp_dir):
        """Test MVC pattern detection."""
        analyzer = ArchitectureAnalyzer()

        # Create MVC structure
        mvc_structure = [
            "models/user.py",
            "models/order.py",
            "views/user_view.py",
            "views/order_view.py",
            "controllers/user_controller.py",
            "controllers/order_controller.py",
        ]

        for path in mvc_structure:
            full_path = temp_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()

        architecture = analyzer.analyze_architecture(temp_dir)

        assert "mvc" in architecture.patterns
        assert architecture.has_pattern("mvc")


class TestTechnologyStackAnalyzer:
    """Test suite for TechnologyStackAnalyzer class."""

    def test_full_stack_analysis(self, temp_dir):
        """Test comprehensive technology stack analysis."""
        analyzer = TechnologyStackAnalyzer()

        # Create full-stack project
        files = {
            "backend/requirements.txt": (
                "fastapi==0.100.0\npsycopg2==2.9.7\nredis==4.6.0"
            ),
            "backend/main.py": "from fastapi import FastAPI",
            "frontend/package.json": (
                '{"dependencies": {"react": "^18.0.0", "axios": "^1.4.0"}}'
            ),
            "frontend/src/App.js": "import React from 'react';",
            "docker-compose.yml": (
                "version: '3'\nservices:\n  postgres:\n    image: postgres:15"
            ),
            "nginx.conf": "server { listen 80; }",
            ".github/workflows/ci.yml": "name: CI\non: [push]",
        }

        for file_path, content in files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        stack = analyzer.analyze_stack(temp_dir)

        # Should detect multiple technology categories
        assert "backend" in stack.categories
        assert "frontend" in stack.categories
        assert "database" in stack.categories
        assert "infrastructure" in stack.categories
        assert "ci_cd" in stack.categories

        # Should identify specific technologies
        technologies = [tech.name for tech in stack.technologies]
        assert "fastapi" in technologies
        assert "react" in technologies
        assert "postgresql" in technologies
        assert "docker" in technologies
        assert "nginx" in technologies

    def test_language_detection_and_analysis(self, temp_dir):
        """Test programming language detection and analysis."""
        analyzer = TechnologyStackAnalyzer()

        # Create multi-language project
        files = {
            "backend/main.py": "print('Python backend')",
            "backend/utils.py": "def helper(): pass",
            "frontend/src/App.js": "console.log('JavaScript frontend');",
            "frontend/src/utils.ts": "export const helper = () => {};",
            "scripts/deploy.sh": "#!/bin/bash\necho 'Deployment script'",
            "automation/main.rs": "fn main() { println!('Rust automation'); }",
            "config/settings.yaml": "database:\n  host: localhost",
        }

        for file_path, content in files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        stack = analyzer.analyze_stack(temp_dir)

        languages = [lang.name for lang in stack.languages]
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "rust" in languages
        assert "bash" in languages

        # Should provide language statistics
        python_stats = next(
            (lang for lang in stack.languages if lang.name == "python"), None
        )
        assert python_stats is not None
        assert python_stats.file_count == 2
        assert python_stats.line_count > 0

    def test_dependency_analysis(self, temp_dir):
        """Test dependency analysis across different package managers."""
        analyzer = TechnologyStackAnalyzer()

        # Create projects with different dependency managers
        dependency_files = {
            "requirements.txt": "django==4.2.0\npsycopg2==2.9.7\npillow==10.0.0",
            "package.json": """
{
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^5.7.0"
  },
  "devDependencies": {
    "jest": "^29.6.2"
  }
}""",
            "Cargo.toml": """
[dependencies]
serde = "1.0"
tokio = { version = "1", features = ["full"] }
clap = "4.0"
""",
            "go.mod": """
module example.com/project

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-redis/redis/v8 v8.11.5
)
""",
        }

        for filename, content in dependency_files.items():
            (temp_dir / filename).write_text(content)

        stack = analyzer.analyze_stack(temp_dir)

        # Should detect dependencies from all package managers
        dependencies = [dep.name for dep in stack.dependencies]
        assert "django" in dependencies
        assert "express" in dependencies
        assert "serde" in dependencies
        assert "gin-gonic/gin" in dependencies

        # Should categorize dependencies
        runtime_deps = [
            dep for dep in stack.dependencies if dep.dependency_type == "runtime"
        ]
        dev_deps = [
            dep for dep in stack.dependencies if dep.dependency_type == "development"
        ]

        assert len(runtime_deps) > 0
        assert len(dev_deps) > 0

    def test_infrastructure_detection(self, temp_dir):
        """Test infrastructure and deployment technology detection."""
        analyzer = TechnologyStackAnalyzer()

        # Create infrastructure files
        infra_files = {
            "Dockerfile": """
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
""",
            "docker-compose.yml": """
version: '3'
services:
  app:
    build: .
  redis:
    image: redis:alpine
  postgres:
    image: postgres:15
""",
            "k8s/deployment.yaml": """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
""",
            ".github/workflows/deploy.yml": """
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
""",
            "terraform/main.tf": """
resource "aws_instance" "app" {
  ami           = "ami-12345"
  instance_type = "t3.micro"
}
""",
        }

        for file_path, content in infra_files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        stack = analyzer.analyze_stack(temp_dir)

        infra_techs = [
            tech.name
            for tech in stack.technologies
            if tech.category == "infrastructure"
        ]
        assert "docker" in infra_techs
        assert "kubernetes" in infra_techs
        assert "github_actions" in infra_techs
        assert "terraform" in infra_techs


class TestAdvancedProjectDetector:
    """Test suite for AdvancedProjectDetector class."""

    def test_comprehensive_project_analysis(self, temp_dir):
        """Test comprehensive project analysis combining all detectors."""
        detector = AdvancedProjectDetector()

        # Create complex multi-technology project
        project_files = {
            # Backend
            "backend/requirements.txt": "fastapi==0.100.0\npsycopg2==2.9.7",
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "backend/models/user.py": "class User: pass",
            "backend/services/user_service.py": "class UserService: pass",
            # Frontend
            "frontend/package.json": (
                '{"dependencies": {"react": "^18.0.0", "typescript": "^5.0.0"}}'
            ),
            "frontend/src/App.tsx": "import React from 'react';",
            "frontend/src/components/Header.tsx": (
                "export const Header = () => <div>Header</div>;"
            ),
            # Infrastructure
            "docker-compose.yml": "version: '3'\nservices:\n  app:\n    build: .",
            "Dockerfile": "FROM python:3.9",
            ".github/workflows/ci.yml": "name: CI",
            # Documentation
            "README.md": "# My Project",
            "docs/api.md": "# API Documentation",
        }

        for file_path, content in project_files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        analysis = detector.analyze_project(temp_dir)

        # Should detect multiple aspects
        assert analysis.project_type == "multi_language"
        assert len(analysis.languages) >= 2
        assert len(analysis.frameworks) >= 2
        assert analysis.architecture.pattern in ["layered", "microservices"]
        assert analysis.technology_stack.categories["frontend"] is not None
        assert analysis.technology_stack.categories["backend"] is not None
        assert analysis.technology_stack.categories["infrastructure"] is not None

    def test_confidence_scoring_and_ranking(self, temp_dir):
        """Test confidence scoring and ranking of detection results."""
        detector = AdvancedProjectDetector()

        # Create project with clear indicators
        clear_indicators = {
            "package.json": (
                '{"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}'
            ),
            "src/App.js": (
                "import React from 'react'; export default function App() { "
                "return <div>App</div>; }"
            ),
            "src/index.js": (
                "import React from 'react'; import ReactDOM from 'react-dom';"
            ),
            "public/index.html": (
                "<html><head><title>React App</title></head><body>"
                "<div id='root'></div></body></html>"
            ),
        }

        for file_path, content in clear_indicators.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        analysis = detector.analyze_project(temp_dir)

        # Should have high confidence for React detection
        react_framework = next(
            (f for f in analysis.frameworks if f.name == "react"), None
        )
        assert react_framework is not None
        assert react_framework.confidence > 0.9

        # Should rank React as primary framework
        primary_framework = analysis.get_primary_framework()
        assert primary_framework.name == "react"

    def test_edge_case_handling(self, temp_dir):
        """Test handling of edge cases and ambiguous projects."""
        detector = AdvancedProjectDetector()

        # Create minimal/empty project
        (temp_dir / "empty.txt").touch()

        analysis = detector.analyze_project(temp_dir)

        # Should handle gracefully without errors
        assert analysis is not None
        assert analysis.project_type == "unknown"
        assert len(analysis.frameworks) == 0
        assert analysis.confidence_score < 0.5

    def test_performance_with_large_projects(self, temp_dir):
        """Test performance with large project structures."""
        detector = AdvancedProjectDetector()

        # Create large project structure
        for i in range(100):
            dir_path = temp_dir / f"module_{i}"
            dir_path.mkdir()
            for j in range(10):
                (dir_path / f"file_{j}.py").write_text(f"# Module {i} File {j}")

        import time

        start_time = time.time()

        analysis = detector.analyze_project(temp_dir)

        end_time = time.time()
        analysis_time = end_time - start_time

        # Should complete in reasonable time (less than 10 seconds for this test)
        assert analysis_time < 10.0
        assert analysis is not None
