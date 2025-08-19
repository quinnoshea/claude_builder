# ${project_name} - Rust Development Guide

## Development Environment Setup

### Rust Installation and Management

```bash

# Install Rust using rustup

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Update Rust to latest stable

rustup update stable

# Install additional components

rustup component add rustfmt clippy

# Install useful cargo extensions

cargo install cargo-watch         # Auto-recompile on file changes
cargo install cargo-expand        # Show macro expansions
cargo install cargo-audit         # Security vulnerability scanning
cargo install cargo-outdated      # Check for outdated dependencies
cargo install cargo-tree          # Show dependency tree
cargo install cargo-nextest       # Next-generation test runner
```

### Project Setup

```bash

# Create new project

cargo new ${project_name} --name ${binary_name}
cd ${project_name}

# Initialize with library and binary

cargo new ${project_name} --lib
cd ${project_name}
mkdir src/bin
```

### Cargo.toml Configuration

```toml
[package]
name = "${project_name}"
version = "0.1.0"
edition = "2021"
rust-version = "${minimum_rust_version}"
authors = ["${author_name} <${author_email}>"]
license = "${license}"
description = "${project_description}"
homepage = "${homepage_url}"
repository = "${repository_url}"
readme = "README.md"
keywords = ["${keyword1}", "${keyword2}", "${keyword3}"]
categories = ["${category1}", "${category2}"]

[dependencies]

# Async runtime

tokio = { version = "${tokio_version}", features = ["full"] }

# Error handling

anyhow = "${anyhow_version}"
thiserror = "${thiserror_version}"

# Serialization

serde = { version = "${serde_version}", features = ["derive"] }
serde_json = "${serde_json_version}"

# Logging and tracing

tracing = "${tracing_version}"
tracing-subscriber = { version = "${tracing_subscriber_version}", features = ["json"] }

# Configuration

config = "${config_version}"

# HTTP client (if needed)

reqwest = { version = "${reqwest_version}", features = ["json", "rustls-tls"] }

# Database (if needed)

sqlx = { version = "${sqlx_version}", features = ["runtime-tokio-rustls", "postgres", "chrono", "uuid"] }

# ${framework_dependencies}

[dev-dependencies]

# Testing

tokio-test = "${tokio_test_version}"
wiremock = "${wiremock_version}"
tempfile = "${tempfile_version}"
pretty_assertions = "${pretty_assertions_version}"

# Property testing

proptest = "${proptest_version}"

# Benchmarking

criterion = { version = "${criterion_version}", features = ["html_reports"] }

[profile.dev]

# Faster linking

split-debuginfo = "unpacked"

[profile.release]

# Optimize for performance

lto = true
codegen-units = 1
panic = "abort"
strip = true

[profile.bench]
inherits = "release"
debug = true  # Keep debug info for profiling

[[bin]]
name = "${binary_name}"
path = "src/main.rs"

[[bench]]
name = "${benchmark_name}"
harness = false
```

## Development Workflow

### Code Formatting and Linting

```bash

# Format code (automatic)

cargo fmt

# Check formatting without modifying

cargo fmt -- --check

# Run clippy lints

cargo clippy

# Run clippy with stricter settings

cargo clippy -- -D warnings -D clippy::pedantic

# Run all quality checks

cargo fmt -- --check && cargo clippy -- -D warnings && cargo test
```

### Testing Commands

```bash

# Run all tests

cargo test

# Run tests with output

cargo test -- --nocapture

# Run specific test

cargo test test_${specific_function}

# Run tests matching pattern

cargo test ${pattern}

# Run tests with nextest (faster)

cargo nextest run

# Run integration tests only

cargo test --test ${integration_test_name}

# Run benchmarks

cargo bench

# Run single benchmark

cargo bench ${benchmark_name}
```

### Development Server

```bash

# Watch for changes and rebuild

cargo watch -x run

# Watch and run tests

cargo watch -x test

# Watch with clear screen

cargo watch -c -x run

# Watch specific files

cargo watch -w src -x run
```

## Project Structure Best Practices

### Module Organization

```rust
// src/lib.rs
pub mod config;
pub mod core;
pub mod error;
pub mod models;
pub mod services;
pub mod utils;

pub use error::{Error, Result};
pub use config::Config;

// Re-export commonly used types
pub mod prelude {
    pub use crate::{Error, Result, Config};
    pub use crate::models::*;
    pub use crate::services::*;
}
```

### Error Handling Architecture

```rust
// src/error.rs
use thiserror::Error;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("HTTP request failed: {0}")]
    Http(#[from] reqwest::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Validation error: {message}")]
    Validation { message: String },
    
    #[error("Not found: {resource}")]
    NotFound { resource: String },
    
    #[error("Internal error: {message}")]
    Internal { message: String },
}

impl Error {
    pub fn validation(message: impl Into<String>) -> Self {
        Self::Validation {
            message: message.into(),
        }
    }
    
    pub fn not_found(resource: impl Into<String>) -> Self {
        Self::NotFound {
            resource: resource.into(),
        }
    }
    
    pub fn internal(message: impl Into<String>) -> Self {
        Self::Internal {
            message: message.into(),
        }
    }
}
```

