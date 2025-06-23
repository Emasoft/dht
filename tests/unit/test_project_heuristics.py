#!/usr/bin/env python3
"""
Test suite for project heuristics module.  Tests intelligent project type detection, system dependency inference, and configuration suggestions.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test suite for project heuristics module.

Tests intelligent project type detection, system dependency inference,
and configuration suggestions.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for project heuristics
# - Added tests for project type detection (Django, Flask, FastAPI)
# - Added tests for system dependency inference
# - Added tests for configuration suggestions
# - Added tests for code quality analysis
# - Added integration tests with project analyzer output

from typing import Any

import pytest

from DHT.modules.project_heuristics import FRAMEWORK_PATTERNS, IMPORT_TO_SYSTEM_DEPS, ProjectHeuristics


class TestProjectHeuristics:
    """Test the project heuristics functionality."""

    @pytest.fixture
    def heuristics(self) -> Any:
        """Create a project heuristics instance."""
        return ProjectHeuristics()

    @pytest.fixture
    def django_analysis_result(self) -> Any:
        """Create a mock Django project analysis result."""
        return {
            "project_type": "python",
            "file_analysis": {
                "manage.py": {"imports": [{"module": "django.core.management"}, {"module": "os"}, {"module": "sys"}]},
                "myapp/settings.py": {"imports": [{"module": "django.conf"}, {"module": "pathlib"}]},
                "myapp/urls.py": {"imports": [{"module": "django.urls"}, {"module": "django.contrib"}]},
                "myapp/models.py": {"imports": [{"module": "django.db.models"}]},
            },
            "structure": {"has_tests": True, "entry_points": ["manage.py"]},
            "dependencies": {"python": {"all": ["django", "psycopg2", "redis", "celery"]}},
        }

    @pytest.fixture
    def flask_analysis_result(self) -> Any:
        """Create a mock Flask project analysis result."""
        return {
            "project_type": "python",
            "file_analysis": {
                "app.py": {
                    "imports": [{"module": "flask"}, {"module": "flask.Flask"}, {"module": "flask_sqlalchemy"}],
                    "functions": [
                        {"name": "create_app", "has_type_hints": True},
                        {"name": "index", "has_type_hints": False},
                    ],
                },
                "models.py": {"imports": [{"module": "sqlalchemy"}]},
                "templates/index.html": {},
                "static/style.css": {},
            },
            "structure": {"has_tests": False, "entry_points": ["app.py"]},
            "dependencies": {"python": {"all": ["flask", "flask-sqlalchemy", "flask-migrate"]}},
        }

    @pytest.fixture
    def fastapi_analysis_result(self) -> Any:
        """Create a mock FastAPI project analysis result."""
        return {
            "project_type": "python",
            "file_analysis": {
                "main.py": {
                    "imports": [
                        {"module": "fastapi"},
                        {"module": "fastapi.FastAPI"},
                        {"module": "pydantic"},
                        {"module": "uvicorn"},
                    ],
                    "functions": [
                        {"name": "read_root", "has_type_hints": True},
                        {"name": "create_item", "has_type_hints": True},
                    ],
                },
                "routers/users.py": {"imports": [{"module": "fastapi.APIRouter"}]},
                "models/user.py": {"imports": [{"module": "pydantic.BaseModel"}]},
            },
            "structure": {"has_tests": True, "entry_points": ["main.py"]},
        }

    @pytest.fixture
    def data_science_analysis_result(self) -> Any:
        """Create a mock data science project analysis result."""
        return {
            "project_type": "python",
            "file_analysis": {
                "notebooks/analysis.ipynb": {},
                "src/train_model.py": {
                    "imports": [
                        {"module": "pandas"},
                        {"module": "numpy"},
                        {"module": "sklearn.model_selection"},
                        {"module": "tensorflow"},
                        {"module": "matplotlib.pyplot"},
                    ]
                },
                "src/preprocess.py": {"imports": [{"module": "cv2"}, {"module": "PIL.Image"}]},
            },
            "structure": {"has_tests": True},
        }

    def test_detect_django_project(self, heuristics, django_analysis_result) -> Any:
        """Test Django project detection."""
        result = heuristics.detect_project_type(django_analysis_result)

        assert result["primary_type"] == "django"
        assert result["category"] == "web"
        assert result["confidence"] > 0.8

        django_info = result["frameworks"]["django"]
        assert django_info["score"] > 20
        assert any("file:manage.py" in match for match in django_info["matches"])
        assert any("import:django.db" in match for match in django_info["matches"])

    def test_detect_flask_project(self, heuristics, flask_analysis_result) -> Any:
        """Test Flask project detection."""
        result = heuristics.detect_project_type(flask_analysis_result)

        assert result["primary_type"] == "flask"
        assert result["category"] == "web"

        flask_info = result["frameworks"]["flask"]
        assert flask_info["score"] > 10
        assert any("file:app.py" in match for match in flask_info["matches"])
        assert any("import:flask" in match for match in flask_info["matches"])
        assert any("structure:templates/" in match for match in flask_info["matches"])

    def test_detect_fastapi_project(self, heuristics, fastapi_analysis_result) -> Any:
        """Test FastAPI project detection."""
        result = heuristics.detect_project_type(fastapi_analysis_result)

        assert result["primary_type"] == "fastapi"
        assert result["category"] == "web"

        fastapi_info = result["frameworks"]["fastapi"]
        assert any("file:main.py" in match for match in fastapi_info["matches"])
        assert any("import:fastapi" in match for match in fastapi_info["matches"])
        assert any("structure:routers/" in match for match in fastapi_info["matches"])

    def test_detect_data_science_project(self, heuristics, data_science_analysis_result) -> Any:
        """Test data science project detection."""
        result = heuristics.detect_project_type(data_science_analysis_result)

        assert result["category"] == "data_science"
        assert "data_science" in result["characteristics"]
        assert "notebooks" in result["characteristics"]

    def test_detect_generic_project(self, heuristics) -> Any:
        """Test generic project detection when no framework matches."""
        generic_result = {
            "project_type": "python",
            "file_analysis": {"script.py": {"imports": [{"module": "os"}, {"module": "sys"}]}},
            "structure": {},
        }

        result = heuristics.detect_project_type(generic_result)

        assert result["primary_type"] == "generic"
        assert result["confidence"] == 0.0
        assert result["category"] == "application"

    def test_infer_system_dependencies(self, heuristics, django_analysis_result) -> Any:
        """Test system dependency inference from imports."""
        result = heuristics.infer_system_dependencies(django_analysis_result)

        assert "inferred_packages" in result
        assert "import_mapping" in result

        # Check psycopg2 dependencies
        assert "postgresql-client" in result["inferred_packages"]
        assert "libpq-dev" in result["inferred_packages"]

        # Check redis dependencies
        assert "redis-tools" in result["inferred_packages"]

        # Check mapping
        assert "psycopg2" in result["import_mapping"]
        assert result["import_mapping"]["psycopg2"] == ["postgresql-client", "libpq-dev"]

    def test_infer_ml_dependencies(self, heuristics, data_science_analysis_result) -> Any:
        """Test ML/data science dependency inference."""
        result = heuristics.infer_system_dependencies(data_science_analysis_result)

        # Check numpy/scipy dependencies
        assert "libopenblas-dev" in result["inferred_packages"]
        assert "gfortran" in result["inferred_packages"]

        # Check OpenCV dependencies
        assert "libopencv-dev" in result["inferred_packages"]

        # Check PIL dependencies
        assert "libjpeg-dev" in result["inferred_packages"]

    def test_suggest_django_configurations(self, heuristics, django_analysis_result) -> Any:
        """Test configuration suggestions for Django projects."""
        project_type = heuristics.detect_project_type(django_analysis_result)
        suggestions = heuristics.suggest_configurations(project_type, django_analysis_result)

        assert "recommended_files" in suggestions
        assert "config_templates" in suggestions
        assert "best_practices" in suggestions

        # Django-specific recommendations
        assert ".env.example" in suggestions["recommended_files"]
        assert "requirements/base.txt" in suggestions["recommended_files"]

        # Best practices
        assert any("environment variables" in bp for bp in suggestions["best_practices"])
        assert any("Split requirements" in bp for bp in suggestions["best_practices"])

    def test_suggest_fastapi_configurations(self, heuristics, fastapi_analysis_result) -> Any:
        """Test configuration suggestions for FastAPI projects."""
        project_type = heuristics.detect_project_type(fastapi_analysis_result)
        suggestions = heuristics.suggest_configurations(project_type, fastapi_analysis_result)

        # FastAPI-specific recommendations
        assert ".env.example" in suggestions["recommended_files"]
        assert "docker-compose.yml" in suggestions["recommended_files"]

        # Config templates
        assert "pyproject.toml" in suggestions["config_templates"]
        assert "tool.pytest.ini_options" in suggestions["config_templates"]["pyproject.toml"]

    def test_analyze_code_quality(self, heuristics, flask_analysis_result) -> Any:
        """Test code quality analysis."""
        result = heuristics.analyze_code_quality(flask_analysis_result)

        assert "has_tests" in result
        assert "has_type_hints" in result
        assert "suggestions" in result

        # Flask example has no tests
        assert result["has_tests"] is False
        assert "Add unit tests with pytest" in result["suggestions"]

        # Has partial type hints
        assert "type_hint_coverage" in result

    def test_analyze_code_quality_with_configs(self, heuristics) -> Any:
        """Test code quality detection with config files."""
        analysis_with_configs = {
            "project_type": "python",
            "file_analysis": {
                ".pre-commit-config.yaml": {},
                "pyproject.toml": {},
                "tests/test_main.py": {"imports": [{"module": "pytest"}]},
            },
        }

        result = heuristics.analyze_code_quality(analysis_with_configs)

        assert result["has_tests"] is True
        assert result["has_linting"] is True  # pyproject.toml counts
        assert result["has_formatting"] is True  # pyproject.toml counts
        assert "Add pre-commit hooks" not in result["suggestions"]

    def test_complete_analysis_flow(self, heuristics, django_analysis_result) -> Any:
        """Test complete heuristic analysis flow."""
        result = heuristics.analyze(django_analysis_result)

        assert "project_type" in result
        assert "system_dependencies" in result
        assert "configuration_suggestions" in result
        assert "code_quality" in result

        # Verify Django detection
        assert result["project_type"]["primary_type"] == "django"

        # Verify system dependencies
        assert len(result["system_dependencies"]["inferred_packages"]) > 0

        # Verify suggestions
        assert len(result["configuration_suggestions"]["best_practices"]) > 0

    def test_project_characteristics_detection(self, heuristics) -> Any:
        """Test detection of various project characteristics."""
        # Create a complex project with multiple characteristics
        complex_project = {
            "project_type": "python",
            "file_analysis": {
                "app.py": {"imports": [{"module": "click"}, {"module": "sqlalchemy"}, {"module": "asyncio"}]},
                "tests/test_app.py": {"imports": [{"module": "pytest"}]},
                "Dockerfile": {},
                "setup.py": {},
            },
            "dependencies": {"python": {"all": ["click", "sqlalchemy", "pytest", "asyncio"]}},
        }

        result = heuristics.detect_project_type(complex_project)
        characteristics = result["characteristics"]

        assert "cli" in characteristics  # Has click
        assert "testing" in characteristics  # Has tests
        assert "pytest" in characteristics  # Uses pytest
        assert "database" in characteristics  # Uses sqlalchemy
        assert "containerized" in characteristics  # Has Dockerfile
        assert "library" in characteristics  # Has setup.py but no web framework

    def test_empty_project_handling(self, heuristics) -> Any:
        """Test handling of empty or minimal projects."""
        empty_project = {"project_type": "unknown", "file_analysis": {}, "structure": {}, "dependencies": {}}

        # Should not crash
        project_type = heuristics.detect_project_type(empty_project)
        system_deps = heuristics.infer_system_dependencies(empty_project)
        suggestions = heuristics.suggest_configurations(project_type, empty_project)
        quality = heuristics.analyze_code_quality(empty_project)

        assert project_type["primary_type"] == "generic"
        assert system_deps["confidence"] == "low"
        assert len(suggestions["missing_files"]) > 0  # Should suggest basic files
        assert quality["has_tests"] is False


class TestFrameworkPatterns:
    """Test framework pattern definitions."""

    def test_framework_patterns_completeness(self) -> Any:
        """Test that all framework patterns have required fields."""
        required_fields = {"files", "imports", "structure_hints", "config_files"}

        for framework, patterns in FRAMEWORK_PATTERNS.items():
            assert required_fields.issubset(patterns.keys()), f"Framework {framework} missing required fields"

            # All fields should be lists
            for field in required_fields:
                assert isinstance(patterns[field], list), f"Framework {framework} field {field} should be a list"

    def test_import_to_system_deps_validity(self) -> Any:
        """Test that system dependency mappings are valid."""
        for import_name, deps in IMPORT_TO_SYSTEM_DEPS.items():
            assert isinstance(deps, list), f"Dependencies for {import_name} should be a list"
            assert len(deps) > 0, f"Dependencies for {import_name} should not be empty"

            # All deps should be strings
            for dep in deps:
                assert isinstance(dep, str), f"Dependency {dep} should be a string"
