# ${project_name} - Django Development Instructions

## Project Context

${project_description}

**Framework**: Django ${django_version}
**Python Version**: ${python_version}
**Database**: ${database}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## Django Development Standards

### Project Structure

```
${project_name}/
├── manage.py                     # Django management script
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── .env.example                  # Environment variables template
├── ${project_name}/              # Main project package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Base settings
│   │   ├── development.py       # Development settings
│   │   ├── production.py        # Production settings
│   │   └── testing.py           # Test settings
│   ├── urls.py                  # Main URL configuration
│   ├── wsgi.py                  # WSGI application
│   └── asgi.py                  # ASGI application (for async)
├── apps/                        # Custom Django apps
│   ├── __init__.py
│   ├── users/                   # User management app
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py       # DRF serializers
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_serializers.py
│   └── ${app_name}/             # Feature-specific app
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── admin.py
│       ├── managers.py
│       ├── signals.py
│       └── tests/
├── static/                      # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── media/                       # User uploaded files
├── templates/                   # Django templates
│   ├── base.html
│   └── ${app_name}/
├── locale/                      # Internationalization files
├── docs/                        # Documentation
├── scripts/                     # Utility scripts
└── tests/                       # Project-wide tests
```

### Settings Configuration

```python

# settings/base.py

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_extensions',
    'django_filters',
]

LOCAL_APPS = [
    'apps.users',
    'apps.${app_name}',
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

WSGI_APPLICATION = '${project_name}.wsgi.application'

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

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

# Custom user model

AUTH_USER_MODEL = 'users.User'

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files

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
}

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        '${project_name}': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Celery Configuration

CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Cache Configuration

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': '${project_name}',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Email Configuration

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@${project_name}.com')

# Security Settings

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS Settings

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
```

### Model Best Practices

```python

# apps/${app_name}/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .managers import ${model_name}Manager

User = get_user_model()

class TimeStampedModel(models.Model):
    """Abstract base class with created and updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ${model_name}(TimeStampedModel):
    """${model_description}."""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')

    title = models.CharField(
        _('Title'),
        max_length=200,
        help_text=_('Enter a descriptive title')
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=200,
        unique=True,
        help_text=_('URL-friendly version of the title')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Optional description')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='${model_name_lower}s',
        verbose_name=_('Author')
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='${model_name_lower}s',
        verbose_name=_('Tags')
    )
    priority = models.PositiveIntegerField(
        _('Priority'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Priority level (1-10)')
    )
    is_featured = models.BooleanField(
        _('Is Featured'),
        default=False,
        help_text=_('Mark as featured item')
    )
    published_at = models.DateTimeField(
        _('Published At'),
        null=True,
        blank=True
    )
    
    # Use custom manager

    objects = ${model_name}Manager()

    class Meta:
        verbose_name = _('${model_name}')
        verbose_name_plural = _('${model_name}s')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_featured', '-priority']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(priority__gte=1) & models.Q(priority__lte=10),
                name='valid_priority_range'
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('${app_name}:${model_name_lower}-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):

        # Auto-generate slug if not provided

        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        
        # Set published_at when status changes to published

        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def is_published(self):
        """Check if the item is published."""
        return self.status == self.Status.PUBLISHED

    def get_related_items(self, limit=5):
        """Get related items based on common tags."""
        if not self.pk:
            return self.__class__.objects.none()
        
        return self.__class__.objects.filter(
            tags__in=self.tags.all(),
            status=self.Status.PUBLISHED
        ).exclude(pk=self.pk).distinct()[:limit]

class Tag(models.Model):
    """Tag model for categorization."""
    name = models.CharField(_('Name'), max_length=50, unique=True)
    slug = models.SlugField(_('Slug'), max_length=50, unique=True)
    color = models.CharField(
        _('Color'),
        max_length=7,
        default='#007bff',
        help_text=_('Hex color code')
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

### Custom Managers and QuerySets

```python

# apps/${app_name}/managers.py

from django.db import models
from django.utils import timezone

