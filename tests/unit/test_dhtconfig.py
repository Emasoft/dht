#!/usr/bin/env python3
"""
Unit tests for dhtconfig module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""Unit tests for dhtconfig module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from DHT.modules.dhtconfig import DHTConfig


class TestDHTConfig:
    """Test cases for DHTConfig class."""

    def test_init(self):
        """Test DHTConfig initialization."""
        config = DHTConfig()
        assert config.SCHEMA_VERSION == "1.0.0"
        assert config.CONFIG_FILENAME == ".dhtconfig"
        assert hasattr(config, "project_analyzer")

    def test_extract_version(self):
        """Test version extraction from various formats."""
        config = DHTConfig()

        # Test various version output formats
        assert config._extract_version("black, 23.7.0") == "23.7.0"
        assert config._extract_version("version 1.2.3") == "1.2.3"
        assert config._extract_version("mypy v0.991") == "0.991"
        assert config._extract_version("pytest 7.4.3") == "7.4.3"
        assert config._extract_version("unknown format") == "unknown"

    @patch("DHT.modules.dhtconfig_validation_utils.subprocess.run")
    def test_generate_validation_info(self, mock_run):
        """Test validation info generation."""
        config = DHTConfig()

        # Mock subprocess responses
        mock_run.return_value = Mock(returncode=0, stdout="black, 23.7.0")

        # Create a temporary project with some files
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create test files
            (project_path / "requirements.txt").write_text("pytest==7.4.3\n")
            (project_path / "pyproject.toml").write_text("[tool.black]\nline-length = 88\n")

            validation = config._generate_validation_info(project_path, {})

            # Check checksums were generated
            assert "checksums" in validation
            assert "requirements.txt" in validation["checksums"]
            assert "pyproject.toml" in validation["checksums"]
            assert len(validation["checksums"]["requirements.txt"]) == 64  # SHA256 length

            # Check tool behaviors
            assert "tool_behaviors" in validation
            assert "black" in validation["tool_behaviors"]
            assert validation["tool_behaviors"]["black"]["version"] == "23.7.0"

    def test_extract_dependencies(self):
        """Test dependency extraction from project info."""
        config = DHTConfig()

        # Test with dict format (from project_analyzer)
        project_info = {
            "dependencies": {
                "python": {
                    "runtime": ["requests", "click", "pydantic"],
                    "development": ["pytest", "mypy", "ruff"],
                    "all": ["requests", "click", "pydantic", "pytest", "mypy", "ruff"],
                }
            },
            "root_path": "/tmp/test_project",
        }

        deps = config._extract_dependencies(project_info)

        assert len(deps["python_packages"]) == 3  # Only runtime deps
        assert deps["python_packages"][0]["name"] == "requests"
        assert deps["python_packages"][1]["name"] == "click"
        assert deps["python_packages"][2]["name"] == "pydantic"

        # Test with empty dependencies
        empty_info = {"root_path": "/tmp/test_project"}
        deps = config._extract_dependencies(empty_info)
        assert deps["python_packages"] == []
        assert deps["lock_files"] == {}

    def test_extract_tool_requirements(self):
        """Test tool requirements extraction."""
        config = DHTConfig()

        project_info = {
            "project_type": "python",
            "configurations": {
                "has_git": True,
                "has_makefile": True,
                "has_dockerfile": True,
                "has_cmake": True,
                "has_pytest": True,
            },
        }

        tools = config._extract_tool_requirements(project_info)

        # Check required tools
        assert any(t["name"] == "git" for t in tools["required"])
        assert any(t["name"] == "make" for t in tools["required"])
        assert any(t["name"] == "cmake" for t in tools["required"])
        assert any(t["name"] == "pip" for t in tools["required"])

        # Check optional tools
        assert any(t["name"] == "docker" for t in tools["optional"])
        assert any(t["name"] == "pytest" for t in tools["optional"])

    def test_extract_build_config(self):
        """Test build configuration extraction."""
        config = DHTConfig()

        project_info = {
            "project_type": "python",
            "configurations": {
                "has_setup_py": True,
                "has_pytest": True,
                "has_makefile": True,
            },
        }

        build = config._extract_build_config(project_info)

        assert "python setup.py build" in build["build_commands"]
        assert "pytest" in build["test_commands"]
        assert "make" in build["build_commands"]
        assert "make test" in build["test_commands"]

    def test_extract_environment_vars(self):
        """Test environment variable extraction."""
        config = DHTConfig()

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create .env file
            env_content = """# Comment
