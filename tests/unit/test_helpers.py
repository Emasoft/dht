#!/usr/bin/env python3
"""
Test Helpers module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial creation of test_helpers.py with comprehensive fixture generators
# - Added realistic project type generators (Django, FastAPI, ML, etc.)
# - Created proper mock factories with correct return types
# - Added path resolution utilities for finding DHT modules
# - Implemented utilities for creating complete project structures
# - Following CLAUDE.md testing principles: realistic fixtures, minimal mocking

"""
Test helpers for DHT unit and integration tests.

This module provides:
1. Realistic fixture generators for different project types
2. Proper mock factories that return correct types (like named tuples for platform.uname)
3. Path resolution utilities for finding DHT modules in tests
4. Utilities for creating complete project structures
"""

import json
import os
import shutil
import subprocess
import tempfile
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# Platform uname mock that matches the actual structure
PlatformUname = namedtuple("PlatformUname", ["system", "node", "release", "version", "machine", "processor"])


def create_platform_uname_mock(
    system: str = "Darwin",
    node: str = "test-machine.local",
    release: str = "20.3.0",
    version: str = "Darwin Kernel Version 20.3.0",
    machine: str = "x86_64",
    processor: str = "x86_64",
) -> PlatformUname:
    """Create a proper platform.uname() mock with correct namedtuple structure."""
    return PlatformUname(system, node, release, version, machine, processor)


def create_psutil_virtual_memory_mock(
    total: int = 16 * 1024 * 1024 * 1024,  # 16GB
    available: int = 8 * 1024 * 1024 * 1024,  # 8GB
    percent: float = 50.0,
    used: int = 8 * 1024 * 1024 * 1024,
    free: int = 8 * 1024 * 1024 * 1024,
) -> MagicMock:
    """Create a mock for psutil.virtual_memory() with correct attributes."""
    mock_vm = MagicMock()
    mock_vm.total = total
    mock_vm.available = available
    mock_vm.percent = percent
    mock_vm.used = used
    mock_vm.free = free
    return mock_vm


def create_psutil_process_mock(
    pid: int = 1234,
    name: str = "python",
    status: str = "running",
    cpu_percent: float = 25.0,
    memory_percent: float = 5.0,
) -> MagicMock:
    """Create a mock for psutil.Process with common attributes."""
    mock_process = MagicMock()
    mock_process.pid = pid
    mock_process.name.return_value = name
    mock_process.status.return_value = status
    mock_process.cpu_percent.return_value = cpu_percent
    mock_process.memory_percent.return_value = memory_percent
    return mock_process


def find_dht_root() -> Path:
    """Find the DHT root directory from any test location."""
    current = Path(__file__).parent
    while current != current.parent:
        # Check for the new UV-style layout (dhtl.sh and src/DHT)
        if (current / "dhtl.sh").exists() and (current / "src" / "DHT").is_dir():
            return current
        # Also check for old layout (dhtl.sh and DHT)
        if (current / "dhtl.sh").exists() and (current / "DHT").is_dir():
            return current
        current = current.parent
    raise RuntimeError("Could not find DHT root directory")


def find_dht_modules_dir() -> Path:
    """Find the DHT modules directory."""
    dht_root = find_dht_root()
    # Try the new UV-style layout first
    modules_dir = dht_root / "src" / "DHT" / "modules"
    if modules_dir.is_dir():
        return modules_dir
    # Fall back to old layout
    modules_dir = dht_root / "DHT" / "modules"
    if not modules_dir.is_dir():
        raise RuntimeError(f"DHT modules directory not found at {modules_dir}")
    return modules_dir


def create_project_structure(
    root_dir: Path,
    project_type: str = "simple",
    project_name: str = "test_project",
    python_version: str = "3.10",
    include_tests: bool = True,
    include_docs: bool = True,
    include_ci: bool = True,
) -> dict[str, Any]:
    """
    Create a complete project structure for testing.

    Args:
        root_dir: Root directory for the project
        project_type: Type of project (simple, django, fastapi, ml, library, fullstack)
        project_name: Name of the project
        python_version: Python version requirement
        include_tests: Whether to include test files
        include_docs: Whether to include documentation
        include_ci: Whether to include CI/CD configuration

    Returns:
        Dict with project metadata and paths
    """
    project_dir = root_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "root": project_dir,
        "type": project_type,
        "name": project_name,
        "python_version": python_version,
        "created_at": datetime.now().isoformat(),
        "files": [],
    }

    # Create base structure common to all projects
    create_base_structure(project_dir, project_name, python_version, metadata)

    # Create project-specific structure
    if project_type == "simple":
        create_simple_project(project_dir, project_name, metadata)
    elif project_type == "django":
        create_django_project(project_dir, project_name, metadata)
    elif project_type == "fastapi":
        create_fastapi_project(project_dir, project_name, metadata)
    elif project_type == "ml":
        create_ml_project(project_dir, project_name, metadata)
    elif project_type == "library":
        create_library_project(project_dir, project_name, metadata)
    elif project_type == "fullstack":
        create_fullstack_project(project_dir, project_name, metadata)
    else:
        raise ValueError(f"Unknown project type: {project_type}")

    # Add optional components
    if include_tests:
        create_test_structure(project_dir, project_type, metadata)

    if include_docs:
        create_docs_structure(project_dir, metadata)

    if include_ci:
        create_ci_structure(project_dir, metadata)

    return metadata


def create_base_structure(project_dir: Path, project_name: str, python_version: str, metadata: dict) -> Any:
    """Create base project structure common to all project types."""
    # Create pyproject.toml
    pyproject_content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Test project for DHT"
readme = "README.md"
requires-python = ">={python_version}"
license = {{text = "MIT"}}
authors = [
    {{name = "Test Author", email = "test@example.com"}},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: {python_version}",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[tool.ruff]
line-length = 88
target-version = "py{python_version.replace(".", "")}"

[tool.black]
line-length = 88
target-version = ["py{python_version.replace(".", "")}"]

[tool.mypy]
python_version = "{python_version}"
warn_return_any = true
warn_unused_configs = true
'''
    (project_dir / "pyproject.toml").write_text(pyproject_content)
    metadata["files"].append("pyproject.toml")

    # Create README.md
    readme_content = f"""# {project_name}

