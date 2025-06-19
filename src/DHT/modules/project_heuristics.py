#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_heuristics.py - Intelligent project type detection and configuration inference

This module provides heuristics for:
- Detecting project types (Django, Flask, FastAPI, etc.)
- Inferring system dependencies from imports
- Suggesting optimal configurations
- Identifying best practices and patterns
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of project heuristics module
# - Added project type detection for Python frameworks
# - Added system dependency inference from imports
# - Added configuration suggestions based on project type
# - Integrated with project analyzer output
# - Added support for data science and CLI projects

from pathlib import Path
from typing import Dict, List, Any, Set
import logging

from prefect import task, flow


# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "django": {
        "files": ["manage.py", "wsgi.py", "asgi.py", "settings.py", "urls.py", "models.py"],
        "imports": ["django", "django.conf", "django.urls", "django.db"],
        "structure_hints": ["apps/", "templates/", "static/", "media/"],
        "config_files": ["django.ini", ".django"],
    },
    "flask": {
        "files": ["app.py", "application.py", "wsgi.py"],
        "imports": ["flask", "flask.Flask", "flask_sqlalchemy", "flask_migrate"],
        "structure_hints": ["templates/", "static/"],
        "config_files": [".flaskenv"],
    },
    "fastapi": {
        "files": ["main.py", "app.py"],
        "imports": ["fastapi", "fastapi.FastAPI", "uvicorn", "pydantic"],
        "structure_hints": ["routers/", "models/", "schemas/"],
        "config_files": [],
    },
    "streamlit": {
        "files": ["app.py", "streamlit_app.py"],
        "imports": ["streamlit", "st."],
        "structure_hints": ["pages/", ".streamlit/"],
        "config_files": [".streamlit/config.toml"],
    },
    "pytest": {
        "files": ["conftest.py", "pytest.ini", "tox.ini"],
        "imports": ["pytest", "unittest", "nose"],
        "structure_hints": ["tests/", "test_*.py", "*_test.py"],
        "config_files": ["pytest.ini", ".pytest.ini", "pyproject.toml"],
    },
    "library": {
        "files": ["setup.py", "setup.cfg", "pyproject.toml"],
        "imports": ["setuptools", "distutils", "flit", "poetry", "hatchling"],
        "structure_hints": ["src/", "dist/", "build/"],
        "config_files": ["setup.cfg", "pyproject.toml", "MANIFEST.in"],
    },
    "data_science": {
        "files": ["train.py", "model.py", "analysis.ipynb"],
        "imports": ["pandas", "numpy", "sklearn", "tensorflow", "torch", "keras", "matplotlib"],
        "structure_hints": ["notebooks/", "data/", "models/", "experiments/"],
        "config_files": ["environment.yml", "conda.yml"],
    },
}

# Import to system dependency mapping
IMPORT_TO_SYSTEM_DEPS = {
    # Database drivers
    "psycopg2": ["postgresql-client", "libpq-dev"],
    "psycopg": ["postgresql-client", "libpq-dev"],
    "mysqlclient": ["mysql-client", "libmysqlclient-dev"],
    "pymongo": ["mongodb-clients", "mongodb-tools"],
    "redis": ["redis-tools"],
    
    # Scientific computing
    "numpy": ["libopenblas-dev", "gfortran"],
    "scipy": ["liblapack-dev", "libblas-dev", "gfortran"],
    "pandas": ["libhdf5-dev"],
    "matplotlib": ["libfreetype6-dev", "libpng-dev"],
    "opencv": ["libopencv-dev", "python3-opencv"],
    "cv2": ["libopencv-dev", "python3-opencv"],
    
    # Machine learning
    "tensorflow": ["cuda-toolkit", "cudnn"],
    "torch": ["cuda-toolkit", "cudnn"],
    "jax": ["cuda-toolkit", "cudnn"],
    
    # Image processing
    "PIL": ["libjpeg-dev", "zlib1g-dev", "libtiff-dev"],
    "Pillow": ["libjpeg-dev", "zlib1g-dev", "libtiff-dev"],
    "wand": ["imagemagick", "libmagickwand-dev"],
    
    # Audio/Video
    "pyaudio": ["portaudio19-dev"],
    "pydub": ["ffmpeg"],
    "moviepy": ["ffmpeg", "imagemagick"],
    
    # Cryptography
    "cryptography": ["libssl-dev", "libffi-dev"],
    "pycrypto": ["libssl-dev"],
    
    # Web scraping
    "lxml": ["libxml2-dev", "libxslt-dev"],
    "beautifulsoup4": ["libxml2-dev", "libxslt-dev"],
    
    # Geographic
    "geopandas": ["libgdal-dev", "gdal-bin"],
    "shapely": ["libgeos-dev"],
    "fiona": ["libgdal-dev"],
    
    # Other
    "uwsgi": ["build-essential", "python3-dev"],
    "gunicorn": ["build-essential"],
    "ldap": ["libldap2-dev", "libsasl2-dev"],
    "python-ldap": ["libldap2-dev", "libsasl2-dev"],
}

