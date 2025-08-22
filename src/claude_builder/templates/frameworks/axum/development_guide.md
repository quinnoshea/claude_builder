# ${project_name} - Axum Development Guide

## Environment Setup

### Rust and Axum Installation

```bash

# Install Rust using rustup (if not already installed)

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Update Rust to latest stable version

rustup update stable

# Install useful cargo extensions

cargo install cargo-watch      # Auto-recompile on file changes
cargo install cargo-expand     # Show macro expansions
cargo install cargo-audit      # Security vulnerability scanning
cargo install sqlx-cli         # SQLx database CLI
cargo install cargo-nextest    # Next-generation test runner

# Verify installation

rustc --version
cargo --version
```

### Project Initialization

```bash

# Create new Axum project

cargo new ${project_name}
cd ${project_name}

# Create project structure

mkdir -p src/{config,handlers,models,services,middleware,utils,routes}
mkdir -p migrations tests/{integration,common}
mkdir config

# Initialize database (PostgreSQL example)

sqlx database create
sqlx migrate add initial
```

### Database Setup with SQLx

```bash

# Install PostgreSQL (Ubuntu/Debian)

sudo apt update
sudo apt install postgresql postgresql-contrib

# Or using Docker

docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:14

# Set DATABASE_URL environment variable

echo "DATABASE_URL=postgresql://username:password@localhost:5432/${project_name}" > .env

# Create database and run migrations

sqlx database create
sqlx migrate run
```

### Development Configuration Files

#### Cargo.toml Configuration

```toml
[package]
name = "${project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]

# Web framework

axum = { version = "0.7", features = ["macros"] }
tokio = { version = "1.0", features = ["full"] }
tower = "0.4"
tower-http = { version = "0.5", features = ["cors", "trace", "compression", "fs"] }
hyper = { version = "1.0", features = ["full"] }

# Database

sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres", "chrono", "uuid", "migrate"] }

# Serialization

serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Authentication

jsonwebtoken = "9.0"
bcrypt = "0.14"

# Utilities

uuid = { version = "1.0", features = ["serde", "v4"] }
chrono = { version = "0.4", features = ["serde"] }
anyhow = "1.0"
thiserror = "1.0"
validator = { version = "0.16", features = ["derive"] }

# Configuration

config = "0.13"
dotenvy = "0.15"

# Logging

tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# HTTP client

reqwest = { version = "0.11", features = ["json", "rustls-tls"] }

# Caching

redis = { version = "0.23", features = ["tokio-comp"] }

[dev-dependencies]
tokio-test = "0.4"
httpc-test = "0.1"
wiremock = "0.5"
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "api_benchmarks"
harness = false

[profile.dev]
opt-level = 0
debug = true

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

#### Environment Configuration

```bash

# .env.development

DATABASE_URL=postgresql://username:password@localhost:5432/${project_name}
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret-key-here
RUST_LOG=debug,${project_name}=debug,sqlx=info
SERVER_HOST=127.0.0.1
SERVER_PORT=3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# .env.production

DATABASE_URL=postgresql://prod_user:prod_pass@db_host:5432/prod_db
REDIS_URL=redis://redis_host:6379
JWT_SECRET=secure-production-secret
RUST_LOG=info,${project_name}=info
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### Configuration Files

```yaml

# config/default.yml

server:
  host: "127.0.0.1"
  port: 3000
  workers: ~

database:
  url: "postgresql://localhost:5432/${project_name}"
  max_connections: 10
  min_connections: 1
  connect_timeout: 30
  idle_timeout: 600

auth:
  secret_key: "dev-secret-key"
  token_expiry: 3600      # 1 hour
  refresh_token_expiry: 604800  # 1 week

cors:
  allowed_origins:

    - "http://localhost:3000"
    - "http://localhost:8080"

redis:
  url: "redis://localhost:6379"
  pool_size: 10

# config/production.yml

server:
  host: "0.0.0.0"
  port: 8000

database:
  max_connections: 20
  min_connections: 5

auth:
  token_expiry: 1800      # 30 minutes
  refresh_token_expiry: 259200  # 3 days

cors:
  allowed_origins:

    - "https://yourdomain.com"
    - "https://www.yourdomain.com"

```

## Development Workflow

### Database Migrations

