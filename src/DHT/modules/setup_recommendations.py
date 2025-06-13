#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_recommendations.py - Project setup recommendations

This module provides recommendations for setting up different types of projects,
including database, cache, testing, and tool configurations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from project_type_detector.py to reduce file size
# - Contains setup recommendation logic for various project types
#

from typing import Dict, Any

from DHT.modules.project_analysis_models import ProjectAnalysis
from DHT.modules.project_type_enums import ProjectType, ProjectCategory


def get_setup_recommendations(analysis: ProjectAnalysis) -> Dict[str, Any]:
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
    
    # Development tools recommendations
    recommendations["development_tools"] = get_dev_tools_recommendations(analysis)
    
    # CI/CD recommendations
    recommendations["ci_cd"] = get_ci_cd_recommendations(analysis)
    
    # Documentation recommendations
    recommendations["documentation"] = get_documentation_recommendations(analysis)
    
    return recommendations


def get_dev_tools_recommendations(analysis: ProjectAnalysis) -> Dict[str, Any]:
    """Get development tools recommendations."""
    tools = {
        "linters": ["ruff", "mypy"],
        "formatters": ["black", "isort"],
        "pre_commit_hooks": ["pre-commit"],
    }
    
    # Add type checking plugins
    if analysis.type == ProjectType.DJANGO:
        tools["type_plugins"] = ["django-stubs", "mypy-django"]
    elif analysis.type == ProjectType.DJANGO_REST:
        tools["type_plugins"] = ["django-stubs", "mypy-django", "djangorestframework-stubs"]
    elif analysis.type == ProjectType.FASTAPI:
        tools["type_plugins"] = ["pydantic.mypy"]
    
    # Add framework-specific tools
    if analysis.type in [ProjectType.DJANGO, ProjectType.DJANGO_REST]:
        tools["django_tools"] = ["django-debug-toolbar", "django-extensions"]
    
    return tools


def get_ci_cd_recommendations(analysis: ProjectAnalysis) -> Dict[str, Any]:
    """Get CI/CD recommendations."""
    ci_cd = {
        "github_actions": {
            "workflows": ["tests", "linting", "type-checking"],
            "matrix_testing": ["3.8", "3.9", "3.10", "3.11"],
        }
    }
    
    # Add deployment recommendations
    if analysis.category == ProjectCategory.WEB_API:
        ci_cd["deployment"] = {
            "platforms": ["Heroku", "Railway", "Fly.io"],
            "containerization": "Docker",
            "orchestration": "Kubernetes (for scale)"
        }
    elif analysis.category == ProjectCategory.WEB_FRAMEWORK:
        ci_cd["deployment"] = {
            "platforms": ["Vercel", "Netlify", "Railway"],
            "static_hosting": "GitHub Pages (for docs)"
        }
    
    # Add release recommendations
    if analysis.is_publishable:
        ci_cd["release"] = {
            "pypi": {
                "tools": ["twine", "build"],
                "workflow": "publish-to-pypi"
            },
            "versioning": "semantic-release"
        }
    
    return ci_cd


def get_documentation_recommendations(analysis: ProjectAnalysis) -> Dict[str, Any]:
    """Get documentation recommendations."""
    docs = {
        "readme": {
            "sections": [
                "Project Description",
                "Installation",
                "Usage",
                "Development",
                "Contributing",
                "License"
            ]
        }
    }
    
    # Add API documentation for web projects
    if analysis.category in [ProjectCategory.WEB_API, ProjectCategory.WEB_FRAMEWORK]:
        docs["api_docs"] = {
            "tools": ["Sphinx", "MkDocs"],
            "api_spec": "OpenAPI/Swagger" if analysis.type == ProjectType.FASTAPI else "Django REST Swagger"
        }
    
    # Add notebook documentation for data science
    if analysis.category.is_data_related():
        docs["notebooks"] = {
            "structure": "docs/notebooks/",
            "naming": "01_data_exploration.ipynb, 02_feature_engineering.ipynb",
            "tools": ["nbconvert", "jupyter-book"]
        }
    
    # Add docstring recommendations
    docs["docstrings"] = {
        "style": "Google",
        "coverage": "All public functions and classes",
        "tools": ["pydocstyle", "darglint"]
    }
    
    return docs