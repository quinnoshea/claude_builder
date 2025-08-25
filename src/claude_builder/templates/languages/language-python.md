# Python Development Guidelines

<!-- REPLACE:guidelines -->
## Python Code Quality Standards

- Follow PEP 8 style guidelines for consistent formatting
- Use type hints for function parameters and return values
- Write docstrings for all public functions, classes, and modules
- Use descriptive variable and function names

### Python Testing Requirements

- Use pytest for testing framework
- Write unit tests for all functions and classes
- Use fixtures for test data and setup
- Aim for >80% code coverage

### Python Development Workflow

- Use virtual environments for dependency isolation
- Keep requirements.txt or pyproject.toml updated
- Use tools like black, ruff, and mypy for code quality
- Follow semantic versioning for releases
<!-- /REPLACE:guidelines -->

<!-- REPLACE:getting-started -->
### Python Prerequisites

- Python 3.8+ installed
- pip or uv for package management
- Virtual environment tools (venv, virtualenv, or uv)

### Python Setup Instructions

1. Clone the repository
2. Create virtual environment: `python -m venv venv` or `uv venv`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt` or \
   `uv pip install -r requirements.txt`
5. Run tests: `pytest`
6. Start development

### Python Key Commands

```bash
# Create virtual environment
python -m venv venv  # or uv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # or uv pip install -r requirements.txt

# Run tests
pytest --cov=src --cov-report=term-missing

# Code quality checks
black src tests
ruff src tests
mypy src

# Install in development mode
pip install -e .  # or uv pip install -e .
```
<!-- /REPLACE:getting-started -->
