#!/usr/bin/env python3
"""
Tests for the Python implementation of dhtl.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Tests for the Python implementation of dhtl."""

import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DHTL_PY = PROJECT_ROOT / "dhtl_entry.py"


def test_dhtl_version() -> Any:
    """Test that dhtl version command works."""
    result = subprocess.run([sys.executable, str(DHTL_PY), "version"], capture_output=True, text=True, cwd=PROJECT_ROOT)
    assert result.returncode == 0
    assert "Development Helper Toolkit" in result.stdout


def test_dhtl_help() -> Any:
    """Test that dhtl help command works."""
    result = subprocess.run([sys.executable, str(DHTL_PY), "help"], capture_output=True, text=True, cwd=PROJECT_ROOT)
    assert result.returncode == 0
    assert "Available commands" in result.stdout


def test_dhtl_unknown_command() -> Any:
    """Test that unknown commands return error."""
    result = subprocess.run(
        [sys.executable, str(DHTL_PY), "totally_unknown_command"], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 1
    assert "Unknown command" in result.stdout


def test_dhtl_init_help() -> Any:
    """Test that init command help works."""
    result = subprocess.run(
        [sys.executable, str(DHTL_PY), "init", "--help"], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
    assert "init" in result.stdout
    assert "--python" in result.stdout


def test_dhtl_setup_help() -> Any:
    """Test that setup command help works."""
    result = subprocess.run(
        [sys.executable, str(DHTL_PY), "setup", "--help"], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    assert result.returncode == 0
    assert "setup" in result.stdout
    assert "--dev" in result.stdout
