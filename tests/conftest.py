#!/usr/bin/env python3
"""
Conftest module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

import os
import sys
from pathlib import Path
from typing import Any

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


def is_running_in_ci() -> bool:
    """Check if tests are running in CI environment."""
    return any([
        os.environ.get("CI"),
        os.environ.get("GITHUB_ACTIONS"),
        os.environ.get("DHT_IN_DOCKER"),
        os.environ.get("DHT_TEST_MODE")
    ])


def get_test_profile() -> str:
    """Get the current test profile."""
    if os.environ.get("DHT_TEST_PROFILE"):
        return os.environ.get("DHT_TEST_PROFILE", "local")
    return "ci" if is_running_in_ci() else "local"


# Test configuration based on profile
TEST_CONFIGS = {
    "local": {
        "max_retries": 10,
        "timeout": 60,
        "skip_slow_tests": False,
        "skip_network_tests": False,
        "skip_docker_tests": False,
        "api_mock_enabled": True,
        "temp_dir_prefix": "/tmp/dht_test_",
        "cleanup_temp_dirs": True,
        "allow_network": True,
        "debug_enabled": True,
        "comprehensive_tests": True,
        "memory_limit_mb": 4096,
    },
    "remote": {
        "max_retries": 2,
        "timeout": 5,
        "skip_slow_tests": True,
        "skip_network_tests": False,
        "skip_docker_tests": True,
        "api_mock_enabled": True,
        "temp_dir_prefix": "/tmp/dht_remote_test_",
        "cleanup_temp_dirs": True,
        "allow_network": False,
        "debug_enabled": False,
        "comprehensive_tests": False,
        "memory_limit_mb": 1024,
    },
    "ci": {
        "max_retries": 2,
        "timeout": 5,
        "skip_slow_tests": True,
        "skip_network_tests": False,
        "skip_docker_tests": True,  # Docker-in-Docker is complex
        "api_mock_enabled": True,
        "temp_dir_prefix": "/tmp/dht_ci_test_",
        "cleanup_temp_dirs": True,
        "allow_network": False,
        "debug_enabled": False,
        "comprehensive_tests": False,
        "memory_limit_mb": 1024,
    },
    "docker": {
        "max_retries": 3,
        "timeout": 10,
        "skip_slow_tests": False,
        "skip_network_tests": False,
        "skip_docker_tests": True,  # Already in Docker
        "api_mock_enabled": True,
        "temp_dir_prefix": "/tmp/dht_docker_test_",
        "cleanup_temp_dirs": True,
        "allow_network": True,
        "debug_enabled": False,
        "comprehensive_tests": True,
        "memory_limit_mb": 2048,
    }
}


@pytest.fixture(scope="session")
def test_profile() -> str:
    """Get current test profile."""
    return get_test_profile()


@pytest.fixture(scope="session")
def test_config(test_profile: str) -> dict[str, Any]:
    """Get test configuration for current profile."""
    return TEST_CONFIGS.get(test_profile, TEST_CONFIGS["local"])


@pytest.fixture
def max_retries(test_config: dict[str, Any]) -> int:
    """Get maximum retries for current profile."""
    return test_config["max_retries"]


@pytest.fixture
def timeout(test_config: dict[str, Any]) -> int:
    """Get timeout for current profile."""
    return test_config["timeout"]


@pytest.fixture(autouse=True)
def skip_by_profile(request: pytest.FixtureRequest, test_config: dict[str, Any]) -> None:
    """Skip tests based on profile configuration."""
    markers = request.node.iter_markers()

    for marker in markers:
        if marker.name == "slow" and test_config["skip_slow_tests"]:
            pytest.skip(f"Skipping slow test in {get_test_profile()} profile")
        elif marker.name == "network" and test_config["skip_network_tests"]:
            pytest.skip(f"Skipping network test in {get_test_profile()} profile")
        elif marker.name == "docker" and test_config["skip_docker_tests"]:
            pytest.skip(f"Skipping docker test in {get_test_profile()} profile")


@pytest.fixture(scope="session")
def project_root() -> Any:
    """Returns the project root directory (parent of DHT)."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_dir_session_scoped(tmp_path_factory) -> Any:
    """Create a temporary directory for tests that is cleaned up after session."""
    temp_dir = tmp_path_factory.mktemp("dht_tests_")
    yield temp_dir
    # tmp_path_factory handles cleanup


@pytest.fixture
def mock_project_dir(temp_dir_session_scoped) -> Any:
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
def mock_dht_env(monkeypatch, project_root) -> Any:
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
def mock_project_with_venv(mock_project_dir) -> Any:
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


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "docker: marks tests that require Docker")
    config.addinivalue_line("markers", "integration: marks integration tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Modify test collection for better organization."""
    profile = get_test_profile()
    for item in items:
        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


def pytest_sessionfinish(session, exitstatus) -> Any:
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
            print(f"🔧 Test Profile: {get_test_profile()}")
    except Exception as e:
        print(f"\nError generating test summary: {e}")
