# ${project_name} - Axum Development Instructions

## Project Context

${project_description}

**Framework**: Axum ${axum_version}
**Rust Version**: ${rust_version}
**Database**: ${database}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## Axum Development Standards

### Project Structure

```
${project_name}/
├── Cargo.toml                   # Project configuration
├── Cargo.lock                   # Dependency lock file
├── .env.example                 # Environment variables template
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose
├── src/
│   ├── main.rs                  # Application entry point
│   ├── lib.rs                   # Library root
│   ├── app.rs                   # Application setup
│   ├── config/
│   │   ├── mod.rs
│   │   ├── database.rs          # Database configuration
│   │   └── settings.rs          # Application settings
│   ├── handlers/
│   │   ├── mod.rs
│   │   ├── auth.rs              # Authentication handlers
│   │   ├── health.rs            # Health check handlers
│   │   └── ${resource}.rs       # Feature handlers
│   ├── models/
│   │   ├── mod.rs
│   │   ├── user.rs              # User model
│   │   └── ${model}.rs          # Feature models
│   ├── services/
│   │   ├── mod.rs
│   │   ├── auth.rs              # Authentication service
│   │   └── ${service}.rs        # Business logic services
│   ├── middleware/
│   │   ├── mod.rs
│   │   ├── auth.rs              # Authentication middleware
│   │   ├── cors.rs              # CORS middleware
│   │   └── logging.rs           # Request logging
│   ├── utils/
│   │   ├── mod.rs
│   │   ├── errors.rs            # Error handling
│   │   ├── response.rs          # Response utilities
│   │   └── validation.rs        # Input validation
│   └── routes/
│       ├── mod.rs
│       ├── api.rs               # API routes
│       ├── auth.rs              # Authentication routes
│       └── ${feature}.rs        # Feature routes
├── migrations/                  # Database migrations
│   └── 001_initial.sql
├── tests/
│   ├── integration/
│   │   ├── mod.rs
│   │   ├── auth_test.rs
│   │   └── ${feature}_test.rs
│   └── common/
│       ├── mod.rs
│       └── helpers.rs
└── README.md
```

### Cargo Configuration

```toml

# Cargo.toml

[package]
name = "${project_name}"
version = "0.1.0"
edition = "2021"
authors = ["${author_name} <${author_email}>"]
license = "${license}"
description = "${project_description}"
repository = "${repository_url}"

[dependencies]

# Core web framework

axum = { version = "${axum_version}", features = ["macros"] }
tokio = { version = "${tokio_version}", features = ["full"] }
tower = "${tower_version}"
tower-http = { version = "${tower_http_version}", features = ["cors", "trace", "compression", "fs"] }
hyper = { version = "${hyper_version}", features = ["full"] }

# Async runtime and utilities

tokio-util = "${tokio_util_version}"
futures = "${futures_version}"

# Serialization

serde = { version = "${serde_version}", features = ["derive"] }
serde_json = "${serde_json_version}"

# Database

sqlx = { version = "${sqlx_version}", features = ["runtime-tokio-rustls", "postgres", "chrono", "uuid", "migrate"] }

# Authentication & Security

jsonwebtoken = "${jwt_version}"
bcrypt = "${bcrypt_version}"
uuid = { version = "${uuid_version}", features = ["serde", "v4"] }

# Configuration

config = "${config_version}"
dotenvy = "${dotenvy_version}"

# Logging and tracing

tracing = "${tracing_version}"
tracing-subscriber = { version = "${tracing_subscriber_version}", features = ["env-filter"] }

# Error handling

anyhow = "${anyhow_version}"
thiserror = "${thiserror_version}"

# Validation

validator = { version = "${validator_version}", features = ["derive"] }

# HTTP client (for external APIs)

reqwest = { version = "${reqwest_version}", features = ["json", "rustls-tls"] }

# Time handling

chrono = { version = "${chrono_version}", features = ["serde"] }

# Redis for caching and sessions

redis = { version = "${redis_version}", features = ["tokio-comp"] }

[dev-dependencies]

# Testing

tokio-test = "${tokio_test_version}"
sqlx-test = "${sqlx_test_version}"
httpx = "${httpx_version}"
wiremock = "${wiremock_version}"
assert_matches = "${assert_matches_version}"

# Benchmarking

criterion = { version = "${criterion_version}", features = ["html_reports"] }

[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true

[profile.dev]
debug = true
opt-level = 0

[[bench]]
name = "api_benchmarks"
harness = false
```

