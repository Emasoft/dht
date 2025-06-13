#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_type_detector.py - Comprehensive project type detection and configuration system

This module provides advanced project type detection, configuration generation,
and setup recommendations for various Python frameworks and project types.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of project type detector
# - Added ProjectType and ProjectCategory enums
# - Added comprehensive framework detection logic
# - Added configuration generation for multiple frameworks
# - Added setup recommendations system
# - Added migration detection from other package managers
# - Added support for hybrid projects
# - Integrated with project analyzer and heuristics

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
import logging
from datetime import datetime

from prefect import task, flow

from DHT.modules.project_analyzer import ProjectAnalyzer
from DHT.modules.project_heuristics import ProjectHeuristics


class ProjectType(Enum):
    """Enumeration of supported project types."""
    GENERIC = "generic"
    DJANGO = "django"
    DJANGO_REST = "django_rest_framework"
    FLASK = "flask"
    FASTAPI = "fastapi"
    STREAMLIT = "streamlit"
    GRADIO = "gradio"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    LIBRARY = "library"
    CLI = "cli"
    REACT = "react"
    VUE = "vue"
    HYBRID = "hybrid"


class ProjectCategory(Enum):
    """High-level project categories."""
    UNKNOWN = "unknown"
    WEB_FRAMEWORK = "web_framework"
    WEB_API = "web_api"
    MACHINE_LEARNING = "machine_learning"
    DATA_ANALYSIS = "data_analysis"
    COMMAND_LINE = "command_line"
    PACKAGE = "package"
    FULL_STACK = "full_stack"
    
    def is_web_related(self) -> bool:
        """Check if category is web-related."""
        return self in {
            self.WEB_FRAMEWORK, 
            self.WEB_API, 
            self.FULL_STACK
        }
    
    def is_data_related(self) -> bool:
        """Check if category is data-related."""
        return self in {
            self.MACHINE_LEARNING,
            self.DATA_ANALYSIS
        }
    
    def requires_database(self) -> bool:
        """Check if category typically requires a database."""
        return self in {
            self.WEB_FRAMEWORK,
            self.WEB_API,
            self.FULL_STACK
        }
    
    def requires_gpu_support(self) -> bool:
        """Check if category might need GPU support."""
        return self == self.MACHINE_LEARNING


@dataclass
class ProjectAnalysis:
    """Results of project type analysis."""
    type: ProjectType
    category: ProjectCategory
    confidence: float
    detected_types: List[ProjectType] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    primary_dependencies: List[str] = field(default_factory=list)
    ml_frameworks: List[str] = field(default_factory=list)
    cli_frameworks: List[str] = field(default_factory=list)
    has_notebooks: bool = False
    uses_poetry: bool = False
    uses_pipenv: bool = False
    uses_conda: bool = False
    migration_suggested: bool = False
    migration_paths: List[str] = field(default_factory=list)
    is_publishable: bool = False
    project_path: Optional[Path] = None
    analysis_timestamp: Optional[str] = None


