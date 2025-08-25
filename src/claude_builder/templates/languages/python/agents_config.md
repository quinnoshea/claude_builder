# ${project_name} - Python Agent Configuration

## Python-Specific Agent Assignments

### Primary Development Agents

#### backend-architect

**Primary Role**: Python backend systems, API design, database integration

- **Specialization**: ${framework} applications, database design, API architecture
- **Responsibilities**:
  - Design scalable Python backend architectures
  - Implement REST/GraphQL APIs using ${framework}
  - Database schema design and optimization
  - Service layer and business logic implementation

#### rapid-prototyper

**Primary Role**: Quick MVP development and proof of concepts

- **Specialization**: Fast Python development, library integration
- **Responsibilities**:
  - Rapid development of Python prototypes
  - Integration of third-party Python packages
  - Quick validation of technical approaches
  - MVP feature implementation

### Testing and Quality Agents

#### test-writer-fixer

**Python Testing Specialization**:

- **Framework**: pytest with comprehensive plugin ecosystem
- **Coverage**: pytest-cov for coverage reporting
- **Mocking**: unittest.mock and pytest-mock for test doubles
- **Async Testing**: pytest-asyncio for async code testing

**Responsibilities**:

- Write comprehensive unit tests following Python testing best practices
- Implement integration tests for ${framework} applications
- Create fixtures and test utilities in conftest.py
- Maintain high test coverage (>90% target)
- Debug failing tests and improve test reliability

#### performance-benchmarker

**Python Performance Focus**:

- **Profiling**: cProfile, line_profiler, memory_profiler
- **Benchmarking**: pytest-benchmark for performance regression testing
- **Optimization**: Identify Python-specific performance bottlenecks
- **Monitoring**: APM integration for production performance tracking

### Code Quality Agents

#### Code Quality Specialist (Implied)

**Python Quality Tools**:

- **Formatting**: black, isort for consistent code style
- **Linting**: flake8, pylint for code quality checks
- **Type Checking**: mypy for static type analysis
- **Security**: bandit for security vulnerability scanning
- **Dependencies**: safety, pip-audit for dependency security

### Framework-Specific Agents

#### ${framework}-specialist

**Framework**: ${framework}
**Specialization**: ${framework}-specific best practices and patterns

- **Responsibilities**:
  - Implement ${framework}-specific features and patterns
  - Optimize ${framework} application performance
  - Handle ${framework} security considerations
  - Manage ${framework} deployment strategies

## Agent Coordination Workflows

### Feature Development Pipeline

```text

1. rapid-prototyper: Initial feature implementation

   ↓

2. backend-architect: Architecture review and optimization

   ↓

3. test-writer-fixer: Comprehensive test coverage

   ↓

4. performance-benchmarker: Performance validation

   ↓

5. devops-automator: Deployment and monitoring setup

```

### Code Quality Pipeline

```text

1. Any Agent: Code implementation

   ↓

2. Automated Quality Checks:
   - black: Code formatting
   - isort: Import organization
   - flake8: Linting
   - mypy: Type checking
   - bandit: Security scanning

   ↓

3. test-writer-fixer: Test validation

   ↓

4. Code review and merge

```

## Python-Specific Development Standards

### Code Style Configuration

```toml

# pyproject.toml

[tool.black]
line-length = 88
target-version = ['py${python_short_version}']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["${package_name}"]

[tool.mypy]
python_version = "${python_version}"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Testing Configuration

```toml

# pyproject.toml

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --cov=${package_name} --cov-report=term-missing"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "benchmark: marks tests as performance benchmarks",
]
```

### Agent-Specific Guidelines

#### For backend-architect

```python

# Example architecture pattern

class ${service_name}Service:
    """Service layer implementation following dependency injection."""

    def __init__(
        self,
        repository: ${repository_interface},
        validator: ${validator_interface},
        logger: Logger
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._logger = logger

    async def process_request(
        self,
        request: ${request_model}
    ) -> ${response_model}:
        """Process business logic with proper error handling."""
        try:

            # Validation

            validated_data = await self._validator.validate(request)

            # Business logic

            result = await self._repository.process(validated_data)

            # Response formatting

            return ${response_model}.from_result(result)

        except ValidationError as e:
            self._logger.error(f"Validation failed: {e}")
            raise ProcessingError(f"Invalid request: {e}") from e
        except RepositoryError as e:
            self._logger.error(f"Repository error: {e}")
            raise ProcessingError("Data processing failed") from e
```

#### For test-writer-fixer

```python

# Example test structure

class Test${service_name}Service:
    """Comprehensive test suite for ${service_name}Service."""

    @pytest.fixture
    def mock_repository(self):
        return Mock(spec=${repository_interface})

    @pytest.fixture
    def mock_validator(self):
        return Mock(spec=${validator_interface})

    @pytest.fixture
    def service(self, mock_repository, mock_validator):
        return ${service_name}Service(
            repository=mock_repository,
            validator=mock_validator,
            logger=Mock()
        )

    @pytest.mark.asyncio
    async def test_process_request_success(
        self,
        service,
        mock_repository,
        mock_validator
    ):
        """Test successful request processing."""

        # Arrange

        request = ${request_model}(${test_data})
        expected_response = ${response_model}(${expected_data})

        mock_validator.validate.return_value = request
        mock_repository.process.return_value = ${result_data}

        # Act

        result = await service.process_request(request)

        # Assert

        assert result == expected_response
        mock_validator.validate.assert_called_once_with(request)
        mock_repository.process.assert_called_once_with(request)
```

#### For performance-benchmarker

```python

# Example performance test

class TestPerformance:
    """Performance tests for critical operations."""

    @pytest.mark.benchmark
    def test_data_processing_benchmark(self, benchmark, test_data):
        """Benchmark data processing operation."""
        processor = ${processor_class}()
        result = benchmark(processor.process_large_dataset, test_data)

        # Assertions about result quality

        assert len(result) == len(test_data)
        assert all(item.is_processed for item in result)

    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """Test processing performance with large dataset."""
        large_data = self._generate_test_data(size=10000)
        processor = ${processor_class}()

        start_time = time.time()
        result = processor.process_large_dataset(large_data)
        execution_time = time.time() - start_time

        # Performance assertions

        assert execution_time < 30.0  # Should complete within 30 seconds
        assert len(result) == len(large_data)
```

## Environment-Specific Configurations

### Development Environment

```python

# config/development.py

class DevelopmentSettings(BaseSettings):
    """Development environment configuration."""

    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///dev.db"
    redis_url: str = "redis://localhost:6379/0"

    # Development-specific features

    enable_debug_toolbar: bool = True
    mock_external_services: bool = True
```

### Testing Environment

```python

# config/testing.py

class TestingSettings(BaseSettings):
    """Testing environment configuration."""

    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///:memory:"

    # Testing-specific features

    force_synchronous: bool = True  # Disable async for simpler testing
    mock_all_external: bool = True
```

### Production Environment

```python

# config/production.py

class ProductionSettings(BaseSettings):
    """Production environment configuration."""

    debug: bool = False
    log_level: str = "WARNING"

    # Production database

    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(20, env="DATABASE_POOL_SIZE")

    # Security settings

    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: List[str] = Field(..., env="ALLOWED_HOSTS")
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
