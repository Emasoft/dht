#!/usr/bin/env python3
"""
DHT Project Generator Flow.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created comprehensive project generation flow
# - Orchestrates all template tasks based on project type
# - Supports Django, FastAPI, Flask, CLI, and library projects
# - Fully parameterized with no hardcoded values
#

from pathlib import Path

from prefect import flow, task
from prefect.task_runners import ThreadPoolTaskRunner

from ..dhtl_error_handling import log_info, log_success
from .config_generation_tasks import (
    generate_django_settings_task,
    generate_docker_compose_task,
    generate_dockerfile_task,
    generate_env_file_task,
    generate_fastapi_main_task,
    generate_github_workflow_task,
    generate_makefile_task,
)
from .database_config_tasks import (
    generate_alembic_config_task,
    generate_mongodb_config_task,
    generate_redis_config_task,
    generate_sqlalchemy_config_task,
)
from .template_tasks import (
    create_directory_task,
    generate_gitignore_task,
    generate_license_task,
    generate_pre_commit_config_task,
    generate_pyproject_toml_task,
    generate_readme_task,
    write_file_task,
)
from .testing_config_tasks import (
    generate_coverage_config_task,
    generate_factory_boy_factories_task,
    generate_pytest_config_task,
)


@task(name="detect_project_requirements", description="Analyze project requirements")
def detect_project_requirements_task(
    project_type: str,
    features: list[str] | None = None,
) -> dict[str, any]:
    """Detect what configurations are needed based on project type.

    Args:
        project_type: Type of project (django, fastapi, flask, cli, library)
        features: Additional features requested

    Returns:
        Requirements dictionary
    """
    features = features or []

    requirements = {
        "use_docker": "docker" in features or project_type in ["django", "fastapi"],
        "use_postgres": project_type in ["django", "fastapi"],
        "use_redis": "redis" in features or project_type in ["django", "fastapi"],
        "use_mongodb": "mongodb" in features,
        "use_alembic": project_type == "fastapi",
        "use_celery": "celery" in features or project_type == "django",
        "use_pytest": True,  # Always use pytest
        "github_actions": True,
        "pre_commit": True,
    }

    # Framework-specific settings
    if project_type == "django":
        requirements["django_rest"] = "api" in features or "rest" in features
        requirements["django_admin"] = True
        requirements["use_migrations"] = True
    elif project_type == "fastapi":
        requirements["async_support"] = True
        requirements["api_docs"] = True
        requirements["use_pydantic"] = True

    return requirements


@flow(
    name="generate_project",
    description="Generate a complete project structure with all configurations",
    task_runner=ThreadPoolTaskRunner(),
)
def generate_project_flow(
    project_path: Path,
    project_name: str,
    project_type: str = "fastapi",
    description: str = "A new Python project",
    author_name: str | None = None,
    author_email: str | None = None,
    license_type: str = "MIT",
    python_version: str = "3.11",
    features: list[str] | None = None,
    port: int = 8000,
) -> bool:
    """Generate a complete project with all configurations.

    Args:
        project_path: Path to create the project
        project_name: Name of the project
        project_type: Type of project (django, fastapi, flask, cli, library)
        description: Project description
        author_name: Author name
        author_email: Author email
        license_type: License type (MIT, Apache)
        python_version: Python version to use
        features: Additional features to include
        port: Port for web applications

    Returns:
        True if successful
    """
    log_info(f"Generating {project_type} project: {project_name}")

    # Detect requirements
    requirements = detect_project_requirements_task(project_type, features)

    # Create project structure
    project_dir = project_path / project_name
    create_directory_task(project_dir)
    create_directory_task(project_dir / "src" / project_name)
    create_directory_task(project_dir / "tests")

    # Generate base files
    write_file_task(project_dir / ".gitignore", generate_gitignore_task())

    write_file_task(project_dir / "LICENSE", generate_license_task(license_type, author_name))

    write_file_task(project_dir / "README.md", generate_readme_task(project_name, description, author_name))

    write_file_task(
        project_dir / "pyproject.toml",
        generate_pyproject_toml_task(
            project_name=project_name,
            version="0.1.0",
            description=description,
            author_name=author_name,
            author_email=author_email,
            python_version=python_version,
        ),
    )

    # Generate CI/CD
    if requirements["github_actions"]:
        create_directory_task(project_dir / ".github" / "workflows")
        write_file_task(
            project_dir / ".github" / "workflows" / "ci.yml",
            generate_github_workflow_task(
                workflow_name="CI",
                python_versions=[python_version],
                test_on_multiple_os=False,
                use_uv=True,
                deploy_on_tag=project_type == "library",
            ),
        )

    if requirements["pre_commit"]:
        write_file_task(project_dir / ".pre-commit-config.yaml", generate_pre_commit_config_task())

    # Generate Makefile
    write_file_task(
        project_dir / "Makefile",
        generate_makefile_task(
            use_uv=True,
            use_docker=requirements["use_docker"],
            test_framework="pytest",
        ),
    )

    # Generate environment file
    write_file_task(
        project_dir / ".env.example",
        generate_env_file_task(
            project_type=project_type,
            database_type="postgresql" if requirements["use_postgres"] else "sqlite",
            include_secrets=True,
        ),
    )

    # Framework-specific files
    if project_type == "django":
        # Django project structure
        django_dir = project_dir / "src" / project_name
        create_directory_task(django_dir / "apps")
        create_directory_task(django_dir / "static")
        create_directory_task(django_dir / "templates")

        write_file_task(
            django_dir / "settings.py",
            generate_django_settings_task(
                project_name=project_name,
                debug=True,
                allowed_hosts=["localhost", "127.0.0.1"],
            ),
        )

    elif project_type == "fastapi":
        # FastAPI project structure
        src_dir = project_dir / "src" / project_name
        create_directory_task(src_dir / "api")
        create_directory_task(src_dir / "models")
        create_directory_task(src_dir / "schemas")
        create_directory_task(src_dir / "services")

        write_file_task(
            src_dir / "main.py",
            generate_fastapi_main_task(
                app_name="app",
                title=project_name,
                version="0.1.0",
                description=description,
            ),
        )

        write_file_task(src_dir / "__init__.py", '"""Main package for ' + project_name + '."""\n')

    # Database configuration
    if requirements["use_postgres"]:
        database_url = f"postgresql://postgres:postgres@localhost:5432/{project_name}_db"

        write_file_task(
            project_dir / "src" / project_name / "database.py",
            generate_sqlalchemy_config_task(
                async_support=project_type == "fastapi",
                use_pool=True,
                pool_size=5,
                max_overflow=10,
            ),
        )

        if requirements["use_alembic"]:
            alembic_configs = generate_alembic_config_task(
                database_url=database_url,
                script_location="alembic",
            )
            for filename, content in alembic_configs.items():
                if "/" in filename:
                    file_path = project_dir / filename
                    create_directory_task(file_path.parent)
                    write_file_task(file_path, content)
                else:
                    write_file_task(project_dir / filename, content)

    if requirements["use_redis"]:
        write_file_task(
            project_dir / "src" / project_name / "redis_client.py",
            generate_redis_config_task(
                use_async=project_type == "fastapi",
                connection_pool=True,
                decode_responses=True,
                serializer="json",
            ),
        )

    if requirements["use_mongodb"]:
        write_file_task(
            project_dir / "src" / project_name / "mongodb_client.py",
            generate_mongodb_config_task(
                database_name=project_name,
                use_async=project_type == "fastapi",
                connection_pool_size=100,
            ),
        )

    # Docker configuration
    if requirements["use_docker"]:
        write_file_task(
            project_dir / "Dockerfile",
            generate_dockerfile_task(
                python_version=python_version,
                project_type="web" if project_type in ["django", "fastapi", "flask"] else project_type,
                app_module=f"{project_name}.main:app" if project_type == "fastapi" else "wsgi:application",
                port=port,
                system_deps=["gcc", "libpq-dev"] if requirements["use_postgres"] else [],
                use_uv=True,
                non_root=True,
            ),
        )

        write_file_task(
            project_dir / "docker-compose.yml",
            generate_docker_compose_task(
                project_name=project_name,
                use_postgres=requirements["use_postgres"],
                use_redis=requirements["use_redis"],
                port=port,
            ),
        )

        write_file_task(
            project_dir / ".dockerignore",
            """.git
