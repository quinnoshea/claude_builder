# ${project_name} - Django Development Guide

## Environment Setup

### Python and Django Installation

```bash

# Create and activate virtual environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django and dependencies

pip install django==${django_version}
pip install -r requirements-dev.txt

# Verify installation

python -m django --version
```

### Project Creation and Setup

```bash

# Create Django project

django-admin startproject ${project_name}
cd ${project_name}

# Create Django apps

python manage.py startapp users
python manage.py startapp ${app_name}

# Create directory structure

mkdir -p apps/{users,${app_name}}
mkdir -p ${project_name}/settings
mkdir -p static/{css,js,images}
mkdir -p media
mkdir -p templates/${app_name}
mkdir -p locale
mkdir -p logs
mkdir -p scripts
mkdir -p tests
```

### Dependencies Configuration

```txt

# requirements.txt (Production)

Django==${django_version}
psycopg2-binary==2.9.5
django-environ==0.9.0
djangorestframework==3.14.0
django-cors-headers==3.13.0
django-filter==22.1
django-redis==5.2.0
celery[redis]==5.2.3
gunicorn==20.1.0
whitenoise==6.2.0
Pillow==9.3.0

# requirements-dev.txt (Development)

-r requirements.txt
django-extensions==3.2.1
django-debug-toolbar==3.2.4
factory-boy==3.2.1
pytest==7.2.0
pytest-django==4.5.2
pytest-cov==4.0.0
black==22.10.0
flake8==6.0.0
mypy==0.991
pre-commit==2.20.0
```

### Settings Configuration

```python

# ${project_name}/settings/__init__.py

import os

# Determine which settings to use

env = os.environ.get('DJANGO_SETTINGS_MODULE')
if not env:
    try:
        from .local import *  # noqa
    except ImportError:
        from .development import *  # noqa

# ${project_name}/settings/base.py

"""Base settings for ${project_name} project."""
import os
from pathlib import Path
import environ

# Build paths

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / 'apps'

# Environment variables

env = environ.Env()

# Core Django settings

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_extensions',
    'django_filters',
]

LOCAL_APPS = [
    'apps.users.apps.UsersConfig',
    'apps.${app_name}.apps.${app_name_title}Config',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '${project_name}.urls'

# Template configuration

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database configuration

DATABASES = {
    'default': env.db(),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

# Custom user model

AUTH_USER_MODEL = 'users.User'

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
SITE_ID = 1

# Static files configuration

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files configuration

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# Logging configuration

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '{levelname} {asctime} {module} {process:d} {thread:d} {message}'
            ),
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        '${project_name}': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Security settings

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings

CORS_ALLOW_CREDENTIALS = True

# Cache configuration

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery configuration

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
```

## Database Management

### Migration Best Practices

```bash

# Create and run migrations

python manage.py makemigrations
python manage.py migrate

# Create migration for specific app

python manage.py makemigrations ${app_name}

# Show migration status

python manage.py showmigrations

# Create empty migration for data migration

python manage.py makemigrations --empty ${app_name}

# Reverse migrations

python manage.py migrate ${app_name} 0001

# Generate SQL for migration

python manage.py sqlmigrate ${app_name} 0001
```

### Custom Data Migration Example

```python

# apps/${app_name}/migrations/0002_populate_initial_data.py

from django.db import migrations

def populate_initial_data(apps, schema_editor):
    """Populate initial data for ${app_name}."""
    Tag = apps.get_model('${app_name}', 'Tag')
    
    initial_tags = [
        {'name': 'Technology', 'color': '#007bff'},
        {'name': 'Business', 'color': '#28a745'},
        {'name': 'Design', 'color': '#dc3545'},
    ]
    
    for tag_data in initial_tags:
        Tag.objects.get_or_create(**tag_data)

def reverse_populate_initial_data(apps, schema_editor):
    """Remove initial data."""
    Tag = apps.get_model('${app_name}', 'Tag')
    Tag.objects.filter(
        name__in=['Technology', 'Business', 'Design']
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('${app_name}', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_initial_data,
            reverse_populate_initial_data,
        ),
    ]
```

### Database Optimization

