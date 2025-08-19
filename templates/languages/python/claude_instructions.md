# ${project_name} - Python Development Instructions

## Project Context
${project_description}

**Language**: Python ${python_version}
**Framework**: ${framework}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## Python Development Standards

### Code Style and Formatting
- Follow PEP 8 style guide strictly
- Use black for automatic code formatting
- Line length: 88 characters (black default)
- Use isort for import organization
- Follow PEP 484 for type hints

### Type Annotations
```python
# Required for all public functions and methods
def process_data(items: List[Dict[str, Any]]) -> Optional[ProcessedData]:
    """Process data items with comprehensive type safety."""
    pass

# Class definitions with proper typing
class ${primary_class}:
    def __init__(self, config: ${config_type}) -> None:
        self._config: ${config_type} = config
```

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional, Union

# Third-party imports
import requests
import pandas as pd

# Local application imports
from ${package_name}.core import ${core_modules}
from ${package_name}.utils import ${utility_modules}
```

### Error Handling
```python
# Use specific exceptions
class ${project_name}Error(Exception):
    """Base exception for ${project_name}."""
    pass

class ValidationError(${project_name}Error):
    """Raised when data validation fails."""
    pass

# Proper exception handling
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ProcessingError(f"Failed to process: {e}") from e
```

## Testing Standards

### Test Organization
```
tests/
├── unit/                 # Unit tests
│   ├── test_${module1}.py
│   └── test_${module2}.py
├── integration/          # Integration tests
│   ├── test_${integration1}.py
│   └── test_${integration2}.py
├── fixtures/             # Test data and fixtures
└── conftest.py           # Pytest configuration
```

### Test Writing Guidelines
```python
import pytest
from unittest.mock import Mock, patch
from ${package_name}.${module} import ${class_name}

class Test${class_name}:
    """Test suite for ${class_name}."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.${instance} = ${class_name}(${test_config})
    
    def test_${method_name}_success(self):
        """Test successful ${method_name} operation."""
        # Arrange
        expected_result = ${expected_value}
        
        # Act
        result = self.${instance}.${method_name}(${test_input})
        
        # Assert
        assert result == expected_result
    
    def test_${method_name}_with_invalid_input(self):
        """Test ${method_name} with invalid input."""
        with pytest.raises(ValidationError):
            self.${instance}.${method_name}(${invalid_input})
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=${package_name} --cov-report=html

# Run specific test file
pytest tests/unit/test_${module}.py

# Run with verbose output
pytest -v -s
```

## Package Structure

### Standard Python Package Layout
```
${package_name}/
├── __init__.py
├── cli/                  # Command-line interface
│   ├── __init__.py
│   └── main.py
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── ${core_module1}.py
│   └── ${core_module2}.py
├── api/                  # API layer (if applicable)
│   ├── __init__.py
│   └── routes/
├── models/               # Data models
│   ├── __init__.py
│   └── ${model}.py
├── utils/                # Utilities and helpers
│   ├── __init__.py
│   ├── exceptions.py
│   └── ${utility}.py
└── config/               # Configuration
    ├── __init__.py
    └── settings.py
```

## Configuration Management

### Settings Structure
```python
# config/settings.py
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    
    # API configuration
    api_key: Optional[str] = Field(None, env="API_KEY")
    api_timeout: int = Field(30, env="API_TIMEOUT")
    
    # Application settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## Logging Configuration

### Structured Logging Setup
```python
import logging
import structlog
from ${package_name}.config import settings

def configure_logging():
    """Configure structured logging for the application."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

## Dependency Management

### Core Dependencies
${core_dependencies}

### Development Dependencies
${dev_dependencies}

### Optional Dependencies
${optional_dependencies}

## Development Tools

### Code Quality Tools
```bash
# Format code
black ${package_name}/
isort ${package_name}/

# Lint code
flake8 ${package_name}/
pylint ${package_name}/

# Type checking
mypy ${package_name}/

# Security scanning
bandit -r ${package_name}/
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

## Performance Guidelines

### Best Practices
- Use appropriate data structures (dict, set, list comprehensions)
- Implement proper caching strategies
- Use async/await for I/O-bound operations
- Profile code before optimizing

### Async Programming
```python
import asyncio
import aiohttp
from typing import List, Dict, Any

async def fetch_data(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Fetch data asynchronously."""
    async with session.get(url) as response:
        return await response.json()

async def process_multiple_requests(urls: List[str]) -> List[Dict[str, Any]]:
    """Process multiple HTTP requests concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## Documentation Standards

### Docstring Format
```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    param3: List[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Perform complex processing with multiple parameters.
    
    Args:
        param1: Description of string parameter
        param2: Optional integer parameter for configuration
        param3: List of dictionaries containing processing data
    
    Returns:
        Tuple containing success boolean and result message
        
    Raises:
        ValidationError: When input parameters are invalid
        ProcessingError: When processing fails
        
    Example:
        >>> result = complex_function("test", param2=42)
        >>> print(result)
        (True, "Processing completed successfully")
    """
    pass
```

---

*Generated by Claude Builder v${version} on ${timestamp}*