### Application Setup

```rust
// src/main.rs
use anyhow::Result;
use ${project_name}::{app::create_app, config::Settings};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "${project_name}=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let settings = Settings::new()?;
    
    tracing::info!("Starting ${project_name} server");
    tracing::info!("Database URL: {}", settings.database.url);
    tracing::info!("Server will listen on {}:{}", settings.server.host, settings.server.port);

    // Create and run the application
    let app = create_app(&settings).await?;
    
    let listener = tokio::net::TcpListener::bind(
        format!("{}:{}", settings.server.host, settings.server.port)
    ).await?;
    
    tracing::info!("Server listening on {}", listener.local_addr()?);
    
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    tracing::info!("Signal received, starting graceful shutdown");
}

// src/app.rs
use axum::{
    http::{header, HeaderValue, Method},
    routing::{get, post},
    Router,
};
use sqlx::PgPool;
use std::sync::Arc;
use tower::ServiceBuilder;
use tower_http::{
    cors::CorsLayer,
    compression::CompressionLayer,
    trace::TraceLayer,
    timeout::TimeoutLayer,
};
use std::time::Duration;

use crate::{
    config::{database::create_pool, Settings},
    handlers::{health, auth, ${resource}},
    middleware::{auth::auth_layer, logging::logging_layer},
    routes,
};

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub settings: Arc<Settings>,
}

pub async fn create_app(settings: &Settings) -> anyhow::Result<Router> {
    // Create database connection pool
    let db_pool = create_pool(&settings.database).await?;
    
    // Run migrations
    sqlx::migrate!("./migrations").run(&db_pool).await?;

    // Create shared application state
    let state = AppState {
        db: db_pool,
        settings: Arc::new(settings.clone()),
    };

    // Create CORS layer
    let cors = CorsLayer::new()
        .allow_origin(settings.cors.allowed_origins.iter().map(|origin| {
            origin.parse::<HeaderValue>().unwrap()
        }).collect::<Vec<_>>())
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION])
        .allow_credentials(true);

    // Build the application with middleware
    let app = Router::new()
        .merge(routes::api::routes())
        .merge(routes::auth::routes())
        .merge(routes::${feature}::routes())
        .route("/health", get(health::health_check))
        .route("/health/ready", get(health::readiness_check))
        .with_state(state)
        .layer(
            ServiceBuilder::new()
                .layer(TraceLayer::new_for_http())
                .layer(logging_layer())
                .layer(CompressionLayer::new())
                .layer(TimeoutLayer::new(Duration::from_secs(30)))
                .layer(cors)
        );

    Ok(app)
}
```

### Configuration Management

```rust
// src/config/settings.rs
use config::{Config, ConfigError, Environment, File};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Settings {
    pub server: ServerSettings,
    pub database: DatabaseSettings,
    pub auth: AuthSettings,
    pub cors: CorsSettings,
    pub redis: RedisSettings,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ServerSettings {
    pub host: String,
    pub port: u16,
    pub workers: Option<usize>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DatabaseSettings {
    pub url: String,
    pub max_connections: u32,
    pub min_connections: u32,
    pub connect_timeout: u64,
    pub idle_timeout: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct AuthSettings {
    pub secret_key: String,
    pub token_expiry: u64,
    pub refresh_token_expiry: u64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CorsSettings {
    pub allowed_origins: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct RedisSettings {
    pub url: String,
    pub pool_size: u32,
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        let run_mode = env::var("RUN_MODE").unwrap_or_else(|_| "development".into());

        let s = Config::builder()
            // Start with default configuration file
            .add_source(File::with_name("config/default"))
            // Add environment-specific configuration
            .add_source(
                File::with_name(&format!("config/{}", run_mode))
                    .required(false)
            )
            // Add local configuration (optional)
            .add_source(File::with_name("config/local").required(false))
            // Override with environment variables
            .add_source(Environment::with_prefix("APP"))
            .build()?;

        s.try_deserialize()
    }
}

// src/config/database.rs
use sqlx::{postgres::PgPoolOptions, PgPool};
use std::time::Duration;
use crate::config::DatabaseSettings;

pub async fn create_pool(settings: &DatabaseSettings) -> anyhow::Result<PgPool> {
    let pool = PgPoolOptions::new()
        .max_connections(settings.max_connections)
        .min_connections(settings.min_connections)
        .acquire_timeout(Duration::from_secs(settings.connect_timeout))
        .idle_timeout(Duration::from_secs(settings.idle_timeout))
        .connect(&settings.url)
        .await?;

    Ok(pool)
}
```