```python

# apps/${app_name}/querysets.py

from django.db import models

class OptimizedQuerySet(models.QuerySet):
    """Optimized queryset methods."""

    def with_related(self):
        """Optimize foreign key lookups."""
        return self.select_related('author').prefetch_related('tags')

    def published_with_counts(self):
        """Get published items with comment counts."""
        return self.filter(status='published').annotate(
            comment_count=models.Count('comments', distinct=True),
            tag_count=models.Count('tags', distinct=True)
        )

    def bulk_update_status(self, status):
        """Efficiently update status for multiple objects."""
        return self.update(status=status, updated_at=timezone.now())
```

## Testing Framework

### pytest Configuration

```python

# pytest.ini

[tool:pytest]
DJANGO_SETTINGS_MODULE = ${project_name}.settings.testing
python_files = tests.py test_*.py *_tests.py
addopts = 
    --strict-markers
    --strict-config
    --cov=${project_name}
    --cov=apps
    --cov-branch
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80

# conftest.py

import pytest
from django.conf import settings
from django.test import RequestFactory
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass

@pytest.fixture
def api_client():
    """DRF API client."""
    return APIClient()

@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def admin_user():
    """Create admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    """API client authenticated with test user."""
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()
```

### Model Testing

```python

# apps/${app_name}/tests/test_models.py

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models import ${model_name}, Tag

User = get_user_model()

@pytest.mark.django_db
class Test${model_name}Model:
    """Test cases for ${model_name} model."""

    def test_create_${model_name_lower}(self, user):
        """Test creating a ${model_name_lower}."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            description='Test description',
            author=user
        )
        
        assert ${model_name_lower}.title == 'Test ${model_name}'
        assert ${model_name_lower}.author == user
        assert ${model_name_lower}.status == ${model_name}.Status.DRAFT
        assert ${model_name_lower}.created_at is not None

    def test_slug_generation(self, user):
        """Test automatic slug generation."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name} Title',
            author=user
        )
        assert ${model_name_lower}.slug == 'test-${model_name_lower}-title'

    def test_str_representation(self, user):
        """Test string representation."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=user
        )
        assert str(${model_name_lower}) == 'Test ${model_name}'

    def test_is_published_method(self, user):
        """Test is_published method."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=user
        )
        assert not ${model_name_lower}.is_published()
        
        ${model_name_lower}.status = ${model_name}.Status.PUBLISHED
        ${model_name_lower}.save()
        assert ${model_name_lower}.is_published()

    def test_priority_validation(self, user):
        """Test priority field validation."""
        ${model_name_lower} = ${model_name}(
            title='Test ${model_name}',
            author=user,
            priority=11  # Invalid
        )
        
        with pytest.raises(ValidationError):
            ${model_name_lower}.full_clean()

    def test_manager_published_method(self, user):
        """Test custom manager published method."""

        # Create published item

        published = ${model_name}.objects.create(
            title='Published Item',
            author=user,
            status=${model_name}.Status.PUBLISHED
        )
        
        # Create draft item

        ${model_name}.objects.create(
            title='Draft Item',
            author=user,
            status=${model_name}.Status.DRAFT
        )
        
        published_items = ${model_name}.objects.published()
        assert published_items.count() == 1
        assert published_items.first() == published
```

### API Testing

