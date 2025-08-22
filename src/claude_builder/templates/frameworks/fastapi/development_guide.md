# ${project_name} - FastAPI Development Guide

## Environment Setup

### Python and FastAPI Installation

```bash

# Create and activate virtual environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install FastAPI and dependencies

pip install fastapi[all]==${fastapi_version}
pip install -r requirements-dev.txt

# Verify installation

python -c "import fastapi; print(fastapi.__version__)"
```

### Dependencies Configuration

```txt

# requirements.txt (Production)

fastapi[all]==${fastapi_version}
uvicorn[standard]==0.20.0
sqlalchemy==1.4.46
alembic==1.9.2
psycopg2-binary==2.9.5
redis==4.5.1
celery==5.2.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.5
emails==0.6
jinja2==3.1.2
aiofiles==22.1.0
python-decouple==3.6

# requirements-dev.txt (Development)

-r requirements.txt
pytest==7.2.0
pytest-asyncio==0.20.3
pytest-cov==4.0.0
httpx==0.23.3
factory-boy==3.2.1
black==22.12.0
isort==5.11.4
flake8==6.0.0
mypy==0.991
pre-commit==3.0.3
```

### Project Initialization

```bash

# Create project structure

mkdir -p app/{api/{v1/{endpoints}},core,models,schemas,services,utils,tests}
mkdir -p alembic/versions
touch app/__init__.py app/main.py
touch app/api/__init__.py app/api/v1/__init__.py
touch app/core/{__init__.py,config.py,database.py,security.py}
touch app/models/{__init__.py,base.py,user.py}
touch app/schemas/{__init__.py,user.py}
touch app/services/{__init__.py,base.py,user.py}
touch app/utils/{__init__.py,email.py}
touch app/tests/{__init__.py,conftest.py}

# Create configuration files

touch .env.example alembic.ini
```

### Environment Configuration

```bash

# .env.example
# Application

PROJECT_NAME="${project_name}"
VERSION="1.0.0"
DESCRIPTION="${project_description}"
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=11520

# Database

DATABASE_URL=postgresql://user:password@localhost:5432/${project_name}
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/${project_name}

# Redis

REDIS_URL=redis://localhost:6379/0

# CORS

BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Email

SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@${project_name}.com
EMAILS_FROM_NAME=${project_name}

# Superuser

FIRST_SUPERUSER=admin@${project_name}.com
FIRST_SUPERUSER_PASSWORD=changethis

# Testing

TEST_DATABASE_URL=postgresql://user:password@localhost:5432/${project_name}_test
```

## Database Setup with SQLAlchemy and Alembic

### Database Configuration

```python

# app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings

# Sync database engine

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Async database engine (optional)

if settings.ASYNC_DATABASE_URL:
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
    )

Base = declarative_base()
```

### Alembic Configuration

```ini

# alembic.ini

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:password@localhost:5432/${project_name}

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

```python

# alembic/env.py

import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context

# Import your models here

from app.models.base import Base
from app.models.user import User  # Import all models
from app.models.${model} import ${model_name}  # Import all models
from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Database Migration Commands

```bash

# Initialize Alembic (first time only)

alembic init alembic

# Create migration

alembic revision --autogenerate -m "Initial migration"

# Run migrations

alembic upgrade head

# Downgrade migrations

alembic downgrade -1

# Show current migration status

alembic current

# Show migration history

alembic history

# Create empty migration for data changes

alembic revision -m "Add initial data"
```

## Development Server and Debugging

### Running the Development Server

```bash

# Run with uvicorn directly

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with detailed logging

uvicorn app.main:app --reload --log-level debug --access-log

# Run with environment variables

uvicorn app.main:app --reload --env-file .env

# Run with multiple workers (production)

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Development Scripts

```python

# scripts/start_dev.py

import os
import uvicorn

if __name__ == "__main__":
    os.environ.setdefault("ENVIRONMENT", "development")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True,
    )

