#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created TDD test for shell architecture integrity
# - Verifies correct entry points exist and work
# - Tests shell-Python integration
# - Validates UV build compatibility
# 

"""
Test Shell Architecture Integrity.

This test ensures that DHT maintains its shell-based architecture
while being compatible with UV packaging requirements.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


class TestShellArchitecture:
    """Test the integrity of DHT's shell-based architecture."""
    
    def setup_method(self):
        """Set up test environment."""
        self.dht_root = Path(__file__).parent.parent.parent
        self.dhtl_sh = self.dht_root / "dhtl.sh"
        self.dhtl_bat = self.dht_root / "dhtl.bat"
        self.dhtl_py = self.dht_root / "src" / "DHT" / "dhtl.py"
        self.orchestrator = self.dht_root / "src" / "DHT" / "modules" / "orchestrator.sh"
    
    def test_shell_entry_points_exist(self):
        """Test that shell entry points exist and are executable."""
        # Test dhtl.sh exists and is executable
        assert self.dhtl_sh.exists(), "dhtl.sh entry point missing"
        assert os.access(self.dhtl_sh, os.X_OK), "dhtl.sh not executable"
        
        # Test dhtl.bat exists
        assert self.dhtl_bat.exists(), "dhtl.bat entry point missing"
        
        # Test Python launcher exists
        assert self.dhtl_py.exists(), "Python launcher missing"
        
        # Test orchestrator exists
        assert self.orchestrator.exists(), "Shell orchestrator missing"
    
    def test_shell_entry_point_syntax(self):
        """Test that shell scripts have correct syntax."""
        # Test bash syntax
        result = subprocess.run(
            ["bash", "-n", str(self.dhtl_sh)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"dhtl.sh syntax error: {result.stderr}"
    
    def test_shell_delegation_works(self):
        """Test that shell entry point correctly delegates to Python."""
        # Test version command through shell
        result = subprocess.run(
            [str(self.dhtl_sh), "--version"],
            capture_output=True,
            text=True,
            cwd=str(self.dht_root)
        )
        assert result.returncode == 0, f"Shell delegation failed: {result.stderr}"
        assert "DHTL) v" in result.stdout, "Version output not found"
    
    def test_python_launcher_respects_shell_architecture(self):
        """Test that Python launcher properly uses shell modules."""
        # Check the launcher module where the actual work is done
        launcher_py = self.dht_root / "src" / "DHT" / "launcher.py"
        with open(launcher_py) as f:
            content = f.read()
            
        # Should reference orchestrator.sh
        assert "orchestrator.sh" in content, "Launcher doesn't reference shell orchestrator"
        
        # Should not implement commands directly (they're in shell modules)
        assert "def setup(" not in content, "Launcher implements shell commands directly"
        assert "def lint(" not in content, "Launcher implements shell commands directly"
    
    def test_shell_modules_structure(self):
        """Test that shell modules maintain proper structure."""
        modules_dir = self.dht_root / "src" / "DHT" / "modules"
        
        # Check essential shell modules exist
        essential_modules = [
            "orchestrator.sh",
            "dhtl_commands_1.sh",
            "dhtl_commands_2.sh", 
            "dhtl_environment_1.sh",
            "dhtl_utils.sh",
            "dhtl_guardian_1.sh"
        ]
        
        for module in essential_modules:
            module_path = modules_dir / module
            assert module_path.exists(), f"Essential shell module missing: {module}"
    
    def test_uv_package_compatibility(self):
        """Test that UV package structure is compatible with shell architecture."""
        # Check that src/ structure exists
        src_dir = self.dht_root / "src"
        assert src_dir.exists(), "src/ directory missing"
        
        # Check that DHT package is in src/
        dht_pkg = src_dir / "DHT"
        assert dht_pkg.exists(), "DHT package not in src/"
        
        # Check that shell modules are included in package
        modules_in_pkg = dht_pkg / "modules"
        assert modules_in_pkg.exists(), "Shell modules not in DHT package"
        
        # Check that orchestrator is accessible
        assert (modules_in_pkg / "orchestrator.sh").exists(), "Orchestrator not in package"


class TestDuplicationElimination:
    """Test that duplicate files and structures are eliminated."""
    
    def setup_method(self):
        """Set up test environment."""
        self.dht_root = Path(__file__).parent.parent.parent
    
    def test_no_duplicate_requirements(self):
        """Test that there are no duplicate requirements directories."""
        root_requirements = self.dht_root / "requirements"
        pkg_requirements = self.dht_root / "src" / "DHT" / "requirements"
        
        # Root requirements should exist
        assert root_requirements.exists(), "Root requirements directory missing"
        
        # Package requirements should NOT exist (eliminated duplication)
        assert not pkg_requirements.exists(), "Duplicate requirements directory in package"
    
    def test_no_duplicate_diagnostic_reporters(self):
        """Test that diagnostic reporter v2 exists in the package without duplication."""
        # We now only have diagnostic_reporter_v2 in the package
        pkg_reporter_v2 = self.dht_root / "src" / "DHT" / "diagnostic_reporter_v2.py"
        
        # Should exist in package
        assert pkg_reporter_v2.exists(), "Package diagnostic reporter v2 missing"
        
        # Should not have old versions
        old_reporter = self.dht_root / "src" / "DHT" / "diagnostic_reporter.py"
        old_reporter_old = self.dht_root / "src" / "DHT" / "diagnostic_reporter_old.py"
        assert not old_reporter.exists(), "Old diagnostic_reporter.py should be removed"
        assert not old_reporter_old.exists(), "Old diagnostic_reporter_old.py should be removed"
        
        # Should not exist at root level
        root_reporter = self.dht_root / "diagnostic_reporter.py"
        assert not root_reporter.exists(), "No diagnostic reporter should be at root level"
    
    def test_no_orphaned_files(self):
        """Test that there are no orphaned shell scripts at root level."""
        # Should NOT have multiple dhtl files
        dhtl_files = list(self.dht_root.glob("dhtl*"))
        expected_files = {"dhtl.sh", "dhtl.bat"}
        actual_files = {f.name for f in dhtl_files}
        
        assert actual_files == expected_files, f"Unexpected dhtl files: {actual_files - expected_files}"


class TestModularity:
    """Test that code is modular, efficient, and lean."""
    
    def setup_method(self):
        """Set up test environment."""
        self.dht_root = Path(__file__).parent.parent.parent
    
    def test_python_files_are_modular(self):
        """Test that Python files follow modular design."""
        # Check main Python launcher
        dhtl_py = self.dht_root / "src" / "DHT" / "dhtl.py"
        launcher_py = self.dht_root / "src" / "DHT" / "launcher.py"
        
        with open(dhtl_py) as f:
            dhtl_content = f.read()
            
        with open(launcher_py) as f:
            launcher_content = f.read()
            
        # Entry point should be under 10KB as per CLAUDE.md
        assert len(dhtl_content) < 10000, f"dhtl.py too large: {len(dhtl_content)} bytes"
        
        # Should have proper docstrings
        assert '"""' in dhtl_content, "Missing docstrings in dhtl.py"
        
        # Launcher should use delegation to shell modules
        assert "subprocess" in launcher_content, "Launcher should delegate to shell modules"
        
        # Entry point should delegate to launcher class
        assert "DHTLauncher" in dhtl_content, "Entry point should use launcher class"
    
    def test_shell_modules_are_focused(self):
        """Test that shell modules are focused and lean."""
        modules_dir = self.dht_root / "src" / "DHT" / "modules"
        
        # Track oversized modules (technical debt)
        oversized_modules = []
        
        # Check that each module is focused (not too large)
        for sh_file in modules_dir.glob("*.sh"):
            with open(sh_file) as f:
                content = f.read()
                
            # Track modules over 20KB (should be refactored)
            if len(content) > 20000:
                oversized_modules.append((sh_file.name, len(content)))
        
        # For now, allow some technical debt but track it
        # TODO: Refactor large modules into smaller, focused modules
        known_oversized = {"dhtl_init.sh"}  # Known technical debt
        
        unexpected_oversized = [name for name, size in oversized_modules 
                              if name not in known_oversized]
        
        assert not unexpected_oversized, f"New oversized modules found: {unexpected_oversized}"
    
    def test_no_duplicate_implementations(self):
        """Test that there are no duplicate implementations."""
        # Check that orchestrator properly sources modules (no duplication)
        orchestrator = self.dht_root / "src" / "DHT" / "modules" / "orchestrator.sh"
        
        with open(orchestrator) as f:
            content = f.read()
            
        # Should source modules, not duplicate their functionality
        assert "source " in content, "Orchestrator should source modules"
        
        # Should not have function definitions (those are in modules)
        lines = content.split('\n')
        function_lines = [line for line in lines if line.strip().startswith('function ')]
        assert len(function_lines) < 3, "Orchestrator should delegate, not implement"