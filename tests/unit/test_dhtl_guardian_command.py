#!/usr/bin/env python3

"""Test for DHT guardian functionality - updated for Python/Prefect migration."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_guardian_prefect_module():
    """Test that guardian_prefect module can be imported."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from modules import guardian_prefect
        assert hasattr(guardian_prefect, 'GuardianResult')
        assert hasattr(guardian_prefect, 'ResourceLimits')
        assert hasattr(guardian_prefect, 'run_with_guardian')
        assert hasattr(guardian_prefect, 'monitor_process')
        assert hasattr(guardian_prefect, 'check_system_resources')
    except ImportError as e:
        pytest.fail(f"Failed to import guardian_prefect: {e}")

@pytest.mark.unit
def test_resource_limits_class():
    """Test ResourceLimits class."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from DHT.modules.guardian_prefect import ResourceLimits

    # Test default values
    limits = ResourceLimits()
    assert limits.memory_mb == 2048
    assert limits.cpu_percent == 80
    assert limits.timeout == 900

    # Test custom values
    custom_limits = ResourceLimits(
        memory_mb=4096,
        cpu_percent=90,
        timeout=600
    )
    assert custom_limits.memory_mb == 4096
    assert custom_limits.cpu_percent == 90
    assert custom_limits.timeout == 600

@pytest.mark.unit
def test_guardian_result_dataclass():
    """Test GuardianResult dataclass."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from DHT.modules.guardian_prefect import GuardianResult

    # Test successful result
    result = GuardianResult(
        return_code=0,
        stdout="test output",
        stderr="",
        execution_time=1.5,
        peak_memory_mb=512.0,
        was_killed=False,
        kill_reason=None
    )
    assert result.success is True
    assert result.return_code == 0
    assert result.stdout == "test output"
    assert result.was_killed is False
    assert result.duration == 1.5  # Test alias property

    # Test terminated result
    terminated_result = GuardianResult(
        return_code=-15,
        stdout="",
        stderr="Process terminated",
        execution_time=0.5,
        peak_memory_mb=2100.0,
        was_killed=True,
        kill_reason="Memory limit exceeded"
    )
    assert terminated_result.success is False
    assert terminated_result.was_killed is True
    assert "Memory limit exceeded" in terminated_result.kill_reason

@pytest.mark.unit
def test_check_system_resources():
    """Test check_system_resources function exists and has correct structure."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from DHT.modules.guardian_prefect import check_system_resources

    # Check that it's a Prefect task
    assert hasattr(check_system_resources, '__wrapped__'), "check_system_resources should be a Prefect task"

    # Check the task has the right attributes
    assert hasattr(check_system_resources, 'name')
    assert check_system_resources.name == 'check-resources'

    # We can't test the actual function execution without a Prefect context
    # but we can verify it exists and is properly decorated

@pytest.mark.unit
def test_run_with_guardian_success():
    """Test run_with_guardian with successful execution."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from unittest.mock import patch

    from DHT.modules.guardian_prefect import GuardianResult, ResourceLimits, run_with_guardian

    with patch('DHT.modules.guardian_prefect.run_command_with_limits') as mock_run_command:
        # Mock successful command result
        mock_run_command.return_value = {
            "returncode": 0,
            "stdout": "Success output",
            "stderr": "",
            "duration": 0.5,
            "peak_memory_mb": 512.0,
            "killed": False,
            "reason": None
        }

        # Run command
        result = run_with_guardian(
            ["echo", "test"],
            limits=ResourceLimits(memory_mb=1024)
        )

        assert isinstance(result, GuardianResult)
        assert result.success is True
        assert result.return_code == 0
        assert result.stdout == "Success output"
        assert result.was_killed is False

@pytest.mark.unit
def test_dhtl_guardian_prefect_module():
    """Test the dhtl_guardian_prefect module exists."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from modules import dhtl_guardian_prefect
        # This module should provide a Python interface for the guardian
        assert hasattr(dhtl_guardian_prefect, 'parse_args')
        assert hasattr(dhtl_guardian_prefect, 'main')
    except ImportError as e:
        pytest.fail(f"Failed to import dhtl_guardian_prefect: {e}")

@pytest.mark.unit
@patch('sys.argv', ['guardian', 'echo', 'test'])
def test_guardian_cli_interface():
    """Test the guardian CLI interface."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from unittest.mock import patch

    from DHT.modules.dhtl_guardian_prefect import main
    from DHT.modules.guardian_prefect import GuardianResult

    with patch('DHT.modules.guardian_prefect.run_with_guardian') as mock_run_with_guardian:
        # Mock successful result
        mock_result = GuardianResult(
            return_code=0,
            stdout="test",
            stderr="",
            execution_time=0.1,
            peak_memory_mb=100.0,
            was_killed=False,
            kill_reason=None
        )
        mock_run_with_guardian.return_value = mock_result

        # Run CLI
        exit_code = main()

        assert exit_code == 0
        mock_run_with_guardian.assert_called_once()

        # Check command was parsed correctly
        call_args = mock_run_with_guardian.call_args
        assert call_args[0][0] == ['echo', 'test']
