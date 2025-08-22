# ${project_name} - FastAPI Development Instructions

## Project Context

${project_description}

**Framework**: FastAPI ${fastapi_version}
**Python Version**: ${python_version}
**Database**: ${database}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## FastAPI Development Standards

### Project Structure

```
${project_name}/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependencies
│   │   ├── errors.py            # Error handlers
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py           # API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py      # Authentication endpoints
│   │           └── ${resource}.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application configuration
│   │   ├── security.py         # Security utilities
│   │   └── database.py         # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base SQLAlchemy models
│   │   ├── user.py             # User model
│   │   └── ${model}.py         # Feature models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   └── ${schema}.py        # Feature schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication service
│   │   └── ${service}.py       # Business logic services
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── email.py            # Email utilities
│   │   └── validators.py       # Custom validators
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py         # Pytest configuration
│       ├── test_auth.py        # Authentication tests
│       └── test_${feature}.py  # Feature tests
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example               # Environment variables template
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose
└── alembic.ini               # Alembic configuration
```

### Application Configuration

```python

# app/core/config.py

from typing import Optional, List, Union
from pydantic import BaseSettings, AnyHttpUrl, EmailStr, validator

class Settings(BaseSettings):
    """Application settings."""

    # API Configuration

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "${project_name}"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "${project_description}"

    # Security

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # CORS

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database

    DATABASE_URL: str
    ASYNC_DATABASE_URL: Optional[str] = None

    @validator("ASYNC_DATABASE_URL", pre=True)
    def assemble_async_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return values.get("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")

    # Redis

    REDIS_URL: str = "redis://localhost:6379/0"

    # Email

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Superuser

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # Testing

    TEST_DATABASE_URL: Optional[str] = None

    # Environment

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Logging

    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
```

### Database Models with SQLAlchemy

```python

# app/models/base.py

from typing import Any
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.sql import func

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# app/models/${model}.py

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
import uuid

from .base import Base, TimestampMixin

class ${model_name}Status(PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ${model_name}(Base, TimestampMixin):
    """${model_name} model."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    content = Column(Text)
    status = Column(Enum(${model_name}Status), default=${model_name}Status.DRAFT, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships

    author_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    author = relationship("User", back_populates="${model_name_lower}s")

    def __repr__(self):
        return f"<${model_name}(id={self.id}, title='{self.title}')>"

# app/models/user.py

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """User model."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships

    ${model_name_lower}s = relationship("${model_name}", back_populates="author")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
```

### Pydantic Schemas

```python

# app/schemas/${schema}.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models.${model} import ${model_name}Status

class ${model_name}Base(BaseModel):
    """Base ${model_name} schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    status: ${model_name}Status = ${model_name}Status.DRAFT
    is_featured: bool = False

class ${model_name}Create(${model_name}Base):
    """Schema for creating ${model_name}."""
    pass

class ${model_name}Update(BaseModel):
    """Schema for updating ${model_name}."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[${model_name}Status] = None
    is_featured: Optional[bool] = None

class ${model_name}InDBBase(${model_name}Base):
    """Base ${model_name} schema with database fields."""
    id: UUID
    slug: str
    author_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ${model_name}(${model_name}InDBBase):
    """${model_name} schema for API responses."""
    pass

class ${model_name}InDB(${model_name}InDBBase):
    """${model_name} schema for database operations."""
    pass

# User schemas

class UserBase(BaseModel):
    """Base user schema."""
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """Schema for creating user."""
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user."""
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class UserInDBBase(UserBase):
    """Base user schema with database fields."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    """User schema for API responses."""
    pass

class UserInDB(UserInDBBase):
    """User schema for database operations."""
    hashed_password: str

# Authentication schemas

class Token(BaseModel):
    """Token schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: Optional[str] = None
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str
```

### API Endpoints