### Configuration Management

```rust
// src/config.rs
use serde::{Deserialize, Serialize};
use config::{Config as ConfigReader, ConfigError, Environment, File};

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub logging: LoggingConfig,
    pub external_services: ExternalServicesConfig,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ServerConfig {
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_workers")]
    pub workers: usize,
    #[serde(default = "default_timeout")]
    pub timeout_seconds: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    #[serde(default = "default_max_connections")]
    pub max_connections: u32,
    #[serde(default = "default_connect_timeout")]
    pub connect_timeout_seconds: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct LoggingConfig {
    #[serde(default = "default_log_level")]
    pub level: String,
    #[serde(default = "default_json_format")]
    pub json_format: bool,
}

impl Config {
    pub fn from_env() -> Result<Self, ConfigError> {
        let run_mode = std::env::var("RUN_MODE").unwrap_or_else(|_| "development".into());
        
        let s = ConfigReader::builder()
            .add_source(File::with_name("config/default"))
            .add_source(File::with_name(&format!("config/{}", run_mode)).required(false))
            .add_source(File::with_name("config/local").required(false))
            .add_source(Environment::with_prefix("APP").separator("_"))
            .build()?;
            
        s.try_deserialize()
    }
}

// Default value functions
fn default_host() -> String { "127.0.0.1".to_string() }
fn default_port() -> u16 { ${default_port} }
fn default_workers() -> usize { num_cpus::get() }
fn default_timeout() -> u64 { 30 }
fn default_max_connections() -> u32 { 10 }
fn default_connect_timeout() -> u64 { 5 }
fn default_log_level() -> String { "info".to_string() }
fn default_json_format() -> bool { false }
```

## Testing Strategies

### Unit Testing Patterns

```rust
// src/services/${service}.rs
#[cfg(test)]
mod tests {
    use super::*;
    use tokio_test;
    use pretty_assertions::assert_eq;

    #[tokio::test]
    async fn test_${service}_success() {
        // Arrange
        let service = ${service}::new(test_config()).await.unwrap();
        let input = ${test_input};
        
        // Act
        let result = service.process(input).await;
        
        // Assert
        assert!(result.is_ok());
        let output = result.unwrap();
        assert_eq!(output.status, "completed");
    }
    
    #[tokio::test]
    async fn test_${service}_error_handling() {
        let service = ${service}::new(test_config()).await.unwrap();
        let invalid_input = ${invalid_input};
        
        let result = service.process(invalid_input).await;
        
        assert!(result.is_err());
        match result.unwrap_err() {
            Error::Validation { message } => {
                assert!(message.contains("${expected_error_text}"));
            }
            _ => panic!("Expected validation error"),
        }
    }
    
    fn test_config() -> Config {
        Config {
            // Test configuration
            server: ServerConfig {
                host: "127.0.0.1".to_string(),
                port: 0, // Random port
                workers: 1,
                timeout_seconds: 5,
            },
            database: DatabaseConfig {
                url: "sqlite://:memory:".to_string(),
                max_connections: 1,
                connect_timeout_seconds: 1,
            },
            // ... other test config
        }
    }
}
```

### Integration Testing

```rust
// tests/${integration_test}.rs
use ${project_name}::{prelude::*, Config};
use sqlx::PgPool;
use tempfile::TempDir;
use wiremock::{MockServer, Mock, ResponseTemplate};
use wiremock::matchers::{method, path};

struct TestContext {
    config: Config,
    _temp_dir: TempDir,
    mock_server: MockServer,
    db_pool: PgPool,
}

impl TestContext {
    async fn new() -> Self {
        let temp_dir = TempDir::new().unwrap();
        let mock_server = MockServer::start().await;
        
        // Setup test database
        let db_url = std::env::var("TEST_DATABASE_URL")
            .unwrap_or_else(|_| "postgres://localhost/test_db".to_string());
        let db_pool = PgPool::connect(&db_url).await.unwrap();
        
        // Run migrations
        sqlx::migrate!("./migrations").run(&db_pool).await.unwrap();
        
        let config = Config {
            // Test configuration using mock server
            external_services: ExternalServicesConfig {
                api_base_url: mock_server.uri(),
                timeout_seconds: 5,
            },
            database: DatabaseConfig {
                url: db_url,
                max_connections: 5,
                connect_timeout_seconds: 5,
            },
            // ... other config
        };
        
        Self {
            config,
            _temp_dir: temp_dir,
            mock_server,
            db_pool,
        }
    }
}

#[tokio::test]
async fn test_full_workflow() {
    let ctx = TestContext::new().await;
    
    // Setup mock responses
    Mock::given(method("GET"))
        .and(path("/api/data"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "status": "success",
            "data": ${mock_response_data}
        })))
        .mount(&ctx.mock_server)
        .await;
    
    // Test the full workflow
    let service = ${main_service}::new(ctx.config).await.unwrap();
    let result = service.execute_workflow(${workflow_input}).await;
    
    assert!(result.is_ok());
    let output = result.unwrap();
    assert_eq!(output.status, "completed");
    
    // Verify database state
    let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM ${table_name}")
        .fetch_one(&ctx.db_pool)
        .await
        .unwrap();
    assert_eq!(count.0, 1);
}
```

