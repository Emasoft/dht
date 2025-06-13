#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
framework_configs.py - Framework-specific configuration templates

This module contains configuration templates and metadata for various
Python frameworks supported by DHT.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains FrameworkConfig class with framework metadata
# - Provides centralized framework configuration access
#

from typing import Dict, Any

from DHT.modules.project_type_enums import ProjectType


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
        ProjectType.STREAMLIT: {
            "name": "Streamlit",
            "core_dependencies": ["streamlit"],
            "test_dependencies": ["pytest"],
            "type_check_plugins": [],
            "default_port": 8501,
            "entry_point": "streamlit_app.py",
            "cache_backend": "file",
            "db_backend": "sqlite",
        },
        ProjectType.GRADIO: {
            "name": "Gradio",
            "core_dependencies": ["gradio"],
            "test_dependencies": ["pytest"],
            "type_check_plugins": [],
            "default_port": 7860,
            "entry_point": "app.py",
            "cache_backend": "file",
            "db_backend": "sqlite",
        },
        ProjectType.DATA_SCIENCE: {
            "name": "Data Science",
            "core_dependencies": ["pandas", "numpy", "matplotlib", "seaborn", "jupyter"],
            "test_dependencies": ["pytest", "pytest-cov"],
            "type_check_plugins": [],
            "notebook_kernel": "python3",
            "common_tools": ["scikit-learn", "statsmodels", "plotly"],
        },
        ProjectType.MACHINE_LEARNING: {
            "name": "Machine Learning",
            "core_dependencies": ["numpy", "pandas", "scikit-learn"],
            "test_dependencies": ["pytest", "pytest-cov"],
            "type_check_plugins": [],
            "ml_frameworks": ["tensorflow", "torch", "xgboost", "lightgbm"],
            "experiment_tracking": ["mlflow", "wandb", "tensorboard"],
        },
        ProjectType.LIBRARY: {
            "name": "Python Library",
            "core_dependencies": [],
            "test_dependencies": ["pytest", "pytest-cov", "tox"],
            "type_check_plugins": [],
            "build_system": "setuptools",
            "distribution": "pypi",
        },
        ProjectType.CLI: {
            "name": "Command Line Interface",
            "core_dependencies": ["click"],
            "test_dependencies": ["pytest", "pytest-click"],
            "type_check_plugins": [],
            "entry_point": "console_scripts",
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