# ${project_name} - Rust Development Instructions

## Project Context

${project_description}

**Language**: Rust ${rust_version}
**Framework**: ${framework}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## Rust Development Standards

### Code Style and Formatting

- Follow official Rust style guidelines (rustfmt)
- Use `cargo fmt` for automatic formatting
- Enable clippy for additional linting
- Use `cargo clippy -- -D warnings` to treat warnings as errors

### Project Structure

```text
${project_name}/
├── Cargo.toml                    # Project configuration
├── Cargo.lock                    # Dependency lock file
├── src/
│   ├── main.rs                   # Binary entry point
│   ├── lib.rs                    # Library root (if applicable)
│   ├── ${module1}/
│   │   ├── mod.rs
│   │   ├── ${submodule1}.rs
│   │   └── ${submodule2}.rs
│   └── bin/                      # Additional binaries
│       └── ${additional_binary}.rs
├── tests/                        # Integration tests
│   └── ${integration_test}.rs
├── benches/                      # Benchmarks
│   └── ${benchmark}.rs
├── examples/                     # Example code
│   └── ${example}.rs
└── docs/                         # Documentation
    └── ${documentation}.md
```

### Error Handling Patterns

```rust
use anyhow::{Context, Result};
use thiserror::Error;

// Define custom error types
#[derive(Error, Debug)]
pub enum ${project_name}Error {
    #[error("Configuration error: {message}")]
    Configuration { message: String },

    #[error("Processing failed: {source}")]
    Processing {
        #[from]
        source: ProcessingError,
    },

    #[error("IO operation failed")]
    Io(#[from] std::io::Error),
}

// Use Result types consistently
pub fn process_data(input: &str) -> Result<ProcessedData> {
    let parsed = parse_input(input)
        .context("Failed to parse input data")?;

    let processed = transform_data(parsed)
        .context("Failed to transform data")?;

    Ok(processed)
}

// Error propagation with context
pub fn complex_operation() -> Result<()> {
    read_config()
        .context("Failed to read configuration")?;

    process_files()
        .context("Failed to process files")?;

    save_results()
        .context("Failed to save results")?;

    Ok(())
}
```

### Memory Safety and Ownership

```rust
use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::RwLock;

// Shared state pattern
pub struct ${shared_state} {
    data: Arc<RwLock<HashMap<String, ${data_type}>>>,
}

impl ${shared_state} {
    pub fn new() -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn get(&self, key: &str) -> Option<${data_type}> {
        let data = self.data.read().await;
        data.get(key).cloned()
    }

    pub async fn insert(&self, key: String, value: ${data_type}) {
        let mut data = self.data.write().await;
        data.insert(key, value);
    }
}

// RAII patterns for resource management
pub struct ${resource_manager} {
    connection: ${connection_type},
}

impl ${resource_manager} {
    pub fn new(config: &Config) -> Result<Self> {
        let connection = establish_connection(config)?;
        Ok(Self { connection })
    }
}

impl Drop for ${resource_manager} {
    fn drop(&mut self) {
        // Cleanup resources
        self.connection.close();
    }
}
```

## Testing Standards

### Test Organization

```rust
// Unit tests in the same file
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_${function_name}_success() {
        let input = ${test_input};
        let result = ${function_name}(input);
        assert_eq!(result, ${expected_output});
    }

    #[test]
    fn test_${function_name}_error_case() {
        let invalid_input = ${invalid_input};
        let result = ${function_name}(invalid_input);
        assert!(result.is_err());
    }
}

// Async testing
#[tokio::test]
async fn test_async_operation() {
    let service = ${service_name}::new().await;
    let result = service.process_async(${test_data}).await;
    assert!(result.is_ok());
}

// Property-based testing with proptest
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_${function_name}_properties(
        input in any::<${input_type}>()
    ) {
        let result = ${function_name}(input);
        // Property assertions
        prop_assert!(result.len() >= input.len());
    }
}
```

### Integration Testing

```rust
// tests/${integration_test}.rs
use ${project_name}::*;
use std::sync::Once;

static INIT: Once = Once::new();

fn setup() {
    INIT.call_once(|| {
        // One-time setup for integration tests
        env_logger::init();
    });
}

#[tokio::test]
async fn test_full_workflow() {
    setup();

    // Arrange
    let config = Config::test_config();
    let service = ${service_name}::new(config).await.unwrap();

    // Act
    let result = service.execute_workflow(${test_workflow_data}).await;

    // Assert
    assert!(result.is_ok());
    let response = result.unwrap();
    assert_eq!(response.status, "completed");
}
```