### Property-Based Testing

```rust
// tests/property_tests.rs
use ${project_name}::*;
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_${function_name}_properties(
        input in prop::collection::vec(any::<${input_type}>(), 0..100)
    ) {
        let result = ${function_name}(input.clone());
        
        // Property 1: Result should not be empty if input isn't empty
        if !input.is_empty() {
            prop_assert!(!result.is_empty());
        }
        
        // Property 2: Result length should be related to input length
        prop_assert!(result.len() <= input.len() * 2);
        
        // Property 3: All elements should satisfy some property
        for item in result {
            prop_assert!(item.is_valid());
        }
    }
    
    #[test]
    fn test_${serialization_function}_roundtrip(
        data in any::<${data_type}>()
    ) {
        let serialized = serialize_data(&data).unwrap();
        let deserialized = deserialize_data(&serialized).unwrap();
        prop_assert_eq!(data, deserialized);
    }
}
```

## Performance Optimization

### Profiling and Benchmarking

```rust
// benches/${benchmark}.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use ${project_name}::*;

fn bench_${operation}(c: &mut Criterion) {
    let mut group = c.benchmark_group("${operation}");
    
    for size in [10, 100, 1000, 10000].iter() {
        let input = generate_test_data(*size);
        
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            size,
            |b, _| {
                b.iter(|| ${operation}(black_box(&input)))
            },
        );
    }
    
    group.finish();
}

fn bench_async_${operation}(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let input = generate_async_test_data();
    
    c.bench_function("async_${operation}", |b| {
        b.to_async(&rt).iter(|| async {
            ${async_operation}(black_box(&input)).await
        })
    });
}

criterion_group!(benches, bench_${operation}, bench_async_${operation});
criterion_main!(benches);

fn generate_test_data(size: usize) -> Vec<${data_type}> {
    (0..size).map(|i| ${data_type}::new(i)).collect()
}
```

### Memory and Performance Profiling

```bash

# Install profiling tools

cargo install cargo-profdata
cargo install flamegraph

# CPU profiling with perf

cargo build --release
perf record --call-graph=dwarf target/release/${binary_name}
perf report

# Memory profiling with valgrind

cargo build
valgrind --tool=massif target/debug/${binary_name}

# Heap profiling

cargo install cargo-valgrind
cargo valgrind run --bin ${binary_name}

# Flamegraph profiling

cargo flamegraph --bin ${binary_name}
```

## Security Best Practices

### Dependency Security

```bash

# Audit dependencies for vulnerabilities

cargo audit

# Check for outdated dependencies

cargo outdated

# Update dependencies

cargo update

# Vendor dependencies for offline builds

cargo vendor
```

### Secure Coding Patterns

```rust
// Secure input validation
use validator::{Validate, ValidationError};

#[derive(Debug, Validate)]
pub struct UserInput {
    #[validate(length(min = 1, max = 100))]
    #[validate(regex = "USERNAME_REGEX")]
    pub username: String,
    
    #[validate(email)]
    pub email: String,
    
    #[validate(custom = "validate_password")]
    pub password: String,
}

lazy_static::lazy_static! {
    static ref USERNAME_REGEX: regex::Regex = 
        regex::Regex::new(r"^[a-zA-Z0-9_-]+$").unwrap();
}

fn validate_password(password: &str) -> Result<(), ValidationError> {
    if password.len() < 8 {
        return Err(ValidationError::new("password_too_short"));
    }
    if !password.chars().any(|c| c.is_ascii_digit()) {
        return Err(ValidationError::new("password_needs_digit"));
    }
    Ok(())
}

// Secure data handling
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
pub struct SensitiveData {
    #[zeroize(skip)]
    pub id: u64,
    pub secret: Vec<u8>,
}
```

## Deployment Configuration

### Docker Setup

```dockerfile

# Dockerfile

FROM rust:${rust_version} as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/${binary_name} /usr/local/bin/
COPY config ./config

EXPOSE ${default_port}
USER 1000

CMD ["${binary_name}"]
```

### CI/CD Pipeline

```yaml

# .github/workflows/ci.yml

name: CI

on: [push, pull_request]

env:
  CARGO_TERM_COLOR: always

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:

    - uses: actions/checkout@v3
    
    - name: Install Rust

      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        components: rustfmt, clippy
    
    - name: Check formatting

      run: cargo fmt -- --check
    
    - name: Run clippy

      run: cargo clippy -- -D warnings
    
    - name: Run tests

      run: cargo test
      env:
        TEST_DATABASE_URL: postgres://postgres:postgres@localhost/test_db
    
    - name: Run benchmarks

      run: cargo bench
```

---

*Generated by Claude Builder v${version} on ${timestamp}*