Test project for DHT development.

## Installation

```bash
pip install -e .
```

## Development

```bash
dhtl setup
dhtl test
```
"""
    (project_dir / "README.md").write_text(readme_content)
    metadata["files"].append("README.md")

    # Create .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
htmlcov/

# DHT
DHT/.dht_environment_report.json
.dhtconfig

# Environment
.env
.env.local
"""
    (project_dir / ".gitignore").write_text(gitignore_content)
    metadata["files"].append(".gitignore")

    # Create .python-version
    (project_dir / ".python-version").write_text(f"{python_version}\n")
    metadata["files"].append(".python-version")

    # Create source directory
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "src" / "__init__.py").touch()
    metadata["files"].extend(["src/__init__.py"])


def create_simple_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a simple Python script project."""
    # Main script
    main_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Simple script for testing DHT functionality."""

import sys
import argparse
from pathlib import Path


def main() -> Any:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple test script")
    parser.add_argument("--input", type=Path, help="Input file")
    parser.add_argument("--output", type=Path, help="Output file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Processing {args.input} -> {args.output}")

    if args.input and args.input.exists():
        content = args.input.read_text()
        if args.output:
            args.output.write_text(content.upper())
            print(f"Processed {len(content)} characters")
    else:
        print("No input file provided or file does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
    (project_dir / "main.py").write_text(main_content)
    metadata["files"].append("main.py")

    # Utils module
    utils_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Utility functions for the simple project."""

from typing import List, Dict, Any


def process_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a list of data items."""
    result = {
        "count": len(data),
        "items": data,
        "processed": True
    }
    return result


def validate_input(value: str) -> bool:
    """Validate input value."""
    return bool(value and value.strip())
'''
    (project_dir / "src" / "utils.py").write_text(utils_content)
    metadata["files"].append("src/utils.py")


def create_django_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a Django project structure."""
    # Django-specific dependencies in pyproject.toml
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()
    content = content.replace(
        'requires-python = ">=',
        """dependencies = [
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
    "django-environ>=0.10.0",
    "psycopg2-binary>=2.9.0",
    "redis>=4.5.0",
    "celery>=5.2.0",
]

requires-python = ">=""",
    )
    pyproject_path.write_text(content)

    # Django project structure
    django_dir = project_dir / project_name
    django_dir.mkdir(exist_ok=True)

    # settings.py
    settings_content = f'''"""
Django settings for {project_name} project.
"""

from pathlib import Path
import environ

env = environ.Env()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-test-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '{project_name}.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = '{project_name}.wsgi.application'

# Database
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='{project_name}_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='password'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }}
}}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {{
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}}

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
'''
    (django_dir / "settings.py").write_text(settings_content)
    metadata["files"].append(f"{project_name}/settings.py")

    # urls.py
    urls_content = f'''"""
URL configuration for {project_name} project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
'''
    (django_dir / "urls.py").write_text(urls_content)
    metadata["files"].append(f"{project_name}/urls.py")

    # wsgi.py
    wsgi_content = f'''"""
WSGI config for {project_name} project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

application = get_wsgi_application()
'''
    (django_dir / "wsgi.py").write_text(wsgi_content)
    metadata["files"].append(f"{project_name}/wsgi.py")

    # __init__.py files
    (django_dir / "__init__.py").touch()
    metadata["files"].append(f"{project_name}/__init__.py")

    # manage.py
    manage_content = f'''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
'''
    (project_dir / "manage.py").write_text(manage_content)
    os.chmod(project_dir / "manage.py", 0o755)
    metadata["files"].append("manage.py")

    # Create api app
    api_dir = project_dir / "api"
    api_dir.mkdir(exist_ok=True)
    (api_dir / "__init__.py").touch()

    # models.py
    models_content = '''from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    """Sample model for API."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> Any:
        return self.name
'''
    (api_dir / "models.py").write_text(models_content)
    metadata["files"].append("api/models.py")

    # views.py
    views_content = '''from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    """API endpoint for items."""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer) -> Any:
        serializer.save(created_by=self.request.user)
'''
    (api_dir / "views.py").write_text(views_content)
    metadata["files"].append("api/views.py")

    # serializers.py
    serializers_content = '''from rest_framework import serializers
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
'''
    (api_dir / "serializers.py").write_text(serializers_content)
    metadata["files"].append("api/serializers.py")

    # urls.py
    api_urls_content = """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