### Models and Database

```rust
// src/models/user.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;
use validator::Validate;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub username: String,
    pub password_hash: String,
    pub first_name: Option<String>,
    pub last_name: Option<String>,
    pub is_active: bool,
    pub is_admin: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUserRequest {
    #[validate(email)]
    pub email: String,
    
    #[validate(length(min = 3, max = 50))]
    pub username: String,
    
    #[validate(length(min = 8))]
    pub password: String,
    
    #[validate(length(max = 100))]
    pub first_name: Option<String>,
    
    #[validate(length(max = 100))]
    pub last_name: Option<String>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct UpdateUserRequest {
    #[validate(email)]
    pub email: Option<String>,
    
    #[validate(length(min = 3, max = 50))]
    pub username: Option<String>,
    
    #[validate(length(max = 100))]
    pub first_name: Option<String>,
    
    #[validate(length(max = 100))]
    pub last_name: Option<String>,
    
    pub is_active: Option<bool>,
}

#[derive(Debug, Serialize)]
pub struct UserResponse {
    pub id: Uuid,
    pub email: String,
    pub username: String,
    pub first_name: Option<String>,
    pub last_name: Option<String>,
    pub is_active: bool,
    pub is_admin: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<User> for UserResponse {
    fn from(user: User) -> Self {
        Self {
            id: user.id,
            email: user.email,
            username: user.username,
            first_name: user.first_name,
            last_name: user.last_name,
            is_active: user.is_active,
            is_admin: user.is_admin,
            created_at: user.created_at,
            updated_at: user.updated_at,
        }
    }
}

// src/models/${model}.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;
use validator::Validate;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ${model_name} {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub content: Option<String>,
    pub status: ${model_name}Status,
    pub author_id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "${model_name_lower}_status", rename_all = "lowercase")]
pub enum ${model_name}Status {
    Draft,
    Published,
    Archived,
}

#[derive(Debug, Deserialize, Validate)]
pub struct Create${model_name}Request {
    #[validate(length(min = 1, max = 200))]
    pub title: String,
    
    #[validate(length(max = 500))]
    pub description: Option<String>,
    
    pub content: Option<String>,
    
    pub status: Option<${model_name}Status>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct Update${model_name}Request {
    #[validate(length(min = 1, max = 200))]
    pub title: Option<String>,
    
    #[validate(length(max = 500))]
    pub description: Option<String>,
    
    pub content: Option<String>,
    
    pub status: Option<${model_name}Status>,
}

#[derive(Debug, Serialize)]
pub struct ${model_name}Response {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub content: Option<String>,
    pub status: ${model_name}Status,
    pub author_id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<${model_name}> for ${model_name}Response {
    fn from(${model_name_lower}: ${model_name}) -> Self {
        Self {
            id: ${model_name_lower}.id,
            title: ${model_name_lower}.title,
            description: ${model_name_lower}.description,
            content: ${model_name_lower}.content,
            status: ${model_name_lower}.status,
            author_id: ${model_name_lower}.author_id,
            created_at: ${model_name_lower}.created_at,
            updated_at: ${model_name_lower}.updated_at,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct ${model_name}Query {
    pub page: Option<u32>,
    pub limit: Option<u32>,
    pub status: Option<${model_name}Status>,
    pub search: Option<String>,
}

impl Default for ${model_name}Query {
    fn default() -> Self {
        Self {
            page: Some(1),
            limit: Some(20),
            status: None,
            search: None,
        }
    }
}
```

