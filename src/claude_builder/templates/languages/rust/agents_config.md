# ${project_name} - Rust Agent Configuration

## Rust-Specific Agent Assignments

### Primary Development Agents

#### backend-architect
**Primary Role**: Rust system architecture, performance optimization, memory safety
- **Specialization**: High-performance Rust applications, concurrent systems, memory management
- **Responsibilities**: 
  - Design scalable Rust architectures using ownership and borrowing
  - Implement async/await patterns with Tokio runtime
  - Optimize for zero-cost abstractions and compile-time guarantees
  - Database integration with SQLx and connection pooling

#### rapid-prototyper  
**Primary Role**: Fast Rust prototyping and proof of concepts
- **Specialization**: Quick Rust development, crate integration, MVP validation
- **Responsibilities**:
  - Rapid development of Rust prototypes with appropriate error handling
  - Integration of ecosystem crates (serde, tokio, anyhow, etc.)
  - Performance-conscious prototyping with proper async patterns
  - Quick validation of Rust architectural approaches

### Specialized Rust Agents

#### rust-performance-specialist
**Role**: Performance optimization and systems programming
- **Focus Areas**: 
  - Memory usage optimization and zero-allocation patterns
  - Async performance tuning and task scheduling
  - Compile-time optimization and generic specialization
  - Profiling with cargo flamegraph and criterion benchmarks

#### rust-safety-expert
**Role**: Memory safety, security, and correctness
- **Focus Areas**:
  - Ownership pattern design and borrow checker satisfaction
  - Thread safety with Send/Sync traits and Arc/Mutex patterns
  - Security audit with cargo-audit and safe coding practices
  - Error handling with thiserror and anyhow integration

### Testing and Quality Agents

#### test-writer-fixer
**Rust Testing Specialization**:
- **Unit Testing**: Built-in test framework with #[test] attributes
- **Integration Testing**: Full integration tests in tests/ directory
- **Property Testing**: Proptest for property-based validation
- **Async Testing**: tokio-test for async function testing
- **Benchmarking**: Criterion for performance regression testing

**Responsibilities**:
- Write comprehensive unit tests following Rust testing conventions
- Implement integration tests with proper test setup and teardown
- Create property-based tests for complex data transformations
- Develop benchmark suites for performance-critical operations
- Mock external dependencies using wiremock and test doubles

#### performance-benchmarker
**Rust Performance Focus**:
- **Benchmarking**: Criterion for statistical benchmarking
- **Profiling**: Flamegraph, perf, and valgrind integration
- **Memory Analysis**: Memory profiling with massif and heaptrack
- **Async Profiling**: Tokio console and tracing for async performance

### Framework-Specific Agents

#### ${framework}-specialist
**Framework**: ${framework}
**Specialization**: ${framework}-specific patterns and optimizations
- **Responsibilities**:
  - Implement ${framework}-specific features using idiomatic Rust patterns
  - Optimize ${framework} applications for performance and resource usage
  - Handle ${framework} security considerations and best practices
  - Manage ${framework} deployment and configuration strategies

## Agent Coordination Workflows

### Rust Development Pipeline
```
1. rapid-prototyper: Initial Rust implementation with proper error handling
   ↓
2. backend-architect: Architecture review, ownership pattern optimization
   ↓
3. rust-safety-expert: Safety review, borrow checker optimization
   ↓
4. test-writer-fixer: Comprehensive test coverage including property tests
   ↓
5. rust-performance-specialist: Performance optimization and benchmarking
   ↓
6. devops-automator: Deployment with optimized build configuration
```

### Quality Assurance Pipeline
```
1. Any Agent: Rust code implementation
   ↓
2. Automated Quality Checks:
   - cargo fmt: Code formatting
   - cargo clippy: Linting and best practices
   - cargo audit: Security vulnerability scanning
   - cargo test: Unit and integration tests
   ↓
3. rust-safety-expert: Manual safety and security review
   ↓
4. performance-benchmarker: Performance validation
   ↓
5. Code review and merge
```

## Rust-Specific Development Standards

### Cargo Configuration
```toml
# Cargo.toml
[package]
name = "${project_name}"
version = "0.1.0"
edition = "2021"
rust-version = "${minimum_rust_version}"

[dependencies]
# Core async runtime
tokio = { version = "${tokio_version}", features = ["full"] }

# Error handling
anyhow = "${anyhow_version}"
thiserror = "${thiserror_version}"

# Serialization
serde = { version = "${serde_version}", features = ["derive"] }

# Tracing and logging
tracing = "${tracing_version}"
tracing-subscriber = { version = "${tracing_subscriber_version}", features = ["json"] }

# ${additional_dependencies}

[dev-dependencies]
tokio-test = "${tokio_test_version}"
proptest = "${proptest_version}"
criterion = { version = "${criterion_version}", features = ["html_reports"] }
wiremock = "${wiremock_version}"

[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

### Development Tools Configuration
```toml
# rustfmt.toml
max_width = 100
hard_tabs = false
tab_spaces = 4
newline_style = "Unix"
use_small_heuristics = "Default"
reorder_imports = true
reorder_modules = true
remove_nested_parens = true
edition = "2021"