"""
    (api_dir / "urls.py").write_text(api_urls_content)
    metadata["files"].append("api/urls.py")


def create_fastapi_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a FastAPI project structure."""
    # Update pyproject.toml with FastAPI dependencies
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()
    content = content.replace(
        'requires-python = ">=',
        """dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.4.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "asyncpg>=0.28.0",
]

requires-python = ">=""",
    )
    pyproject_path.write_text(content)

    # Main application file
    main_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Handle application lifecycle events."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check() -> Any:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}
'''
    (project_dir / "main.py").write_text(main_content)
    metadata["files"].append("main.py")

    # Create app structure
    app_dir = project_dir / "app"
    app_dir.mkdir(exist_ok=True)
    (app_dir / "__init__.py").touch()

    # Core module
    core_dir = app_dir / "core"
    core_dir.mkdir(exist_ok=True)
    (core_dir / "__init__.py").touch()

    # config.py
    config_content = f'''from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "{project_name}"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "changethisinproduction"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/{project_name}"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
'''
    (core_dir / "config.py").write_text(config_content)
    metadata["files"].append("app/core/config.py")

    # security.py
    security_content = '''from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Any:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)
'''
    (core_dir / "security.py").write_text(security_content)
    metadata["files"].append("app/core/security.py")

    # Database module
    db_dir = app_dir / "db"
    db_dir.mkdir(exist_ok=True)
    (db_dir / "__init__.py").touch()

    # base.py
    base_content = """from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
"""
    (db_dir / "base.py").write_text(base_content)
    metadata["files"].append("app/db/base.py")

    # session.py
    session_content = '''from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> Any:
    """Dependency to get DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
'''
    (db_dir / "session.py").write_text(session_content)
    metadata["files"].append("app/db/session.py")

    # API module
    api_dir = app_dir / "api"
    api_dir.mkdir(exist_ok=True)
    (api_dir / "__init__.py").touch()

    v1_dir = api_dir / "v1"
    v1_dir.mkdir(exist_ok=True)
    (v1_dir / "__init__.py").touch()

    # api.py
    api_content = """from fastapi import APIRouter
from app.api.v1.endpoints import users, items

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
"""
    (v1_dir / "api.py").write_text(api_content)
    metadata["files"].append("app/api/v1/api.py")

    # Endpoints
    endpoints_dir = v1_dir / "endpoints"
    endpoints_dir.mkdir(exist_ok=True)
    (endpoints_dir / "__init__.py").touch()

    # users.py endpoint
    users_endpoint_content = '''from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieve users."""
    return {"users": [], "skip": skip, "limit": limit}


@router.post("/")
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    """Create new user."""
    return {"message": "User created", "data": user_data}
'''
    (endpoints_dir / "users.py").write_text(users_endpoint_content)
    metadata["files"].append("app/api/v1/endpoints/users.py")

    # items.py endpoint
    items_endpoint_content = '''from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def read_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieve items."""
    return {"items": [], "skip": skip, "limit": limit}


@router.post("/")
async def create_item(item_data: dict, db: AsyncSession = Depends(get_db)):
    """Create new item."""
    return {"message": "Item created", "data": item_data}
'''
    (endpoints_dir / "items.py").write_text(items_endpoint_content)
    metadata["files"].append("app/api/v1/endpoints/items.py")


def create_ml_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a machine learning project structure."""
    # Update pyproject.toml with ML dependencies
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()
    content = content.replace(
        'requires-python = ">=',
        """dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "transformers>=4.30.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "jupyter>=1.0.0",
    "tensorboard>=2.13.0",
    "wandb>=0.15.0",
    "hydra-core>=1.3.0",
    "omegaconf>=2.3.0",
]

requires-python = ">=""",
    )
    pyproject_path.write_text(content)

    # Main training script
    train_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main training script for ML project."""

import os
import hydra
from omegaconf import DictConfig, OmegaConf
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import wandb

from src.models import create_model
from src.datasets import create_dataset
from src.trainers import Trainer
from src.utils import set_seed, get_logger


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main training function."""
    logger = get_logger(__name__)
    logger.info(f"Config:\\n{OmegaConf.to_yaml(cfg)}")

    # Set random seeds
    set_seed(cfg.seed)

    # Initialize wandb
    if cfg.use_wandb:
        wandb.init(
            project=cfg.project_name,
            config=OmegaConf.to_container(cfg, resolve=True),
            name=cfg.run_name,
        )

    # Create datasets
    train_dataset = create_dataset(cfg.dataset, split="train")
    val_dataset = create_dataset(cfg.dataset, split="validation")

    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
    )

    # Create model
    model = create_model(cfg.model)

    # Create trainer
    trainer = Trainer(
        model=model,
        cfg=cfg,
        train_loader=train_loader,
        val_loader=val_loader,
    )

    # Train model
    trainer.train()

    # Save final model
    trainer.save_checkpoint("final")

    if cfg.use_wandb:
        wandb.finish()


if __name__ == "__main__":
    main()