### Services Layer

```rust
// src/services/${service}.rs
use anyhow::Result;
use sqlx::PgPool;
use uuid::Uuid;
use chrono::Utc;

use crate::models::{
    ${model}::{${model_name}, Create${model_name}Request, Update${model_name}Request, ${model_name}Query, ${model_name}Status},
    user::User,
};
use crate::utils::errors::{AppError, AppResult};

pub struct ${service_name}Service {
    db: PgPool,
}

impl ${service_name}Service {
    pub fn new(db: PgPool) -> Self {
        Self { db }
    }

    pub async fn create_${model_name_lower}(
        &self,
        user_id: Uuid,
        request: Create${model_name}Request,
    ) -> AppResult<${model_name}> {
        let ${model_name_lower}_id = Uuid::new_v4();
        let now = Utc::now();
        
        let ${model_name_lower} = sqlx::query_as!(
            ${model_name},
            r#"
            INSERT INTO ${model_name_lower}s (id, title, description, content, status, author_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, title, description, content, status as "status: ${model_name}Status", author_id, created_at, updated_at
            "#,
            ${model_name_lower}_id,
            request.title,
            request.description,
            request.content,
            request.status.unwrap_or(${model_name}Status::Draft) as ${model_name}Status,
            user_id,
            now,
            now
        )
        .fetch_one(&self.db)
        .await
        .map_err(|e| {
            tracing::error!("Failed to create ${model_name_lower}: {}", e);
            AppError::DatabaseError("Failed to create ${model_name_lower}".to_string())
        })?;

        Ok(${model_name_lower})
    }

    pub async fn get_${model_name_lower}_by_id(&self, id: Uuid) -> AppResult<Option<${model_name}>> {
        let ${model_name_lower} = sqlx::query_as!(
            ${model_name},
            r#"
            SELECT id, title, description, content, status as "status: ${model_name}Status", author_id, created_at, updated_at
            FROM ${model_name_lower}s
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.db)
        .await
        .map_err(|e| {
            tracing::error!("Failed to get ${model_name_lower}: {}", e);
            AppError::DatabaseError("Failed to get ${model_name_lower}".to_string())
        })?;

        Ok(${model_name_lower})
    }

    pub async fn get_${model_name_lower}s(
        &self,
        query: ${model_name}Query,
        user_id: Option<Uuid>,
    ) -> AppResult<Vec<${model_name}>> {
        let page = query.page.unwrap_or(1);
        let limit = query.limit.unwrap_or(20).min(100); // Max 100 items per page
        let offset = (page - 1) * limit;

        let mut sql_query = "SELECT id, title, description, content, status, author_id, created_at, updated_at FROM ${model_name_lower}s WHERE 1=1".to_string();
        let mut params: Vec<Box<dyn sqlx::Encode<'_, sqlx::Postgres> + Send + Sync>> = Vec::new();
        let mut param_count = 0;

        // Add status filter
        if let Some(status) = query.status {
            param_count += 1;
            sql_query.push_str(&format!(" AND status = ${}", param_count));
            params.push(Box::new(status));
        }

        // Add search filter
        if let Some(search) = &query.search {
            if !search.is_empty() {
                param_count += 1;
                sql_query.push_str(&format!(" AND (title ILIKE ${} OR description ILIKE ${})", param_count, param_count));
                params.push(Box::new(format!("%{}%", search)));
            }
        }

        // Add author filter for non-admin users
        if let Some(uid) = user_id {
            param_count += 1;
            sql_query.push_str(&format!(" AND author_id = ${}", param_count));
            params.push(Box::new(uid));
        }

        // Add ordering and pagination
        param_count += 1;
        sql_query.push_str(&format!(" ORDER BY created_at DESC LIMIT ${}", param_count));
        params.push(Box::new(limit as i64));

        param_count += 1;
        sql_query.push_str(&format!(" OFFSET ${}", param_count));
        params.push(Box::new(offset as i64));

        let ${model_name_lower}s = sqlx::query_as(&sql_query)
            .bind_all(params)
            .fetch_all(&self.db)
            .await
            .map_err(|e| {
                tracing::error!("Failed to get ${model_name_lower}s: {}", e);
                AppError::DatabaseError("Failed to get ${model_name_lower}s".to_string())
            })?;

        Ok(${model_name_lower}s)
    }

    pub async fn update_${model_name_lower}(
        &self,
        id: Uuid,
        user_id: Uuid,
        request: Update${model_name}Request,
    ) -> AppResult<${model_name}> {
        // First check if the ${model_name_lower} exists and user owns it
        let existing = self.get_${model_name_lower}_by_id(id).await?;
        let existing = existing.ok_or(AppError::NotFound("${model_name} not found".to_string()))?;

        if existing.author_id != user_id {
            return Err(AppError::Forbidden("You can only update your own ${model_name_lower}s".to_string()));
        }

        let now = Utc::now();

        let ${model_name_lower} = sqlx::query_as!(
            ${model_name},
            r#"
            UPDATE ${model_name_lower}s
            SET 
                title = COALESCE($1, title),
                description = COALESCE($2, description),
                content = COALESCE($3, content),
                status = COALESCE($4, status),
                updated_at = $5
            WHERE id = $6
            RETURNING id, title, description, content, status as "status: ${model_name}Status", author_id, created_at, updated_at
            "#,
            request.title,
            request.description,
            request.content,
            request.status as Option<${model_name}Status>,
            now,
            id
        )
        .fetch_one(&self.db)
        .await
        .map_err(|e| {
            tracing::error!("Failed to update ${model_name_lower}: {}", e);
            AppError::DatabaseError("Failed to update ${model_name_lower}".to_string())
        })?;

        Ok(${model_name_lower})
    }

    pub async fn delete_${model_name_lower}(&self, id: Uuid, user_id: Uuid) -> AppResult<()> {
        let result = sqlx::query!(
            "DELETE FROM ${model_name_lower}s WHERE id = $1 AND author_id = $2",
            id,
            user_id
        )
        .execute(&self.db)
        .await
        .map_err(|e| {
            tracing::error!("Failed to delete ${model_name_lower}: {}", e);
            AppError::DatabaseError("Failed to delete ${model_name_lower}".to_string())
        })?;

        if result.rows_affected() == 0 {
            return Err(AppError::NotFound("${model_name} not found or not owned by user".to_string()));
        }

        Ok(())
    }

    pub async fn get_${model_name_lower}s_count(
        &self,
        status: Option<${model_name}Status>,
        user_id: Option<Uuid>,
    ) -> AppResult<i64> {
        let count = match (status, user_id) {
            (Some(s), Some(uid)) => {
                sqlx::query_scalar!(
                    "SELECT COUNT(*) FROM ${model_name_lower}s WHERE status = $1 AND author_id = $2",
                    s as ${model_name}Status,
                    uid
                )
                .fetch_one(&self.db)
                .await
            },
            (Some(s), None) => {
                sqlx::query_scalar!(
                    "SELECT COUNT(*) FROM ${model_name_lower}s WHERE status = $1",
                    s as ${model_name}Status
                )
                .fetch_one(&self.db)
                .await
            },
            (None, Some(uid)) => {
                sqlx::query_scalar!(
                    "SELECT COUNT(*) FROM ${model_name_lower}s WHERE author_id = $1",
                    uid
                )
                .fetch_one(&self.db)
                .await
            },
            (None, None) => {
                sqlx::query_scalar!("SELECT COUNT(*) FROM ${model_name_lower}s")
                    .fetch_one(&self.db)
                    .await
            }
        };

        count
            .map(|c| c.unwrap_or(0))
            .map_err(|e| {
                tracing::error!("Failed to count ${model_name_lower}s: {}", e);
                AppError::DatabaseError("Failed to count ${model_name_lower}s".to_string())
            })
    }
}
```

