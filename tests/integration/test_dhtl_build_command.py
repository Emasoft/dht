#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Integration tests for dhtl build command."""

import shutil
import subprocess
from pathlib import Path

import pytest

from DHT.modules.dhtl_commands import DHTLCommands


class TestDHTLBuildCommand:
    """Test cases for dhtl build command."""
    
    @pytest.fixture
    def commands(self):
        """Create DHTLCommands instance."""
        return DHTLCommands()
    
    def test_build_basic_project(self, commands, tmp_path):
        """Test building a basic Python project."""
        # Create project directory
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        
        # Initialize project first
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]
        
        # Create a simple Python module
        src_dir = project_dir / "src" / "test_project"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "main.py").write_text('''
def hello():
    """Return a greeting."""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
''')
        
        # Build the project
        result = commands.build(str(project_dir))
        
        # Check result
        assert result["success"]
        assert "dist_dir" in result
        assert "artifacts" in result
        assert len(result["artifacts"]) > 0
        
        # Verify dist directory exists
        dist_dir = Path(result["dist_dir"])
        assert dist_dir.exists()
        assert dist_dir.is_dir()
        
        # Check for wheel file
        wheel_files = list(dist_dir.glob("*.whl"))
        assert len(wheel_files) >= 1
        assert "test_project-0.1.0" in wheel_files[0].name
    
    def test_build_with_wheel_only(self, commands, tmp_path):
        """Test building only wheel distribution."""
        # Create project
        project_dir = tmp_path / "wheel-project"
        project_dir.mkdir()
        
        # Initialize project
        init_result = commands.init(str(project_dir), python="3.11", package=True)
        assert init_result["success"]
        
        # Build wheel only
        result = commands.build(str(project_dir), wheel=True)
        
        # Check result
        assert result["success"]
        dist_dir = Path(result["dist_dir"])
        
        # Should have only wheel, no sdist
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))
        assert len(wheel_files) == 1
        assert len(tar_files) == 0
    
    def test_build_with_sdist_only(self, commands, tmp_path):
        """Test building only source distribution."""
        # Create project
        project_dir = tmp_path / "sdist-project"
        project_dir.mkdir()
        
        # Initialize project
        init_result = commands.init(str(project_dir), python="3.11", package=True)
        assert init_result["success"]
        
        # Build sdist only
        result = commands.build(str(project_dir), sdist=True)
        
        # Check result
        assert result["success"]
        dist_dir = Path(result["dist_dir"])
        
        # Should have only sdist, no wheel
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))
        assert len(wheel_files) == 0
        assert len(tar_files) == 1
    
    def test_build_with_custom_output_dir(self, commands, tmp_path):
        """Test building with custom output directory."""
        # Create project
        project_dir = tmp_path / "custom-output-project"
        project_dir.mkdir()
        
        # Initialize project
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]
        
        # Create custom output directory
        custom_out = tmp_path / "custom-dist"
        
        # Build with custom output
        result = commands.build(str(project_dir), out_dir=str(custom_out))
        
        # Check result
        assert result["success"]
        assert result["dist_dir"] == str(custom_out)
        
        # Verify custom directory was used
        assert custom_out.exists()
        assert len(list(custom_out.glob("*.whl"))) >= 1
        
        # Default dist directory should not exist
        default_dist = project_dir / "dist"
        assert not default_dist.exists()
    
    def test_build_with_no_checks(self, commands, tmp_path):
        """Test building with pre-build checks disabled."""
        # Create project
        project_dir = tmp_path / "no-checks-project"
        project_dir.mkdir()
        
        # Initialize project
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]
        
        # Add a file that would fail linting
        src_dir = project_dir / "src" / "no_checks_project"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "bad_code.py").write_text('''
# This code has linting issues
import unused_module
def bad_function( ):
    x=1;y=2
    return x+y
''')
        
        # Build with no checks should succeed
        result = commands.build(str(project_dir), no_checks=True)
        assert result["success"]
        
        # Build with checks might fail (depending on lint config)
        # We won't test this as it depends on project setup
    
    def test_build_nonexistent_project(self, commands, tmp_path):
        """Test building a nonexistent project."""
        # Try to build nonexistent project
        fake_dir = tmp_path / "nonexistent"
        result = commands.build(str(fake_dir))
        
        # Should fail
        assert not result["success"]
        assert "error" in result
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()
    
    def test_build_project_without_pyproject(self, commands, tmp_path):
        """Test building project without pyproject.toml."""
        # Create directory without pyproject.toml
        project_dir = tmp_path / "no-pyproject"
        project_dir.mkdir()
        
        # Try to build
        result = commands.build(str(project_dir))
        
        # Should fail
        assert not result["success"]
        assert "pyproject.toml" in result["error"]
    
    def test_build_cleans_previous_artifacts(self, commands, tmp_path):
        """Test that build cleans previous build artifacts."""
        # Create and initialize project
        project_dir = tmp_path / "clean-test"
        project_dir.mkdir()
        init_result = commands.init(str(project_dir), python="3.11")
        assert init_result["success"]
        
        # Create old build artifacts
        old_dist = project_dir / "dist"
        old_dist.mkdir()
        (old_dist / "old-artifact.whl").write_text("old")
        
        old_build = project_dir / "build"
        old_build.mkdir()
        (old_build / "old-build-file").write_text("old")
        
        # Build project
        result = commands.build(str(project_dir))
        assert result["success"]
        
        # Old artifacts should be gone
        assert not (old_dist / "old-artifact.whl").exists()
        assert not old_build.exists()
        
        # New artifacts should exist
        new_wheels = list(old_dist.glob("*.whl"))
        assert len(new_wheels) >= 1
        assert "old-artifact" not in new_wheels[0].name
    
    def test_build_incremental_version(self, commands, tmp_path):
        """Test building with updated version number."""
        # Create and initialize project
        project_dir = tmp_path / "version-test"
        project_dir.mkdir()
        init_result = commands.init(str(project_dir), python="3.11", package=True)
        assert init_result["success"]
        
        # First build
        result1 = commands.build(str(project_dir))
        assert result1["success"]
        artifacts1 = result1["artifacts"]
        
        # Update version in pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        content = pyproject_path.read_text()
        new_content = content.replace('version = "0.1.0"', 'version = "0.2.0"')
        pyproject_path.write_text(new_content)
        
        # Update version in __init__.py if it exists
        init_files = list(project_dir.rglob("__init__.py"))
        for init_file in init_files:
            if "__version__" in init_file.read_text():
                init_content = init_file.read_text()
                new_init = init_content.replace('"0.1.0"', '"0.2.0"')
                init_file.write_text(new_init)
        
        # Second build with new version
        result2 = commands.build(str(project_dir))
        assert result2["success"]
        artifacts2 = result2["artifacts"]
        
        # Check version in artifact names
        assert any("0.1.0" in art for art in artifacts1)
        assert any("0.2.0" in art for art in artifacts2)
        assert not any("0.1.0" in art for art in artifacts2)