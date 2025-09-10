# Contributing to Claude Builder

Welcome to Claude Builder! We're excited to have you contribute to making this
the best universal Claude Code environment generator.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected
to uphold this code. Please report unacceptable behavior to the project
maintainers.

### Our Standards

- **Be respectful** - Treat everyone with respect and kindness
- **Be inclusive** - Welcome newcomers and help them learn
- **Be constructive** - Provide helpful feedback and suggestions
- **Be collaborative** - Work together towards common goals

## Getting Started

### Prerequisites

- Python 3.8+ installed
- Git installed and configured
- Basic understanding of Python development
- Familiarity with Claude Code ecosystem (helpful but not required)

### Development Setup

1. **Fork and Clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/claude_builder.git
   cd claude_builder
   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**

   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

5. **Verify Setup**

   ```bash
   pytest
   claude-builder --help
   ```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes** - Fix issues and improve reliability
- ✨ **New features** - Add new functionality or templates
- 📚 **Documentation** - Improve docs, examples, and guides
- 🧪 **Tests** - Add test coverage or improve existing tests
- 🏗️ **Templates** - Create new project templates
- 🤖 **Agents** - Add or improve agent configurations
- 🎨 **Performance** - Optimize speed and efficiency

### Before You Start

1. **Check existing issues** - See if your idea is already being discussed
2. **Create an issue** - For new features or major changes, create an issue first
3. **Get feedback** - Discuss your approach with maintainers
4. **Start small** - Begin with smaller contributions to understand the codebase

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clean, well-documented code
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=claude_builder --cov-report=html

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
pytest -m "e2e"

# Test code quality
black claude_builder tests
ruff check claude_builder tests
mypy claude_builder
```

### 4. Commit Your Changes

Use conventional commit format:

```bash
git commit -m "feat: add support for Go project detection"
git commit -m "fix: resolve template loading issue on Windows"
git commit -m "docs: update installation instructions"
git commit -m "test: add integration tests for git workflows"
```

**Commit Types:**

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- Clear title and description
- Reference to related issues
- Screenshots/examples if applicable
- Checklist of changes made

### 6. PR Review Process

- **Automated checks** must pass (CI, tests, code quality)
- **Code review** by maintainers
- **Address feedback** and make requested changes
- **Final approval** and merge

## Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Environment details** (OS, Python version, claude-builder version)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** and stack traces
- **Sample project** or minimal reproduction case

### Feature Requests

Use the feature request template and include:

- **Clear description** of the feature
- **Use case** and motivation
- **Proposed solution** or implementation ideas
- **Alternatives considered**
- **Examples** of similar features in other tools

### Template Contributions

For new templates:

- **Template metadata** (languages, frameworks, project types)
- **Template files** with proper variable substitution
- **Documentation** explaining the template's purpose
- **Test cases** to validate template generation
- **Examples** of generated output

### Domain Template Guidelines (DevOps & MLOps)

Domain templates provide infrastructure and MLOps guidance that is appended to
CLAUDE.md when relevant tools are detected in a project.

- Location: `src/claude_builder/templates/domains/{devops,mlops}`
- Filenames: `INFRA.md`, `DEPLOYMENT.md`, `OBSERVABILITY.md`, `SECURITY.md`,
  `MLOPS.md`, `DATA_PIPELINE.md`, `ML_GOVERNANCE.md`
- Rendering: Sections are included only when matching tools are present in the
  analysis. Gating is handled by the generator, and you can also use
  conditionals inside templates.
- Supported syntax:
  - Conditionals: `{% if dev_environment.tools.terraform %} ... {% endif %}`
  - Loops: `{% for file in dev_environment.tools.terraform.files %} ...`
    `{% endfor %}`
  - Variables: `{{ dev_environment.tools.terraform.confidence }}`
  - Dotted paths are supported in `if/for` and `{{ }}` expressions.
- Available context:
  - `dev_environment.tools` is a dict keyed by lowercase tool name
    (`terraform`, `kubernetes`, `helm`, `prometheus`, `grafana`, `opentelemetry`,
    `vault`, `tfsec`, `trivy`, `mlflow`, `airflow`, `prefect`, `dagster`, `dvc`,
    `dbt`, `great_expectations`, `feast`, etc.).
  - Each entry provides: `{ present: bool, confidence: str|"unknown",`
    `files: list }`.
  - Not all detectors populate `confidence` or `files` yet; write templates to
    degrade gracefully when values are missing.
- Best practices:
  - Make guidance practical and action-oriented (commands, checklists).
  - Avoid external network fetches; link text is fine but generation must not
    depend on network.
  - Keep conditionals specific to avoid emitting irrelevant sections.
  - Use lowercase tool keys; prefer portable shell snippets.
  - Add focused unit tests under `tests/unit/templates/` that exercise your
    template with and without relevant tools present.

Example snippet:

````markdown
{% if dev_environment.tools.kubernetes %}
### Kubernetes Deployments

Define resource requests/limits and probes. Example:

```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }
  initialDelaySeconds: 10
  periodSeconds: 5