```python

# apps/${app_name}/tests/test_views.py

import pytest
from django.urls import reverse
from rest_framework import status
from ..models import ${model_name}, Tag

@pytest.mark.django_db
class Test${model_name}API:
    """Test ${model_name} API endpoints."""

    def test_list_${model_name_lower}s(self, api_client, user):
        """Test listing ${model_name_lower}s."""

        # Create test data

        ${model_name}.objects.create(
            title='Test ${model_name}',
            author=user,
            status=${model_name}.Status.PUBLISHED
        )
        
        url = reverse('api:${app_name}:${model_name_lower}-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_create_${model_name_lower}(self, authenticated_client):
        """Test creating ${model_name_lower}."""
        data = {
            'title': 'New ${model_name}',
            'description': 'New description',
            'status': 'draft'
        }
        
        url = reverse('api:${app_name}:${model_name_lower}-list')
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']

    def test_create_${model_name_lower}_requires_auth(self, api_client):
        """Test that creating ${model_name_lower} requires authentication."""
        data = {'title': 'New ${model_name}'}
        
        url = reverse('api:${app_name}:${model_name_lower}-list')
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_${model_name_lower}_own_item(self, authenticated_client, user):
        """Test updating own ${model_name_lower}."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Original Title',
            author=user
        )
        
        data = {'title': 'Updated Title'}
        url = reverse('api:${app_name}:${model_name_lower}-detail', kwargs={'slug': ${model_name_lower}.slug})
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'

    def test_cannot_update_others_${model_name_lower}(self, authenticated_client, user):
        """Test that users cannot update others' ${model_name_lower}s."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        
        ${model_name_lower} = ${model_name}.objects.create(
            title='Other User Item',
            author=other_user
        )
        
        data = {'title': 'Hacked Title'}
        url = reverse('api:${app_name}:${model_name_lower}-detail', kwargs={'slug': ${model_name_lower}.slug})
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_featured_${model_name_lower}s_endpoint(self, api_client, user):
        """Test featured ${model_name_lower}s endpoint."""

        # Create featured item

        featured = ${model_name}.objects.create(
            title='Featured Item',
            author=user,
            status=${model_name}.Status.PUBLISHED,
            is_featured=True
        )
        
        # Create non-featured item

        ${model_name}.objects.create(
            title='Regular Item',
            author=user,
            status=${model_name}.Status.PUBLISHED,
            is_featured=False
        )
        
        url = reverse('api:${app_name}:${model_name_lower}-featured')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Featured Item'

    def test_my_${model_name_lower}s_endpoint(self, authenticated_client, user):
        """Test my ${model_name_lower}s endpoint."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        
        # Create user's item

        my_item = ${model_name}.objects.create(
            title='My Item',
            author=user
        )
        
        # Create other user's item

        ${model_name}.objects.create(
            title='Other Item',
            author=other_user
        )
        
        url = reverse('api:${app_name}:${model_name_lower}-my-items')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'My Item'

    @pytest.mark.parametrize('field,value,expected_error', [
        ('title', '', 'This field may not be blank.'),
        ('priority', 0, 'Ensure this value is greater than or equal to 1.'),
        ('priority', 11, 'Ensure this value is less than or equal to 10.'),
    ])
    def test_validation_errors(self, authenticated_client, field, value, expected_error):
        """Test validation errors."""
        data = {
            'title': 'Valid Title',
            'description': 'Valid description',
            'priority': 5
        }
        data[field] = value
        
        url = reverse('api:${app_name}:${model_name_lower}-list')
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_error in str(response.data[field])
```

## Performance and Optimization

### Database Query Optimization

```python

# apps/${app_name}/views.py - Optimized ViewSet

from django.db import models
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

class OptimizedViewSet(ModelViewSet):
    """Performance-optimized ViewSet."""
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        return super().get_queryset().select_related(
            'author'
        ).prefetch_related(
            'tags',
            models.Prefetch(
                'comments',
                queryset=Comment.objects.select_related('author')
            )
        ).annotate(
            comment_count=models.Count('comments', distinct=True),
            tag_count=models.Count('tags', distinct=True)
        )

    @method_decorator(cache_page(60 * 15))  # 15 minutes
    @method_decorator(vary_on_headers('User-Agent', 'Accept-Language'))
    def list(self, request, *args, **kwargs):
        """Cached list view."""
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Optimized create with bulk operations."""
        instance = serializer.save(author=self.request.user)
        
        # Bulk create related objects if needed

        if 'tag_ids' in serializer.validated_data:
            tag_ids = serializer.validated_data['tag_ids']
            instance.tags.set(tag_ids)
        
        return instance
```

### Caching Strategies