### Handlers (Controllers)

```rust
// src/handlers/${resource}.rs
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::Json,
};
use uuid::Uuid;
use validator::Validate;

use crate::{
    app::AppState,
    models::{
        ${model}::{Create${model_name}Request, Update${model_name}Request, ${model_name}Query, ${model_name}Response},
        user::User,
    },
    services::${service}::${service_name}Service,
    utils::{
        errors::{AppError, AppResult},
        response::{ApiResponse, PaginatedResponse},
    },
    middleware::auth::Claims,
};

pub async fn create_${model_name_lower}(
    State(state): State<AppState>,
    claims: Claims,
    Json(request): Json<Create${model_name}Request>,
) -> AppResult<(StatusCode, Json<ApiResponse<${model_name}Response>>)> {
    // Validate request
    request.validate()
        .map_err(|e| AppError::ValidationError(e.to_string()))?;

    let service = ${service_name}Service::new(state.db.clone());
    let ${model_name_lower} = service.create_${model_name_lower}(claims.user_id, request).await?;

    Ok((
        StatusCode::CREATED,
        Json(ApiResponse::success(${model_name}Response::from(${model_name_lower}))),
    ))
}

pub async fn get_${model_name_lower}(
    State(state): State<AppState>,
    claims: Claims,
    Path(id): Path<Uuid>,
) -> AppResult<Json<ApiResponse<${model_name}Response>>> {
    let service = ${service_name}Service::new(state.db.clone());
    let ${model_name_lower} = service.get_${model_name_lower}_by_id(id).await?;

    match ${model_name_lower} {
        Some(${model_name_lower}) => {
            // Check if user can access this ${model_name_lower}
            if ${model_name_lower}.author_id != claims.user_id && !claims.is_admin {
                return Err(AppError::Forbidden("Access denied".to_string()));
            }
            Ok(Json(ApiResponse::success(${model_name}Response::from(${model_name_lower}))))
        },
        None => Err(AppError::NotFound("${model_name} not found".to_string())),
    }
}

pub async fn get_${model_name_lower}s(
    State(state): State<AppState>,
    claims: Claims,
    Query(query): Query<${model_name}Query>,
) -> AppResult<Json<ApiResponse<PaginatedResponse<${model_name}Response>>>> {
    let service = ${service_name}Service::new(state.db.clone());
    
    // Non-admin users can only see their own ${model_name_lower}s
    let user_filter = if claims.is_admin { None } else { Some(claims.user_id) };
    
    let ${model_name_lower}s = service.get_${model_name_lower}s(query.clone(), user_filter).await?;
    let total = service.get_${model_name_lower}s_count(query.status, user_filter).await?;

    let page = query.page.unwrap_or(1);
    let limit = query.limit.unwrap_or(20);
    let total_pages = (total as f64 / limit as f64).ceil() as u32;

    let response = PaginatedResponse {
        data: ${model_name_lower}s.into_iter().map(${model_name}Response::from).collect(),
        pagination: crate::utils::response::PaginationInfo {
            page,
            limit,
            total: total as u32,
            total_pages,
            has_next: page < total_pages,
            has_prev: page > 1,
        },
    };

    Ok(Json(ApiResponse::success(response)))
}

pub async fn update_${model_name_lower}(
    State(state): State<AppState>,
    claims: Claims,
    Path(id): Path<Uuid>,
    Json(request): Json<Update${model_name}Request>,
) -> AppResult<Json<ApiResponse<${model_name}Response>>> {
    // Validate request
    request.validate()
        .map_err(|e| AppError::ValidationError(e.to_string()))?;

    let service = ${service_name}Service::new(state.db.clone());
    let ${model_name_lower} = service.update_${model_name_lower}(id, claims.user_id, request).await?;

    Ok(Json(ApiResponse::success(${model_name}Response::from(${model_name_lower}))))
}

pub async fn delete_${model_name_lower}(
    State(state): State<AppState>,
    claims: Claims,
    Path(id): Path<Uuid>,
) -> AppResult<StatusCode> {
    let service = ${service_name}Service::new(state.db.clone());
    service.delete_${model_name_lower}(id, claims.user_id).await?;

    Ok(StatusCode::NO_CONTENT)
}
```