```bash

# Create new migration

sqlx migrate add create_users_table

# Create migration with SQL content

cat > migrations/001_create_users_table.sql << 'EOF'
-- Create users table
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
EOF

# Run migrations

sqlx migrate run

# Revert last migration

sqlx migrate revert

# Check migration status

sqlx migrate info
```

### Development Commands

```bash

# Run development server with auto-reload

cargo watch -x run

# Run with environment variables

RUST_LOG=debug cargo run

# Run tests

cargo test

# Run tests with output

cargo test -- --nocapture

# Run integration tests

cargo test --test integration_tests

# Run benchmarks

cargo bench

# Check code formatting

cargo fmt --check

# Format code

cargo fmt

# Run clippy lints

cargo clippy -- -D warnings

# Audit for security vulnerabilities

cargo audit

# Generate documentation

cargo doc --open
```

### Database Operations

```bash

# Prepare queries for offline compilation

cargo sqlx prepare

# Check queries against database

cargo sqlx check

# Generate database schema introspection

sqlx migrate info

# Create database backup

pg_dump ${DATABASE_URL} > backup.sql

# Restore from backup

psql ${DATABASE_URL} < backup.sql
```

## Testing Framework

### Test Organization

```rust
// tests/common/mod.rs
use anyhow::Result;
use ${project_name}::{app::create_app, config::Settings};
use axum::{body::Body, http::Request};
use hyper::StatusCode;
use sqlx::{PgPool, Postgres, Transaction};
use tower::ServiceExt;
use uuid::Uuid;

pub struct TestContext {
    pub db: PgPool,
    pub settings: Settings,
}

impl TestContext {
    pub async fn new() -> Result<Self> {
        let settings = Settings::test_config()?;
        let db = sqlx::PgPool::connect(&settings.database.url).await?;

        // Run migrations
        sqlx::migrate!("./migrations").run(&db).await?;

        Ok(Self { db, settings })
    }

    pub async fn cleanup(&self) -> Result<()> {
        // Clean up test data
        sqlx::query("TRUNCATE TABLE users, ${model_name_lower}s RESTART IDENTITY CASCADE")
            .execute(&self.db)
            .await?;
        Ok(())
    }

    pub async fn create_test_user(&self) -> Result<Uuid> {
        let user_id = sqlx::query_scalar!(
            r#"
            INSERT INTO users (email, username, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            "#,
            "test@example.com",
            "testuser",
            "$2b$12$dummy.hash.for.testing",
            "Test",
            "User"
        )
        .fetch_one(&self.db)
        .await?;

        Ok(user_id)
    }

    pub async fn create_auth_token(&self, user_id: Uuid) -> Result<String> {
        use jsonwebtoken::{encode, Header, EncodingKey};
        use ${project_name}::middleware::auth::Claims;

        let claims = Claims {
            user_id,
            email: "test@example.com".to_string(),
            is_admin: false,
            exp: (chrono::Utc::now() + chrono::Duration::hours(1)).timestamp() as usize,
        };

        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(self.settings.auth.secret_key.as_bytes()),
        )?;

        Ok(token)
    }
}
```

### Unit Testing Examples

```rust
// src/services/${service}.rs - Unit tests
#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::PgPool;
    use crate::models::${model}::{Create${model_name}Request, ${model_name}Status};

    async fn setup_test_db() -> PgPool {
        let pool = PgPool::connect("postgresql://localhost/test_db").await.unwrap();
        sqlx::migrate!("./migrations").run(&pool).await.unwrap();
        pool
    }

    #[tokio::test]
    async fn test_create_${model_name_lower}_success() {
        let db = setup_test_db().await;
        let service = ${service_name}Service::new(db);
        let user_id = Uuid::new_v4();

        let request = Create${model_name}Request {
            title: "Test ${model_name}".to_string(),
            description: Some("Test description".to_string()),
            content: Some("Test content".to_string()),
            status: Some(${model_name}Status::Draft),
        };

        let result = service.create_${model_name_lower}(user_id, request).await;
        assert!(result.is_ok());

        let ${model_name_lower} = result.unwrap();
        assert_eq!(${model_name_lower}.title, "Test ${model_name}");
        assert_eq!(${model_name_lower}.author_id, user_id);
        assert_eq!(${model_name_lower}.status, ${model_name}Status::Draft);
    }

    #[tokio::test]
    async fn test_get_nonexistent_${model_name_lower}() {
        let db = setup_test_db().await;
        let service = ${service_name}Service::new(db);
        let id = Uuid::new_v4();

        let result = service.get_${model_name_lower}_by_id(id).await;
        assert!(result.is_ok());
        assert!(result.unwrap().is_none());
    }

    #[tokio::test]
    async fn test_update_${model_name_lower}_not_owned() {
        let db = setup_test_db().await;
        let service = ${service_name}Service::new(db);
        let owner_id = Uuid::new_v4();
        let other_user_id = Uuid::new_v4();

        // Create ${model_name_lower} with owner
        let create_request = Create${model_name}Request {
            title: "Test ${model_name}".to_string(),
            description: None,
            content: None,
            status: None,
        };

        let ${model_name_lower} = service.create_${model_name_lower}(owner_id, create_request).await.unwrap();

        // Try to update with different user
        let update_request = Update${model_name}Request {
            title: Some("Updated title".to_string()),
            description: None,
            content: None,
            status: None,
        };

        let result = service.update_${model_name_lower}(${model_name_lower}.id, other_user_id, update_request).await;
        assert!(result.is_err());

        match result.unwrap_err() {
            AppError::Forbidden(_) => (),
            _ => panic!("Expected Forbidden error"),
        }
    }
}
```

