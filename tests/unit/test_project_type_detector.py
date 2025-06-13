#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for project type detection system.

Tests comprehensive project type detection, configuration generation,
and framework-specific setup recommendations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for project type detector
# - Added tests for detection accuracy and confidence scoring
# - Added tests for configuration generation
# - Added tests for setup recommendations
# - Added tests for migration detection
# - Added tests for hybrid project support

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from DHT.modules.project_type_detector import (
    ProjectTypeDetector, ProjectType, ProjectCategory, FrameworkConfig
)


class TestProjectTypeDetector:
    """Test the project type detection system."""
    
    @pytest.fixture
    def detector(self):
        """Create a project type detector instance."""
        return ProjectTypeDetector()
    
    @pytest.fixture
    def django_project(self, tmp_path):
        """Create a Django project structure."""
        project_dir = tmp_path / "django_project"
        project_dir.mkdir()
        
        # Django markers
        (project_dir / "manage.py").write_text("""
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
""")
        
        # Settings file
        settings_dir = project_dir / "mysite"
        settings_dir.mkdir()
        (settings_dir / "settings.py").write_text("""
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'myapp',
]
""")
        
        # URLs
        (settings_dir / "urls.py").write_text("""
from django.urls import path, include
urlpatterns = []
""")
        
        # App
        app_dir = project_dir / "myapp"
        app_dir.mkdir()
        (app_dir / "models.py").write_text("""
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
""")
        
        # Templates
        templates_dir = project_dir / "templates"
        templates_dir.mkdir()
        
        # Requirements
        (project_dir / "requirements.txt").write_text("""
Django>=4.2,<5.0
psycopg2-binary>=2.9
celery>=5.3
redis>=4.5
""")
        
        return project_dir
    
    @pytest.fixture
    def fastapi_project(self, tmp_path):
        """Create a FastAPI project structure."""
        project_dir = tmp_path / "fastapi_project"
        project_dir.mkdir()
        
        # Main app
        (project_dir / "main.py").write_text("""
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items/")
async def create_item(item: Item):
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
        
        # Routers
        routers_dir = project_dir / "routers"
        routers_dir.mkdir()
        (routers_dir / "users.py").write_text("""
from fastapi import APIRouter
router = APIRouter()
""")
        
        # Models
        models_dir = project_dir / "models"
        models_dir.mkdir()
        (models_dir / "user.py").write_text("""
from pydantic import BaseModel
class User(BaseModel):
    id: int
    name: str
""")
        
        # pyproject.toml
        (project_dir / "pyproject.toml").write_text("""
[project]
name = "fastapi-app"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]
""")
        
        return project_dir
    
    @pytest.fixture
    def ml_project(self, tmp_path):
        """Create a machine learning project structure."""
        project_dir = tmp_path / "ml_project"
        project_dir.mkdir()
        
        # Notebooks
        notebooks_dir = project_dir / "notebooks"
        notebooks_dir.mkdir()
        (notebooks_dir / "analysis.ipynb").write_text('{"cells": []}')
        
        # Source code
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "train.py").write_text("""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
import torch
""")
        
        # Data directory
        (project_dir / "data").mkdir()
        (project_dir / "models").mkdir()
        
        # Requirements
        (project_dir / "requirements.txt").write_text("""
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
tensorflow>=2.13
torch>=2.0
matplotlib>=3.7
jupyterlab>=4.0
""")
        
        return project_dir
    
    def test_detect_django_project(self, detector, django_project):
        """Test Django project detection with high confidence."""
        # Debug: Print the created structure
        print(f"\nDjango project path: {django_project}")
        print("Files created:")
        for file in django_project.rglob("*"):
            if file.is_file():
                print(f"  - {file.relative_to(django_project)}")
        
        result = detector.analyze(django_project)
        
        # Debug: Print analysis results
        print(f"\nAnalysis result:")
        print(f"  Type: {result.type}")
        print(f"  Category: {result.category}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Detected types: {result.detected_types}")
        print(f"  Markers: {result.markers}")
        print(f"  Primary dependencies: {result.primary_dependencies}")
        
        assert result.type == ProjectType.DJANGO
        assert result.category == ProjectCategory.WEB_FRAMEWORK
        assert result.confidence >= 0.9
        assert "import:django" in result.markers or "file:manage.py" in result.markers
        assert any("django" in d.lower() for d in result.primary_dependencies)
    
    def test_detect_fastapi_project(self, detector, fastapi_project):
        """Test FastAPI project detection."""
        result = detector.analyze(fastapi_project)
        
        assert result.type == ProjectType.FASTAPI
        assert result.category == ProjectCategory.WEB_API
        assert result.confidence > 0.7
        assert "fastapi" in result.primary_dependencies
        assert "uvicorn" in result.primary_dependencies
    
    def test_detect_ml_project(self, detector, ml_project):
        """Test machine learning project detection."""
        result = detector.analyze(ml_project)
        
        assert result.type == ProjectType.DATA_SCIENCE
        assert result.category == ProjectCategory.MACHINE_LEARNING
        assert result.confidence > 0.8
        assert result.has_notebooks
        assert "tensorflow" in result.ml_frameworks
        assert "torch" in result.ml_frameworks
    
    def test_generate_django_config(self, detector, django_project):
        """Test Django configuration generation."""
        analysis = detector.analyze(django_project)
        configs = detector.generate_configurations(analysis)
        
        # Check pyproject.toml generation
        assert "pyproject.toml" in configs
        pyproject = configs["pyproject.toml"]
        assert "[tool.django]" in pyproject
        assert "[tool.pytest.ini_options]" in pyproject
        assert "DJANGO_SETTINGS_MODULE" in pyproject
        
        # Check .env.example
        assert ".env.example" in configs
        env_example = configs[".env.example"]
        assert "SECRET_KEY=" in env_example
        assert "DATABASE_URL=" in env_example
        
        # Check pre-commit config
        assert ".pre-commit-config.yaml" in configs
        precommit = configs[".pre-commit-config.yaml"]
        assert "django-upgrade" in precommit
    
    def test_generate_fastapi_config(self, detector, fastapi_project):
        """Test FastAPI configuration generation."""
        analysis = detector.analyze(fastapi_project)
        configs = detector.generate_configurations(analysis)
        
        # Check Docker configuration
        assert "Dockerfile" in configs
        dockerfile = configs["Dockerfile"]
        assert "FROM python:3.11-slim" in dockerfile
        # Check for uvicorn command in CMD format
        assert "uvicorn" in dockerfile and "main:app" in dockerfile
        
        # Check docker-compose
        assert "docker-compose.yml" in configs
        compose = configs["docker-compose.yml"]
        assert "services:" in compose
        assert "redis:" in compose  # For caching
        
        # Check alembic config
        assert "alembic.ini" in configs
    
    def test_generate_ml_config(self, detector, ml_project):
        """Test ML project configuration generation."""
        analysis = detector.analyze(ml_project)
        configs = detector.generate_configurations(analysis)
        
        # Check DVC config
        assert ".dvc/config" in configs
        dvc_config = configs[".dvc/config"]
        assert "[core]" in dvc_config
        assert "remote = storage" in dvc_config
        
        # Check MLflow config
        assert "mlflow.yaml" in configs
        
        # Check notebook config
        assert ".jupyter/jupyter_notebook_config.py" in configs
    
    def test_detect_hybrid_project(self, detector, tmp_path):
        """Test detection of projects with multiple frameworks."""
        project_dir = tmp_path / "hybrid_project"
        project_dir.mkdir()
        
        # Django backend setup
        (project_dir / "manage.py").write_text("""