'''
    (project_dir / "train.py").write_text(train_content)
    metadata["files"].append("train.py")

    # Create src structure
    src_dir = project_dir / "src"

    # models/__init__.py
    models_dir = src_dir / "models"
    models_dir.mkdir(exist_ok=True)
    (models_dir / "__init__.py").write_text("""from .factory import create_model

__all__ = ["create_model"]
""")

    # models/factory.py
    factory_content = '''import torch.nn as nn
from omegaconf import DictConfig
from .resnet import ResNet
from .transformer import TransformerModel


def create_model(cfg: DictConfig) -> nn.Module:
    """Factory function to create models."""
    if cfg.name == "resnet":
        return ResNet(
            num_classes=cfg.num_classes,
            pretrained=cfg.get("pretrained", False),
        )
    elif cfg.name == "transformer":
        return TransformerModel(
            vocab_size=cfg.vocab_size,
            d_model=cfg.d_model,
            num_heads=cfg.num_heads,
            num_layers=cfg.num_layers,
            max_seq_length=cfg.max_seq_length,
        )
    else:
        raise ValueError(f"Unknown model: {cfg.name}")
'''
    (models_dir / "factory.py").write_text(factory_content)
    metadata["files"].extend(["src/models/__init__.py", "src/models/factory.py"])

    # models/resnet.py
    resnet_content = '''import torch
import torch.nn as nn
import torchvision.models as models


class ResNet(nn.Module):
    """ResNet model wrapper."""

    def __init__(self, num_classes: int, pretrained: bool = True) -> Any:
        super().__init__()
        self.backbone = models.resnet50(pretrained=pretrained)
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)

    def forward(self, x) -> Any:
        return self.backbone(x)
'''
    (models_dir / "resnet.py").write_text(resnet_content)
    metadata["files"].append("src/models/resnet.py")

    # models/transformer.py
    transformer_content = '''import torch
import torch.nn as nn
import math


class TransformerModel(nn.Module):
    """Simple transformer model."""

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        num_heads: int = 8,
        num_layers: int = 6,
        max_seq_length: int = 512,
    ) -> Any:
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, max_seq_length)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model * 4,
            dropout=0.1,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.output_projection = nn.Linear(d_model, vocab_size)

    def forward(self, x) -> Any:
        x = self.embedding(x) * math.sqrt(self.d_model)
        x = self.pos_encoding(x)
        x = self.transformer(x)
        return self.output_projection(x)


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer."""

    def __init__(self, d_model: int, max_len: int = 5000) -> Any:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x) -> Any:
        return x + self.pe[:, :x.size(1)]
'''
    (models_dir / "transformer.py").write_text(transformer_content)
    metadata["files"].append("src/models/transformer.py")

    # datasets/__init__.py
    datasets_dir = src_dir / "datasets"
    datasets_dir.mkdir(exist_ok=True)
    (datasets_dir / "__init__.py").write_text("""from .factory import create_dataset

__all__ = ["create_dataset"]
""")

    # datasets/factory.py
    dataset_factory_content = '''from torch.utils.data import Dataset
from omegaconf import DictConfig
from .dummy_dataset import DummyDataset


def create_dataset(cfg: DictConfig, split: str = "train") -> Dataset:
    """Factory function to create datasets."""
    if cfg.name == "dummy":
        return DummyDataset(
            size=cfg.size,
            num_classes=cfg.num_classes,
            split=split,
        )
    else:
        raise ValueError(f"Unknown dataset: {cfg.name}")
'''
    (datasets_dir / "factory.py").write_text(dataset_factory_content)
    metadata["files"].extend(["src/datasets/__init__.py", "src/datasets/factory.py"])

    # datasets/dummy_dataset.py
    dummy_dataset_content = '''import torch
from torch.utils.data import Dataset


class DummyDataset(Dataset):
    """Dummy dataset for testing."""

    def __init__(self, size: int = 1000, num_classes: int = 10, split: str = "train") -> Any:
        self.size = size
        self.num_classes = num_classes
        self.split = split

        # Generate dummy data
        torch.manual_seed(42 if split == "train" else 123)
        self.data = torch.randn(size, 3, 224, 224)
        self.labels = torch.randint(0, num_classes, (size,))

    def __len__(self) -> Any:
        return self.size

    def __getitem__(self, idx) -> Any:
        return self.data[idx], self.labels[idx]
'''
    (datasets_dir / "dummy_dataset.py").write_text(dummy_dataset_content)
    metadata["files"].append("src/datasets/dummy_dataset.py")

    # trainers/__init__.py
    trainers_dir = src_dir / "trainers"
    trainers_dir.mkdir(exist_ok=True)
    (trainers_dir / "__init__.py").write_text("""from .trainer import Trainer

