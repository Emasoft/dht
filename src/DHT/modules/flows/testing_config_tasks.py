#!/usr/bin/env python3
"""
DHT Testing Configuration Tasks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created testing configuration generation tasks
# - Support for pytest, unittest, and other frameworks
# - Test fixtures and factories
# - Coverage configuration
#

from prefect import task


@task(name="generate_pytest_config", description="Generate pytest configuration")
def generate_pytest_config_task(
    test_paths: list[str] | None = None,
    min_coverage: int = 80,
    markers: dict[str, str] | None = None,
    plugins: list[str] | None = None,
) -> dict[str, str]:
    """Generate pytest configuration files.

    Args:
        test_paths: Paths to test directories
        min_coverage: Minimum coverage percentage
        markers: Custom pytest markers
        plugins: Additional pytest plugins

    Returns:
        Dict with pytest.ini and conftest.py content
    """
    configs = {}
    test_paths = test_paths or ["tests"]
    markers = markers or {
        "slow": "marks tests as slow",
        "integration": "marks tests as integration tests",
        "unit": "marks tests as unit tests",
    }
    plugins = plugins or []

    # pytest.ini
    pytest_ini = f"""[tool:pytest]
testpaths = {" ".join(test_paths)}
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts =
    -ra
    --strict-markers
    --strict-config
    --cov=src
    --cov-branch
    --cov-report=term-missing:skip-covered
    --cov-report=html
    --cov-report=xml
    --cov-fail-under={min_coverage}
    --tb=short
    --maxfail=1

markers ="""

    for marker, description in markers.items():
        pytest_ini += f"\n    {marker}: {description}"

    if plugins:
        pytest_ini += f"\n\nplugins = {' '.join(plugins)}"

    configs["pytest.ini"] = pytest_ini

    # pyproject.toml version
    configs["pyproject.toml"] = f"""[tool.pytest.ini_options]