# clippy.toml
cognitive-complexity-threshold = 30
type-complexity-threshold = 250
too-many-arguments-threshold = 7
```

### Agent-Specific Guidelines

#### For backend-architect
```rust
// Example service architecture pattern
use std::sync::Arc;
use tokio::sync::RwLock;
use anyhow::{Context, Result};

pub struct ${service_name}Service {
    repository: Arc<dyn ${repository_name}Repository>,
    config: Arc<${config_name}Config>,
    cache: Arc<RwLock<${cache_type}>>,
}

impl ${service_name}Service {
    pub fn new(
        repository: Arc<dyn ${repository_name}Repository>,
        config: Arc<${config_name}Config>,
    ) -> Self {
        Self {
            repository,
            config,
            cache: Arc::new(RwLock::new(${cache_type}::new())),
        }
    }
    
    #[tracing::instrument(skip(self), fields(request_id = %request.id))]
    pub async fn process_request(
        &self, 
        request: ${request_type}
    ) -> Result<${response_type}> {
        // Input validation
        request.validate()
            .context("Invalid request parameters")?;
        
        // Check cache first
        if let Some(cached) = self.check_cache(&request.key()).await {
            return Ok(cached);
        }
        
        // Process with repository
        let result = self.repository
            .process(request)
            .await
            .context("Repository processing failed")?;
        
        // Update cache
        self.update_cache(&result).await;
        
        Ok(result)
    }
    
    async fn check_cache(&self, key: &str) -> Option<${response_type}> {
        let cache = self.cache.read().await;
        cache.get(key).cloned()
    }
    
    async fn update_cache(&self, result: &${response_type}) {
        let mut cache = self.cache.write().await;
        cache.insert(result.key(), result.clone());
    }
}

// Trait-based dependency injection
#[async_trait::async_trait]
pub trait ${repository_name}Repository: Send + Sync {
    async fn process(&self, request: ${request_type}) -> Result<${response_type}>;
    async fn find_by_id(&self, id: ${id_type}) -> Result<Option<${entity_type}>>;
}
```

#### For test-writer-fixer
```rust
// Example comprehensive test suite
#[cfg(test)]
mod tests {
    use super::*;
    use tokio_test;
    use proptest::prelude::*;
    use wiremock::{MockServer, Mock, ResponseTemplate};
    use std::sync::Arc;

    // Unit tests
    #[tokio::test]
    async fn test_process_request_success() {
        // Arrange
        let mock_repo = Arc::new(MockRepository::new());
        let config = Arc::new(test_config());
        let service = ${service_name}Service::new(mock_repo.clone(), config);
        
        let request = ${request_type} {
            id: "test-id".to_string(),
            data: "test-data".to_string(),
        };
        
        let expected_response = ${response_type} {
            id: request.id.clone(),
            result: "processed".to_string(),
        };
        
        mock_repo.expect_process()
            .with(eq(request.clone()))
            .return_once(move |_| Ok(expected_response.clone()));
        
        // Act
        let result = service.process_request(request).await;
        
        // Assert
        assert!(result.is_ok());
        let response = result.unwrap();
        assert_eq!(response.result, "processed");
    }
    
    #[tokio::test]
    async fn test_process_request_with_cache() {
        // Test caching behavior
        let mock_repo = Arc::new(MockRepository::new());
        let config = Arc::new(test_config());
        let service = ${service_name}Service::new(mock_repo.clone(), config);
        
        let request = ${request_type} {
            id: "cached-test".to_string(),
            data: "test-data".to_string(),
        };
        
        // First call should hit repository
        mock_repo.expect_process()
            .times(1)
            .return_once(|_| Ok(${response_type}::default()));
        
        // First call
        let _ = service.process_request(request.clone()).await.unwrap();
        
        // Second call should hit cache (no additional repository calls)
        let _ = service.process_request(request).await.unwrap();
        
        // Verify expectations
        mock_repo.checkpoint();
    }
    
    // Property-based tests
    proptest! {
        #[test]
        fn test_request_validation_properties(
            id in "[a-zA-Z0-9-]{1,50}",
            data in "[a-zA-Z0-9 ]{1,100}"
        ) {
            let request = ${request_type} { id, data };
            let result = request.validate();
            
            // All valid inputs should pass validation
            prop_assert!(result.is_ok());
        }
        
        #[test]
        fn test_cache_key_consistency(
            requests in prop::collection::vec(any::<${request_type}>(), 1..10)
        ) {
            for request in requests {
                let key1 = request.key();
                let key2 = request.key();
                
                // Cache keys should be consistent
                prop_assert_eq!(key1, key2);
                
                // Keys should not be empty
                prop_assert!(!key1.is_empty());
            }
        }
    }
    