# Configuration templates for different project types
CONFIG_TEMPLATES = {
    "django": {
        "pyproject.toml": {
            "tool.django": {
                "settings_module": "project.settings",
            },
            "tool.coverage.run": {
                "source": ["."],
                "omit": ["*/migrations/*", "*/tests/*", "*/venv/*"],
            }
        },
        "setup.cfg": {
            "flake8": {
                "exclude": "migrations,__pycache__,venv",
                "max-line-length": "88",
            }
        },
        ".pre-commit-config.yaml": {
            "repos": [
                {
                    "repo": "https://github.com/psf/black",
                    "hooks": [{"id": "black"}]
                },
                {
                    "repo": "https://github.com/pycqa/isort", 
                    "hooks": [{"id": "isort"}]
                },
            ]
        }
    },
    "fastapi": {
        "pyproject.toml": {
            "tool.pytest.ini_options": {
                "testpaths": ["tests"],
                "python_files": "test_*.py",
            },
            "tool.mypy": {
                "plugins": ["pydantic.mypy"],
            }
        },
        ".env.example": "DATABASE_URL=postgresql://user:pass@localhost/dbname\nSECRET_KEY=your-secret-key\n",
    },
    "data_science": {
        "pyproject.toml": {
            "tool.jupyter": {
                "kernel": "python3",
            },
            "tool.black": {
                "include": '"\\.ipynb$"',
            }
        },
        ".gitignore": "*.csv\n*.h5\n*.pkl\n*.model\ndata/\nmodels/\n",
    },
}