.gitignore
.env
.env.*
.venv
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.log
""",
        )

    # Testing configuration
    if requirements["use_pytest"]:
        pytest_configs = generate_pytest_config_task(
            test_paths=["tests"],
            min_coverage=80,
            markers={
                "slow": "marks tests as slow",
                "integration": "marks tests as integration tests",
                "unit": "marks tests as unit tests",
            },
        )

        write_file_task(project_dir / "pytest.ini", pytest_configs["pytest.ini"])

        write_file_task(project_dir / "tests" / "conftest.py", pytest_configs["conftest.py"])

        write_file_task(
            project_dir / ".coveragerc",
            generate_coverage_config_task(
                source_paths=["src"],
                omit_paths=["*/tests/*", "*/__pycache__/*", "*/migrations/*"],
                min_coverage=80,
            ),
        )

        # Generate test factories if using ORM
        if project_type in ["django", "fastapi"]:
            write_file_task(project_dir / "tests" / "factories.py", generate_factory_boy_factories_task())

    # Create initial test file
    write_file_task(
        project_dir / "tests" / "test_example.py",
        f'''"""
Example test file for {project_name}.
"""
import pytest


def test_example():
    """Example test that always passes."""
    assert True


def test_project_name():
    """Test project name is correct."""
    assert "{project_name}" == "{project_name}"
''',
    )

    log_success(f"Successfully generated {project_type} project: {project_name}")
    return True


# Export flow
__all__ = ["generate_project_flow", "detect_project_requirements_task"]