    // Integration tests
    #[tokio::test]
    async fn test_full_service_integration() {
        // Setup test database/external services
        let mock_server = MockServer::start().await;
        
        Mock::given(method("POST"))
            .and(path("/api/process"))
            .respond_with(ResponseTemplate::new(200)
                .set_body_json(json!({"status": "success"})))
            .mount(&mock_server)
            .await;
        
        // Test with real repository implementation
        let repository = Arc::new(HttpRepository::new(mock_server.uri()));
        let config = Arc::new(integration_test_config());
        let service = ${service_name}Service::new(repository, config);
        
        let request = ${request_type} {
            id: "integration-test".to_string(),
            data: "integration-data".to_string(),
        };
        
        let result = service.process_request(request).await;
        assert!(result.is_ok());
    }
    
    // Helper functions
    fn test_config() -> ${config_name}Config {
        ${config_name}Config {
            timeout_seconds: 5,
            cache_ttl_seconds: 60,
            max_retries: 3,
        }
    }
    
    fn integration_test_config() -> ${config_name}Config {
        ${config_name}Config {
            timeout_seconds: 30,
            cache_ttl_seconds: 300,
            max_retries: 5,
        }
    }
}

// Benchmark tests
#[cfg(test)]
mod benchmarks {
    use super::*;
    use criterion::{black_box, Criterion};
    
    pub fn bench_process_request(c: &mut Criterion) {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let service = setup_benchmark_service();
        
        c.bench_function("process_request", |b| {
            b.to_async(&rt).iter(|| async {
                let request = create_benchmark_request();
                service.process_request(black_box(request)).await.unwrap()
            });
        });
    }
    
    pub fn bench_cache_operations(c: &mut Criterion) {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let service = setup_benchmark_service();
        
        let mut group = c.benchmark_group("cache_operations");
        
        for size in [10, 100, 1000].iter() {
            group.bench_with_input(
                criterion::BenchmarkId::from_parameter(size),
                size,
                |b, &size| {
                    b.to_async(&rt).iter(|| async {
                        for i in 0..size {
                            let request = create_numbered_request(i);
                            service.process_request(black_box(request)).await.unwrap();
                        }
                    });
                },
            );
        }
        
        group.finish();
    }
}
```

#### For rust-performance-specialist
```rust
// Performance optimization examples
use std::sync::Arc;
use dashmap::DashMap;  // Lock-free concurrent hashmap
use once_cell::sync::Lazy;  // Lazy static initialization
use tokio::task::JoinSet;  // Efficient task management

// Zero-allocation string processing
pub fn process_string_efficiently(input: &str) -> String {
    // Use iterators and avoid intermediate allocations
    input
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_ascii_uppercase())
        .collect()
}

// Efficient concurrent processing
pub async fn process_items_concurrent<T, R>(
    items: Vec<T>,
    processor: impl Fn(T) -> R + Send + Sync + 'static,
    concurrency_limit: usize,
) -> Vec<R>
where
    T: Send + 'static,
    R: Send + 'static,
{
    let processor = Arc::new(processor);
    let mut set = JoinSet::new();
    let semaphore = Arc::new(tokio::sync::Semaphore::new(concurrency_limit));
    
    for item in items {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        let processor = processor.clone();
        
        set.spawn(async move {
            let _permit = permit;  // Hold permit until task completes
            processor(item)
        });
    }
    
    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        results.push(result.unwrap());
    }
    
    results
}

// Lock-free caching
static GLOBAL_CACHE: Lazy<DashMap<String, Arc<CachedData>>> = 
    Lazy::new(|| DashMap::new());

pub fn get_or_compute<F>(key: &str, compute: F) -> Arc<CachedData>
where
    F: FnOnce() -> CachedData,
{
    GLOBAL_CACHE
        .entry(key.to_string())
        .or_insert_with(|| Arc::new(compute()))
        .clone()
}
```

## Environment-Specific Configurations

### Development Environment
```toml
# config/development.toml
[server]
host = "127.0.0.1"
port = ${dev_port}
workers = 2

[database]
url = "postgres://localhost/dev_db"
max_connections = 5

[logging]
level = "debug"
json_format = false
```

### Production Environment
```toml
# config/production.toml
[server]
host = "0.0.0.0"
port = ${prod_port}
workers = 0  # Use all available cores

[database]
max_connections = 20
connect_timeout_seconds = 10

[logging]
level = "info"
json_format = true
```

---

*Generated by Claude Builder v${version} on ${timestamp}*