#!/usr/bin/env python
import os
import sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
""")
        
        # Create backend directory with Django files
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()
        (backend_dir / "settings.py").write_text("INSTALLED_APPS = ['django.contrib.admin']")
        (backend_dir / "urls.py").write_text("urlpatterns = []")
        
        # Django requirements
        (project_dir / "requirements.txt").write_text("Django>=4.2\n")
        
        # React frontend setup
        (project_dir / "package.json").write_text("""
{
    "name": "frontend",
    "dependencies": {
        "react": "^18.0.0",
        "next": "^13.0.0"
    }
}
""")
        
        result = detector.analyze(project_dir)
        
        assert result.type == ProjectType.HYBRID
        assert ProjectType.DJANGO in result.detected_types
        assert ProjectType.REACT in result.detected_types
        assert result.category == ProjectCategory.FULL_STACK
    
    def test_migration_detection(self, detector, tmp_path):
        """Test detection of projects needing migration."""
        project_dir = tmp_path / "poetry_project"
        project_dir.mkdir()
        
        # Poetry project
        (project_dir / "pyproject.toml").write_text("""
[tool.poetry]
name = "my-app"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.10"
django = "^4.0"
""")
        (project_dir / "poetry.lock").touch()
        
        result = detector.analyze(project_dir)
        
        assert result.uses_poetry
        assert result.migration_suggested
        assert "poetry_to_uv" in result.migration_paths
    
    def test_setup_recommendations(self, detector, django_project):
        """Test project setup recommendations."""
        analysis = detector.analyze(django_project)
        recommendations = detector.get_setup_recommendations(analysis)
        
        assert "database" in recommendations
        assert recommendations["database"]["suggested"] == "postgresql"
        assert recommendations["database"]["packages"] == ["psycopg2-binary"]
        
        assert "cache" in recommendations
        assert recommendations["cache"]["suggested"] == "redis"
        
        assert "task_queue" in recommendations
        assert recommendations["task_queue"]["suggested"] == "celery"
        
        assert "testing" in recommendations
        assert "pytest-django" in recommendations["testing"]["packages"]
    
    def test_cli_detection(self, detector, tmp_path):
        """Test CLI application detection."""
        project_dir = tmp_path / "cli_app"
        project_dir.mkdir()
        
        (project_dir / "cli.py").write_text("""
import click
import typer

@click.command()
def main():
    pass

app = typer.Typer()
""")
        
        (project_dir / "setup.py").write_text("""
