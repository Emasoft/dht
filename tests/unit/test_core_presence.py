from typing import Any

#!/usr/bin/env python3
"""
Test for DHT core files presence - updated for Python/Prefect migration.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Test for DHT core files presence - updated for Python/Prefect migration."""


def test_dht_core_files_exist(project_root) -> Any:
    """Test that essential DHT core files exist after Python migration."""
    # UV-style src layout - project_root points to /Users/emanuelesabetta/Code/DHT
    # The actual project is in the dht subdirectory
    actual_project_root = project_root / "dht"
    dht_dir = actual_project_root / "src" / "DHT"
    assert dht_dir.is_dir(), f"DHT directory {dht_dir} does not exist"

    modules_dir = dht_dir / "modules"
    assert modules_dir.is_dir(), f"DHT modules directory {modules_dir} does not exist"

    # Check for existing Python modules
    core_python_modules = [
        "modules/__init__.py",
        "modules/guardian_prefect.py",
        "modules/uv_prefect_tasks.py",
        "modules/uv_manager.py",
        "modules/dhtconfig.py",
        "modules/project_analyzer.py",
        "modules/environment_configurator.py",
        "modules/environment_reproducer.py",
        "modules/cli_commands_registry.py",
        "diagnostic_reporter_v2.py",  # Current diagnostic reporter
        "modules/dht_flows/__init__.py",
        "modules/dht_flows/restore_flow.py",
        "modules/dht_flows/test_flow.py",
    ]

    for module_path in core_python_modules:
        full_path = dht_dir / module_path
        assert full_path.is_file(), f"Essential DHT Python module {full_path} does not exist"

    # Check for the main entry point
    main_py = actual_project_root / "main.py"
    assert main_py.is_file(), f"Main entry point {main_py} does not exist"

    # Check that pyproject.toml exists with proper dependencies
    pyproject = actual_project_root / "pyproject.toml"
    assert pyproject.is_file(), f"pyproject.toml {pyproject} does not exist"

    # Verify Prefect is in dependencies
    pyproject_content = pyproject.read_text()
    assert "prefect" in pyproject_content, "Prefect dependency not found in pyproject.toml"
    assert 'requires-python = ">=3.10"' in pyproject_content or 'requires-python = ">=3.11"' in pyproject_content, (
        "Python 3.10+ requirement not found"
    )


def test_dht_parsers_exist(project_root) -> Any:
    """Test that parser modules exist."""
    # UV-style src layout - project_root points to /Users/emanuelesabetta/Code/DHT
    # The actual project is in the dht subdirectory
    actual_project_root = project_root / "dht"
    parsers_dir = actual_project_root / "src" / "DHT" / "modules" / "parsers"
    assert parsers_dir.is_dir(), f"Parsers directory {parsers_dir} does not exist"

    parser_files = [
        "__init__.py",
        "base_parser.py",
        "python_parser.py",
        "bash_parser.py",
    ]

    for parser_file in parser_files:
        full_path = parsers_dir / parser_file
        assert full_path.is_file(), f"Parser module {full_path} does not exist"