```python

# apps/${app_name}/utils/cache.py

from django.core.cache import cache
from django.conf import settings
import hashlib
import json

class CacheManager:
    """Centralized cache management."""
    
    @staticmethod
    def get_cache_key(prefix, **kwargs):
        """Generate cache key from prefix and kwargs."""
        key_data = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"${project_name}:{prefix}:{key_hash}"
    
    @classmethod
    def cache_${model_name_lower}(cls, ${model_name_lower}, timeout=3600):
        """Cache ${model_name_lower} object."""
        cache_key = cls.get_cache_key('${model_name_lower}', id=${model_name_lower}.id)
        cache.set(cache_key, ${model_name_lower}, timeout)
    
    @classmethod
    def get_cached_${model_name_lower}(cls, ${model_name_lower}_id):
        """Get cached ${model_name_lower} object."""
        cache_key = cls.get_cache_key('${model_name_lower}', id=${model_name_lower}_id)
        return cache.get(cache_key)
    
    @classmethod
    def invalidate_${model_name_lower}_cache(cls, ${model_name_lower}_id):
        """Invalidate ${model_name_lower} cache."""
        cache_key = cls.get_cache_key('${model_name_lower}', id=${model_name_lower}_id)
        cache.delete(cache_key)

# Usage in models.py

from .utils.cache import CacheManager

class ${model_name}(TimeStampedModel):

    # ... model definition ...
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update cache after save

        CacheManager.cache_${model_name_lower}(self)
    
    def delete(self, *args, **kwargs):

        # Invalidate cache before delete

        CacheManager.invalidate_${model_name_lower}_cache(self.id)
        super().delete(*args, **kwargs)
```

### Celery Task Management

```python

# apps/${app_name}/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import ${model_name}

User = get_user_model()

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def send_${model_name_lower}_notification(self, ${model_name_lower}_id, user_id):
    """Send notification when ${model_name_lower} is published."""
    try:
        ${model_name_lower} = ${model_name}.objects.get(id=${model_name_lower}_id)
        user = User.objects.get(id=user_id)
        
        send_mail(
            subject=f'New ${model_name}: {${model_name_lower}.title}',
            message=f'A new ${model_name_lower} "{${model_name_lower}.title}" has been published.',
            from_email='noreply@${project_name}.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return f'Notification sent for ${model_name_lower} {${model_name_lower}_id}'
        
    except ${model_name}.DoesNotExist:
        raise self.retry(countdown=60)
    except User.DoesNotExist:
        raise self.retry(countdown=60)

@shared_task
def cleanup_old_${model_name_lower}s():
    """Clean up old draft ${model_name_lower}s."""
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count, _ = ${model_name}.objects.filter(
        status=${model_name}.Status.DRAFT,
        created_at__lt=cutoff_date
    ).delete()
    
    return f'Deleted {deleted_count} old draft ${model_name_lower}s'

@shared_task
def bulk_update_${model_name_lower}_status(${model_name_lower}_ids, new_status):
    """Bulk update ${model_name_lower} status."""
    updated_count = ${model_name}.objects.filter(
        id__in=${model_name_lower}_ids
    ).update(status=new_status)
    
    return f'Updated {updated_count} ${model_name_lower}s to {new_status}'
```

## Security Best Practices

### Authentication and Permissions

```python

# apps/${app_name}/permissions.py

from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission to only allow authors to edit their own objects."""

    def has_object_permission(self, request, view, obj):

        # Read permissions for any request

        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for author

        return obj.author == request.user

class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Permission for authors and admins."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user or request.user.is_staff

# Input validation and sanitization

from django.core.exceptions import ValidationError
import bleach

def clean_html_content(content):
    """Clean HTML content to prevent XSS."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3']
    allowed_attributes = {'a': ['href', 'title']}
    
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)

# Rate limiting

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
def limited_view(request):
    """Rate-limited view."""
    pass
```

### Environment Variables and Security

```bash

# .env.example

DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Deployment Configuration

### Docker Setup

```dockerfile

# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project

COPY . .

# Create logs directory

RUN mkdir -p logs

# Collect static files

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "${project_name}.wsgi:application", "--bind", "0.0.0.0:8000"]
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

      - DEBUG=False
      - DATABASE_URL=postgres://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379/0

    depends_on:

      - db
      - redis

    volumes:

      - media_volume:/app/media
      - static_volume:/app/staticfiles

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:

      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:

      - "6379:6379"

  celery:
    build: .
    command: celery -A ${project_name} worker -l info
    environment:

      - DATABASE_URL=postgres://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379/0

    depends_on:

      - db
      - redis

volumes:
  postgres_data:
  media_volume:
  static_volume:
```

---

*Generated by Claude Builder v${version} on ${timestamp}*