import os
import sys
from pathlib import Path

import pytest

# Add the DHT directory to sys.path to allow imports from DHT modules if needed
# This assumes conftest.py is in DHT/tests/
dht_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if dht_dir not in sys.path:
    sys.path.insert(0, dht_dir)

# Also add the parent directory to allow 'from DHT' imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


@pytest.fixture(scope="session")
def project_root():
    """Returns the project root directory (parent of DHT)."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_dir_session_scoped(tmp_path_factory):
    """Create a temporary directory for tests that is cleaned up after session."""
    temp_dir = tmp_path_factory.mktemp("dht_tests_")
    yield temp_dir
    # tmp_path_factory handles cleanup


@pytest.fixture
def mock_project_dir(temp_dir_session_scoped):
    """Create a mock project directory with basic structure within a temp dir."""
    project_dir = Path(temp_dir_session_scoped) / "mock_project"
    project_dir.mkdir(exist_ok=True)

    # Create basic project structure
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "DHT").mkdir(exist_ok=True)  # For testing dhtl init within mock

    # Create some mock files
    (project_dir / "pyproject.toml").touch()
    (project_dir / "README.md").touch()

    yield project_dir


@pytest.fixture
def mock_dht_env(monkeypatch, project_root):
    """Set up environment variables for DHT testing."""
    dht_dir = project_root / "DHT"
    monkeypatch.setenv("DHTL_SESSION_ID", "test_session_123")
    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("DHTL_DIR", str(dht_dir))  # dhtl.sh is in DHT
    monkeypatch.setenv("DHT_DIR", str(dht_dir))
    monkeypatch.setenv("DEFAULT_VENV_DIR", str(project_root / ".venv"))
    monkeypatch.setenv("DHTL_SKIP_ENV_SETUP", "1")
    monkeypatch.setenv("SKIP_ENV_CHECK", "1")
    monkeypatch.setenv("IN_DHTL", "1")
    monkeypatch.setenv("DEBUG_MODE", "true")  # Enable debug for more output

    # Ensure PATH includes potential venv bin if tests need it
    venv_bin = project_root / ".venv" / "bin"
    if venv_bin.is_dir():
        monkeypatch.setenv("PATH", f"{venv_bin}:{os.environ.get('PATH', '')}", prepend=":")

    return os.environ.copy()


@pytest.fixture
def mock_project_with_venv(mock_project_dir):
    """Create a mock project with a virtual environment."""
    # Create venv directory structure
    venv_dir = mock_project_dir / ".venv"
    venv_dir.mkdir(exist_ok=True)

    # Create basic venv structure
    (venv_dir / "bin").mkdir(exist_ok=True)
    (venv_dir / "lib").mkdir(exist_ok=True)
    (venv_dir / "include").mkdir(exist_ok=True)

    # Create activate script
    activate_script = venv_dir / "bin" / "activate"
    activate_script.write_text("#!/bin/bash\n# Mock activate script\n")
    activate_script.chmod(0o755)

    # Create python executable
    python_exe = venv_dir / "bin" / "python"
    python_exe.write_text("#!/bin/bash\n# Mock python\n")
    python_exe.chmod(0o755)

    # Create pyvenv.cfg
    pyvenv_cfg = venv_dir / "pyvenv.cfg"
    pyvenv_cfg.write_text("home = /usr/local/bin\nversion = 3.11.0\n")

    return mock_project_dir


def pytest_sessionfinish(session, exitstatus):
    """Print a summary of test results at the end of the session."""
    try:
        reporter = session.config.pluginmanager.getplugin("terminalreporter")
        if reporter:  # Reporter might not be available in all contexts (e.g. collection error)
            passed = len(reporter.stats.get("passed", []))
            failed = len(reporter.stats.get("failed", []))
            skipped = len(reporter.stats.get("skipped", []))

            print("\n📊 DHT Test Summary")
            print(f"Total Tests: {passed + failed + skipped}")
            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"⏩ Skipped: {skipped}")
    except Exception as e:
        print(f"\nError generating test summary: {e}")
