#!/usr/bin/env python3
"""
Test Dhtl Cli module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

import subprocess
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DHTL = PROJECT_ROOT / "dhtl_entry.py"


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl_entry.py not found")
def test_version() -> Any:
    res = subprocess.run(
        ["python", str(DHTL), "--no-guardian", "--quiet", "version"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    assert "Development Helper Toolkit Launcher" in res.stdout


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl_entry.py not found")
def test_help() -> Any:
    res = subprocess.run(
        ["python", str(DHTL), "--no-guardian", "--quiet", "help"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    assert "Available commands" in res.stdout


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl_entry.py not found")
def test_unknown_command_exit_code() -> Any:
    res = subprocess.run(
        ["python", str(DHTL), "--no-guardian", "--quiet", "totally_unknown"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert res.returncode != 0
    assert "Unknown command" in res.stdout or "Unknown command" in res.stderr
