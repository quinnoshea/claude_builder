# ${project_name} - Python Development Guide

## Development Environment Setup

### Python Version Management

```bash

# Install Python ${python_version}

pyenv install ${python_version}
pyenv local ${python_version}

# Verify installation

python --version
```

### Virtual Environment Setup

```bash

# Create virtual environment

python -m venv venv

# Activate virtual environment
# On Linux/Mac:

source venv/bin/activate

# On Windows:

venv\Scripts\activate

# Install dependencies

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Development Dependencies

```bash

# Core development tools

pip install black isort flake8 mypy
pip install pytest pytest-cov pytest-mock
pip install pre-commit bandit safety

# Optional tools

pip install ipython jupyter
pip install ${additional_dev_tools}
```

## Code Quality Standards

### Automated Code Formatting

```bash

# Black configuration in pyproject.toml

[tool.black]
line-length = 88
target-version = ['py${python_short_version}']
include = '\.pyi?$'
extend-exclude = '''
/(

  # directories

  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''

# Format all Python files

black .

# Check formatting without changes

black --check .
```

### Import Sorting

```bash

# isort configuration in pyproject.toml

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["${package_name}"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

# Sort imports

isort .

# Check import sorting

isort --check-only .
```

### Linting Configuration

```bash

# flake8 configuration in .flake8

[flake8]
max-line-length = 88
extend-ignore =
    E203,  # whitespace before ':'
    E501,  # line too long (handled by black)
    W503,  # line break before binary operator
exclude =
    .git,
    __pycache__,
    .venv,
    build,
    dist

# Run linting

flake8 ${package_name}/
```

### Type Checking

```bash

# mypy configuration in pyproject.toml

[tool.mypy]
python_version = "${python_version}"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true

[[tool.mypy.overrides]]
module = [
    "${external_modules_without_types}",
]
ignore_missing_imports = true

# Run type checking

mypy ${package_name}/
```

## Testing Strategy

### Test Structure and Organization

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_${module1}.py
│   ├── test_${module2}.py
│   └── core/
│       ├── test_${core_module}.py
│       └── __init__.py
├── integration/                   # Integration tests (slower)
│   ├── __init__.py
│   ├── test_${integration1}.py
│   └── test_${integration2}.py
├── e2e/                          # End-to-end tests (slowest)
│   ├── __init__.py
│   └── test_${workflow}.py
└── fixtures/                     # Test data and fixtures
    ├── sample_data.json
    └── mock_responses.py
```

### Pytest Configuration

```python

# conftest.py

import pytest
from unittest.mock import Mock
from ${package_name}.config import Settings
from ${package_name}.core import ${core_class}

@pytest.fixture
def test_settings():
    """Provide test configuration settings."""
    return Settings(
        database_url="sqlite:///:memory:",
        debug=True,
        log_level="DEBUG"
    )

@pytest.fixture
def mock_${service}():
    """Mock external service for testing."""
    mock = Mock()
    mock.get_data.return_value = {"test": "data"}
    return mock

@pytest.fixture
def ${core_instance}(test_settings):
    """Provide configured core instance for testing."""
    return ${core_class}(test_settings)
```

### Test Writing Patterns

```python

# test_example.py

import pytest
from unittest.mock import patch, Mock, call
from ${package_name}.core.${module} import ${class_name}
from ${package_name}.utils.exceptions import ValidationError

class Test${class_name}:
    """Test suite for ${class_name} class."""

    def setup_method(self):
        """Setup method called before each test."""
        self.instance = ${class_name}()

    def test_initialization_with_valid_config(self, test_settings):
        """Test successful initialization with valid configuration."""
        instance = ${class_name}(test_settings)
        assert instance.config == test_settings
        assert instance.is_initialized is True

    def test_process_data_success(self, ${core_instance}):
        """Test successful data processing."""

        # Arrange

        input_data = {"key": "value", "number": 42}
        expected_output = {"processed": True, "data": input_data}

        # Act

        result = ${core_instance}.process_data(input_data)

        # Assert

        assert result == expected_output

    @patch('${package_name}.core.${module}.external_service_call')
    def test_process_with_external_service(self, mock_service, ${core_instance}):
        """Test processing with mocked external service."""

        # Arrange

        mock_service.return_value = {"status": "success"}
        input_data = {"test": "data"}

        # Act

        result = ${core_instance}.process_with_service(input_data)

        # Assert

        mock_service.assert_called_once_with(input_data)
        assert result["status"] == "success"

    def test_invalid_input_raises_validation_error(self, ${core_instance}):
        """Test that invalid input raises appropriate exception."""
        with pytest.raises(ValidationError) as exc_info:
            ${core_instance}.process_data(None)

        assert "Invalid input data" in str(exc_info.value)

    @pytest.mark.parametrize("input_value,expected", [
        ("test1", "processed_test1"),
        ("test2", "processed_test2"),
        ("", "processed_"),
    ])
    def test_transform_data_parametrized(self, input_value, expected, ${core_instance}):
        """Test data transformation with multiple inputs."""
        result = ${core_instance}.transform_data(input_value)
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_operation(self, ${core_instance}):
        """Test asynchronous operation."""
        result = await ${core_instance}.async_process_data({"async": True})
        assert result["completed"] is True
```

### Test Execution Commands

```bash

# Run all tests

pytest

# Run with coverage report

pytest --cov=${package_name} --cov-report=html --cov-report=term

# Run specific test categories

pytest tests/unit/           # Only unit tests
pytest tests/integration/    # Only integration tests
pytest tests/e2e/           # Only end-to-end tests

# Run tests matching pattern

pytest -k "test_process"    # Run tests with "process" in name
pytest tests/unit/test_core.py::TestCore::test_method  # Specific test

# Run tests with verbose output

pytest -v -s

# Run tests in parallel (with pytest-xdist)

pytest -n auto

# Run tests and stop on first failure

pytest -x

# Run only failed tests from last run

pytest --lf
```

## Performance and Profiling

### Performance Testing

```python
import time
import pytest
from ${package_name}.core import ${performance_critical_module}

class TestPerformance:
    """Performance tests for critical operations."""

    def test_large_dataset_processing_performance(self):
        """Test processing performance with large dataset."""

        # Arrange

        large_dataset = self._generate_test_data(10000)
        max_allowed_time = 5.0  # seconds

        # Act

        start_time = time.time()
        result = ${performance_critical_module}.process_large_dataset(large_dataset)
        execution_time = time.time() - start_time

        # Assert

        assert execution_time < max_allowed_time
        assert len(result) == len(large_dataset)

    @pytest.mark.benchmark
    def test_benchmark_core_operation(self, benchmark):
        """Benchmark core operation using pytest-benchmark."""
        test_data = {"key": "value" * 100}
        result = benchmark(${performance_critical_module}.core_operation, test_data)
        assert result is not None
```

### Memory Profiling

```bash

# Install memory profiler

pip install memory-profiler

# Profile memory usage

python -m memory_profiler ${script_name}.py

# Line-by-line memory profiling

@profile
def memory_intensive_function():

    # Function implementation

    pass
```

## Security Best Practices

### Dependency Security Scanning

```bash

# Check for known vulnerabilities

safety check

# Audit dependencies

pip-audit

# Update dependencies

pip-compile --upgrade requirements.in
```

### Code Security Scanning

```bash

# Run bandit security linter

bandit -r ${package_name}/

# Check for secrets in code

detect-secrets scan --all-files
```

### Secure Coding Patterns

```python
import secrets
import hashlib
from cryptography.fernet import Fernet

# Secure random generation

secure_token = secrets.token_urlsafe(32)

# Secure password hashing

def hash_password(password: str) -> str:
    """Hash password securely using PBKDF2."""
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + key

# Environment variable handling

import os
from typing import Optional

def get_secret(key: str) -> Optional[str]:
    """Get secret from environment variables securely."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} not found")
    return value
```

## Debugging and Development Tools

### Debug Configuration

```python

# debug.py - Development debugging utilities

import logging
import pdb
from typing import Any

def debug_decorator(func):
    """Decorator to add debugging info to function calls."""
    def wrapper(*args, **kwargs):
        logging.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logging.error(f"{func.__name__} raised: {e}")
            pdb.set_trace()  # Drop into debugger on exception
            raise
    return wrapper

def log_object_state(obj: Any, name: str = "object") -> None:
    """Log the current state of an object for debugging."""
    logging.debug(f"{name} state: {vars(obj)}")
```

### Interactive Development

```python

# IPython configuration for enhanced debugging

%load_ext autoreload
%autoreload 2

# Enhanced debugging with rich

from rich.console import Console
from rich.traceback import install

install()  # Beautiful tracebacks
console = Console()
console.print("Debug message", style="bold red")
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