@dataclass
class ValidationResult:
    """Configuration validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""


class FrameworkConfig:
    """Framework-specific configuration templates."""
    
    _configs = {
        ProjectType.DJANGO: {
            "name": "Django",
            "core_dependencies": ["django"],
            "test_dependencies": ["pytest-django", "factory-boy"],
            "type_check_plugins": ["django-stubs", "mypy-django"],
            "default_port": 8000,
            "wsgi_module": "wsgi:application",
            "migration_tool": "django",
            "cache_backend": "redis",
            "db_backend": "postgresql",
        },
        ProjectType.DJANGO_REST: {
            "name": "Django REST Framework",
            "core_dependencies": ["django", "djangorestframework"],
            "test_dependencies": ["pytest-django", "factory-boy", "pytest-mock"],
            "type_check_plugins": ["django-stubs", "mypy-django", "djangorestframework-stubs"],
            "default_port": 8000,
            "wsgi_module": "wsgi:application",
            "migration_tool": "django",
            "cache_backend": "redis",
            "db_backend": "postgresql",
        },
        ProjectType.FASTAPI: {
            "name": "FastAPI",
            "core_dependencies": ["fastapi", "uvicorn", "pydantic"],
            "test_dependencies": ["pytest-asyncio", "httpx"],
            "type_check_plugins": ["pydantic.mypy"],
            "default_port": 8000,
            "asgi_module": "main:app",
            "migration_tool": "alembic",
            "cache_backend": "redis",
            "db_backend": "postgresql",
        },
        ProjectType.FLASK: {
            "name": "Flask",
            "core_dependencies": ["flask"],
            "test_dependencies": ["pytest-flask"],
            "type_check_plugins": [],
            "default_port": 5000,
            "wsgi_module": "app:app",
            "migration_tool": "flask-migrate",
            "cache_backend": "redis",
            "db_backend": "postgresql",
        },
    }
    
    @classmethod
    def get_config(cls, project_type: ProjectType) -> Dict[str, Any]:
        """Get configuration for a project type."""
        base_config = cls._configs.get(project_type, {})
        
        # Handle inheritance (e.g., DRF inherits from Django)
        if project_type == ProjectType.DJANGO_REST:
            django_config = cls._configs[ProjectType.DJANGO].copy()
            django_config.update(base_config)
            # Merge dependencies
            django_config["core_dependencies"] = list(set(
                django_config.get("core_dependencies", []) + 
                base_config.get("core_dependencies", [])
            ))
            django_config["test_dependencies"] = list(set(
                django_config.get("test_dependencies", []) + 
                base_config.get("test_dependencies", [])
            ))
            return type('FrameworkConfig', (), django_config)()
        
        return type('FrameworkConfig', (), base_config)()


class ProjectTypeDetector:
    """
    Advanced project type detection system that analyzes project structure,
    dependencies, and code patterns to determine project type and generate
    appropriate configurations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = ProjectAnalyzer()
        self.heuristics = ProjectHeuristics()
    
    @task
    def analyze(self, project_path: Path) -> ProjectAnalysis:
        """
        Analyze project and detect its type with confidence scoring.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            ProjectAnalysis with detection results
        """
        project_path = Path(project_path)
        
        # Run project analyzer
        analysis_result = self.analyzer.analyze_project(project_path)
        
        # Add project path to analysis result for file access
        analysis_result["project_path"] = str(project_path)
        
        # Run heuristics
        heuristic_result = self.heuristics.analyze(analysis_result)
        
        # Detect project type
        project_type, detected_types = self._detect_project_type(
            analysis_result, heuristic_result
        )
        
        # Determine category
        category = self._determine_category(project_type, detected_types)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            project_type, analysis_result, heuristic_result
        )
        
        # Extract markers
        markers = self._extract_markers(analysis_result, heuristic_result)
        
        # Get primary dependencies
        primary_deps = self._get_primary_dependencies(analysis_result)
        
        # Check for special characteristics
        ml_frameworks = self._detect_ml_frameworks(analysis_result)
        cli_frameworks = self._detect_cli_frameworks(analysis_result)
        has_notebooks = self._has_notebooks(analysis_result)
        
        # Check package managers
        uses_poetry = (project_path / "poetry.lock").exists()
        uses_pipenv = (project_path / "Pipfile.lock").exists()
        uses_conda = (project_path / "environment.yml").exists()
        
        # Check if migration needed
        migration_suggested = uses_poetry or uses_pipenv or uses_conda
        migration_paths = []
        if uses_poetry:
            migration_paths.append("poetry_to_uv")
        if uses_pipenv:
            migration_paths.append("pipenv_to_uv")
        if uses_conda:
            migration_paths.append("conda_to_uv")
        
        # Check if publishable
        is_publishable = self._is_publishable_library(
            project_type, analysis_result
        )
        
        return ProjectAnalysis(
            type=project_type,
            category=category,
            confidence=confidence,
            detected_types=detected_types,
            markers=markers,
            primary_dependencies=primary_deps,
            ml_frameworks=ml_frameworks,
            cli_frameworks=cli_frameworks,
            has_notebooks=has_notebooks,
            uses_poetry=uses_poetry,
            uses_pipenv=uses_pipenv,
            uses_conda=uses_conda,
            migration_suggested=migration_suggested,
            migration_paths=migration_paths,
            is_publishable=is_publishable,
            project_path=project_path,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    @task
    def generate_configurations(
        self, 
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """
        Generate configuration files based on project type.
        
        Args:
            analysis: Project analysis results
            
        Returns:
            Dictionary of filename to file content
        """
        configs = {}
        
        if analysis.type == ProjectType.DJANGO:
            configs.update(self._generate_django_configs(analysis))
        elif analysis.type == ProjectType.FASTAPI:
            configs.update(self._generate_fastapi_configs(analysis))
        elif analysis.type == ProjectType.DATA_SCIENCE:
            configs.update(self._generate_ml_configs(analysis))
        elif analysis.type == ProjectType.LIBRARY:
            configs.update(self._generate_library_configs(analysis))
        elif analysis.type == ProjectType.CLI:
            configs.update(self._generate_cli_configs(analysis))
        
        # Add common configs
        configs.update(self._generate_common_configs(analysis))
        
        return configs
    
    @task
    def get_setup_recommendations(
        self, 
        analysis: ProjectAnalysis
    ) -> Dict[str, Any]:
        """
        Get setup recommendations based on project type.
        
        Args:
            analysis: Project analysis results
            
        Returns:
            Dictionary of recommendations by category
        """
        recommendations = {}
        
        # Database recommendations
        if analysis.category.requires_database():
            recommendations["database"] = {
                "suggested": "postgresql",
                "packages": ["psycopg2-binary"],
                "docker_image": "postgres:15-alpine",
                "env_vars": ["DATABASE_URL", "POSTGRES_PASSWORD"]
            }
        
        # Cache recommendations
        if analysis.type in [ProjectType.DJANGO, ProjectType.FASTAPI]:
            recommendations["cache"] = {
                "suggested": "redis",
                "packages": ["redis", "hiredis"],
                "docker_image": "redis:7-alpine"
            }
        
        # Task queue recommendations
        if analysis.type == ProjectType.DJANGO:
            recommendations["task_queue"] = {
                "suggested": "celery",
                "packages": ["celery", "django-celery-beat"],
                "broker": "redis"
            }
        
        # Testing recommendations
        test_packages = ["pytest", "pytest-cov", "pytest-mock"]
        if analysis.type == ProjectType.DJANGO:
            test_packages.append("pytest-django")
        elif analysis.type == ProjectType.FASTAPI:
            test_packages.extend(["pytest-asyncio", "httpx"])
        
        recommendations["testing"] = {
            "framework": "pytest",
            "packages": test_packages
        }
        
        # ML-specific recommendations
        if analysis.category.is_data_related():
            recommendations["ml_tools"] = {
                "experiment_tracking": "mlflow",
                "data_versioning": "dvc",
                "gpu_support": analysis.category.requires_gpu_support()
            }
        
        # Project structure recommendations
        if analysis.type == ProjectType.GENERIC:
            recommendations["project_structure"] = {
                "actions": [
                    "Choose a project type",
                    "Add framework-specific structure",
                    "Create proper package layout"
                ]
            }
        
        return recommendations
    
    @task
    def validate_configurations(
        self,
        configs: Dict[str, str],
        analysis: ProjectAnalysis
    ) -> ValidationResult:
        """
        Validate generated configurations.
        
        Args:
            configs: Generated configuration files
            analysis: Project analysis results
            
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Validate required files exist
        if analysis.type == ProjectType.DJANGO:
            if "pyproject.toml" not in configs:
                errors.append("Missing pyproject.toml for Django project")
            if ".env.example" not in configs:
                warnings.append("Missing .env.example file")
        
        # Validate Docker configs for API projects
        if analysis.category == ProjectCategory.WEB_API:
            if "Dockerfile" not in configs:
                warnings.append("API project should have Dockerfile")
        
        # More validation logic...
        
        is_valid = len(errors) == 0
        summary = "All configurations valid" if is_valid else f"{len(errors)} errors found"
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            summary=summary
        )
    
    def _detect_project_type(
        self,
        analysis_result: Dict[str, Any],
        heuristic_result: Dict[str, Any]
    ) -> Tuple[ProjectType, List[ProjectType]]:
        """Detect project type from analysis results."""
        detected_types = []
        
        # Get primary type from heuristics
        primary_type = heuristic_result["project_type"]["primary_type"]
        
        # Map heuristic types to our enum
        type_mapping = {
            "django": ProjectType.DJANGO,
            "flask": ProjectType.FLASK,
            "fastapi": ProjectType.FASTAPI,
            "streamlit": ProjectType.STREAMLIT,
            "generic": ProjectType.GENERIC
        }
        
        project_type = type_mapping.get(primary_type, ProjectType.GENERIC)
        detected_types.append(project_type)
        
        # Check for additional types
        file_analysis = analysis_result.get("file_analysis", {})
        
        # Check for React/Vue
        for file_path, file_data in file_analysis.items():
            if "package.json" in file_path:
                # The analyzer might have already parsed it
                if "parsed_content" in file_data:
                    pkg = file_data["parsed_content"]
                    deps = pkg.get("dependencies", {})
                    if "react" in deps:
                        detected_types.append(ProjectType.REACT)
                    if "vue" in deps:
                        detected_types.append(ProjectType.VUE)
                else:
                    # Try to read the actual file
                    try:
                        full_path = Path(analysis_result.get("project_path", ".")) / file_path
                        if full_path.exists():
                            with open(full_path, 'r') as f:
                                pkg = json.load(f)
                                deps = pkg.get("dependencies", {})
                                if "react" in deps:
                                    detected_types.append(ProjectType.REACT)
                                if "vue" in deps:
                                    detected_types.append(ProjectType.VUE)
                    except Exception:
                        pass
        
        # Check for Django REST
        deps = self._get_all_dependencies(analysis_result)
        if "djangorestframework" in deps and project_type == ProjectType.DJANGO:
            project_type = ProjectType.DJANGO_REST
        
        # Check for ML/DS
        characteristics = heuristic_result["project_type"].get("characteristics", [])
        if "data_science" in characteristics:
            if project_type == ProjectType.GENERIC:
                project_type = ProjectType.DATA_SCIENCE
            detected_types.append(ProjectType.DATA_SCIENCE)
        
        # Check for library
        if "library" in characteristics and project_type == ProjectType.GENERIC:
            project_type = ProjectType.LIBRARY
            detected_types.append(ProjectType.LIBRARY)
        
        # Check for CLI
        if "cli" in characteristics:
            if project_type == ProjectType.GENERIC:
                project_type = ProjectType.CLI
            detected_types.append(ProjectType.CLI)
        
        # Handle hybrid projects
        if len(detected_types) > 1 and ProjectType.GENERIC not in detected_types:
            # Django + React = Full stack
            if (ProjectType.DJANGO in detected_types and 
                (ProjectType.REACT in detected_types or ProjectType.VUE in detected_types)):
                project_type = ProjectType.HYBRID
        
        return project_type, detected_types
    
    def _determine_category(
        self,
        project_type: ProjectType,
        detected_types: List[ProjectType]
    ) -> ProjectCategory:
        """Determine project category from type."""
        if project_type == ProjectType.HYBRID:
            return ProjectCategory.FULL_STACK
        
        category_mapping = {
            ProjectType.DJANGO: ProjectCategory.WEB_FRAMEWORK,
            ProjectType.DJANGO_REST: ProjectCategory.WEB_API,
            ProjectType.FLASK: ProjectCategory.WEB_FRAMEWORK,
            ProjectType.FASTAPI: ProjectCategory.WEB_API,
            ProjectType.STREAMLIT: ProjectCategory.DATA_ANALYSIS,
            ProjectType.DATA_SCIENCE: ProjectCategory.MACHINE_LEARNING,
            ProjectType.MACHINE_LEARNING: ProjectCategory.MACHINE_LEARNING,
            ProjectType.CLI: ProjectCategory.COMMAND_LINE,
            ProjectType.LIBRARY: ProjectCategory.PACKAGE,
        }
        
        return category_mapping.get(project_type, ProjectCategory.UNKNOWN)
    
    def _calculate_confidence(
        self,
        project_type: ProjectType,
        analysis_result: Dict[str, Any],
        heuristic_result: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for detection."""
        base_confidence = heuristic_result["project_type"]["confidence"]
        
        # Adjust based on markers found
        markers = 0
        structure = analysis_result.get("structure", {})
        file_paths = list(analysis_result.get("file_analysis", {}).keys())
        
        if project_type == ProjectType.DJANGO:
            # Check for Django-specific files
            entry_points = structure.get("entry_points", [])
            if any("manage.py" in str(ep) for ep in entry_points):
                markers += 2  # manage.py is a strong indicator
                
            # Also check in project structure for Django detection
            frameworks = analysis_result.get("frameworks", [])
            if "django" in frameworks:
                markers += 3  # Framework was detected by analyzer
            
            # Check for Django files
            if any("settings.py" in f for f in file_paths):
                markers += 1
            if any("urls.py" in f for f in file_paths):
                markers += 1
            if any("models.py" in f for f in file_paths):
                markers += 1
            if any("manage.py" in f for f in file_paths):
                markers += 2  # manage.py presence
            
            # Check for Django in dependencies
            deps = self._get_all_dependencies(analysis_result)
            if any("django" in d.lower() for d in deps):
                markers += 2
                
        elif project_type == ProjectType.FASTAPI:
            # Check for FastAPI markers
            if any("main.py" in f or "app.py" in f for f in file_paths):
                markers += 2
            if any("routers" in f for f in file_paths):
                markers += 1
            if any("models" in f for f in file_paths):
                markers += 1
                
            # Check dependencies
            deps = self._get_all_dependencies(analysis_result)
            if any("fastapi" in d.lower() for d in deps):
                markers += 3
            if any("uvicorn" in d.lower() for d in deps):
                markers += 1
                
        elif project_type == ProjectType.DATA_SCIENCE:
            # Check for data science markers
            characteristics = heuristic_result["project_type"].get("characteristics", [])
            if "data_science" in characteristics:
                markers += 3
            if "notebooks" in characteristics:
                markers += 2
                
            # Check for ML frameworks
            deps = self._get_all_dependencies(analysis_result)
            ml_deps = {"tensorflow", "torch", "pytorch", "sklearn", "scikit-learn", "keras"}
            for dep in deps:
                if any(ml in dep.lower() for ml in ml_deps):
                    markers += 1
                    
            # Check for data directories
            if any("data" in str(f) for f in file_paths):
                markers += 1
            if any("models" in str(f) for f in file_paths):
                markers += 1
            if any("notebooks" in str(f) for f in file_paths):
                markers += 1
        
        # Boost confidence based on markers
        # Each marker adds 0.1, with more weight for critical markers
        confidence_boost = min(markers * 0.1, 0.5)
        
        # For well-known frameworks with many markers, set minimum confidence
        if markers >= 4 and project_type in [ProjectType.DJANGO, ProjectType.FASTAPI]:
            return max(0.9, base_confidence + confidence_boost)
        elif markers >= 3 and project_type == ProjectType.DATA_SCIENCE:
            return max(0.85, base_confidence + confidence_boost)
        
        return min(base_confidence + confidence_boost, 1.0)
    
    def _extract_markers(
        self,
        analysis_result: Dict[str, Any],
        heuristic_result: Dict[str, Any]
    ) -> List[str]:
        """Extract project markers."""
        markers = []
        
        # Get entry points
        structure = analysis_result.get("structure", {})
        entry_points = structure.get("entry_points", [])
        markers.extend(entry_points)
        
        # Get framework matches from heuristics
        frameworks = heuristic_result["project_type"].get("frameworks", {})
        for framework, info in frameworks.items():
            markers.extend(info.get("matches", []))
        
        return list(set(markers))
    
    def _get_primary_dependencies(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Get primary project dependencies."""
        deps = self._get_all_dependencies(analysis_result)
        
        # Filter to primary/framework dependencies
        primary = []
        framework_deps = {
            "django", "flask", "fastapi", "streamlit",
            "gradio", "uvicorn", "gunicorn", "celery"
        }
        
        for dep in deps:
            dep_lower = dep.lower()
            if any(fw in dep_lower for fw in framework_deps):
                primary.append(dep)
        
        return primary
    
    def _get_all_dependencies(
        self,
        analysis_result: Dict[str, Any]
    ) -> Set[str]:
        """Get all project dependencies."""
        deps = set()
        
        dep_data = analysis_result.get("dependencies", {})
        for lang, lang_deps in dep_data.items():
            if isinstance(lang_deps, dict):
                deps.update(lang_deps.get("all", []))
                deps.update(lang_deps.get("runtime", []))
                deps.update(lang_deps.get("dev", []))
        
        return deps
    
    def _detect_ml_frameworks(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Detect machine learning frameworks."""
        ml_frameworks = []
        deps = self._get_all_dependencies(analysis_result)
        
        framework_names = {
            "tensorflow", "torch", "pytorch", "keras",
            "scikit-learn", "sklearn", "xgboost", "lightgbm"
        }
        
        for dep in deps:
            dep_lower = dep.lower()
            for fw in framework_names:
                if fw in dep_lower:
                    ml_frameworks.append(dep)
                    break
        
        return list(set(ml_frameworks))
    
    def _detect_cli_frameworks(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Detect CLI frameworks."""
        cli_frameworks = []
        deps = self._get_all_dependencies(analysis_result)
        
        cli_names = {"click", "typer", "fire", "argparse"}
        
        for dep in deps:
            dep_lower = dep.lower()
            if dep_lower in cli_names:
                cli_frameworks.append(dep)
        
        # Also check imports
        for file_data in analysis_result.get("file_analysis", {}).values():
            for imp in file_data.get("imports", []):
                module = imp.get("module", "") if isinstance(imp, dict) else str(imp)
                if module in cli_names:
                    cli_frameworks.append(module)
        
        return list(set(cli_frameworks))
    
    def _has_notebooks(self, analysis_result: Dict[str, Any]) -> bool:
        """Check if project has Jupyter notebooks."""
        # Check in file analysis
        for file_path in analysis_result.get("file_analysis", {}):
            if file_path.endswith(".ipynb"):
                return True
                
        # Also check in all collected files
        files = analysis_result.get("files", [])
        for file_info in files:
            if isinstance(file_info, dict) and file_info.get("path", "").endswith(".ipynb"):
                return True
            elif isinstance(file_info, str) and file_info.endswith(".ipynb"):
                return True
                
        # Check in project path if we have it
        project_path = analysis_result.get("project_path")
        if project_path:
            project_dir = Path(project_path)
            if project_dir.exists():
                for ipynb in project_dir.rglob("*.ipynb"):
                    return True
                    
        return False
    
    def _is_publishable_library(
        self,
        project_type: ProjectType,
        analysis_result: Dict[str, Any]
    ) -> bool:
        """Check if project is a publishable library."""
        if project_type != ProjectType.LIBRARY:
            return False
        
        # Check for package metadata
        has_pyproject = any(
            "pyproject.toml" in f 
            for f in analysis_result.get("file_analysis", {})
        )
        has_setup = any(
            "setup.py" in f or "setup.cfg" in f
            for f in analysis_result.get("file_analysis", {})
        )
        
        return has_pyproject or has_setup
    
    def _generate_django_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate Django-specific configurations."""
        configs = {}
        
        # pyproject.toml
        configs["pyproject.toml"] = """[tool.django]
settings_module = "mysite.settings"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "mysite.settings"
python_files = ["test_*.py", "*_test.py", "tests.py"]
addopts = "--reuse-db --nomigrations"

[tool.coverage.run]
source = ["."]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/venv/*",
    "manage.py",
]

[tool.mypy]
plugins = ["mypy_django_plugin.main"]

[tool.djlint]
profile = "django"
"""
        
        # .env.example
        configs[".env.example"] = """# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis cache
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
"""
        
        # .pre-commit-config.yaml
        configs[".pre-commit-config.yaml"] = """repos:
  - repo: https://github.com/adamchainz/django-upgrade
    rev: 1.15.0
    hooks:
      - id: django-upgrade
        args: [--target-version, "4.2"]
  
  - repo: https://github.com/rtts/djhtml
    rev: 3.0.6
    hooks:
      - id: djhtml
      - id: djcss
      - id: djjs
"""
        
        return configs
    
    def _generate_fastapi_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate FastAPI-specific configurations."""
        configs = {}
        
        # Dockerfile
        configs["Dockerfile"] = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        # docker-compose.yml
        configs["docker-compose.yml"] = """version: "3.9"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
"""
        
        # alembic.ini
        configs["alembic.ini"] = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
"""
        
        return configs
    
    def _generate_ml_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate ML/Data Science configurations."""
        configs = {}
        
        # DVC config
        configs[".dvc/config"] = """[core]
    remote = storage
    autostage = true

['remote "storage"']
    url = s3://my-bucket/dvc-storage
"""
        
        # MLflow config
        configs["mlflow.yaml"] = """# MLflow configuration
artifact_location: ./mlruns
backend_store_uri: sqlite:///mlflow.db
default_artifact_root: ./mlruns
"""
        
        # Jupyter config
        configs[".jupyter/jupyter_notebook_config.py"] = """c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.open_browser = False
c.NotebookApp.port = 8888
"""
        
        return configs
    
    def _generate_library_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate library project configurations."""
        configs = {}
        
        # Add library-specific configs
        configs["setup.cfg"] = """[metadata]
name = my-library
version = attr: my_library.__version__

[options]
packages = find:
python_requires = >=3.8

[options.packages.find]
where = src
"""
        
        return configs
    
    def _generate_cli_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate CLI project configurations."""
        configs = {}
        
        # Add CLI-specific configs
        if "click" in analysis.cli_frameworks:
            configs["setup.py"] = """from setuptools import setup, find_packages

setup(
    name="my-cli",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mycli=cli:main',
        ],
    },
)
"""
        
        return configs
    
    def _generate_common_configs(
        self,
        analysis: ProjectAnalysis
    ) -> Dict[str, str]:
        """Generate common configuration files."""
        configs = {}
        
        # Common .gitignore
        if analysis.category.is_data_related():
            configs[".gitignore"] = """# Data files
*.csv
*.h5
*.pkl
*.model
data/
models/
mlruns/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/
"""
        
        return configs


@flow(name="detect_and_configure_project")
def detect_and_configure_project(project_path: Path) -> Tuple[ProjectAnalysis, Dict[str, str]]:
    """
    Complete flow for project detection and configuration generation.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Tuple of analysis results and generated configurations
    """
    detector = ProjectTypeDetector()
    
    # Analyze project
    analysis = detector.analyze(project_path)
    
    # Generate configurations
    configs = detector.generate_configurations(analysis)
    
    # Validate configurations
    validation = detector.validate_configurations(configs, analysis)
    
    if not validation.is_valid:
        logger = logging.getLogger(__name__)
        for error in validation.errors:
            logger.error(f"Configuration error: {error}")
    
    return analysis, configs