class ${model_name}QuerySet(models.QuerySet):
    """Custom QuerySet for ${model_name}."""

    def published(self):
        """Filter published items."""
        return self.filter(status='published', published_at__lte=timezone.now())

    def featured(self):
        """Filter featured items."""
        return self.filter(is_featured=True)

    def by_author(self, author):
        """Filter by author."""
        return self.filter(author=author)

    def with_tags(self):
        """Prefetch tags to avoid N+1 queries."""
        return self.prefetch_related('tags')

    def search(self, query):
        """Search in title and description."""
        return self.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        )

    def recent(self, days=7):
        """Get recent items."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

class ${model_name}Manager(models.Manager):
    """Custom manager for ${model_name}."""

    def get_queryset(self):
        return ${model_name}QuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()

    def by_author(self, author):
        return self.get_queryset().by_author(author)

    def search(self, query):
        return self.get_queryset().search(query)

    def recent(self, days=7):
        return self.get_queryset().recent(days)
```

### Django REST Framework Serializers

```python

# apps/${app_name}/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ${model_name}, Tag

User = get_user_model()

class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color']
        read_only_fields = ['slug']

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer."""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']

class ${model_name}ListSerializer(serializers.ModelSerializer):
    """Serializer for ${model_name} list view."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_published = serializers.SerializerMethodField()

    class Meta:
        model = ${model_name}
        fields = [
            'id', 'title', 'slug', 'description', 'status',
            'author', 'tags', 'priority', 'is_featured',
            'is_published', 'created_at', 'updated_at'
        ]

    def get_is_published(self, obj):
        return obj.is_published()

class ${model_name}DetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for ${model_name}."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True
    )
    related_items = serializers.SerializerMethodField()
    is_published = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(
        view_name='api:${app_name}:${model_name_lower}-detail',
        lookup_field='slug'
    )

    class Meta:
        model = ${model_name}
        fields = [
            'id', 'title', 'slug', 'description', 'status',
            'author', 'tags', 'tag_ids', 'priority', 'is_featured',
            'is_published', 'published_at', 'related_items',
            'created_at', 'updated_at', 'url'
        ]
        read_only_fields = ['slug', 'author', 'published_at']

    def get_related_items(self, obj):
        related = obj.get_related_items()
        return ${model_name}ListSerializer(related, many=True, context=self.context).data

    def get_is_published(self, obj):
        return obj.is_published()

    def create(self, validated_data):

        # Set the author to the current user

        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    def validate_title(self, value):
        """Validate that title is unique for the current user."""
        user = self.context['request'].user
        if ${model_name}.objects.filter(title=value, author=user).exists():
            raise serializers.ValidationError(
                "You already have an item with this title."
            )
        return value

class ${model_name}CreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ${model_name}."""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = ${model_name}
        fields = [
            'title', 'description', 'status', 'tag_ids',
            'priority', 'is_featured'
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
```

### API Views with Django REST Framework

```python

# apps/${app_name}/views.py

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from .models import ${model_name}, Tag
from .serializers import (
    ${model_name}ListSerializer,
    ${model_name}DetailSerializer,
    ${model_name}CreateUpdateSerializer,
    TagSerializer
)
from .filters import ${model_name}Filter
from .permissions import IsAuthorOrReadOnly

class ${model_name}ViewSet(ModelViewSet):
    """ViewSet for ${model_name} CRUD operations."""
    
    queryset = ${model_name}.objects.select_related('author').prefetch_related('tags')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ${model_name}Filter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'title']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return ${model_name}ListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ${model_name}CreateUpdateSerializer
        return ${model_name}DetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        if self.action == 'list':

            # Show published items to everyone, all items to authors

            if self.request.user.is_authenticated:
                return queryset.filter(
                    models.Q(status='published') | 
                    models.Q(author=self.request.user)
                )
            return queryset.published()
        
        return queryset

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @method_decorator(vary_on_headers('User-Agent'))
    def list(self, request, *args, **kwargs):
        """List ${model_name}s with caching."""
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_items(self, request):
        """Get current user's items."""
        queryset = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured items."""
        queryset = self.get_queryset().featured().published()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthorOrReadOnly])
    def toggle_featured(self, request, slug=None):
        """Toggle featured status of an item."""
        item = self.get_object()
        item.is_featured = not item.is_featured
        item.save(update_fields=['is_featured'])
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthorOrReadOnly])
    def publish(self, request, slug=None):
        """Publish an item."""
        item = self.get_object()
        if item.status != 'published':
            item.status = 'published'
            item.save(update_fields=['status', 'published_at'])
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)

class TagViewSet(ModelViewSet):
    """ViewSet for Tag CRUD operations."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def list(self, request, *args, **kwargs):
        """List tags with caching."""
        return super().list(request, *args, **kwargs)
