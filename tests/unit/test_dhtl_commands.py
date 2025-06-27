#!/usr/bin/env python3
"""
Tests for DHT command modules.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Set environment variable to prevent actual command execution
os.environ["DHT_TEST_MODE"] = "1"

from DHT.modules.dhtl_commands_1 import restore_command
from DHT.modules.dhtl_commands_2 import test_command
from DHT.modules.dhtl_commands_5 import coverage_command
from DHT.modules.dhtl_commands_6 import commit_command
from DHT.modules.dhtl_commands_7 import publish_command
from DHT.modules.dhtl_commands_8 import clean_command


def test_imports():
    """Test that all command modules can be imported."""
    assert callable(restore_command)
    assert callable(test_command)
    assert callable(coverage_command)
    assert callable(commit_command)
    assert callable(publish_command)
    assert callable(clean_command)


class TestRestoreCommand:
    """Test restore command functionality."""

    def test_restore_with_uv_lock(self, tmp_path: Path) -> None:
        """Test restoring with uv.lock file."""
        # Create mock files
        (tmp_path / "uv.lock").touch()
        (tmp_path / "pyproject.toml").touch()

        with patch("DHT.modules.dhtl_commands_1.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_1.shutil.which", return_value="uv"):
                with patch("DHT.modules.dhtl_commands_1.run_with_guardian", return_value=0):
                    result = restore_command()
                    assert result == 0

    def test_restore_with_requirements_txt(self, tmp_path: Path) -> None:
        """Test restoring with requirements.txt file."""
        # Create mock files
        (tmp_path / "requirements.txt").write_text("pytest>=7.0.0\n")

        with patch("DHT.modules.dhtl_commands_1.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_1.shutil.which", return_value=None):
                with patch("DHT.modules.dhtl_commands_1.run_with_guardian", return_value=0):
                    with patch("DHT.modules.dhtl_commands_1.subprocess.run", return_value=MagicMock(returncode=0)):
                        result = restore_command()
                        assert result == 0

    def test_restore_no_lock_files(self, tmp_path: Path) -> None:
        """Test restoring with no lock files."""
        with patch("DHT.modules.dhtl_commands_1.find_project_root", return_value=tmp_path):
            result = restore_command()
            assert result == 1


class TestTestCommand:
    """Test test command functionality."""

    def test_test_with_pytest(self, tmp_path: Path) -> None:
        """Test running tests with pytest."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "bin").mkdir()
        (venv_dir / "bin" / "pytest").touch()

        with patch("DHT.modules.dhtl_commands_2.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_2.find_virtual_env", return_value=venv_dir):
                with patch("DHT.modules.dhtl_commands_2.run_with_guardian", return_value=0) as mock_guardian:
                    result = test_command()
                    assert result == 0
                    # Verify run_with_guardian was called
                    mock_guardian.assert_called_once()

    def test_test_with_extra_args(self, tmp_path: Path) -> None:
        """Test running tests with extra arguments."""
        with patch("DHT.modules.dhtl_commands_2.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_2.shutil.which", return_value="pytest"):
                with patch("DHT.modules.dhtl_commands_2.run_with_guardian", return_value=0) as mock_guardian:
                    result = test_command(["-v", "--tb=short"])
                    assert result == 0
                    # Check that extra args were passed
                    args = mock_guardian.call_args[0]
                    assert "-v" in args
                    assert "--tb=short" in args


class TestCoverageCommand:
    """Test coverage command functionality."""

    def test_coverage_with_pytest_cov(self, tmp_path: Path) -> None:
        """Test running coverage with pytest-cov."""
        with patch("DHT.modules.dhtl_commands_5.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_5.shutil.which", return_value="pytest"):
                with patch("DHT.modules.dhtl_commands_5.run_with_guardian", return_value=0) as mock_guardian:
                    result = coverage_command()
                    assert result == 0
                    # Verify run_with_guardian was called
                    mock_guardian.assert_called_once()

    def test_coverage_no_pytest(self, tmp_path: Path) -> None:
        """Test coverage when pytest is not installed."""
        with patch("DHT.modules.dhtl_commands_5.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_5.shutil.which", return_value=None):
                result = coverage_command()
                assert result == 1


class TestCommitCommand:
    """Test commit command functionality."""

    def test_commit_with_message(self, tmp_path: Path) -> None:
        """Test creating commit with message."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("DHT.modules.dhtl_commands_6.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_6.shutil.which", return_value="git"):
                with patch("DHT.modules.dhtl_commands_6.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="M file.py\n")
                    result = commit_command(["--message", "Test commit"])
                    assert result == 0

    def test_commit_no_changes(self, tmp_path: Path) -> None:
        """Test commit when no changes."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("DHT.modules.dhtl_commands_6.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_6.shutil.which", return_value="git"):
                with patch("DHT.modules.dhtl_commands_6.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="")
                    result = commit_command()
                    assert result == 0


class TestPublishCommand:
    """Test publish command functionality."""

    def test_publish_with_uv(self, tmp_path: Path) -> None:
        """Test publishing with uv."""
        (tmp_path / "pyproject.toml").touch()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "package-1.0.0.whl").touch()

        with patch("DHT.modules.dhtl_commands_7.find_project_root", return_value=tmp_path):
            with patch("DHT.modules.dhtl_commands_7.shutil.which", return_value="uv"):
                with patch("DHT.modules.dhtl_commands_7.run_with_guardian", return_value=0):
                    result = publish_command()
                    assert result == 0

    def test_publish_no_dist(self, tmp_path: Path) -> None:
        """Test publish when no dist directory."""
        (tmp_path / "pyproject.toml").touch()

        with patch("DHT.modules.dhtl_commands_7.find_project_root", return_value=tmp_path):
            result = publish_command()
            assert result == 1


class TestCleanCommand:
    """Test clean command functionality."""

    def test_clean_basic(self, tmp_path: Path) -> None:
        """Test basic clean operation."""
        # Create some files to clean
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").touch()

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        with patch("DHT.modules.dhtl_commands_8.find_project_root", return_value=tmp_path):
            result = clean_command()
            assert result == 0
            # Check that directories were cleaned
            assert not pycache.exists()
            assert not build_dir.exists()

    def test_clean_with_all(self, tmp_path: Path) -> None:
        """Test clean with --all flag."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        with patch("DHT.modules.dhtl_commands_8.find_project_root", return_value=tmp_path):
            result = clean_command(["--all"])
            assert result == 0
            # .venv should be removed with --all
            assert not venv_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