__all__ = ["Trainer"]
""")

    # trainers/trainer.py
    trainer_content = '''import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from omegaconf import DictConfig
from pathlib import Path
import wandb
from tqdm import tqdm


class Trainer:
    """Basic trainer class."""

    def __init__(
        self,
        model: nn.Module,
        cfg: DictConfig,
        train_loader: DataLoader,
        val_loader: DataLoader,
    ) -> Any:
        self.model = model
        self.cfg = cfg
        self.train_loader = train_loader
        self.val_loader = val_loader

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(model.parameters(), lr=cfg.learning_rate)
        self.criterion = nn.CrossEntropyLoss()

        self.checkpoint_dir = Path("checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)

    def train(self) -> Any:
        """Main training loop."""
        for epoch in range(self.cfg.num_epochs):
            self.model.train()
            train_loss = 0.0

            with tqdm(self.train_loader, desc=f"Epoch {epoch+1}/{self.cfg.num_epochs}") as pbar:
                for batch_idx, (data, target) in enumerate(pbar):
                    data, target = data.to(self.device), target.to(self.device)

                    self.optimizer.zero_grad()
                    output = self.model(data)
                    loss = self.criterion(output, target)
                    loss.backward()
                    self.optimizer.step()

                    train_loss += loss.item()
                    pbar.set_postfix({"loss": loss.item()})

                    if self.cfg.use_wandb:
                        wandb.log({
                            "train_loss": loss.item(),
                            "epoch": epoch,
                            "batch": batch_idx,
                        })

            # Validation
            val_loss, val_acc = self.validate()

            print(f"Epoch {epoch+1}: Train Loss: {train_loss/len(self.train_loader):.4f}, "
                  f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

            if self.cfg.use_wandb:
                wandb.log({
                    "epoch": epoch,
                    "train_loss_epoch": train_loss / len(self.train_loader),
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                })

            # Save checkpoint
            if (epoch + 1) % self.cfg.save_every == 0:
                self.save_checkpoint(f"epoch_{epoch+1}")

    def validate(self) -> Any:
        """Validation loop."""
        self.model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for data, target in self.val_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                val_loss += self.criterion(output, target).item()

                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()

        val_loss /= len(self.val_loader)
        val_acc = correct / total

        return val_loss, val_acc

    def save_checkpoint(self, name: str) -> Any:
        """Save model checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.cfg,
        }
        torch.save(checkpoint, self.checkpoint_dir / f"{name}.pt")
'''
    (trainers_dir / "trainer.py").write_text(trainer_content)
    metadata["files"].extend(["src/trainers/__init__.py", "src/trainers/trainer.py"])

    # utils/__init__.py
    utils_dir = src_dir / "utils"
    utils_dir.mkdir(exist_ok=True)
    utils_content = '''import random
import numpy as np
import torch
import logging


def set_seed(seed: int) -> Any:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
'''
    (utils_dir / "__init__.py").write_text(utils_content)
    metadata["files"].append("src/utils/__init__.py")

    # Create configs directory
    configs_dir = project_dir / "configs"
    configs_dir.mkdir(exist_ok=True)

    # config.yaml
    config_yaml = f"""# Main configuration file
project_name: {project_name}
run_name: experiment_001
seed: 42
use_wandb: false

# Model configuration
model:
  name: resnet
  num_classes: 10
  pretrained: true

# Dataset configuration
dataset:
  name: dummy
  size: 1000
  num_classes: 10

# Training configuration
batch_size: 32
num_epochs: 10
learning_rate: 0.001
num_workers: 4
save_every: 5
"""
    (configs_dir / "config.yaml").write_text(config_yaml)
    metadata["files"].append("configs/config.yaml")

    # Create notebooks directory
    notebooks_dir = project_dir / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)

    # exploration.ipynb
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Data Exploration Notebook\n",
                    "\n",
                    "This notebook is for exploring the dataset and model.",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import numpy as np\n",
                    "import pandas as pd\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "\n",
                    "# Configure plotting\n",
                    "plt.style.use('seaborn-v0_8')\n",
                    "sns.set_palette('husl')",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Load and explore data\n",
                    "# Add your data exploration code here",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    (notebooks_dir / "exploration.ipynb").write_text(json.dumps(notebook_content, indent=2))
    metadata["files"].append("notebooks/exploration.ipynb")


def create_library_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a library project structure."""
    # Update pyproject.toml for library distribution
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()
    content = content.replace(
        "[project.optional-dependencies]",
        """[project.urls]
"Homepage" = "https://github.com/username/{project_name}"
"Bug Tracker" = "https://github.com/username/{project_name}/issues"

[project.scripts]
{project_name} = "{project_name}.cli:main"

[project.optional-dependencies]""".replace("{project_name}", project_name),
    )
    pyproject_path.write_text(content)

    # Create package directory
    package_dir = project_dir / project_name
    package_dir.mkdir(exist_ok=True)

    # __init__.py
    init_content = f'''"""
{project_name}: A test library for DHT.

This library provides example functionality for testing DHT's
library project handling capabilities.
"""

from .core import process_data, validate_input
from .version import __version__

__all__ = ["process_data", "validate_input", "__version__"]
'''
    (package_dir / "__init__.py").write_text(init_content)
    metadata["files"].append(f"{project_name}/__init__.py")

    # version.py
    (package_dir / "version.py").write_text('__version__ = "0.1.0"\n')
    metadata["files"].append(f"{project_name}/version.py")

    # core.py
    core_content = '''"""Core functionality for the library."""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path