### Integration Testing

```rust
// tests/integration/${feature}_test.rs
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use hyper::Method;
use serde_json::{json, Value};
use tower::ServiceExt;

mod common;

#[tokio::test]
async fn test_create_${model_name_lower}_success() -> anyhow::Result<()> {
    let ctx = common::TestContext::new().await?;
    let app = ${project_name}::app::create_app(&ctx.settings).await?;

    let user_id = ctx.create_test_user().await?;
    let token = ctx.create_auth_token(user_id).await?;

    let payload = json!({
        "title": "Test ${model_name}",
        "description": "Test description",
        "content": "Test content",
        "status": "draft"
    });

    let request = Request::builder()
        .method(Method::POST)
        .uri("/api/${model_name_lower}s")
        .header("content-type", "application/json")
        .header("authorization", format!("Bearer {}", token))
        .body(Body::from(payload.to_string()))?;

    let response = app.oneshot(request).await?;
    assert_eq!(response.status(), StatusCode::CREATED);

    let body = hyper::body::to_bytes(response.into_body()).await?;
    let json: Value = serde_json::from_slice(&body)?;

    assert_eq!(json["success"], true);
    assert_eq!(json["data"]["title"], "Test ${model_name}");
    assert_eq!(json["data"]["status"], "draft");

    ctx.cleanup().await?;
    Ok(())
}

#[tokio::test]
async fn test_create_${model_name_lower}_unauthorized() -> anyhow::Result<()> {
    let ctx = common::TestContext::new().await?;
    let app = ${project_name}::app::create_app(&ctx.settings).await?;

    let payload = json!({
        "title": "Test ${model_name}",
        "description": "Test description"
    });

    let request = Request::builder()
        .method(Method::POST)
        .uri("/api/${model_name_lower}s")
        .header("content-type", "application/json")
        .body(Body::from(payload.to_string()))?;

    let response = app.oneshot(request).await?;
    assert_eq!(response.status(), StatusCode::UNAUTHORIZED);

    ctx.cleanup().await?;
    Ok(())
}

#[tokio::test]
async fn test_get_${model_name_lower}s_with_pagination() -> anyhow::Result<()> {
    let ctx = common::TestContext::new().await?;
    let app = ${project_name}::app::create_app(&ctx.settings).await?;

    let user_id = ctx.create_test_user().await?;
    let token = ctx.create_auth_token(user_id).await?;

    // Create multiple ${model_name_lower}s
    for i in 1..=25 {
        let payload = json!({
            "title": format!("Test ${model_name} {}", i),
            "description": format!("Description {}", i)
        });

        let request = Request::builder()
            .method(Method::POST)
            .uri("/api/${model_name_lower}s")
            .header("content-type", "application/json")
            .header("authorization", format!("Bearer {}", token))
            .body(Body::from(payload.to_string()))?;

        app.clone().oneshot(request).await?;
    }

    // Test pagination
    let request = Request::builder()
        .method(Method::GET)
        .uri("/api/${model_name_lower}s?page=1&limit=10")
        .header("authorization", format!("Bearer {}", token))
        .body(Body::empty())?;

    let response = app.clone().oneshot(request).await?;
    assert_eq!(response.status(), StatusCode::OK);

    let body = hyper::body::to_bytes(response.into_body()).await?;
    let json: Value = serde_json::from_slice(&body)?;

    assert_eq!(json["success"], true);
    assert_eq!(json["data"]["data"].as_array().unwrap().len(), 10);
    assert_eq!(json["data"]["pagination"]["total"], 25);
    assert_eq!(json["data"]["pagination"]["total_pages"], 3);
    assert_eq!(json["data"]["pagination"]["has_next"], true);

    ctx.cleanup().await?;
    Ok(())
}

#[tokio::test]
async fn test_health_check() -> anyhow::Result<()> {
    let ctx = common::TestContext::new().await?;
    let app = ${project_name}::app::create_app(&ctx.settings).await?;

    let request = Request::builder()
        .method(Method::GET)
        .uri("/health")
        .body(Body::empty())?;

    let response = app.oneshot(request).await?;
    assert_eq!(response.status(), StatusCode::OK);

    let body = hyper::body::to_bytes(response.into_body()).await?;
    let json: Value = serde_json::from_slice(&body)?;

    assert_eq!(json["status"], "ok");

    ctx.cleanup().await?;
    Ok(())
}
```