# scripts/create_superuser.py

import asyncio
from app.core.database import SessionLocal
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.core.config import settings

async def create_superuser():
    """Create initial superuser."""
    db = SessionLocal()
    try:
        user_service = UserService(db)

        # Check if superuser exists

        superuser = user_service.get_by_email(settings.FIRST_SUPERUSER)
        if not superuser:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                username="admin",
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
            )
            superuser = user_service.create(obj_in=user_in)
            print(f"Superuser created: {superuser.email}")
        else:
            print(f"Superuser already exists: {superuser.email}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_superuser())
```

## Testing Framework

### pytest Configuration

```python

# app/tests/conftest.py

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.main import app
from app.core.database import Base
from app.api import deps
from app.core.config import settings
from app.models.user import User
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.core.security import create_access_token

# Test database

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[deps.get_db] = override_get_db

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client() -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
async def async_client() -> AsyncClient:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_user(db_session) -> User:
    """Create test user."""
    user_service = UserService(db_session)
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        first_name="Test",
        last_name="User",
    )
    return user_service.create(obj_in=user_in)

@pytest.fixture
def superuser(db_session) -> User:
    """Create test superuser."""
    user_service = UserService(db_session)
    user_in = UserCreate(
        email="admin@example.com",
        username="admin",
        password="adminpassword123",
        is_superuser=True,
    )
    return user_service.create(obj_in=user_in)

@pytest.fixture
def user_token_headers(test_user: User) -> Dict[str, str]:
    """Get token headers for test user."""
    access_token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def superuser_token_headers(superuser: User) -> Dict[str, str]:
    """Get token headers for superuser."""
    access_token = create_access_token(superuser.id)
    return {"Authorization": f"Bearer {access_token}"}

# Event loop for async tests

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### API Testing Examples