```python

# app/api/v1/endpoints/${resource}.py

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.${model} import ${model_name}
from app.schemas.${schema} import (
    ${model_name},
    ${model_name}Create,
    ${model_name}Update,
    ${model_name}InDB
)
from app.services.${service} import ${service_name}Service

router = APIRouter()

@router.get("/", response_model=List[${model_name}])
async def read_${model_name_lower}s(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[${model_name}]:
    """
    Retrieve ${model_name_lower}s.
    """
    service = ${service_name}Service(db)
    filters = {}
    if status:
        filters['status'] = status
    if is_featured is not None:
        filters['is_featured'] = is_featured

    ${model_name_lower}s = service.get_multi(
        skip=skip,
        limit=limit,
        filters=filters
    )
    return ${model_name_lower}s

@router.post("/", response_model=${model_name}, status_code=status.HTTP_201_CREATED)
async def create_${model_name_lower}(
    *,
    db: Session = Depends(deps.get_db),
    ${model_name_lower}_in: ${model_name}Create,
    current_user: User = Depends(deps.get_current_active_user)
) -> ${model_name}:
    """
    Create new ${model_name_lower}.
    """
    service = ${service_name}Service(db)
    ${model_name_lower} = service.create_with_owner(
        obj_in=${model_name_lower}_in,
        owner_id=current_user.id
    )
    return ${model_name_lower}

@router.get("/{id}", response_model=${model_name})
async def read_${model_name_lower}(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> ${model_name}:
    """
    Get ${model_name_lower} by ID.
    """
    service = ${service_name}Service(db)
    ${model_name_lower} = service.get(id)
    if not ${model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="${model_name} not found"
        )

    # Check permissions

    if not current_user.is_superuser and ${model_name_lower}.author_id != current_user.id:

        # Only show published items to non-owners

        if ${model_name_lower}.status != "${model_name}Status.PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

    return ${model_name_lower}

@router.put("/{id}", response_model=${model_name})
async def update_${model_name_lower}(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    ${model_name_lower}_in: ${model_name}Update,
    current_user: User = Depends(deps.get_current_active_user)
) -> ${model_name}:
    """
    Update ${model_name_lower}.
    """
    service = ${service_name}Service(db)
    ${model_name_lower} = service.get(id)
    if not ${model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="${model_name} not found"
        )

    # Check permissions

    if not current_user.is_superuser and ${model_name_lower}.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    ${model_name_lower} = service.update(
        db_obj=${model_name_lower},
        obj_in=${model_name_lower}_in
    )
    return ${model_name_lower}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_${model_name_lower}(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> None:
    """
    Delete ${model_name_lower}.
    """
    service = ${service_name}Service(db)
    ${model_name_lower} = service.get(id)
    if not ${model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="${model_name} not found"
        )

    # Check permissions

    if not current_user.is_superuser and ${model_name_lower}.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    service.remove(id)

@router.get("/featured/", response_model=List[${model_name}])
async def read_featured_${model_name_lower}s(
    db: Session = Depends(deps.get_db),
    limit: int = Query(10, ge=1, le=50)
) -> List[${model_name}]:
    """
    Get featured ${model_name_lower}s.
    """
    service = ${service_name}Service(db)
    ${model_name_lower}s = service.get_featured(limit=limit)
    return ${model_name_lower}s

@router.post("/{id}/toggle-featured", response_model=${model_name})
async def toggle_featured_${model_name_lower}(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> ${model_name}:
    """
    Toggle featured status (admin only).
    """
    service = ${service_name}Service(db)
    ${model_name_lower} = service.get(id)
    if not ${model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="${model_name} not found"
        )

    ${model_name_lower} = service.toggle_featured(${model_name_lower})
    return ${model_name_lower}
```

### Service Layer

```python

# app/services/${service}.py

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.${model} import ${model_name}, ${model_name}Status
from app.schemas.${schema} import ${model_name}Create, ${model_name}Update
from .base import CRUDBase
from ..utils.text import slugify

class ${service_name}Service(CRUDBase[${model_name}, ${model_name}Create, ${model_name}Update]):
    """Service for ${model_name} operations."""

    def __init__(self, db: Session):
        super().__init__(${model_name}, db)

    def create_with_owner(
        self,
        *,
        obj_in: ${model_name}Create,
        owner_id: UUID
    ) -> ${model_name}:
        """Create ${model_name_lower} with owner."""
        obj_in_data = obj_in.dict()
        obj_in_data["author_id"] = owner_id
        obj_in_data["slug"] = self._generate_unique_slug(obj_in.title)

        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self,
        *,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[${model_name}]:
        """Get multiple ${model_name_lower}s by owner."""
        return (
            self.db.query(self.model)
            .filter(${model_name}.author_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_published(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[${model_name}]:
        """Get published ${model_name_lower}s."""
        return (
            self.db.query(self.model)
            .filter(${model_name}.status == ${model_name}Status.PUBLISHED)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_featured(
        self,
        *,
        limit: int = 10
    ) -> List[${model_name}]:
        """Get featured ${model_name_lower}s."""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    ${model_name}.is_featured == True,
                    ${model_name}.status == ${model_name}Status.PUBLISHED
                )
            )
            .limit(limit)
            .all()
        )

    def search(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[${model_name}]:
        """Search ${model_name_lower}s by title and content."""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    ${model_name}.status == ${model_name}Status.PUBLISHED,
                    ${model_name}.title.contains(query) |
                    ${model_name}.content.contains(query)
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def toggle_featured(self, db_obj: ${model_name}) -> ${model_name}:
        """Toggle featured status."""
        db_obj.is_featured = not db_obj.is_featured
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def publish(self, db_obj: ${model_name}) -> ${model_name}:
        """Publish ${model_name_lower}."""
        if db_obj.status != ${model_name}Status.PUBLISHED:
            db_obj.status = ${model_name}Status.PUBLISHED
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def archive(self, db_obj: ${model_name}) -> ${model_name}:
        """Archive ${model_name_lower}."""
        db_obj.status = ${model_name}Status.ARCHIVED
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[${model_name}]:
        """Get multiple ${model_name_lower}s with filters."""
        query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.offset(skip).limit(limit).all()

    def _generate_unique_slug(self, title: str) -> str:
        """Generate unique slug for ${model_name_lower}."""
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while self.db.query(self.model).filter(${model_name}.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

# Base CRUD service

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound=Any)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, *, id: Any) -> ModelType:
        obj = self.db.query(self.model).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
```

### Authentication and Security

```python

# app/core/security.py

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Get password hash."""
    return pwd_context.hash(password)

def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None

# app/api/deps.py

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.user import TokenPayload
from app.services.user import UserService

security_scheme = HTTPBearer()

def get_db() -> Generator:
    """Get database session."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(security_scheme)
) -> User:
    """Get current user from token."""
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user_service = UserService(db)
    user = user_service.get(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user doesn't have enough privileges"
        )
    return current_user
```

### Main Application Setup

```python

# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set CORS

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Include API router

app.include_router(api_router, prefix=settings.API_V1_STR)

# Exception handlers

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