### Benchmark Testing

```rust
// benches/${benchmark}.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use ${project_name}::${module_to_benchmark};

fn benchmark_${operation}(c: &mut Criterion) {
    let input = ${benchmark_input};

    c.bench_function("${operation}", |b| {
        b.iter(|| ${operation}(black_box(&input)))
    });
}

fn benchmark_${async_operation}(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let input = ${benchmark_input};

    c.bench_function("${async_operation}", |b| {
        b.iter(|| {
            rt.block_on(async {
                ${async_operation}(black_box(&input)).await
            })
        })
    });
}

criterion_group!(benches, benchmark_${operation}, benchmark_${async_operation});
criterion_main!(benches);
```

## Async Programming Patterns

### Tokio Best Practices

```rust
use tokio::{
    sync::{mpsc, oneshot},
    time::{sleep, Duration, timeout},
    task::JoinSet,
};
use futures_util::{stream::StreamExt, future::try_join_all};

// Async service pattern
pub struct ${async_service} {
    tx: mpsc::Sender<${command_type}>,
}

impl ${async_service} {
    pub fn new() -> (Self, ${service_handle}) {
        let (tx, rx) = mpsc::channel(100);
        let handle = tokio::spawn(Self::run_service(rx));

        (Self { tx }, ServiceHandle { handle })
    }

    async fn run_service(mut rx: mpsc::Receiver<${command_type}>) {
        while let Some(command) = rx.recv().await {
            match command {
                ${command_type}::${command_variant}(data, response_tx) => {
                    let result = Self::process_command(data).await;
                    let _ = response_tx.send(result);
                }
            }
        }
    }

    pub async fn send_command(&self, data: ${data_type}) -> Result<${response_type}> {
        let (tx, rx) = oneshot::channel();
        let command = ${command_type}::${command_variant}(data, tx);

        self.tx.send(command).await
            .map_err(|_| ${project_name}Error::ServiceUnavailable)?;

        rx.await
            .map_err(|_| ${project_name}Error::ServiceTimeout)?
    }
}

// Parallel processing pattern
pub async fn process_items_parallel(
    items: Vec<${item_type}>,
    concurrency_limit: usize,
) -> Result<Vec<${result_type}>> {
    use futures_util::stream::{self, StreamExt};

    stream::iter(items)
        .map(|item| async move { process_single_item(item).await })
        .buffer_unordered(concurrency_limit)
        .collect::<Vec<_>>()
        .await
        .into_iter()
        .collect()
}

// Timeout and retry patterns
pub async fn reliable_operation<T, F, Fut>(
    operation: F,
    max_retries: usize,
    timeout_duration: Duration,
) -> Result<T>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T>>,
{
    let mut attempts = 0;

    loop {
        match timeout(timeout_duration, operation()).await {
            Ok(Ok(result)) => return Ok(result),
            Ok(Err(e)) if attempts >= max_retries => return Err(e),
            Ok(Err(_)) => {
                attempts += 1;
                sleep(Duration::from_millis(100 * attempts as u64)).await;
            }
            Err(_) => {
                if attempts >= max_retries {
                    return Err(${project_name}Error::Timeout);
                }
                attempts += 1;
            }
        }
    }
}
```

## Configuration Management

### Configuration Structure

```rust
use serde::{Deserialize, Serialize};
use config::{Config, ConfigError, Environment, File};

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ${config_name} {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub logging: LoggingConfig,
    pub features: FeatureFlags,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub workers: usize,
    pub timeout_seconds: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
    pub connect_timeout_seconds: u64,
}

impl ${config_name} {
    pub fn from_env() -> Result<Self, ConfigError> {
        let s = Config::builder()
            .add_source(File::with_name("config/default"))
            .add_source(File::with_name(&format!("config/{}",
                std::env::var("RUN_MODE").unwrap_or_else(|_| "development".into())
            )).required(false))
            .add_source(Environment::with_prefix("APP"))
            .build()?;

        s.try_deserialize()
    }
}
```

## Logging and Observability

### Structured Logging