```python

# app/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

def test_login_access_token(client: TestClient, test_user):
    """Test login endpoint."""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }

    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient):
    """Test login with invalid credentials."""
    login_data = {
        "username": "invalid@example.com",
        "password": "invalidpassword"
    }

    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )

    assert response.status_code == 400
    assert "detail" in response.json()

def test_get_current_user(client: TestClient, test_user, user_token_headers):
    """Test get current user endpoint."""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=user_token_headers
    )

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user.email
    assert user_data["username"] == test_user.username

def test_create_user_existing_email(client: TestClient, test_user):
    """Test creating user with existing email."""
    user_data = {
        "email": test_user.email,
        "username": "newusername",
        "password": "newpassword123"
    }

    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json=user_data
    )

    assert response.status_code == 400

# app/tests/test_${feature}.py

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.core.config import settings
from app.models.${model} import ${model_name}
from app.services.${service} import ${service_name}Service

class Test${model_name}API:
    """Test ${model_name} API endpoints."""

    def test_create_${model_name_lower}(
        self,
        client: TestClient,
        db_session,
        user_token_headers
    ):
        """Test creating ${model_name_lower}."""
        ${model_name_lower}_data = {
            "title": "Test ${model_name}",
            "description": "Test description",
            "content": "Test content"
        }

        response = client.post(
            f"{settings.API_V1_STR}/${model_name_lower}s/",
            headers=user_token_headers,
            json=${model_name_lower}_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == ${model_name_lower}_data["title"]
        assert data["description"] == ${model_name_lower}_data["description"]
        assert "id" in data
        assert "slug" in data

    def test_read_${model_name_lower}s(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_token_headers
    ):
        """Test reading ${model_name_lower}s."""

        # Create test ${model_name_lower}

        service = ${service_name}Service(db_session)
        from app.schemas.${schema} import ${model_name}Create

        ${model_name_lower}_in = ${model_name}Create(
            title="Test ${model_name}",
            description="Test description"
        )
        service.create_with_owner(obj_in=${model_name_lower}_in, owner_id=test_user.id)

        response = client.get(
            f"{settings.API_V1_STR}/${model_name_lower}s/",
            headers=user_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_read_${model_name_lower}(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_token_headers
    ):
        """Test reading single ${model_name_lower}."""

        # Create test ${model_name_lower}

        service = ${service_name}Service(db_session)
        from app.schemas.${schema} import ${model_name}Create

        ${model_name_lower}_in = ${model_name}Create(
            title="Test ${model_name}",
            description="Test description"
        )
        ${model_name_lower} = service.create_with_owner(
            obj_in=${model_name_lower}_in,
            owner_id=test_user.id
        )

        response = client.get(
            f"{settings.API_V1_STR}/${model_name_lower}s/{${model_name_lower}.id}",
            headers=user_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(${model_name_lower}.id)
        assert data["title"] == ${model_name_lower}.title

    def test_update_${model_name_lower}(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_token_headers
    ):
        """Test updating ${model_name_lower}."""

        # Create test ${model_name_lower}

        service = ${service_name}Service(db_session)
        from app.schemas.${schema} import ${model_name}Create

        ${model_name_lower}_in = ${model_name}Create(
            title="Original Title",
            description="Original description"
        )
        ${model_name_lower} = service.create_with_owner(
            obj_in=${model_name_lower}_in,
            owner_id=test_user.id
        )

        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }

        response = client.put(
            f"{settings.API_V1_STR}/${model_name_lower}s/{${model_name_lower}.id}",
            headers=user_token_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    def test_delete_${model_name_lower}(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_token_headers
    ):
        """Test deleting ${model_name_lower}."""

        # Create test ${model_name_lower}

        service = ${service_name}Service(db_session)
        from app.schemas.${schema} import ${model_name}Create

        ${model_name_lower}_in = ${model_name}Create(
            title="To Delete",
            description="Will be deleted"
        )
        ${model_name_lower} = service.create_with_owner(
            obj_in=${model_name_lower}_in,
            owner_id=test_user.id
        )

        response = client.delete(
            f"{settings.API_V1_STR}/${model_name_lower}s/{${model_name_lower}.id}",
            headers=user_token_headers
        )

        assert response.status_code == 204

        # Verify deletion

        ${model_name_lower}_deleted = service.get(${model_name_lower}.id)
        assert ${model_name_lower}_deleted is None

    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to protected endpoints."""
        response = client.get(f"{settings.API_V1_STR}/${model_name_lower}s/")
        assert response.status_code == 403

    def test_access_others_${model_name_lower}(
        self,
        client: TestClient,
        db_session,
        test_user,
        user_token_headers
    ):
        """Test accessing other user's ${model_name_lower}."""

        # Create another user and ${model_name_lower}

        from app.services.user import UserService
        from app.schemas.user import UserCreate

        user_service = UserService(db_session)
        other_user_in = UserCreate(
            email="other@example.com",
            username="otheruser",
            password="otherpass123"
        )
        other_user = user_service.create(obj_in=other_user_in)

        service = ${service_name}Service(db_session)
        from app.schemas.${schema} import ${model_name}Create

        ${model_name_lower}_in = ${model_name}Create(
            title="Other User ${model_name}",
            description="Belongs to other user"
        )
        other_${model_name_lower} = service.create_with_owner(
            obj_in=${model_name_lower}_in,
            owner_id=other_user.id
        )

        # Try to update other user's ${model_name_lower}

        response = client.put(
            f"{settings.API_V1_STR}/${model_name_lower}s/{other_${model_name_lower}.id}",
            headers=user_token_headers,
            json={"title": "Hacked Title"}
        )

        assert response.status_code == 403

@pytest.mark.asyncio
class TestAsync${model_name}API:
    """Test ${model_name} API with async client."""

    async def test_async_create_${model_name_lower}(
        self,
        async_client,
        db_session,
        user_token_headers
    ):
        """Test creating ${model_name_lower} with async client."""
        ${model_name_lower}_data = {
            "title": "Async Test ${model_name}",
            "description": "Async test description"
        }

        response = await async_client.post(
            f"{settings.API_V1_STR}/${model_name_lower}s/",
            headers=user_token_headers,
            json=${model_name_lower}_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == ${model_name_lower}_data["title"]
```

