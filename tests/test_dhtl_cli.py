import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DHTL = PROJECT_ROOT / "dhtl.sh"


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl.sh non trovato")
def test_version():
    res = subprocess.run(
        [str(DHTL), "--no-guardian", "--quiet", "version"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    assert "Development Helper Toolkit Launcher" in res.stdout


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl.sh non trovato")
def test_help():
    res = subprocess.run(
        [str(DHTL), "--no-guardian", "--quiet", "help"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    assert "Available commands" in res.stdout


@pytest.mark.skipif(not DHTL.exists(), reason="dhtl.sh non trovato")
def test_unknown_command_exit_code():
    res = subprocess.run(
        [str(DHTL), "--no-guardian", "--quiet", "totally_unknown"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert res.returncode != 0
    assert "Unknown command" in res.stdout or "Unknown command" in res.stderr