API_KEY=
DATABASE_URL=postgresql://localhost/db
DEBUG=true
SECRET_KEY=CHANGE_ME
"""
            (project_path / ".env").write_text(env_content)

            env = config._extract_environment_vars(project_path)

            assert "API_KEY" in env["required"]
            assert "SECRET_KEY" in env["required"]
            assert "DATABASE_URL" in env["optional"]
            assert env["optional"]["DATABASE_URL"] == "postgresql://localhost/db"
            assert "DEBUG" in env["optional"]

    def test_deep_merge(self):
        """Test deep merge functionality."""
        config = DHTConfig()

        base = {"a": {"b": 1, "c": [1, 2]}, "d": "test"}

        override = {"a": {"b": 2, "c": [3], "e": 4}, "d": "updated", "f": "new"}

        config._deep_merge(base, override)

        assert base["a"]["b"] == 2
        assert base["a"]["c"] == [1, 2, 3]  # Lists are extended
        assert base["a"]["e"] == 4
        assert base["d"] == "updated"
        assert base["f"] == "new"

    def test_merge_platform_config(self):
        """Test platform-specific config merging."""
        config = DHTConfig()

        base_config = {
            "dependencies": {"system_packages": []},
            "platform_overrides": {
                "macos": {"dependencies": {"system_packages": [{"name": "xcode-select"}]}},
                "linux": {"dependencies": {"system_packages": [{"name": "build-essential"}]}},
            },
        }

        # Test macOS merge
        merged = config.merge_platform_config(base_config, "macos")
        assert len(merged["dependencies"]["system_packages"]) == 1
        assert merged["dependencies"]["system_packages"][0]["name"] == "xcode-select"

        # Test Linux merge
        merged = config.merge_platform_config(base_config, "linux")
        assert len(merged["dependencies"]["system_packages"]) == 1
        assert merged["dependencies"]["system_packages"][0]["name"] == "build-essential"

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = DHTConfig()

        test_config = {
            "version": "1.0.0",
            "project": {"name": "test", "type": "python"},
            "python": {"version": "3.10.0"},
        }

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Test JSON format
            saved_path = config.save_config(test_config, project_path, format="json")
            assert saved_path.exists()
            assert saved_path.name == ".dhtconfig"

            # Load and verify
            loaded = config.load_config(saved_path)
            assert loaded == test_config

            # Test file not found
            with pytest.raises(FileNotFoundError):
                config.load_config(project_path / "nonexistent.yaml")

    def test_validate_config(self):
        """Test configuration validation."""
        config = DHTConfig()

        # Valid config
        valid_config = {"version": "1.0.0", "project": {"name": "test"}, "python": {"version": "3.10.0"}}

        is_valid, errors = config.validate_config(valid_config)
        assert is_valid
        # Errors may contain schema warnings, but basic validation should pass
        if errors:
            # Only schema validation warnings are acceptable
            assert all("Schema validation error" in error for error in errors)

        # Invalid config - missing version
        invalid_config = {"project": {"name": "test"}, "python": {"version": "3.10.0"}}

        is_valid, errors = config.validate_config(invalid_config)
        assert not is_valid
        assert any("version" in error for error in errors)

        # Invalid config - missing python version
        invalid_config2 = {"version": "1.0.0", "project": {"name": "test"}, "python": {}}

        is_valid, errors = config.validate_config(invalid_config2)
        assert not is_valid
        assert any("python.version" in error for error in errors)

    @patch("DHT.modules.project_analyzer.ProjectAnalyzer.analyze_project")
    @patch("DHT.modules.dhtconfig.diagnostic_reporter_v2.build_system_report")
    def test_generate_from_project_integration(self, mock_system_report, mock_analyze):
        """Test full config generation from project."""
        config = DHTConfig()

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create lock file
            (project_path / "uv.lock").write_text("# Lock file")

            # Mock project analysis - use the actual tmpdir path
            mock_analyze.return_value = {
                "name": "test_project",
                "project_type": "python",
                "project_subtypes": ["cli", "structured"],
                "root_path": str(project_path),  # Use actual path
                "dependencies": {
                    "python": {
                        "runtime": ["click", "requests"],
                        "development": ["pytest"],
                        "all": ["click", "requests", "pytest"],
                    }
                },
                "configurations": {
                    "has_git": True,
                    "has_pytest": True,
                },
                "frameworks": ["click"],
                "languages": {"Python": 10},
                "files_analyzed": 10,
                "structure": {"has_tests": True},
                "statistics": {},
                "project_hash": "abc123",
            }

            # Mock system report
            mock_system_report.return_value = {"system": {"platform": "macos"}, "tools": {"build_tools": {}}}

            result = config.generate_from_project(project_path, include_system_info=True, include_checksums=False)

            # Verify structure
            assert result["version"] == "1.0.0"
            assert result["project"]["name"] == "test_project"
            assert result["project"]["type"] == "python"
            assert result["project"]["subtypes"] == ["cli", "structured"]

            # Verify dependencies
            assert len(result["dependencies"]["python_packages"]) == 2
            assert result["dependencies"]["python_packages"][0]["name"] == "click"
            # Lock file should be detected since we created it
            assert "uv" in result["dependencies"]["lock_files"]
            assert result["dependencies"]["lock_files"]["uv"] == "uv.lock"

            # Verify tools
            assert any(t["name"] == "git" for t in result["tools"]["required"])
            assert any(t["name"] == "pytest" for t in result["tools"]["optional"])

            # Verify platform overrides
            assert "platform_overrides" in result
            assert "macos" in result["platform_overrides"]