### Performance Testing

```rust
// benches/api_benchmarks.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use tokio::runtime::Runtime;
use axum::{body::Body, http::Request};
use hyper::Method;
use tower::ServiceExt;

async fn setup_app() -> ${project_name}::app::Router {
    let settings = ${project_name}::config::Settings::new().unwrap();
    ${project_name}::app::create_app(&settings).await.unwrap()
}

fn bench_health_check(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let app = rt.block_on(setup_app());

    c.bench_function("health_check", |b| {
        b.to_async(&rt).iter(|| async {
            let request = Request::builder()
                .method(Method::GET)
                .uri("/health")
                .body(Body::empty())
                .unwrap();

            let response = app.clone().oneshot(black_box(request)).await.unwrap();
            black_box(response);
        });
    });
}

fn bench_${model_name_lower}_creation(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let app = rt.block_on(setup_app());

    let mut group = c.benchmark_group("${model_name_lower}_creation");

    for size in [10, 100, 1000].iter() {
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            size,
            |b, &size| {
                b.to_async(&rt).iter(|| async {
                    for i in 0..size {
                        let payload = serde_json::json!({
                            "title": format!("Benchmark ${model_name} {}", i),
                            "description": "Benchmark description"
                        });

                        let request = Request::builder()
                            .method(Method::POST)
                            .uri("/api/${model_name_lower}s")
                            .header("content-type", "application/json")
                            .header("authorization", "Bearer test-token")
                            .body(Body::from(payload.to_string()))
                            .unwrap();

                        let response = app.clone().oneshot(black_box(request)).await.unwrap();
                        black_box(response);
                    }
                });
            },
        );
    }

    group.finish();
}

fn bench_concurrent_requests(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let app = rt.block_on(setup_app());

    c.bench_function("concurrent_requests", |b| {
        b.to_async(&rt).iter(|| async {
            let mut handles = vec![];

            for _ in 0..100 {
                let app_clone = app.clone();
                let handle = tokio::spawn(async move {
                    let request = Request::builder()
                        .method(Method::GET)
                        .uri("/health")
                        .body(Body::empty())
                        .unwrap();

                    app_clone.oneshot(request).await.unwrap()
                });
                handles.push(handle);
            }

            for handle in handles {
                let response = handle.await.unwrap();
                black_box(response);
            }
        });
    });
}

criterion_group!(
    benches,
    bench_health_check,
    bench_${model_name_lower}_creation,
    bench_concurrent_requests
);
criterion_main!(benches);
```

## Production Deployment

### Docker Configuration

```dockerfile

# Dockerfile

FROM rust:1.75-slim as builder

WORKDIR /app

# Install system dependencies

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests

COPY Cargo.toml Cargo.lock ./

# Create dummy main.rs to build dependencies

RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies

RUN cargo build --release && rm -rf src/

# Copy source code

COPY src ./src
COPY migrations ./migrations

# Build application

RUN cargo build --release

# Runtime image

FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies

RUN apt-get update && apt-get install -y \
    libssl3 \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder

COPY --from=builder /app/target/release/${project_name} ./

# Copy migrations

COPY migrations ./migrations

# Create non-root user

RUN useradd -r -s /bin/false appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["./$(project_name)"]
```