def process_data(data: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a list of data items according to configuration.

    Args:
        data: List of data items to process
        config: Optional configuration dictionary

    Returns:
        Processed data with metadata
    """
    if config is None:
        config = {}

    processed_items = []
    for item in data:
        processed_item = {
            **item,
            "processed": True,
            "timestamp": None,  # Would be datetime.now() in real code
        }
        processed_items.append(processed_item)

    return {
        "items": processed_items,
        "count": len(processed_items),
        "config": config,
        "version": "0.1.0",
    }


def validate_input(value: Any, expected_type: type = str, min_length: int = 0) -> bool:
    """
    Validate input value against expected criteria.

    Args:
        value: Value to validate
        expected_type: Expected type of the value
        min_length: Minimum length for string/list values

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(value, expected_type):
        return False

    if hasattr(value, "__len__") and len(value) < min_length:
        return False

    if expected_type == str and not value.strip():
        return False

    return True


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return json.load(f)


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
'''
    (package_dir / "core.py").write_text(core_content)
    metadata["files"].append(f"{project_name}/core.py")

    # cli.py
    cli_content = f'''"""Command-line interface for {project_name}."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .core import process_data, load_config, save_results
from .version import __version__


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="{project_name}",
        description="Process data using {project_name} library",
    )
    parser.add_argument(
        "--version", action="version", version=f"{{prog}} {{__version__}}"
    )
    parser.add_argument(
        "input", type=Path, help="Input data file (JSON)"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output file path"
    )
    parser.add_argument(
        "-c", "--config", type=Path, help="Configuration file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    args = parser.parse_args(argv)

    try:
        # Load input data
        if args.verbose:
            print(f"Loading data from {{args.input}}")

        with open(args.input) as f:
            data = json.load(f)

        # Load config if provided
        config = {{}}
        if args.config:
            if args.verbose:
                print(f"Loading config from {{args.config}}")
            config = load_config(args.config)

        # Process data
        if args.verbose:
            print("Processing data...")

        results = process_data(data, config)

        # Save or print results
        if args.output:
            save_results(results, args.output)
            if args.verbose:
                print(f"Results saved to {{args.output}}")
        else:
            print(json.dumps(results, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
    (package_dir / "cli.py").write_text(cli_content)
    metadata["files"].append(f"{project_name}/cli.py")

    # py.typed marker for type hints
    (package_dir / "py.typed").touch()
    metadata["files"].append(f"{project_name}/py.typed")


def create_fullstack_project(project_dir: Path, project_name: str, metadata: dict) -> Any:
    """Create a full-stack project with frontend and backend."""
    # First create a FastAPI backend
    create_fastapi_project(project_dir, project_name, metadata)

    # Add frontend structure
    frontend_dir = project_dir / "frontend"
    frontend_dir.mkdir(exist_ok=True)

    # package.json
    package_json = {
        "name": f"{project_name}-frontend",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint",
            "test": "jest --watch",
            "test:ci": "jest",
        },
        "dependencies": {
            "next": "^14.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.5.0",
            "swr": "^2.2.0",
            "@mui/material": "^5.14.0",
            "@emotion/react": "^11.11.0",
            "@emotion/styled": "^11.11.0",
        },
        "devDependencies": {
            "@types/node": "^20.0.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^5.0.0",
            "eslint": "^8.0.0",
            "eslint-config-next": "^14.0.0",
            "jest": "^29.0.0",
            "@testing-library/react": "^14.0.0",
            "@testing-library/jest-dom": "^6.0.0",
        },
    }
    (frontend_dir / "package.json").write_text(json.dumps(package_json, indent=2))
    metadata["files"].append("frontend/package.json")

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "paths": {"@/*": ["./src/*"]},
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
        "exclude": ["node_modules"],
    }
    (frontend_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
    metadata["files"].append("frontend/tsconfig.json")

    # Create src structure
    src_dir = frontend_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # pages directory
    pages_dir = src_dir / "pages"
    pages_dir.mkdir(exist_ok=True)

    # _app.tsx
    app_content = """import type { AppProps } from 'next/app'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

const theme = createTheme({
  palette: {
    mode: 'light',
  },
})

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Component {...pageProps} />
    </ThemeProvider>
  )
}
"""
    (pages_dir / "_app.tsx").write_text(app_content)
    metadata["files"].append("frontend/src/pages/_app.tsx")

    # index.tsx
    index_content = f"""import {{ useState, useEffect }} from 'react'
import {{ Container, Typography, Button, Box }} from '@mui/material'
import axios from 'axios'

export default function Home() {{
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {{
    setLoading(true)
    try {{
      const response = await axios.get('http://localhost:8000/api/v1/items')
      setData(response.data)
    }} catch (error) {{
      console.error('Error fetching data:', error)
    }} finally {{
      setLoading(false)
    }}
  }}

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          {project_name} Frontend
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Full-stack application with Next.js and FastAPI
        </Typography>
        <Button
          variant="contained"
          onClick={{fetchData}}
          disabled={{loading}}
          sx={{ mt: 2 }}
        >
          {{loading ? 'Loading...' : 'Fetch Data'}}
        </Button>
        {{data && (
          <Box sx={{ mt: 2 }}>
            <pre>{{JSON.stringify(data, null, 2)}}</pre>
          </Box>
        )}}
      </Box>
    </Container>
  )
}}
"""
    (pages_dir / "index.tsx").write_text(index_content)
    metadata["files"].append("frontend/src/pages/index.tsx")

    # Update main README
    readme_path = project_dir / "README.md"
    fullstack_readme = f"""# {project_name}