### Middleware

```rust
// src/middleware/auth.rs
use axum::{
    extract::{Request, State},
    http::{header::AUTHORIZATION, StatusCode},
    middleware::Next,
    response::Response,
};
use axum_extra::extract::FromRequestParts;
use jsonwebtoken::{decode, DecodingKey, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::{
    app::AppState,
    utils::errors::{AppError, AppResult},
};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub user_id: Uuid,
    pub email: String,
    pub is_admin: bool,
    pub exp: usize,
}

#[axum::async_trait]
impl<S> FromRequestParts<S> for Claims
where
    S: Send + Sync,
    AppState: axum::extract::FromRef<S>,
{
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut axum::http::request::Parts,
        state: &S,
    ) -> Result<Self, Self::Rejection> {
        let app_state = AppState::from_ref(state);
        
        let authorization = parts
            .headers
            .get(AUTHORIZATION)
            .and_then(|value| value.to_str().ok())
            .ok_or(AppError::Unauthorized("Missing authorization header".to_string()))?;

        let token = authorization
            .strip_prefix("Bearer ")
            .ok_or(AppError::Unauthorized("Invalid authorization format".to_string()))?;

        let claims = decode::<Claims>(
            token,
            &DecodingKey::from_secret(app_state.settings.auth.secret_key.as_bytes()),
            &Validation::default(),
        )
        .map_err(|_| AppError::Unauthorized("Invalid token".to_string()))?;

        Ok(claims.claims)
    }
}

pub fn auth_layer() -> axum::middleware::FromFnLayer<
    fn(Request, Next) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<Response, StatusCode>> + Send>>,
    (),
> {
    axum::middleware::from_fn(auth_middleware)
}

async fn auth_middleware(
    request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Extract the authorization header
    let auth_header = request
        .headers()
        .get(AUTHORIZATION)
        .and_then(|header| header.to_str().ok());

    if auth_header.is_none() {
        return Err(StatusCode::UNAUTHORIZED);
    }

    // Continue with the request
    Ok(next.run(request).await)
}
```