```

{% endif %}

````

<a name="code-standards"></a>

## Code Standards

### Python Code Style

- **Black** for code formatting
- **Ruff** for linting and import sorting
- **mypy** for type checking
- **Line length**: 88 characters (Black default)
- **Type hints**: Required for all public APIs

### Code Quality

```bash
# Format code
black claude_builder tests

# Check linting
ruff check claude_builder tests

# Type checking
mypy claude_builder

# Security scanning
bandit -r claude_builder
```

### Project Structure

Follow the established structure:

```text
claude_builder/
├── core/           # Core analysis and generation logic
├── cli/            # Command-line interface
├── templates/      # Built-in templates
├── utils/          # Utility functions
└── tests/          # Test suite
    ├── unit/       # Unit tests
    ├── integration/ # Integration tests
    ├── e2e/        # End-to-end tests
    └── fixtures/   # Test data and fixtures
```

### Documentation Standards

- **Docstrings**: Use Google-style docstrings for all public functions/classes
- **Type hints**: Include comprehensive type annotations
- **Comments**: Explain complex logic and business rules
- **README updates**: Update relevant documentation for new features

## Testing

### Test Categories

- **Unit Tests** (`tests/unit/`) - Fast, isolated tests for individual components
- **Integration Tests** (`tests/integration/`) - Test component interactions
- **End-to-End Tests** (`tests/e2e/`) - Full workflow testing
- **Performance Tests** (`tests/performance/`) - Speed and efficiency tests

### Writing Tests

```python
import pytest
from claude_builder.core.analyzer import ProjectAnalyzer

@pytest.mark.unit
def test_python_project_detection(sample_python_project):
    """Test detection of Python projects."""
    analyzer = ProjectAnalyzer()
    result = analyzer.analyze(sample_python_project)

    assert result.language_info.primary == "python"
    assert result.language_info.confidence >= 90
```

### Test Fixtures

Use the established fixtures in `conftest.py`:

- `temp_dir` - Temporary directory for tests
- `sample_project_path` - Sample project structure
- `git_repo` - Git repository for testing
- `sample_analysis` - Mock project analysis result

### Running Tests

```bash
# All tests
pytest

# Specific categories
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage
pytest --cov=claude_builder --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Documentation

### Documentation Types

- **API Documentation** - Docstrings in code
- **User Guide** - README.md and examples
- **Developer Guide** - This CONTRIBUTING.md
- **Template Documentation** - Template-specific guides

### Writing Guidelines

- **Clear and concise** language
- **Code examples** for all features
- **Screenshots** for CLI interfaces (when helpful)
- **Up-to-date** with current codebase

## Release Process

For maintainers, the release process includes:

1. **Version bump** in `__init__.py` and `pyproject.toml`
2. **Changelog update** with new features and fixes
3. **Tag creation** with `git tag v1.2.3`
4. **GitHub release** with release notes
5. **PyPI publication** via CI/CD

## Getting Help

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Email** - For security issues or private concerns

### Resources

- **Project Documentation** - README.md and docs/
- **Code Examples** - examples/ directory
- **Test Cases** - tests/ directory for implementation examples

## Recognition

Contributors are recognized through:

- **Contributors list** in README.md
- **Release notes** crediting contributors
- **GitHub contributor insights**

Thank you for contributing to Claude Builder! 🚀

---

For questions about contributing, please create an issue or discussion on\nGitHub.