Full-stack application with FastAPI backend and Next.js frontend.

## Backend Setup

```bash
cd {project_name}
dhtl setup
dhtl run  # or: uvicorn main:app --reload
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Development

Backend API: http://localhost:8000
Frontend: http://localhost:3000
API Docs: http://localhost:8000/docs
"""
    readme_path.write_text(fullstack_readme)


def create_test_structure(project_dir: Path, project_type: str, metadata: dict) -> Any:
    """Create test files appropriate for the project type."""
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").touch()

    # conftest.py
    conftest_content = '''import pytest
from pathlib import Path


@pytest.fixture
def project_root() -> Any:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_data() -> Any:
    """Provide sample data for tests."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
    ]
'''
    (tests_dir / "conftest.py").write_text(conftest_content)
    metadata["files"].append("tests/conftest.py")

    if project_type == "simple":
        # Test for simple project
        test_content = '''import pytest
from pathlib import Path
from src.utils import process_data, validate_input


def test_process_data(sample_data) -> Any:
    """Test data processing function."""
    result = process_data(sample_data)
    assert result["count"] == 2
    assert result["processed"] is True
    assert len(result["items"]) == 2


def test_validate_input() -> Any:
    """Test input validation."""
    assert validate_input("valid string") is True
    assert validate_input("") is False
    assert validate_input("   ") is False
    assert validate_input(123, expected_type=int) is True
    assert validate_input("123", expected_type=int) is False
'''
        (tests_dir / "test_utils.py").write_text(test_content)
        metadata["files"].append("tests/test_utils.py")

    elif project_type in ["django", "fastapi"]:
        # API tests
        test_api_content = '''import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Any:
    """Create test client."""
    from main import app
    return TestClient(app)


def test_health_check(client) -> Any:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_items(client) -> Any:
    """Test items endpoint."""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    assert "items" in response.json()
'''
        (tests_dir / "test_api.py").write_text(test_api_content)
        metadata["files"].append("tests/test_api.py")

    elif project_type == "ml":
        # ML tests
        test_ml_content = '''import pytest
import torch
from src.models import create_model
from src.datasets import create_dataset
from omegaconf import OmegaConf


def test_model_creation() -> Any:
    """Test model creation."""
    cfg = OmegaConf.create({
        "name": "resnet",
        "num_classes": 10,
        "pretrained": False,
    })
    model = create_model(cfg)
    assert model is not None

    # Test forward pass
    batch_size = 2
    x = torch.randn(batch_size, 3, 224, 224)
    output = model(x)
    assert output.shape == (batch_size, 10)


def test_dataset_creation() -> Any:
    """Test dataset creation."""
    cfg = OmegaConf.create({
        "name": "dummy",
        "size": 100,
        "num_classes": 10,
    })
    dataset = create_dataset(cfg, split="train")
    assert len(dataset) == 100

    # Test data loading
    data, label = dataset[0]
    assert data.shape == (3, 224, 224)
    assert 0 <= label < 10
'''
        (tests_dir / "test_ml.py").write_text(test_ml_content)
        metadata["files"].append("tests/test_ml.py")

    elif project_type == "library":
        # Library tests
        test_lib_content = f'''import pytest
import json
from pathlib import Path
from {metadata["name"]}.core import process_data, validate_input, load_config, save_results


def test_process_data_basic(sample_data) -> Any:
    """Test basic data processing."""
    result = process_data(sample_data)
    assert result["count"] == len(sample_data)
    assert all(item["processed"] for item in result["items"])
    assert result["version"] == "0.1.0"


def test_process_data_with_config(sample_data) -> Any:
    """Test data processing with configuration."""
    config = {{"option1": "value1", "option2": 42}}
    result = process_data(sample_data, config)
    assert result["config"] == config


def test_validate_input_strings() -> Any:
    """Test string validation."""
    assert validate_input("valid") is True
    assert validate_input("") is False
    assert validate_input("   ") is False
    assert validate_input("short", min_length=10) is False
    assert validate_input("long enough", min_length=5) is True


def test_validate_input_types() -> Any:
    """Test type validation."""
    assert validate_input(123, expected_type=int) is True
    assert validate_input("123", expected_type=int) is False
    assert validate_input([1, 2, 3], expected_type=list) is True
    assert validate_input([], expected_type=list, min_length=1) is False


def test_config_operations(tmp_path) -> Any:
    """Test config loading and saving."""
    config = {{"key": "value", "number": 42}}
    config_path = tmp_path / "config.json"

    # Save config
    config_path.write_text(json.dumps(config))

    # Load config
    loaded = load_config(config_path)
    assert loaded == config

    # Test missing file
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.json")


def test_save_results(tmp_path, sample_data) -> Any:
    """Test saving results."""
    results = process_data(sample_data)
    output_path = tmp_path / "output" / "results.json"

    save_results(results, output_path)

    assert output_path.exists()
    with open(output_path) as f:
        saved = json.load(f)
    assert saved == results
'''
        (tests_dir / "test_core.py").write_text(test_lib_content)
        metadata["files"].append("tests/test_core.py")


def create_docs_structure(project_dir: Path, metadata: dict) -> Any:
    """Create documentation structure."""
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    # index.md
    index_content = f"""# {metadata["name"]} Documentation

Welcome to the {metadata["name"]} documentation.

## Overview

This project was created as a test for DHT (Development Helper Toolkit).

## Quick Start

```bash
# Setup development environment
dhtl setup