setup(
    entry_points={
        'console_scripts': [
            'myapp=cli:main',
        ],
    },
)
""")
        
        result = detector.analyze(project_dir)
        
        assert result.type == ProjectType.CLI
        assert result.category == ProjectCategory.COMMAND_LINE
        assert "click" in result.cli_frameworks
        assert "typer" in result.cli_frameworks
    
    def test_library_detection(self, detector, tmp_path):
        """Test library project detection."""
        project_dir = tmp_path / "my_library"
        project_dir.mkdir()
        
        (project_dir / "pyproject.toml").write_text("""
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-awesome-lib"
version = "0.1.0"
description = "An awesome library"
""")
        
        (project_dir / "src" / "my_awesome_lib").mkdir(parents=True)
        (project_dir / "src" / "my_awesome_lib" / "__init__.py").touch()
        
        # No web framework or CLI
        
        result = detector.analyze(project_dir)
        
        assert result.type == ProjectType.LIBRARY
        assert result.category == ProjectCategory.PACKAGE
        assert result.is_publishable
    
    def test_minimal_project_handling(self, detector, tmp_path):
        """Test detection of minimal/new projects."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        
        # Just a single Python file
        (project_dir / "main.py").write_text("print('Hello')")
        
        result = detector.analyze(project_dir)
        
        assert result.type == ProjectType.GENERIC
        assert result.category == ProjectCategory.UNKNOWN
        assert result.confidence < 0.5
        
        recommendations = detector.get_setup_recommendations(result)
        assert "project_structure" in recommendations
        assert "Choose a project type" in recommendations["project_structure"]["actions"]
    
    def test_confidence_scoring(self, detector, django_project):
        """Test confidence scoring accuracy."""
        # Full Django project should have high confidence
        result = detector.analyze(django_project)
        assert result.confidence >= 0.9
        
        # Remove some files to lower confidence
        (django_project / "manage.py").unlink()
        result2 = detector.analyze(django_project)
        assert 0.6 < result2.confidence <= 0.9
        
        # Remove more files
        (django_project / "mysite" / "urls.py").unlink()
        result3 = detector.analyze(django_project)
        assert result3.confidence <= 0.6
    
    def test_config_validation(self, detector, fastapi_project):
        """Test configuration validation."""
        analysis = detector.analyze(fastapi_project)
        configs = detector.generate_configurations(analysis)
        
        # Validate generated configs
        validation = detector.validate_configurations(configs, analysis)
        
        assert validation.is_valid
        assert len(validation.errors) == 0
        assert "All configurations valid" in validation.summary
    
    def test_incremental_detection(self, detector, tmp_path):
        """Test incremental project type detection."""
        project_dir = tmp_path / "evolving_project"
        project_dir.mkdir()
        
        # Start with generic Python
        (project_dir / "main.py").write_text("print('Hello')")
        result1 = detector.analyze(project_dir)
        assert result1.type == ProjectType.GENERIC
        
        # Add FastAPI
        (project_dir / "main.py").write_text("""
from fastapi import FastAPI
app = FastAPI()
""")
        result2 = detector.analyze(project_dir)
        assert result2.type == ProjectType.FASTAPI
        
        # Add Django too
        (project_dir / "manage.py").touch()
        result3 = detector.analyze(project_dir)
        assert result3.type == ProjectType.HYBRID


class TestFrameworkConfig:
    """Test framework configuration templates."""
    
    def test_django_framework_config(self):
        """Test Django framework configuration."""
        config = FrameworkConfig.get_config(ProjectType.DJANGO)
        
        assert config.name == "Django"
        assert "pytest-django" in config.test_dependencies
        assert "mypy-django" in config.type_check_plugins
        assert config.default_port == 8000
        assert config.wsgi_module == "wsgi:application"
    
    def test_fastapi_framework_config(self):
        """Test FastAPI framework configuration."""
        config = FrameworkConfig.get_config(ProjectType.FASTAPI)
        
        assert config.name == "FastAPI"
        assert config.asgi_module == "main:app"
        assert config.default_port == 8000
        assert "alembic" in config.migration_tool
    
    def test_config_inheritance(self):
        """Test configuration inheritance for related frameworks."""
        django_config = FrameworkConfig.get_config(ProjectType.DJANGO)
        drf_config = FrameworkConfig.get_config(ProjectType.DJANGO_REST)
        
        # DRF should inherit Django configs
        # Check that DRF has all Django test dependencies
        django_test_deps = set(django_config.test_dependencies)
        drf_test_deps = set(drf_config.test_dependencies)
        assert django_test_deps.issubset(drf_test_deps)
        assert "djangorestframework" in drf_config.core_dependencies


class TestProjectCategory:
    """Test project category classification."""
    
    def test_category_properties(self):
        """Test category properties and methods."""
        web_category = ProjectCategory.WEB_FRAMEWORK
        
        assert web_category.is_web_related()
        assert not web_category.is_data_related()
        assert web_category.requires_database()
        
        ml_category = ProjectCategory.MACHINE_LEARNING
        
        assert ml_category.is_data_related()
        assert ml_category.requires_gpu_support()
        assert not ml_category.is_web_related()