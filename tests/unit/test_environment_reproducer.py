#!/usr/bin/env python3
"""Tests for the environment reproducer module."""

import json
import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from dataclasses import asdict
import subprocess

import pytest

from DHT.modules.environment_reproducer import (
    EnvironmentReproducer,
    EnvironmentSnapshot,
    ReproductionResult
)


@pytest.fixture
def reproducer():
    """Create an EnvironmentReproducer instance."""
    return EnvironmentReproducer()


@pytest.fixture
def sample_snapshot():
    """Create a sample environment snapshot."""
    return EnvironmentSnapshot(
        timestamp="2024-01-15T10:30:00",
        platform="darwin",
        architecture="arm64",
        dht_version="1.0.0",
        snapshot_id="dht_dar_20240115_103000_abc12345",
        python_version="3.11.5",
        python_executable="/usr/bin/python3",
        python_packages={
            "requests": "2.31.0",
            "click": "8.1.7",
            "pytest": "7.4.3",
            "black": "23.7.0"
        },
        system_packages={
            "git": "2.39.3",
            "curl": "8.1.2"
        },
        tool_versions={
            "git": "2.39.3",
            "python": "3.11.5",
            "pip": "23.2.1",
            "uv": "0.1.32",
            "black": "23.7.0",
            "pytest": "7.4.3"
        },
        tool_paths={
            "git": "/usr/bin/git",
            "python": "/usr/bin/python3",
            "pip": "/usr/bin/pip",
            "uv": "/opt/homebrew/bin/uv",
            "black": "/path/to/venv/bin/black",
            "pytest": "/path/to/venv/bin/pytest"
        },
        environment_variables={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "PYTHONPATH": "/path/to/project",
            "VIRTUAL_ENV": "/path/to/venv"
        },
        path_entries=["/usr/bin", "/bin", "/usr/local/bin"],
        project_path="/path/to/project",
        project_type="python",
        lock_files={
            "uv.lock": "# uv lock file content\n[package]\nname = \"requests\"\nversion = \"2.31.0\"",
            "requirements.txt": "requests==2.31.0\nclick==8.1.7"
        },
        config_files={
            "pyproject.toml": "[project]\nname = \"test-project\"\nversion = \"0.1.0\"",
            "ruff.toml": "line-length = 88"
        },
        checksums={
            "uv.lock": "abc123def456",
            "requirements.txt": "def456ghi789",
            "pyproject.toml": "ghi789jkl012",
            "ruff.toml": "jkl012mno345"
        },
        reproduction_steps=[
            "Install Python 3.11.5",
            "Install UV 0.1.32",
            "uv python pin 3.11.5",
            "Create virtual environment",
            "uv venv",
            "uv sync",
            "Verify git version 2.39.3"
        ],
        platform_notes=[
            "macOS: Use Homebrew for system packages",
            "Install Xcode Command Line Tools if needed"
        ]
    )


@pytest.fixture
def sample_project_path(tmp_path):
    """Create a sample project directory."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    
    # Create project files
    (project_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests", "click"]

[project.optional-dependencies]
dev = ["pytest", "black"]
""")
    
    (project_path / "uv.lock").write_text("""
# uv lock file
[[package]]
name = "requests"
version = "2.31.0"
""")
    
    (project_path / "requirements.txt").write_text("requests==2.31.0\nclick==8.1.7")
    
    return project_path