# Run tests
dhtl test

# Build the project
dhtl build
```

## Project Structure

```
{metadata["name"]}/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── pyproject.toml # Project configuration
```

## API Reference

See [API documentation](api.md) for detailed API reference.

## Contributing

See [Contributing Guide](contributing.md) for development guidelines.
"""
    (docs_dir / "index.md").write_text(index_content)
    metadata["files"].append("docs/index.md")

    # api.md
    api_content = """# API Reference

## Core Functions

### `process_data(data, config=None)`

Process a list of data items according to configuration.

**Parameters:**
- `data` (List[Dict]): List of data items to process
- `config` (Dict, optional): Configuration dictionary

**Returns:**
- Dict containing processed items and metadata

### `validate_input(value, expected_type=str, min_length=0)`

Validate input value against expected criteria.

**Parameters:**
- `value`: Value to validate
- `expected_type` (type): Expected type of the value
- `min_length` (int): Minimum length for string/list values

**Returns:**
- bool: True if valid, False otherwise
"""
    (docs_dir / "api.md").write_text(api_content)
    metadata["files"].append("docs/api.md")

    # contributing.md
    contributing_content = """# Contributing Guide

## Development Setup

1. Clone the repository
2. Run `dhtl init` to set up the development environment
3. Install pre-commit hooks: `pre-commit install`

## Code Style

- Use Black for Python formatting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for all public functions

## Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Run tests with: `dhtl test`

## Submitting Changes

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request
"""
    (docs_dir / "contributing.md").write_text(contributing_content)
    metadata["files"].append("docs/contributing.md")


def create_ci_structure(project_dir: Path, metadata: dict) -> Any:
    """Create CI/CD configuration files."""
    # GitHub Actions
    workflows_dir = project_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # tests.yml
    tests_workflow = f"""name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{{{ matrix.os }}}}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["{metadata["python_version"]}", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        enable-cache: true

    - name: Set up Python ${{{{ matrix.python-version }}}}
      run: uv python install ${{{{ matrix.python-version }}}}

    - name: Install dependencies
      run: |
        uv venv
        uv sync --all-extras

    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
"""
    (workflows_dir / "tests.yml").write_text(tests_workflow)
    metadata["files"].append(".github/workflows/tests.yml")

    # lint.yml
    lint_workflow = """name: Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v3

    - name: Set up Python
      run: uv python install

    - name: Install dependencies
      run: |
        uv venv
        uv sync --all-extras

    - name: Run ruff
      run: uv run ruff check .

    - name: Run mypy
      run: uv run mypy .

    - name: Check formatting
      run: uv run ruff format --check .
"""
    (workflows_dir / "lint.yml").write_text(lint_workflow)
    metadata["files"].append(".github/workflows/lint.yml")

    # Pre-commit config
    precommit_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
"""
    (project_dir / ".pre-commit-config.yaml").write_text(precommit_content)
    metadata["files"].append(".pre-commit-config.yaml")


def create_temporary_project(
    project_type: str = "simple", project_name: str | None = None, **kwargs
) -> tuple[Path, dict[str, Any]]:
    """
    Create a temporary project for testing.

    Returns:
        Tuple of (project_path, metadata)
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="dht_test_"))

    if project_name is None:
        project_name = f"test_{project_type}_project"

    metadata = create_project_structure(temp_dir, project_type=project_type, project_name=project_name, **kwargs)

    return metadata["root"], metadata


def cleanup_temporary_project(project_path: Path) -> None:
    """Clean up a temporary project directory."""
    if project_path.exists() and str(project_path).startswith(tempfile.gettempdir()):
        shutil.rmtree(project_path)


# Additional utility functions for tests


def run_in_project(project_path: Path, command: str | list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command in a project directory."""
    if isinstance(command, str):
        command = command.split()

    env = os.environ.copy()
    env.update(kwargs.get("env", {}))

    return subprocess.run(
        command,
        cwd=project_path,
        capture_output=True,
        text=True,
        env=env,
        **{k: v for k, v in kwargs.items() if k != "env"},
    )


def assert_project_structure(project_path: Path, expected_files: list[str]) -> None:
    """Assert that a project has the expected file structure."""
    for file_path in expected_files:
        full_path = project_path / file_path
        assert full_path.exists(), f"Expected file not found: {file_path}"


def create_mock_pyproject_toml(
    project_dir: Path,
    name: str = "test-project",
    version: str = "0.1.0",
    python_version: str = "3.10",
    dependencies: list[str] | None = None,
    dev_dependencies: list[str] | None = None,
) -> Path:
    """Create a minimal pyproject.toml for testing."""
    if dependencies is None:
        dependencies = []

    if dev_dependencies is None:
        dev_dependencies = ["pytest>=7.0.0", "ruff>=0.1.0"]

    content = f'''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "{version}"
requires-python = ">={python_version}"
dependencies = {json.dumps(dependencies)}

[project.optional-dependencies]
dev = {json.dumps(dev_dependencies)}
'''

    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_text(content)
    return pyproject_path