```yaml

# docker-compose.yml

version: '3.8'

services:
  app:
    build: .
    ports:

      - "8000:8000"

    environment:

      - DATABASE_URL=postgresql://postgres:password@db:5432/${project_name}
      - REDIS_URL=redis://redis:6379
      - RUST_LOG=info,${project_name}=debug
      - JWT_SECRET=your-jwt-secret

    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:

      - ./config:/app/config:ro

  db:
    image: postgres:14
    environment:

      - POSTGRES_DB=${project_name}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

    volumes:

      - postgres_data:/var/lib/postgresql/data

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

### Production Optimizations

```bash

# Build optimizations in Cargo.toml

[profile.release]
lto = true              # Link-time optimization
codegen-units = 1       # Better optimization
panic = "abort"         # Reduce binary size
strip = true            # Remove debug info
opt-level = 3           # Maximum optimization

# Cross-compilation for different architectures

rustup target add x86_64-unknown-linux-musl
cargo build --target x86_64-unknown-linux-musl --release

# Static linking for minimal Docker images

RUSTFLAGS="-C target-feature=+crt-static" cargo build --release --target x86_64-unknown-linux-musl
```

### CI/CD Pipeline

```yaml

# .github/workflows/ci.yml

name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  CARGO_TERM_COLOR: always

jobs:
  test:
    name: Test
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
        ports:

          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:

          - 6379:6379

    steps:

    - uses: actions/checkout@v4

    - name: Install Rust

      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        components: rustfmt, clippy
        override: true

    - name: Cache dependencies

      uses: actions/cache@v3
      with:
        path: |
          ~/.cargo/registry
          ~/.cargo/git
          target
        key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

    - name: Install SQLx CLI

      run: cargo install sqlx-cli --no-default-features --features postgres

    - name: Run migrations

      run: |
        export DATABASE_URL=postgresql://postgres:postgres@localhost/test_db
        sqlx migrate run

    - name: Check formatting

      run: cargo fmt -- --check

    - name: Run clippy

      run: cargo clippy -- -D warnings

    - name: Run tests

      run: cargo test
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
        REDIS_URL: redis://localhost:6379

    - name: Run integration tests

      run: cargo test --test '*'
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
        REDIS_URL: redis://localhost:6379

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test

    steps:

    - uses: actions/checkout@v4

    - name: Install Rust

      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        target: x86_64-unknown-linux-musl
        override: true

    - name: Build binary

      run: |
        sudo apt-get update && sudo apt-get install -y musl-tools
        cargo build --release --target x86_64-unknown-linux-musl

    - name: Upload binary

      uses: actions/upload-artifact@v3
      with:
        name: ${project_name}-binary
        path: target/x86_64-unknown-linux-musl/release/${project_name}

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'

    steps:

    - uses: actions/checkout@v4

    - name: Download binary

      uses: actions/download-artifact@v3
      with:
        name: ${project_name}-binary

    - name: Build and push Docker image

      env:
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      run: |
        echo $DOCKER_PASSWORD | docker login $DOCKER_REGISTRY -u $DOCKER_USERNAME --password-stdin
        docker build -t $DOCKER_REGISTRY/${project_name}:${{ github.sha }} .
        docker push $DOCKER_REGISTRY/${project_name}:${{ github.sha }}
        docker tag $DOCKER_REGISTRY/${project_name}:${{ github.sha }} $DOCKER_REGISTRY/${project_name}:latest
        docker push $DOCKER_REGISTRY/${project_name}:latest
```

### Monitoring and Logging

```rust
// src/middleware/metrics.rs
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};
use std::time::Instant;

pub async fn metrics_middleware(request: Request, next: Next) -> Response {
    let start = Instant::now();
    let method = request.method().clone();
    let uri = request.uri().clone();

    let response = next.run(request).await;

    let latency = start.elapsed();
    let status = response.status();

    tracing::info!(
        method = %method,
        uri = %uri,
        status = %status,
        latency_ms = %latency.as_millis(),
        "Request completed"
    );

    response
}

// Enhanced error reporting
use sentry::{configure_scope, capture_error};

pub fn init_sentry() -> sentry::ClientInitGuard {
    let guard = sentry::init((
        std::env::var("SENTRY_DSN").unwrap_or_default(),
        sentry::ClientOptions {
            release: sentry::release_name!(),
            ..Default::default()
        },
    ));

    configure_scope(|scope| {
        scope.set_tag("service", "${project_name}");
    });

    guard
}
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