class TestEnvironmentReproducer:
    """Tests for EnvironmentReproducer class."""
    
    def test_init(self, reproducer):
        """Test reproducer initialization."""
        assert reproducer.configurator is not None
        assert reproducer.version_critical_tools is not None
        assert reproducer.behavior_compatible_tools is not None
        assert reproducer.platform_tool_equivalents is not None
        
        # Check critical tools
        assert "python" in reproducer.version_critical_tools
        assert "black" in reproducer.version_critical_tools
        assert "pytest" in reproducer.version_critical_tools
        
        # Check behavior compatible tools
        assert "curl" in reproducer.behavior_compatible_tools
        assert "make" in reproducer.behavior_compatible_tools
    
    def test_generate_snapshot_id(self, reproducer):
        """Test snapshot ID generation."""
        snapshot_id = reproducer._generate_snapshot_id()
        
        assert snapshot_id.startswith("dht_")
        assert len(snapshot_id.split("_")) == 5  # dht_platform_timestamp_hash
        
        # Generate another ID to ensure uniqueness
        snapshot_id2 = reproducer._generate_snapshot_id()
        assert snapshot_id != snapshot_id2
    
    def test_get_dht_version(self, reproducer):
        """Test DHT version detection."""
        version = reproducer._get_dht_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_extract_version_from_output(self, reproducer):
        """Test version extraction from tool output."""
        test_cases = [
            ("Python 3.11.5", "3.11.5"),
            ("git version 2.39.3", "2.39.3"),
            ("black, 23.7.0 (compiled: yes)", "23.7.0"),
            ("pytest 7.4.3", "7.4.3"),
            ("uv 0.1.32", "0.1.32"),
            ("v1.2.3", "1.2.3"),
            ("version 4.5.6", "4.5.6"),
            ("no version here", None),
            ("", None)
        ]
        
        for output, expected in test_cases:
            result = reproducer._extract_version_from_output(output)
            assert result == expected, f"Failed for '{output}', expected {expected}, got {result}"
    
    def test_get_version_command(self, reproducer):
        """Test version command lookup."""
        test_cases = [
            ("git", ["git", "--version"]),
            ("python", ["python", "--version"]),
            ("uv", ["uv", "--version"]),
            ("nonexistent_tool", None)
        ]
        
        for tool, expected in test_cases:
            result = reproducer._get_version_command(tool)
            assert result == expected
    
    def test_compare_versions(self, reproducer):
        """Test version comparison logic."""
        # Exact matches
        assert reproducer._compare_versions("1.2.3", "1.2.3", "python", True) is True
        assert reproducer._compare_versions("1.2.3", "1.2.3", "python", False) is True
        
        # Critical tools in strict mode
        assert reproducer._compare_versions("1.2.3", "1.2.4", "python", True) is False
        assert reproducer._compare_versions("1.2.3", "1.3.0", "python", True) is False
        
        # Critical tools in non-strict mode (same major version)
        assert reproducer._compare_versions("1.2.3", "1.2.4", "python", False) is True
        assert reproducer._compare_versions("1.2.3", "1.3.0", "python", False) is True
        assert reproducer._compare_versions("1.2.3", "2.0.0", "python", False) is False
        
        # Behavior compatible tools (always compatible)
        assert reproducer._compare_versions("1.0.0", "2.0.0", "curl", True) is True
        assert reproducer._compare_versions("1.0.0", "2.0.0", "curl", False) is True
    
    @patch('subprocess.check_output')
    @patch('DHT.modules.environment_reproducer.build_system_report')
    @patch('DHT.modules.environment_reproducer.subprocess.run')
    @patch('sys.executable', '/usr/bin/python3')
    @patch.object(sys, 'version_info', (3, 11, 5))
    def test_capture_environment_snapshot(
        self, 
        mock_subprocess, 
        mock_build_system_report,
        mock_check_output,
        reproducer, 
        sample_project_path
    ):
        """Test environment snapshot capture."""
        # Mock subprocess.check_output for platform.architecture()
        mock_check_output.return_value = b"Mach-O 64-bit executable arm64"
        
        # Mock system report
        mock_build_system_report.return_value = {"system": {"platform": "darwin"}}
        
        # Mock pip list output
        mock_pip_result = Mock()
        mock_pip_result.returncode = 0
        mock_pip_result.stdout = json.dumps([
            {"name": "requests", "version": "2.31.0"},
            {"name": "click", "version": "8.1.7"}
        ])
        mock_subprocess.return_value = mock_pip_result
        
        # Mock environment configurator
        with patch.object(reproducer.configurator, 'analyze_environment_requirements') as mock_analyze:
            mock_analyze.return_value = {
                "project_info": {
                    "project_type": "python",
                    "name": "test-project"
                }
            }
            
            snapshot = reproducer.capture_environment_snapshot(
                project_path=sample_project_path,
                include_system_info=True,
                include_configs=True
            )
            
            assert isinstance(snapshot, EnvironmentSnapshot)
            assert snapshot.python_version == "3.11.5"
            assert snapshot.platform == platform.system().lower()
            assert snapshot.project_type == "python"
            assert len(snapshot.snapshot_id) > 0
            assert "requests" in snapshot.python_packages
            assert len(snapshot.reproduction_steps) > 0
    
    @patch('shutil.which')
    @patch('DHT.modules.environment_reproducer.subprocess.run')
    def test_capture_system_tools(self, mock_subprocess, mock_which, reproducer):
        """Test system tools capture."""
        snapshot = EnvironmentSnapshot(
            timestamp="2024-01-15T10:30:00",
            platform="darwin",
            architecture="arm64", 
            dht_version="1.0.0",
            snapshot_id="test_id",
            python_version="3.11.5",
            python_executable="/usr/bin/python3"
        )
        
        # Mock which to return paths for some tools
        def which_side_effect(tool):
            tool_paths = {
                "git": "/usr/bin/git",
                "python": "/usr/bin/python3",
                "uv": "/opt/homebrew/bin/uv"
            }
            return tool_paths.get(tool)
        
        mock_which.side_effect = which_side_effect
        
        # Mock subprocess results
        def subprocess_side_effect(cmd, **kwargs):
            result = Mock()
            result.returncode = 0
            if cmd[0] == "git":
                result.stdout = "git version 2.39.3"
                result.stderr = ""
            elif cmd[0] == "python":
                result.stdout = "Python 3.11.5"
                result.stderr = ""
            elif cmd[0] == "uv":
                result.stdout = "uv 0.1.32"
                result.stderr = ""
            else:
                result.returncode = 1
                result.stdout = ""
                result.stderr = "command not found"
            return result
        
        mock_subprocess.side_effect = subprocess_side_effect
        
        reproducer._capture_system_tools(snapshot)
        
        assert "git" in snapshot.tool_versions
        assert "python" in snapshot.tool_versions
        assert "uv" in snapshot.tool_versions
        assert snapshot.tool_versions["git"] == "2.39.3"
        assert snapshot.tool_versions["python"] == "3.11.5"
        assert snapshot.tool_versions["uv"] == "0.1.32"
        
        assert snapshot.tool_paths["git"] == "/usr/bin/git"
        assert snapshot.tool_paths["uv"] == "/opt/homebrew/bin/uv"
    
    def test_capture_environment_variables(self, reproducer):
        """Test environment variables capture."""
        snapshot = EnvironmentSnapshot(
            timestamp="2024-01-15T10:30:00",
            platform="darwin",
            architecture="arm64",
            dht_version="1.0.0", 
            snapshot_id="test_id",
            python_version="3.11.5",
            python_executable="/usr/bin/python3"
        )
        
        with patch.dict('os.environ', {
            'PATH': '/usr/bin:/bin',
            'PYTHONPATH': '/path/to/project',
            'VIRTUAL_ENV': '/path/to/venv',
            'CUSTOM_VAR': 'should_not_be_captured'
        }):
            reproducer._capture_environment_variables(snapshot)
            
            assert 'PATH' in snapshot.environment_variables
            assert 'PYTHONPATH' in snapshot.environment_variables
            assert 'VIRTUAL_ENV' in snapshot.environment_variables
            assert 'CUSTOM_VAR' not in snapshot.environment_variables
            
            assert snapshot.path_entries == ['/usr/bin', '/bin']
    
    def test_capture_project_info(self, reproducer, sample_project_path):
        """Test project information capture."""
        snapshot = EnvironmentSnapshot(
            timestamp="2024-01-15T10:30:00",
            platform="darwin",
            architecture="arm64",
            dht_version="1.0.0",
            snapshot_id="test_id", 
            python_version="3.11.5",
            python_executable="/usr/bin/python3"
        )
        
        with patch.object(reproducer.configurator, 'analyze_environment_requirements') as mock_analyze:
            mock_analyze.return_value = {
                "project_info": {"project_type": "python"}
            }
            
            reproducer._capture_project_info(snapshot, sample_project_path, True)
            
            assert snapshot.project_path == str(sample_project_path)
            assert snapshot.project_type == "python"
            assert "uv.lock" in snapshot.lock_files
            assert "requirements.txt" in snapshot.lock_files
            assert "pyproject.toml" in snapshot.config_files
            assert len(snapshot.checksums) > 0
    
    def test_generate_reproduction_steps(self, reproducer, sample_snapshot):
        """Test reproduction steps generation."""
        reproducer._generate_reproduction_steps(sample_snapshot)
        
        steps = sample_snapshot.reproduction_steps
        assert len(steps) > 0
        assert any("Python 3.11.5" in step for step in steps)
        assert any("uv" in step.lower() for step in steps)
        assert any("verify" in step.lower() for step in steps)
        
        # Check platform notes
        notes = sample_snapshot.platform_notes
        assert len(notes) > 0
        if sample_snapshot.platform == "darwin":
            assert any("homebrew" in note.lower() for note in notes)
    
    @patch('platform.system')
    def test_verify_platform_compatibility(self, mock_platform, reproducer, sample_snapshot):
        """Test platform compatibility verification."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="linux"
        )
        
        # Test same platform
        mock_platform.return_value = "Darwin"
        reproducer._verify_platform_compatibility(sample_snapshot, result)
        assert len(result.warnings) == 0
        
        # Test different platform
        mock_platform.return_value = "Linux"
        reproducer._verify_platform_compatibility(sample_snapshot, result)
        assert len(result.warnings) > 0
        assert any("mismatch" in warning.lower() for warning in result.warnings)
    
    @patch.object(sys, 'version_info', (3, 11, 5))
    def test_verify_python_version_exact_match(self, reproducer, sample_snapshot):
        """Test Python version verification with exact match."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        reproducer._verify_python_version(sample_snapshot, result, False)
        
        assert result.versions_verified["python"] is True
        assert "python" not in result.version_mismatches
    
    @patch.object(sys, 'version_info', (3, 11, 6))
    def test_verify_python_version_compatible(self, reproducer, sample_snapshot):
        """Test Python version verification with compatible version."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        reproducer._verify_python_version(sample_snapshot, result, False)
        
        assert result.versions_verified["python"] is False
        assert "python" in result.version_mismatches
        assert len(result.warnings) > 0  # Should have compatibility warning
    
    @patch('shutil.which')
    @patch('DHT.modules.environment_reproducer.subprocess.run')
    def test_verify_tools_success(self, mock_subprocess, mock_which, reproducer, sample_snapshot):
        """Test successful tool verification."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        # Mock which to return paths
        mock_which.return_value = "/usr/bin/git"
        
        # Mock version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.39.3"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        reproducer._verify_tools(sample_snapshot, result, True, False)
        
        assert result.tools_verified.get("git") is True
        assert result.versions_verified.get("git") is True
        assert "git" not in result.missing_tools
        assert "git" not in result.version_mismatches
    
    @patch('shutil.which')
    def test_verify_tools_missing(self, mock_which, reproducer, sample_snapshot):
        """Test tool verification with missing tools."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        # Mock which to return None (tool not found)
        mock_which.return_value = None
        
        reproducer._verify_tools(sample_snapshot, result, True, False)
        
        assert "git" in result.missing_tools
        assert result.tools_verified.get("git") is False
    
    @patch('shutil.which')
    @patch('DHT.modules.environment_reproducer.subprocess.run')
    def test_verify_tools_version_mismatch(self, mock_subprocess, mock_which, reproducer, sample_snapshot):
        """Test tool verification with version mismatch."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        # Mock which to return path
        mock_which.return_value = "/usr/bin/git"
        
        # Mock version check with different version
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.40.0"  # Different from snapshot
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        reproducer._verify_tools(sample_snapshot, result, True, False)
        
        assert result.tools_verified.get("git") is True
        assert result.versions_verified.get("git") is False
        assert "git" in result.version_mismatches
        assert result.version_mismatches["git"] == ("2.39.3", "2.40.0")
    
    def test_reproduce_environment_success(self, reproducer, sample_snapshot, tmp_path):
        """Test successful environment reproduction."""
        with patch.object(reproducer, '_verify_platform_compatibility'), \
             patch.object(reproducer, '_verify_python_version'), \
             patch.object(reproducer, '_verify_tools'), \
             patch.object(reproducer, '_reproduce_project_environment'), \
             patch.object(reproducer, '_verify_configurations'):
            
            result = reproducer.reproduce_environment(
                snapshot=sample_snapshot,
                target_path=tmp_path / "reproduction",
                strict_mode=False,
                auto_install=False
            )
            
            assert isinstance(result, ReproductionResult)
            assert result.snapshot_id == sample_snapshot.snapshot_id
    
    def test_reproduce_project_environment(self, reproducer, sample_snapshot, tmp_path):
        """Test project environment reproduction."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        target_path = tmp_path / "reproduction"
        
        reproducer._reproduce_project_environment(
            sample_snapshot, result, target_path, False
        )
        
        # Check that lock files were restored
        assert (target_path / "uv.lock").exists()
        assert (target_path / "requirements.txt").exists()
        
        # Check that config files were restored
        assert (target_path / "pyproject.toml").exists()
        assert (target_path / "ruff.toml").exists()
        
        # Check content
        uv_lock_content = (target_path / "uv.lock").read_text()
        assert uv_lock_content == sample_snapshot.lock_files["uv.lock"]
        
        # Check that all expected files were restored
        expected_restorations = ["uv.lock", "requirements.txt", "pyproject.toml", "ruff.toml"]
        for file in expected_restorations:
            assert any(file in action for action in result.actions_completed), f"Expected {file} to be restored"
    
    def test_verify_configurations(self, reproducer, sample_snapshot, tmp_path):
        """Test configuration verification."""
        result = ReproductionResult(
            success=False,
            snapshot_id=sample_snapshot.snapshot_id,
            platform="darwin"
        )
        
        # Create files with matching content
        (tmp_path / "pyproject.toml").write_text(sample_snapshot.config_files["pyproject.toml"])
        
        # Create file with different content
        (tmp_path / "ruff.toml").write_text("line-length = 100")  # Different from snapshot
        
        reproducer._verify_configurations(sample_snapshot, result, tmp_path)
        
        assert result.configs_verified["pyproject.toml"] is True
        assert result.configs_verified["ruff.toml"] is False
        assert "ruff.toml" in result.config_differences
        assert result.config_differences["ruff.toml"] == "Content differs"
    
    def test_save_environment_snapshot(self, reproducer, sample_snapshot, tmp_path):
        """Test saving environment snapshot to file."""
        output_file = tmp_path / "snapshot.json"
        
        saved_path = reproducer.save_environment_snapshot(
            snapshot=sample_snapshot,
            output_path=output_file,
            format="json"
        )
        
        assert saved_path == output_file
        assert output_file.exists()
        
        # Verify content
        with open(output_file) as f:
            data = json.load(f)
        
        assert data["metadata"]["snapshot_id"] == sample_snapshot.snapshot_id
        assert data["environment"]["python_version"] == sample_snapshot.python_version
        assert data["project"]["project_type"] == sample_snapshot.project_type
        assert "steps" in data["reproduction"]
    
    def test_save_environment_snapshot_yaml(self, reproducer, sample_snapshot, tmp_path):
        """Test saving environment snapshot in YAML format."""
        output_file = tmp_path / "snapshot.yaml"
        
        saved_path = reproducer.save_environment_snapshot(
            snapshot=sample_snapshot,
            output_path=output_file,
            format="yaml"
        )
        
        assert saved_path == output_file
        assert output_file.exists()
        
        # Verify content
        import yaml
        with open(output_file) as f:
            data = yaml.safe_load(f)
        
        assert data["metadata"]["snapshot_id"] == sample_snapshot.snapshot_id
        assert data["environment"]["python_version"] == sample_snapshot.python_version
    
    def test_load_environment_snapshot(self, reproducer, sample_snapshot, tmp_path):
        """Test loading environment snapshot from file."""
        # Save snapshot first
        output_file = tmp_path / "snapshot.json"
        reproducer.save_environment_snapshot(
            snapshot=sample_snapshot,
            output_path=output_file
        )
        
        # Load it back
        loaded_snapshot = reproducer.load_environment_snapshot(output_file)
        
        assert isinstance(loaded_snapshot, EnvironmentSnapshot)
        assert loaded_snapshot.snapshot_id == sample_snapshot.snapshot_id
        assert loaded_snapshot.python_version == sample_snapshot.python_version
        assert loaded_snapshot.platform == sample_snapshot.platform
        assert loaded_snapshot.tool_versions == sample_snapshot.tool_versions
        assert loaded_snapshot.lock_files == sample_snapshot.lock_files
    
    def test_load_environment_snapshot_yaml(self, reproducer, sample_snapshot, tmp_path):
        """Test loading environment snapshot from YAML file."""
        # Save snapshot in YAML format
        output_file = tmp_path / "snapshot.yaml"
        reproducer.save_environment_snapshot(
            snapshot=sample_snapshot,
            output_path=output_file,
            format="yaml"
        )
        
        # Load it back
        loaded_snapshot = reproducer.load_environment_snapshot(output_file)
        
        assert isinstance(loaded_snapshot, EnvironmentSnapshot)
        assert loaded_snapshot.snapshot_id == sample_snapshot.snapshot_id
        assert loaded_snapshot.python_version == sample_snapshot.python_version
    
    def test_load_environment_snapshot_not_found(self, reproducer, tmp_path):
        """Test loading snapshot from non-existent file."""
        nonexistent_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            reproducer.load_environment_snapshot(nonexistent_file)


class TestEnvironmentSnapshot:
    """Tests for EnvironmentSnapshot dataclass."""
    
    def test_environment_snapshot_creation(self):
        """Test creating EnvironmentSnapshot."""
        snapshot = EnvironmentSnapshot(
            timestamp="2024-01-15T10:30:00",
            platform="darwin",
            architecture="arm64",
            dht_version="1.0.0",
            snapshot_id="test_id",
            python_version="3.11.5",
            python_executable="/usr/bin/python3"
        )
        
        assert snapshot.timestamp == "2024-01-15T10:30:00"
        assert snapshot.platform == "darwin"
        assert snapshot.python_version == "3.11.5"
        assert snapshot.python_packages == {}  # Default empty dict
        assert snapshot.reproduction_steps == []  # Default empty list
    
    def test_environment_snapshot_with_data(self):
        """Test creating EnvironmentSnapshot with all data."""
        snapshot = EnvironmentSnapshot(
            timestamp="2024-01-15T10:30:00",
            platform="darwin",
            architecture="arm64",
            dht_version="1.0.0",
            snapshot_id="test_id",
            python_version="3.11.5",
            python_executable="/usr/bin/python3",
            python_packages={"requests": "2.31.0"},
            tool_versions={"git": "2.39.3"},
            environment_variables={"PATH": "/usr/bin"},
            lock_files={"uv.lock": "content"},
            checksums={"uv.lock": "abc123"}
        )
        
        assert len(snapshot.python_packages) == 1
        assert snapshot.python_packages["requests"] == "2.31.0"
        assert snapshot.tool_versions["git"] == "2.39.3"
        assert snapshot.environment_variables["PATH"] == "/usr/bin"
        assert snapshot.lock_files["uv.lock"] == "content"
        assert snapshot.checksums["uv.lock"] == "abc123"


class TestReproductionResult:
    """Tests for ReproductionResult dataclass."""
    
    def test_reproduction_result_creation(self):
        """Test creating ReproductionResult."""
        result = ReproductionResult(
            success=True,
            snapshot_id="test_id",
            platform="darwin"
        )
        
        assert result.success is True
        assert result.snapshot_id == "test_id"
        assert result.platform == "darwin"
        assert result.tools_verified == {}  # Default empty dict
        assert result.missing_tools == []   # Default empty list
    
    def test_reproduction_result_with_data(self):
        """Test creating ReproductionResult with all data."""
        result = ReproductionResult(
            success=False,
            snapshot_id="test_id",
            platform="darwin",
            tools_verified={"git": True, "python": False},
            version_mismatches={"python": ("3.11.5", "3.11.6")},
            missing_tools=["uv"],
            actions_completed=["restore_files"],
            actions_failed=["install_python"],
            warnings=["Version mismatch detected"]
        )
        
        assert result.success is False
        assert len(result.tools_verified) == 2
        assert result.tools_verified["git"] is True
        assert result.tools_verified["python"] is False
        assert "python" in result.version_mismatches
        assert result.version_mismatches["python"] == ("3.11.5", "3.11.6")
        assert "uv" in result.missing_tools
        assert len(result.actions_completed) == 1
        assert len(result.actions_failed) == 1
        assert len(result.warnings) == 1


class TestIntegration:
    """Integration tests for environment reproducer."""
    
    @patch('DHT.modules.environment_reproducer.build_system_report')
    @patch('DHT.modules.environment_reproducer.subprocess.run')
    def test_end_to_end_snapshot_and_reproduction(
        self, 
        mock_subprocess, 
        mock_build_system_report,
        sample_project_path
    ):
        """Test complete snapshot capture and reproduction workflow."""
        # Setup mocks
        mock_build_system_report.return_value = {"system": {"platform": "darwin"}}
        
        mock_pip_result = Mock()
        mock_pip_result.returncode = 0
        mock_pip_result.stdout = json.dumps([{"name": "requests", "version": "2.31.0"}])
        mock_subprocess.return_value = mock_pip_result
        
        reproducer = EnvironmentReproducer()
        
        # Mock environment configurator
        with patch.object(reproducer.configurator, 'analyze_environment_requirements') as mock_analyze:
            mock_analyze.return_value = {
                "project_info": {"project_type": "python", "name": "test-project"}
            }
            
            # Capture snapshot
            snapshot = reproducer.capture_environment_snapshot(
                project_path=sample_project_path,
                include_system_info=False,
                include_configs=True
            )
            
            assert isinstance(snapshot, EnvironmentSnapshot)
            assert snapshot.project_type == "python"
            assert len(snapshot.lock_files) > 0
            
            # Test reproduction (without actual installation)
            with tempfile.TemporaryDirectory() as temp_dir:
                result = reproducer.reproduce_environment(
                    snapshot=snapshot,
                    target_path=Path(temp_dir) / "reproduction",
                    strict_mode=False,
                    auto_install=False
                )
                
                assert isinstance(result, ReproductionResult)
                assert result.snapshot_id == snapshot.snapshot_id
    
    @patch('DHT.modules.environment_reproducer.create_markdown_artifact')
    @patch('DHT.modules.environment_reproducer.create_table_artifact')
    def test_create_reproducible_environment_flow(
        self,
        mock_create_table,
        mock_create_markdown,
        sample_project_path
    ):
        """Test the complete reproducible environment creation flow."""
        reproducer = EnvironmentReproducer()
        
        # Mock all external dependencies
        with patch.object(reproducer, 'capture_environment_snapshot') as mock_capture, \
             patch.object(reproducer, 'save_environment_snapshot') as mock_save, \
             patch.object(reproducer, 'reproduce_environment') as mock_reproduce:
            
            # Setup mock returns
            mock_snapshot = EnvironmentSnapshot(
                timestamp="2024-01-15T10:30:00",
                platform="darwin",
                architecture="arm64",
                dht_version="1.0.0",
                snapshot_id="test_flow_id",
                python_version="3.11.5",
                python_executable="/usr/bin/python3"
            )
            mock_capture.return_value = mock_snapshot
            mock_save.return_value = Path("/path/to/snapshot.json")
            mock_reproduce.return_value = ReproductionResult(
                success=True,
                snapshot_id="test_flow_id",
                platform="darwin"
            )
            
            # Run the flow
            results = reproducer.create_reproducible_environment(
                project_path=sample_project_path,
                save_snapshot=True,
                verify_reproduction=True
            )
            
            assert results["success"] is True
            assert results["snapshot_id"] == "test_flow_id"
            assert "capture_snapshot" in results["steps"]
            assert "save_snapshot" in results["steps"]
            assert "verify_reproduction" in results["steps"]
            assert "verification" in results
            
            # Verify artifacts were created
            mock_create_markdown.assert_called()
            mock_create_table.assert_called()