```

### Testing Best Practices

```python

# apps/${app_name}/tests/test_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import ${model_name}, Tag

User = get_user_model()

class ${model_name}ModelTest(TestCase):
    """Test cases for ${model_name} model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag = Tag.objects.create(name='Test Tag')

    def test_create_${model_name_lower}(self):
        """Test creating a ${model_name_lower}."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            description='Test description',
            author=self.user
        )
        
        self.assertEqual(${model_name_lower}.title, 'Test ${model_name}')
        self.assertEqual(${model_name_lower}.author, self.user)
        self.assertEqual(${model_name_lower}.status, ${model_name}.Status.DRAFT)
        self.assertIsNotNone(${model_name_lower}.created_at)
        self.assertIsNotNone(${model_name_lower}.updated_at)

    def test_auto_slug_generation(self):
        """Test that slug is auto-generated from title."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name} Title',
            author=self.user
        )
        self.assertEqual(${model_name_lower}.slug, 'test-${model_name_lower}-title')

    def test_published_at_auto_set(self):
        """Test that published_at is set when status changes to published."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=self.user
        )
        self.assertIsNone(${model_name_lower}.published_at)
        
        ${model_name_lower}.status = ${model_name}.Status.PUBLISHED
        ${model_name_lower}.save()
        
        ${model_name_lower}.refresh_from_db()
        self.assertIsNotNone(${model_name_lower}.published_at)

    def test_str_method(self):
        """Test string representation."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=self.user
        )
        self.assertEqual(str(${model_name_lower}), 'Test ${model_name}')

    def test_get_absolute_url(self):
        """Test get_absolute_url method."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=self.user
        )
        expected_url = f'/${app_name}/{${model_name_lower}.slug}/'
        self.assertEqual(${model_name_lower}.get_absolute_url(), expected_url)

    def test_is_published_method(self):
        """Test is_published method."""
        ${model_name_lower} = ${model_name}.objects.create(
            title='Test ${model_name}',
            author=self.user
        )
        self.assertFalse(${model_name_lower}.is_published())
        
        ${model_name_lower}.status = ${model_name}.Status.PUBLISHED
        ${model_name_lower}.save()
        self.assertTrue(${model_name_lower}.is_published())

    def test_get_related_items(self):
        """Test get_related_items method."""

        # Create main item with tags

        main_item = ${model_name}.objects.create(
            title='Main Item',
            author=self.user,
            status=${model_name}.Status.PUBLISHED
        )
        main_item.tags.add(self.tag)
        
        # Create related item with same tag

        related_item = ${model_name}.objects.create(
            title='Related Item',
            author=self.user,
            status=${model_name}.Status.PUBLISHED
        )
        related_item.tags.add(self.tag)
        
        # Create unrelated item

        ${model_name}.objects.create(
            title='Unrelated Item',
            author=self.user,
            status=${model_name}.Status.PUBLISHED
        )
        
        related_items = main_item.get_related_items()
        self.assertEqual(related_items.count(), 1)
        self.assertEqual(related_items.first(), related_item)

    def test_manager_methods(self):
        """Test custom manager methods."""

        # Create published item

        published_item = ${model_name}.objects.create(
            title='Published Item',
            author=self.user,
            status=${model_name}.Status.PUBLISHED
        )
        
        # Create draft item

        ${model_name}.objects.create(
            title='Draft Item',
            author=self.user,
            status=${model_name}.Status.DRAFT
        )
        
        # Test published manager method

        published_items = ${model_name}.objects.published()
        self.assertEqual(published_items.count(), 1)
        self.assertEqual(published_items.first(), published_item)

    def test_priority_validation(self):
        """Test priority field validation."""
        ${model_name_lower} = ${model_name}(
            title='Test ${model_name}',
            author=self.user,
            priority=11  # Invalid priority
        )
        
        with self.assertRaises(ValidationError):
            ${model_name_lower}.full_clean()
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