class ProjectHeuristics:
    """
    Analyzes project structure and content to make intelligent inferences
    about project type, dependencies, and optimal configuration.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @task
    def detect_project_type(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the primary project type and characteristics.
        
        Args:
            analysis_result: Output from ProjectAnalyzer
            
        Returns:
            Dictionary with project type information and confidence scores
        """
        scores = {}
        
        # Extract relevant data from analysis
        file_paths = self._extract_file_paths(analysis_result)
        imports = self._extract_all_imports(analysis_result)
        structure = analysis_result.get("structure", {})
        
        # Score each framework
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            score = 0
            matches = []
            
            # Check for marker files
            for marker_file in patterns["files"]:
                if any(marker_file in str(f) for f in file_paths):
                    # Give less weight to generic files
                    if marker_file in ["main.py", "app.py"] and framework in ["fastapi", "flask"]:
                        score += 2  # Reduced from 10
                    elif marker_file == "manage.py" and framework == "django":
                        score += 15  # manage.py is a strong Django indicator
                    elif marker_file in ["settings.py", "urls.py", "models.py"] and framework == "django":
                        score += 3  # Generic Django files get less weight
                    else:
                        score += 10
                    matches.append(f"file:{marker_file}")
            
            # Check for imports
            for import_pattern in patterns["imports"]:
                if import_pattern in imports:
                    score += 3  # Reduced from 5
                    matches.append(f"import:{import_pattern}")
            
            # Check structure hints
            for hint in patterns["structure_hints"]:
                if any(hint in str(f) for f in file_paths):
                    score += 2  # Reduced from 3
                    matches.append(f"structure:{hint}")
            
            # Check config files
            for config in patterns["config_files"]:
                if any(config in str(f) for f in file_paths):
                    score += 2
                    matches.append(f"config:{config}")
            
            if score > 0:
                scores[framework] = {
                    "score": score,
                    "matches": matches,
                    "confidence": min(score / 30.0, 1.0)  # Normalize to 0-1, adjusted for new scoring
                }
        
        # Detect additional project characteristics
        characteristics = self._detect_characteristics(file_paths, imports, analysis_result)
        
        # Sort frameworks by score
        ranked_frameworks = sorted(
            scores.items(), 
            key=lambda x: x[1]["score"], 
            reverse=True
        )
        
        result = {
            "primary_type": ranked_frameworks[0][0] if ranked_frameworks else "generic",
            "frameworks": dict(ranked_frameworks),
            "characteristics": characteristics,
            "confidence": ranked_frameworks[0][1]["confidence"] if ranked_frameworks else 0.0,
        }
        
        # Add project category
        if result["primary_type"] in ["django", "flask", "fastapi", "streamlit"]:
            result["category"] = "web"
        elif result["primary_type"] == "library":
            result["category"] = "library"
        elif "data_science" in characteristics:
            result["category"] = "data_science"
        elif "cli" in characteristics:
            result["category"] = "cli"
        elif "library" in characteristics:
            result["category"] = "library"
        else:
            result["category"] = "application"
        
        return result
    
    @task
    def infer_system_dependencies(self, analysis_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Infer system dependencies based on Python imports.
        
        Args:
            analysis_result: Output from ProjectAnalyzer
            
        Returns:
            Dictionary mapping dependency names to system packages
        """
        imports = self._extract_all_imports(analysis_result)
        system_deps = {}
        
        for import_name in imports:
            # Check direct mapping
            if import_name in IMPORT_TO_SYSTEM_DEPS:
                deps = IMPORT_TO_SYSTEM_DEPS[import_name]
                system_deps[import_name] = deps
            else:
                # Check if it's a submodule of a known package
                base_module = import_name.split('.')[0]
                if base_module in IMPORT_TO_SYSTEM_DEPS:
                    deps = IMPORT_TO_SYSTEM_DEPS[base_module]
                    system_deps[base_module] = deps
        
        # Deduplicate system packages
        all_packages = set()
        for deps in system_deps.values():
            all_packages.update(deps)
        
        return {
            "inferred_packages": sorted(all_packages),
            "import_mapping": system_deps,
            "confidence": "high" if system_deps else "low",
        }
    
    @task
    def suggest_configurations(
        self, 
        project_type_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest optimal configurations based on project type.
        
        Args:
            project_type_info: Output from detect_project_type
            analysis_result: Output from ProjectAnalyzer
            
        Returns:
            Configuration suggestions and templates
        """
        suggestions = {
            "recommended_files": [],
            "config_templates": {},
            "best_practices": [],
            "missing_files": [],
        }
        
        primary_type = project_type_info.get("primary_type", "generic")
        characteristics = project_type_info.get("characteristics", [])
        
        # Get config templates for primary type
        if primary_type in CONFIG_TEMPLATES:
            suggestions["config_templates"] = CONFIG_TEMPLATES[primary_type]
        
        # Check for missing recommended files
        existing_files = {Path(f).name for f in self._extract_file_paths(analysis_result)}
        
        # Common recommendations
        if "pyproject.toml" not in existing_files:
            suggestions["missing_files"].append("pyproject.toml")
            suggestions["best_practices"].append("Use pyproject.toml for modern Python packaging")
        
        if ".gitignore" not in existing_files:
            suggestions["missing_files"].append(".gitignore")
            suggestions["best_practices"].append("Add .gitignore to exclude build artifacts")
        
        if "README.md" not in existing_files and "README.rst" not in existing_files:
            suggestions["missing_files"].append("README.md")
            suggestions["best_practices"].append("Add README for project documentation")
        
        # Type-specific recommendations
        if primary_type == "django":
            suggestions["recommended_files"].extend([
                ".env.example",
                "requirements/base.txt",
                "requirements/dev.txt",
                "requirements/prod.txt",
            ])
            suggestions["best_practices"].extend([
                "Use environment variables for sensitive settings",
                "Split requirements by environment",
                "Add django-debug-toolbar for development",
            ])
        
        elif primary_type == "fastapi":
            suggestions["recommended_files"].extend([
                ".env.example",
                "alembic.ini",
                "docker-compose.yml",
            ])
            suggestions["best_practices"].extend([
                "Use Alembic for database migrations",
                "Implement proper CORS configuration",
                "Add OpenAPI documentation",
            ])
        
        elif primary_type == "flask":
            suggestions["recommended_files"].extend([
                ".env",
                ".flaskenv",
                "requirements.txt",
            ])
            suggestions["best_practices"].extend([
                "Use Flask-Migrate for database migrations",
                "Implement application factory pattern",
                "Add Flask-CORS for API endpoints",
            ])
        
        # Testing recommendations
        if "testing" in characteristics:
            if "pytest.ini" not in existing_files and "tox.ini" not in existing_files:
                suggestions["missing_files"].append("pytest.ini")
            suggestions["best_practices"].append("Configure pytest with coverage reporting")
        
        # CI/CD recommendations
        if not any(".github/workflows" in str(f) for f in self._extract_file_paths(analysis_result)):
            suggestions["recommended_files"].append(".github/workflows/tests.yml")
            suggestions["best_practices"].append("Add GitHub Actions for CI/CD")
        
        # Docker recommendations
        if "containerized" in characteristics or primary_type in ["fastapi", "django"]:
            if "Dockerfile" not in existing_files:
                suggestions["missing_files"].append("Dockerfile")
            if "docker-compose.yml" not in existing_files:
                suggestions["recommended_files"].append("docker-compose.yml")
        
        return suggestions
    
    @task
    def analyze_code_quality(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code quality indicators and suggest improvements.
        
        Args:
            analysis_result: Output from ProjectAnalyzer
            
        Returns:
            Code quality metrics and suggestions
        """
        quality_indicators = {
            "has_tests": False,
            "has_type_hints": False,
            "has_docstrings": False,
            "has_linting": False,
            "has_formatting": False,
            "test_coverage": "unknown",
            "suggestions": [],
        }
        
        file_analysis = analysis_result.get("file_analysis", {})
        existing_files = {Path(f).name for f in self._extract_file_paths(analysis_result)}
        
        # Check for tests
        test_files = [f for f in file_analysis if "test" in f.lower()]
        quality_indicators["has_tests"] = len(test_files) > 0
        
        # Check for type hints in Python files
        type_hint_count = 0
        total_functions = 0
        
        for file_path, file_data in file_analysis.items():
            if file_path.endswith(".py") and "functions" in file_data:
                for func in file_data.get("functions", []):
                    total_functions += 1
                    if func.get("has_type_hints"):
                        type_hint_count += 1
        
        if total_functions > 0:
            type_hint_ratio = type_hint_count / total_functions
            quality_indicators["has_type_hints"] = type_hint_ratio > 0.5
            quality_indicators["type_hint_coverage"] = f"{type_hint_ratio:.1%}"
        
        # Check for linting/formatting configs
        linting_configs = {
            ".flake8", "setup.cfg", ".pylintrc", "pyproject.toml",
            ".pre-commit-config.yaml", "ruff.toml"
        }
        quality_indicators["has_linting"] = bool(linting_configs & existing_files)
        
        formatting_configs = {".black", "pyproject.toml", ".yapfrc", ".style.yapf"}
        quality_indicators["has_formatting"] = bool(formatting_configs & existing_files)
        
        # Generate suggestions
        if not quality_indicators["has_tests"]:
            quality_indicators["suggestions"].append("Add unit tests with pytest")
        
        if not quality_indicators["has_type_hints"]:
            quality_indicators["suggestions"].append("Add type hints to improve code clarity")
        
        if not quality_indicators["has_linting"]:
            quality_indicators["suggestions"].append("Configure linting with ruff or flake8")
        
        if not quality_indicators["has_formatting"]:
            quality_indicators["suggestions"].append("Set up automatic formatting with black")
        
        if ".pre-commit-config.yaml" not in existing_files:
            quality_indicators["suggestions"].append("Add pre-commit hooks for code quality")
        
        return quality_indicators
    
    @flow(name="analyze_project_heuristics")
    def analyze(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete heuristic analysis on a project.
        
        Args:
            analysis_result: Output from ProjectAnalyzer
            
        Returns:
            Complete heuristic analysis including type, dependencies, and suggestions
        """
        # Detect project type
        project_type = self.detect_project_type(analysis_result)
        
        # Infer system dependencies
        system_deps = self.infer_system_dependencies(analysis_result)
        
        # Suggest configurations
        config_suggestions = self.suggest_configurations(project_type, analysis_result)
        
        # Analyze code quality
        quality_analysis = self.analyze_code_quality(analysis_result)
        
        return {
            "project_type": project_type,
            "system_dependencies": system_deps,
            "configuration_suggestions": config_suggestions,
            "code_quality": quality_analysis,
            "analysis_timestamp": analysis_result.get("analysis_timestamp"),
        }
    
    def _extract_file_paths(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Extract all file paths from analysis result."""
        file_paths = []
        
        # From file_analysis section
        if "file_analysis" in analysis_result:
            file_paths.extend(analysis_result["file_analysis"].keys())
        
        # From structure section
        structure = analysis_result.get("structure", {})
        if "entry_points" in structure:
            file_paths.extend(structure["entry_points"])
        
        return file_paths
    
    def _extract_all_imports(self, analysis_result: Dict[str, Any]) -> Set[str]:
        """Extract all unique imports from the analysis."""
        imports = set()
        
        # From file analysis
        for file_data in analysis_result.get("file_analysis", {}).values():
            if "imports" in file_data:
                for imp in file_data["imports"]:
                    if isinstance(imp, dict):
                        module = imp.get("module", "")
                        if module:
                            imports.add(module)
                            # Also add parent modules for submodule matching
                            parts = module.split(".")
                            for i in range(1, len(parts)):
                                imports.add(".".join(parts[:i]))
                    else:
                        imports.add(str(imp))
        
        # From dependencies
        deps = analysis_result.get("dependencies", {})
        for lang_deps in deps.values():
            if isinstance(lang_deps, dict) and "all" in lang_deps:
                imports.update(lang_deps["all"])
        
        return imports
    
    def _detect_characteristics(
        self, 
        file_paths: List[str], 
        imports: Set[str],
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Detect additional project characteristics."""
        characteristics = []
        
        # Testing framework
        if any("test" in str(f) for f in file_paths):
            characteristics.append("testing")
            if "pytest" in imports:
                characteristics.append("pytest")
            elif "unittest" in imports:
                characteristics.append("unittest")
        
        # Data science indicators
        ml_imports = {"sklearn", "tensorflow", "torch", "keras", "pandas", "numpy"}
        if ml_imports & imports:
            characteristics.append("data_science")
            if any(".ipynb" in str(f) for f in file_paths):
                characteristics.append("notebooks")
        
        # CLI indicators
        cli_imports = {"click", "argparse", "typer", "fire"}
        if cli_imports & imports:
            characteristics.append("cli")
        
        # API indicators
        api_imports = {"fastapi", "flask", "django.rest_framework", "graphene"}
        if api_imports & imports:
            characteristics.append("api")
        
        # Database usage
        db_imports = {"sqlalchemy", "django.db", "pymongo", "redis", "psycopg2"}
        if db_imports & imports:
            characteristics.append("database")
        
        # Async programming
        if any("async def" in str(analysis_result.get("file_analysis", {}).get(f, {})) 
               for f in file_paths):
            characteristics.append("async")
        
        # Containerization
        if any("Dockerfile" in str(f) or "docker-compose" in str(f) for f in file_paths):
            characteristics.append("containerized")
        
        # Library project
        # Check configurations from analyzer
        configs = analysis_result.get("configurations", {})
        has_package_files = (
            configs.get("has_setup_py", False) or 
            configs.get("has_pyproject", False) or
            any("setup.cfg" in str(f) for f in file_paths)
        )
        
        if has_package_files:
            # Check if it's not a web framework project
            web_frameworks = {"django", "flask", "fastapi", "streamlit", "tornado", "aiohttp"}
            if not any(framework in imports for framework in web_frameworks):
                characteristics.append("library")
        
        return characteristics