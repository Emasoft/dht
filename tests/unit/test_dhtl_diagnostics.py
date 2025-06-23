#!/usr/bin/env python3
"""
Test for DHT diagnostics functionality - updated for Python/Prefect migration.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Test for DHT diagnostics functionality - updated for Python/Prefect migration."""

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest


# Test the Python diagnostic reporter directly
def test_diagnostic_reporter_v2_module() -> Any:
    """Test that diagnostic_reporter_v2 module can be imported."""
    try:
        from DHT import diagnostic_reporter_v2

        assert hasattr(diagnostic_reporter_v2, "build_system_report")
        assert hasattr(diagnostic_reporter_v2, "parse_args")
        assert hasattr(diagnostic_reporter_v2, "main")
    except ImportError as e:
        pytest.fail(f"Failed to import diagnostic_reporter_v2: {e}")


@pytest.mark.unit
@patch("subprocess.run")
def test_build_system_report(mock_subprocess) -> Any:
    """Test the build_system_report function from diagnostic_reporter_v2."""
    from DHT.diagnostic_reporter_v2 import build_system_report

    # Mock subprocess responses
    def mock_run(*args, **kwargs) -> Any:
        cmd = args[0] if isinstance(args[0], list) else args[0].split()
        result = Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""

        # Mock common commands
        if "python" in cmd[0] and "--version" in cmd:
            result.stdout = "Python 3.11.12"
        elif "git" in cmd[0] and "--version" in cmd:
            result.stdout = "git version 2.39.3"
        elif "uv" in cmd[0] and "--version" in cmd:
            result.stdout = "uv 0.7.12"
        elif "pip" in cmd[0] and "--version" in cmd:
            result.stdout = "pip 23.3.1 from /path/to/pip (python 3.11)"
        else:
            result.returncode = 127  # Command not found

        return result

    mock_subprocess.side_effect = mock_run

    # Run the system report
    report = build_system_report()

    # Verify structure
    assert isinstance(report, dict)
    assert "system" in report
    assert "tools" in report

    # Check system info
    system_info = report["system"]
    assert "platform" in system_info
    assert "machine" in system_info  # Architecture info is in 'machine' field
    assert "network" in system_info  # Hostname is in network.hostname

    # Check tools were detected
    tools = report["tools"]
    assert "version_control" in tools
    assert "language_runtimes" in tools
    assert "package_managers" in tools


@pytest.mark.unit
def test_diagnostic_cli_registry() -> Any:
    """Test that diagnostic commands are registered in CLI registry."""
    from DHT.modules.cli_commands_registry import CLI_COMMANDS, get_commands_by_category

    # Check that common diagnostic-related commands exist
    expected_commands = ["python", "pip", "git", "uv"]
    for cmd in expected_commands:
        assert cmd in CLI_COMMANDS, f"Expected command '{cmd}' not found in registry"

    # Check commands have proper structure
    for cmd_name, cmd_data in CLI_COMMANDS.items():
        assert "commands" in cmd_data, f"Command {cmd_name} missing 'commands' field"
        assert "category" in cmd_data, f"Command {cmd_name} missing 'category' field"

    # Test category filtering
    version_control_cmds = get_commands_by_category("version_control")
    assert "git" in version_control_cmds

    language_runtime_cmds = get_commands_by_category("language_runtimes")
    assert "python" in language_runtime_cmds


@pytest.mark.unit
@patch("DHT.diagnostic_reporter_v2.build_system_report")
def test_diagnostic_main_function(mock_build_report, tmp_path) -> Any:
    """Test the main function of diagnostic_reporter_v2."""
    from DHT.diagnostic_reporter_v2 import main

    # Mock the system report
    mock_report = {
        "system": {"platform": "darwin", "architecture": "arm64", "hostname": "test-machine"},
        "tools": {"version_control": {"git": {"is_installed": True, "version": "2.39.3"}}},
    }
    mock_build_report.return_value = mock_report

    # Create output file path
    output_file = tmp_path / "test_report.yaml"

    # Test with YAML output
    with patch("sys.argv", ["diagnostic_reporter.py", "--output", str(output_file), "--format", "yaml"]):
        main()

    # Verify output file was created
    assert output_file.exists()

    # Verify YAML content
    import yaml  # type: ignore[import-untyped]

    with open(output_file) as f:
        data = yaml.safe_load(f)

    assert data["system"]["platform"] == "darwin"
    assert data["tools"]["version_control"]["git"]["version"] == "2.39.3"


@pytest.mark.unit
def test_diagnostic_taxonomy() -> Any:
    """Test that system taxonomy is properly structured."""
    from DHT.modules.system_taxonomy import PRACTICAL_TAXONOMY as TAXONOMY

    # Check main categories exist - PRACTICAL_TAXONOMY is a flat structure of tool categories
    assert "version_control" in TAXONOMY
    assert "language_runtimes" in TAXONOMY
    assert "package_managers" in TAXONOMY

    # Check tool categories exist at top level
    expected_categories = [
        "version_control",
        "language_runtimes",
        "package_managers",
        "build_tools",
        "containers_virtualization",
    ]

    for category in expected_categories:
        assert category in TAXONOMY, f"Expected category '{category}' not in taxonomy"


@pytest.mark.unit
def test_diagnostic_output_formats(tmp_path) -> Any:
    """Test different output formats for diagnostics."""
    import yaml

    from DHT.diagnostic_reporter_v2 import build_system_report

    # Get a report
    report = build_system_report()

    # Test JSON serialization
    json_file = tmp_path / "report.json"
    with open(json_file, "w") as f:
        json.dump(report, f, indent=2)
    assert json_file.exists()

    # Test YAML serialization
    yaml_file = tmp_path / "report.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(report, f, default_flow_style=False)
    assert yaml_file.exists()

    # Verify both files have content
    assert json_file.stat().st_size > 100
    assert yaml_file.stat().st_size > 100
