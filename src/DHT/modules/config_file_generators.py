#!/usr/bin/env python3
"""
config_file_generators.py - Configuration file generators for development tools  This module generates configuration files for various development tools.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
config_file_generators.py - Configuration file generators for development tools

This module generates configuration files for various development tools.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains generators for ruff, black, mypy, pytest, and pre-commit configs
#

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]


def generate_ruff_config(project_path: Path) -> None:
    """Generate ruff configuration."""
    config_content = """# Ruff configuration
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011"]

[isort]
known-first-party = ["dht"]
"""

    ruff_config = project_path / "ruff.toml"
    ruff_config.write_text(config_content)


def generate_black_config(project_path: Path) -> None:
    """Generate black configuration in pyproject.toml."""
    pyproject = project_path / "pyproject.toml"

    # Read existing or create new
    config_dict = {}
    if pyproject.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        try:
            with open(pyproject, "rb") as f:
                config_dict = tomllib.load(f)
        except Exception:
            pass

    # Add black configuration
    if "tool" not in config_dict:
        config_dict["tool"] = {}

    config_dict["tool"]["black"] = {
        "line-length": 88,
        "target-version": ["py311"],
        "include": r"\.pyi?$",
        "extend-exclude": r"""
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
""",
    }

    # Write back
    try:
        import tomli_w

        with open(pyproject, "wb") as f:
            tomli_w.dump(config_dict, f)
    except ImportError:
        # Fallback: write TOML manually for the common case
        # This is a simplified TOML writer that handles our specific case
        lines = []
        if "tool" in config_dict and "black" in config_dict["tool"]:
            lines.append("[tool.black]")
            black_config = config_dict["tool"]["black"]
            for key, value in black_config.items():
                if isinstance(value, str):
                    # Handle multiline strings
                    if "\n" in value:
                        lines.append(f'{key} = """{value}"""')
                    else:
                        lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    lines.append(f"{key} = {value}")
                else:
                    lines.append(f"{key} = {value}")

        with open(pyproject, "w") as f:
            f.write("\n".join(lines) + "\n")


def generate_mypy_config(project_path: Path) -> None:
    """Generate mypy configuration."""
    config_content = """[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

# Per-module options
[mypy-tests.*]
disallow_untyped_defs = False

[mypy-setup]
ignore_errors = True
"""

    mypy_config = project_path / "mypy.ini"
    mypy_config.write_text(config_content)


def generate_pytest_config(project_path: Path) -> None:
    """Generate pytest configuration."""
    config_content = """[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    requires_network: marks tests that require network access
"""

    pytest_config = project_path / "pytest.ini"
    pytest_config.write_text(config_content)


def generate_precommit_config(project_path: Path, quality_tools: list[str]) -> None:
    """Generate pre-commit configuration."""
    repos = []

    # Add pre-commit hooks based on configured tools
    if "black" in quality_tools:
        repos.append({"repo": "https://github.com/psf/black", "rev": "23.7.0", "hooks": [{"id": "black"}]})

    if "ruff" in quality_tools:
        repos.append(
            {
                "repo": "https://github.com/astral-sh/ruff-pre-commit",
                "rev": "v0.0.287",
                "hooks": [{"id": "ruff", "args": ["--fix"]}, {"id": "ruff-format"}],
            }
        )

    if "mypy" in quality_tools:
        repos.append(
            {
                "repo": "https://github.com/pre-commit/mirrors-mypy",
                "rev": "v1.5.1",
                "hooks": [{"id": "mypy", "additional_dependencies": ["types-all"]}],
            }
        )

    # Add common hooks
    repos.append(
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v4.4.0",
            "hooks": [
                {"id": "trailing-whitespace"},
                {"id": "end-of-file-fixer"},
                {"id": "check-yaml"},
                {"id": "check-added-large-files"},
                {"id": "check-merge-conflict"},
                {"id": "check-case-conflict"},
                {"id": "check-json"},
                {"id": "check-toml"},
                {"id": "check-xml"},
                {"id": "debug-statements"},
                {"id": "mixed-line-ending"},
            ],
        }
    )

    config = {
        "repos": repos,
        "default_language_version": {"python": "python3.11"},
        "ci": {
            "autoupdate_schedule": "weekly",
            "skip": ["mypy"],  # Often needs manual dependency updates
        },
    }

    precommit_config = project_path / ".pre-commit-config.yaml"
    with open(precommit_config, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def generate_editorconfig(project_path: Path) -> None:
    """Generate .editorconfig file."""
    config_content = """# EditorConfig is awesome: https://EditorConfig.org

# top-most EditorConfig file
root = true

# Unix-style newlines with a newline ending every file
[*]
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
charset = utf-8

# Python files
[*.py]
indent_style = space
indent_size = 4
max_line_length = 88

# YAML files
[*.{yml,yaml}]
indent_style = space
indent_size = 2

# JSON files
[*.json]
indent_style = space
indent_size = 2

# Markdown files
[*.md]
trim_trailing_whitespace = false

# Makefiles
[Makefile]
indent_style = tab
"""

    editorconfig = project_path / ".editorconfig"
    editorconfig.write_text(config_content)


def generate_all_configs(project_path: Path, quality_tools: list[str], project_type: str = "python") -> list[str]:
    """
    Generate all configuration files.

    Args:
        project_path: Path to project directory
        quality_tools: List of quality tools to configure
        project_type: Type of project

    Returns:
        List of files created
    """
    files_created = []

    # Generate tool configs based on what's in quality_tools
    if "ruff" in quality_tools:
        generate_ruff_config(project_path)
        files_created.append("ruff.toml")

    if "black" in quality_tools:
        generate_black_config(project_path)
        files_created.append("pyproject.toml [tool.black]")

    if "mypy" in quality_tools:
        generate_mypy_config(project_path)
        files_created.append("mypy.ini")

    if "pytest" in quality_tools:
        generate_pytest_config(project_path)
        files_created.append("pytest.ini")

    # Always generate these
    generate_precommit_config(project_path, quality_tools)
    files_created.append(".pre-commit-config.yaml")

    generate_editorconfig(project_path)
    files_created.append(".editorconfig")

    return files_created