### Error Handling

```rust
// src/utils/errors.rs
use axum::{
    http::StatusCode,
    response::{IntoResponse, Json, Response},
};
use serde_json::json;
use thiserror::Error;

pub type AppResult<T> = Result<T, AppError>;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Database error: {0}")]
    DatabaseError(String),
    
    #[error("Validation error: {0}")]
    ValidationError(String),
    
    #[error("Authentication error: {0}")]
    Unauthorized(String),
    
    #[error("Authorization error: {0}")]
    Forbidden(String),
    
    #[error("Not found: {0}")]
    NotFound(String),
    
    #[error("Conflict: {0}")]
    Conflict(String),
    
    #[error("Internal server error: {0}")]
    InternalServerError(String),
    
    #[error("Bad request: {0}")]
    BadRequest(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_message) = match self {
            AppError::DatabaseError(msg) => {
                tracing::error!("Database error: {}", msg);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            },
            AppError::ValidationError(msg) => (StatusCode::BAD_REQUEST, &msg),
            AppError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, &msg),
            AppError::Forbidden(msg) => (StatusCode::FORBIDDEN, &msg),
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, &msg),
            AppError::Conflict(msg) => (StatusCode::CONFLICT, &msg),
            AppError::InternalServerError(msg) => {
                tracing::error!("Internal server error: {}", msg);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            },
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, &msg),
        };

        let body = Json(json!({
            "error": true,
            "message": error_message,
        }));

        (status, body).into_response()
    }
}

// src/utils/response.rs
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub message: Option<String>,
}

impl<T> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            message: None,
        }
    }

    pub fn error(message: String) -> Self {
        Self {
            success: false,
            data: None,
            message: Some(message),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaginatedResponse<T> {
    pub data: Vec<T>,
    pub pagination: PaginationInfo,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaginationInfo {
    pub page: u32,
    pub limit: u32,
    pub total: u32,
    pub total_pages: u32,
    pub has_next: bool,
    pub has_prev: bool,
}
```

---

*Generated by Claude Builder v${version} on ${timestamp}*