### Performance and Load Testing

```python

# app/tests/test_performance.py

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

@pytest.mark.performance
class TestPerformance:
    """Performance tests for API endpoints."""

    def test_concurrent_requests(
        self,
        client: TestClient,
        user_token_headers
    ):
        """Test concurrent API requests."""
        def make_request():
            response = client.get(
                f"{settings.API_V1_STR}/${model_name_lower}s/",
                headers=user_token_headers
            )
            return response.status_code

        # Execute 10 concurrent requests

        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
            end_time = time.time()

        # All requests should succeed

        assert all(status == 200 for status in results)

        # Should complete within reasonable time

        assert end_time - start_time < 5.0

    def test_response_time(self, client: TestClient, user_token_headers):
        """Test API response time."""
        start_time = time.time()
        response = client.get(
            f"{settings.API_V1_STR}/${model_name_lower}s/",
            headers=user_token_headers
        )
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Should respond within 1 second

    @pytest.mark.asyncio
    async def test_async_performance(
        self,
        async_client,
        user_token_headers
    ):
        """Test async endpoint performance."""
        async def make_async_request():
            response = await async_client.get(
                f"{settings.API_V1_STR}/${model_name_lower}s/",
                headers=user_token_headers
            )
            return response.status_code

        start_time = time.time()
        tasks = [make_async_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        assert all(status == 200 for status in results)
        assert end_time - start_time < 3.0
```

## Production Deployment

### Docker Configuration

```dockerfile

# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code

COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# Create non-root user

RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port

EXPOSE 8000

# Run the application

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml

# docker-compose.yml

version: '3.8'

services:
  web:
    build: .
    ports:

      - "8000:8000"

    environment:

      - DATABASE_URL=postgresql://postgres:password@db:5432/${project_name}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key
      - FIRST_SUPERUSER=admin@${project_name}.com
      - FIRST_SUPERUSER_PASSWORD=changethis

    depends_on:

      - db
      - redis

    volumes:

      - ./app:/app/app

    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:14
    environment:

      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=${project_name}

    volumes:

      - postgres_data:/var/lib/postgresql/data

    ports:

      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:

      - "6379:6379"

  celery:
    build: .
    command: celery -A app.core.celery worker --loglevel=info
    environment:

      - DATABASE_URL=postgresql://postgres:password@db:5432/${project_name}
      - REDIS_URL=redis://redis:6379/0

    depends_on:

      - db
      - redis

volumes:
  postgres_data:
```

### Production Configuration

```python

# app/core/config.py - Production settings

class ProductionSettings(Settings):
    """Production-specific settings."""

    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Security

    SECURE_COOKIES: bool = True
    COOKIE_DOMAIN: str = ".${project_name}.com"

    # Database

    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    ASYNC_DATABASE_URL: Optional[str] = Field(None, env="ASYNC_DATABASE_URL")

    # Logging

    LOG_LEVEL: str = "INFO"

    # CORS - restrict in production

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "https://${project_name}.com",
        "https://www.${project_name}.com"
    ]

    class Config:
        env_file = ".env.production"

# Use production settings based on environment

if settings.ENVIRONMENT == "production":
    settings = ProductionSettings()
```

### Health Checks and Monitoring

```python

# app/api/v1/endpoints/health.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
import psutil

from app.api import deps
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(deps.get_db)):
    """Detailed health check including dependencies."""
    health_status = {"status": "healthy", "checks": {}}

    # Database check

    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Redis check

    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # System resources

    health_status["checks"]["memory"] = f"{psutil.virtual_memory().percent}%"
    health_status["checks"]["cpu"] = f"{psutil.cpu_percent()}%"
    health_status["checks"]["disk"] = f"{psutil.disk_usage('/').percent}%"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