testpaths = {test_paths}
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under={min_coverage}",
    "--tb=short",
    "--maxfail=1",
]
markers = ["""

    for marker, description in markers.items():
        configs["pyproject.toml"] += f'\n    "{marker}: {description}",'

    configs["pyproject.toml"] += "\n]"

    # conftest.py
    configs["conftest.py"] = '''"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path
from typing import Generator

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    # Setup test database
    from sqlalchemy import create_engine
    from app.database import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_database):
    """Create a database session for tests."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=test_database)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # Create test user and get token
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_database(db_session):
    """Reset database between tests."""
    # Clean all tables
    meta = db_session.bind.metadata
    with db_session.bind.connect() as conn:
        trans = conn.begin()
        for table in reversed(meta.sorted_tables):
            conn.execute(table.delete())
        trans.commit()
'''

    return configs


@task(name="generate_factory_boy_factories", description="Generate test factories")
def generate_factory_boy_factories_task(
    models: dict[str, list[str]] | None = None,
) -> str:
    """Generate Factory Boy factories for testing.

    Args:
        models: Dict of model names and their fields

    Returns:
        factories.py content
    """
    models = models or {
        "User": ["email", "username", "password", "is_active"],
        "Post": ["title", "content", "author_id", "created_at"],
    }

    factories = '''"""
Test factories for creating test data.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText
from datetime import datetime, timezone

from app.models import Base
from tests.conftest import db_session

'''

    # Base factory
    factories += '''
class BaseFactory(SQLAlchemyModelFactory):
    """Base factory for all models."""

    class Meta:
        abstract = True
        sqlalchemy_session = db_session
        sqlalchemy_session_persistence = "commit"


'''

    # Generate factories for each model
    for model_name, fields in models.items():
        factories += f'''class {model_name}Factory(BaseFactory):
    """Factory for {model_name} model."""

    class Meta:
        model = {model_name}

'''

        for field in fields:
            if "email" in field:
                factories += f'    {field} = factory.Faker("email")\n'
            elif "username" in field or "name" in field:
                factories += f'    {field} = factory.Faker("user_name")\n'
            elif "password" in field:
                factories += f'    {field} = factory.Faker("password")\n'
            elif "title" in field:
                factories += f'    {field} = factory.Faker("sentence", nb_words=4)\n'
            elif "content" in field or "description" in field:
                factories += f'    {field} = factory.Faker("text")\n'
            elif "_id" in field:
                factories += f"    {field} = factory.SubFactory({field.replace('_id', '').title()}Factory)\n"
            elif "is_" in field:
                factories += f"    {field} = FuzzyChoice([True, False])\n"
            elif "_at" in field:
                factories += f'    {field} = factory.Faker("date_time_this_year", tzinfo=timezone.utc)\n'
            else:
                factories += f"    {field} = FuzzyText(length=10)\n"

        factories += "\n\n"

    return factories


@task(name="generate_coverage_config", description="Generate coverage configuration")
def generate_coverage_config_task(
    source_paths: list[str] | None = None,
    omit_paths: list[str] | None = None,
    min_coverage: int = 80,
) -> str:
    """Generate coverage configuration.

    Args:
        source_paths: Source code paths
        omit_paths: Paths to omit from coverage
        min_coverage: Minimum coverage percentage

    Returns:
        .coveragerc content
    """
    source_paths = source_paths or ["src"]
    omit_paths = omit_paths or [
        "*/tests/*",
        "*/test_*",
        "*/__pycache__/*",
        "*/venv/*",
        "*/.venv/*",
        "*/migrations/*",
        "*/config/*",
        "*/setup.py",
    ]

    coveragerc = f"""[run]
source = {", ".join(source_paths)}
branch = True
parallel = True
omit =
"""

    for path in omit_paths:
        coveragerc += f"    {path}\n"

    coveragerc += f"""
[report]
precision = 2
show_missing = True
skip_covered = False
fail_under = {min_coverage}
exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @overload
    @abstractmethod
    pass
    \\.\\.\\.

[html]
directory = htmlcov

[xml]
output = coverage.xml

[json]
output = coverage.json
pretty_print = True
"""

    return coveragerc


@task(name="generate_tox_config", description="Generate tox configuration")
def generate_tox_config_task(
    python_versions: list[str] | None = None,
    test_command: str = "pytest",
    environments: list[str] | None = None,
) -> str:
    """Generate tox configuration for multi-environment testing.

    Args:
        python_versions: Python versions to test
        test_command: Test command to run
        environments: Additional environments

    Returns:
        tox.ini content
    """
    python_versions = python_versions or ["3.10", "3.11", "3.12"]
    environments = environments or ["lint", "type", "docs"]

    # Create py versions
    py_versions = []
    for version in python_versions:
        py_versions.append(f"py{version.replace('.', '')}")

    tox_ini = f"""[tox]
envlist = {", ".join(py_versions + environments)}
isolated_build = True
skip_missing_interpreters = True

[testenv]
deps =
    pytest>=7.0
    pytest-cov
    pytest-asyncio
    pytest-timeout
    pytest-mock
commands =
    {test_command} {{posargs}}

[testenv:lint]
deps =
    ruff>=0.1.0
    black>=23.0
commands =
    ruff check .
    ruff format --check .

[testenv:type]
deps =
    mypy>=1.0
    types-all
commands =
    mypy src tests

[testenv:docs]
deps =
    mkdocs
    mkdocs-material
    mkdocstrings[python]
commands =
    mkdocs build

[testenv:security]
deps =
    bandit[toml]
    safety
commands =
    bandit -r src/
    safety check

[testenv:clean]
deps = coverage[toml]
skip_install = true
commands = coverage erase
"""

    return tox_ini


@task(name="generate_hypothesis_strategies", description="Generate Hypothesis test strategies")
def generate_hypothesis_strategies_task(
    model_schemas: dict[str, dict[str, str]] | None = None,
) -> str:
    """Generate Hypothesis strategies for property-based testing.

    Args:
        model_schemas: Schema definitions for models

    Returns:
        strategies.py content
    """
    model_schemas = model_schemas or {
        "User": {
            "email": "email",
            "username": "text",
            "age": "integer",
        },
        "Product": {
            "name": "text",
            "price": "decimal",
            "quantity": "integer",
        },
    }

    strategies = '''"""
Hypothesis strategies for property-based testing.
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite
from decimal import Decimal
import string

# Basic strategies
email_strategy = st.emails()
username_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=3,
    max_size=20,
).filter(lambda x: not x.startswith("-") and not x.endswith("-"))
password_strategy = st.text(min_size=8, max_size=100)
positive_integer = st.integers(min_value=1, max_value=1000000)
price_strategy = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2)

'''

    # Generate composite strategies for models
    for model_name, schema in model_schemas.items():
        strategies += f'''
@composite
def {model_name.lower()}_strategy(draw):
    """Generate valid {model_name} data."""
    return {{
'''

        for field_name, field_type in schema.items():
            if field_type == "email":
                strategies += f'        "{field_name}": draw(email_strategy),\n'
            elif field_type == "text":
                strategies += f'        "{field_name}": draw(st.text(min_size=1, max_size=100)),\n'
            elif field_type == "integer":
                strategies += f'        "{field_name}": draw(positive_integer),\n'
            elif field_type == "decimal":
                strategies += f'        "{field_name}": draw(price_strategy),\n'
            elif field_type == "boolean":
                strategies += f'        "{field_name}": draw(st.booleans()),\n'
            elif field_type == "datetime":
                strategies += f'        "{field_name}": draw(st.datetimes()),\n'

        strategies += "    }\n"

    strategies += """

# List strategies
user_list_strategy = st.lists(user_strategy(), min_size=0, max_size=10)
product_list_strategy = st.lists(product_strategy(), min_size=0, max_size=50)

# Optional field strategies
optional_text = st.one_of(st.none(), st.text(min_size=1, max_size=100))
optional_integer = st.one_of(st.none(), positive_integer)
"""

    return strategies


# Export all tasks
__all__ = [
    "generate_pytest_config_task",
    "generate_factory_boy_factories_task",
    "generate_coverage_config_task",
    "generate_tox_config_task",
    "generate_hypothesis_strategies_task",
]