```rust
use tracing::{info, warn, error, debug, instrument, span, Level};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// Initialize tracing
pub fn init_tracing() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "${project_name}=debug,tower_http=debug".into()),
        ))
        .with(tracing_subscriber::fmt::layer().json())
        .init();
}

// Instrumented functions
#[instrument(skip(data), fields(data_len = data.len()))]
pub async fn process_data(data: Vec<${data_type}>) -> Result<${result_type}> {
    let span = span!(Level::INFO, "processing_stage");
    let _enter = span.enter();

    debug!("Starting data processing with {} items", data.len());

    let result = expensive_operation(data).await?;

    info!("Processing completed successfully");
    Ok(result)
}

// Error logging with context
pub fn handle_error(error: &${project_name}Error) {
    match error {
        ${project_name}Error::Configuration { message } => {
            error!("Configuration error: {}", message);
        }
        ${project_name}Error::Processing { source } => {
            error!("Processing failed: {:?}", source);
        }
        _ => {
            error!("Unexpected error: {:?}", error);
        }
    }
}
```

## Performance Guidelines

### Memory Management

```rust
// Use appropriate collection types
use std::collections::{HashMap, BTreeMap, HashSet};
use ahash::AHashMap; // Faster HashMap for non-cryptographic use

// Pool expensive resources
use deadpool::managed::{Manager, Pool};

pub struct ${connection_manager};

#[async_trait::async_trait]
impl Manager for ${connection_manager} {
    type Type = ${connection_type};
    type Error = ${error_type};

    async fn create(&self) -> Result<Self::Type, Self::Error> {
        ${connection_type}::connect(&self.config).await
    }

    async fn recycle(&self, obj: &mut Self::Type) -> Result<(), Self::Error> {
        obj.reset().await
    }
}

// Zero-copy operations where possible
pub fn process_slice(data: &[u8]) -> &[u8] {
    // Process data in-place without allocation
    &data[skip_bytes..]
}

// Use Cow for conditional ownership
use std::borrow::Cow;

pub fn maybe_transform<'a>(input: &'a str, should_transform: bool) -> Cow<'a, str> {
    if should_transform {
        Cow::Owned(input.to_uppercase())
    } else {
        Cow::Borrowed(input)
    }
}
```

### Compilation Optimizations

```toml

# Cargo.toml optimization profiles

[profile.release]
lto = true              # Link-time optimization
codegen-units = 1       # Better optimization
panic = "abort"         # Smaller binary
strip = true            # Remove debug info

[profile.bench]
inherits = "release"
debug = true            # Keep debug info for profiling
```

## Security Best Practices

### Input Validation

```rust
use validator::{Validate, ValidationError};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Validate)]
pub struct ${input_type} {
    #[validate(length(min = 1, max = 100))]
    pub name: String,

    #[validate(email)]
    pub email: String,

    #[validate(range(min = 1, max = 1000))]
    pub age: u32,

    #[validate(custom = "validate_custom_field")]
    pub custom_field: String,
}

fn validate_custom_field(value: &str) -> Result<(), ValidationError> {
    if value.contains("forbidden") {
        return Err(ValidationError::new("forbidden_content"));
    }
    Ok(())
}

// Sanitize input
pub fn sanitize_input(input: &str) -> String {
    input
        .chars()
        .filter(|c| c.is_alphanumeric() || c.is_whitespace())
        .collect()
}
```

### Secure Data Handling

```rust
use ring::digest::{digest, SHA256};
use ring::hmac;
use zeroize::Zeroize;

#[derive(Zeroize)]
#[zeroize(drop)]
pub struct SecretData {
    value: Vec<u8>,
}

impl SecretData {
    pub fn new(data: Vec<u8>) -> Self {
        Self { value: data }
    }

    pub fn expose(&self) -> &[u8] {
        &self.value
    }
}

pub fn hash_password(password: &[u8], salt: &[u8]) -> Vec<u8> {
    let mut hasher = sha2::Sha256::new();
    hasher.update(password);
    hasher.update(salt);
    hasher.finalize().to_vec()
}

pub fn verify_signature(
    key: &[u8],
    message: &[u8],
    signature: &[u8],
) -> Result<(), ring::error::Unspecified> {
    let key = hmac::Key::new(hmac::HMAC_SHA256, key);
    hmac::verify(&key, message, signature)
}
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
