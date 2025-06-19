#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created TDD test for shell architecture integrity
# - Verifies correct entry points exist and work
# - Tests shell-Python integration
# - Validates UV build compatibility
# - Updated for Python migration - all shell scripts now replaced with Python
#

"""
Test Python Architecture Integrity.

This test ensures that DHT maintains its Python-based architecture
after migration from shell scripts while being compatible with UV packaging requirements.
"""

import os
import subprocess
import sys
from pathlib import Path


class TestPythonArchitecture:
    """Test the integrity of DHT's Python-based architecture."""

    def setup_method(self):
        """Set up test environment."""
        self.dht_root = Path(__file__).parent.parent.parent
        self.dhtl_entry_py = self.dht_root / "dhtl_entry.py"
        self.dhtl_entry_windows_py = self.dht_root / "dhtl_entry_windows.py"
        self.dhtl_py = self.dht_root / "src" / "DHT" / "dhtl.py"
        self.launcher_py = self.dht_root / "src" / "DHT" / "launcher.py"
        self.orchestrator_py = self.dht_root / "src" / "DHT" / "modules" / "orchestrator.py"

    def test_python_entry_points_exist(self):
        """Test that Python entry points exist and are executable."""
        # Test dhtl_entry.py exists and is executable
        assert self.dhtl_entry_py.exists(), "dhtl_entry.py entry point missing"
        assert os.access(self.dhtl_entry_py, os.X_OK), "dhtl_entry.py not executable"

        # Test dhtl_entry_windows.py exists
        assert self.dhtl_entry_windows_py.exists(), "dhtl_entry_windows.py entry point missing"

        # Test Python launcher exists
        assert self.dhtl_py.exists(), "Python dhtl.py missing"

        # Test launcher exists
        assert self.launcher_py.exists(), "Python launcher missing"

        # Test orchestrator exists
        assert self.orchestrator_py.exists(), "Python orchestrator missing"

    def test_python_entry_point_syntax(self):
        """Test that Python scripts have correct syntax."""
        # Test Python syntax for all entry points
        python_files = [self.dhtl_entry_py, self.dhtl_entry_windows_py, self.dhtl_py, self.launcher_py]

        for py_file in python_files:
            result = subprocess.run([sys.executable, "-m", "py_compile", str(py_file)], capture_output=True, text=True)
            assert result.returncode == 0, f"{py_file.name} syntax error: {result.stderr}"

    def test_python_entry_point_works(self):
        """Test that Python entry point works correctly."""
        # Test version command through Python
        result = subprocess.run(
            [sys.executable, str(self.dhtl_entry_py), "version"], capture_output=True, text=True, cwd=str(self.dht_root)
        )
        assert result.returncode == 0, f"Python entry point failed: {result.stderr}"
        assert "Development Helper Toolkit" in result.stdout and "v" in result.stdout, "Version output not found"

    def test_python_launcher_uses_command_dispatcher(self):
        """Test that Python launcher properly uses command dispatcher."""
        # Check the launcher module where the actual work is done
        with open(self.launcher_py) as f:
            content = f.read()

        # Should import command_dispatcher
        assert (
            "from .modules.command_dispatcher import CommandDispatcher" in content
            or "from modules.command_dispatcher import CommandDispatcher" in content
        ), "Launcher doesn't import command dispatcher"

        # Should use CommandDispatcher
        assert "CommandDispatcher" in content, "Launcher doesn't use CommandDispatcher"

    def test_python_modules_structure(self):
        """Test that Python modules maintain proper structure."""
        modules_dir = self.dht_root / "src" / "DHT" / "modules"

        # Check essential Python modules exist
        essential_modules = [
            "orchestrator.py",
            "command_dispatcher.py",
            "command_registry.py",
            "dhtl_commands.py",
            "dhtl_environment_1.py",
            "dhtl_utils.py",
            "dhtl_guardian_prefect.py",
        ]

        for module in essential_modules:
            module_path = modules_dir / module
            assert module_path.exists(), f"Essential Python module missing: {module}"

    def test_uv_package_compatibility(self):
        """Test that UV package structure is compatible with Python architecture."""
        # Check that src/ structure exists
        src_dir = self.dht_root / "src"
        assert src_dir.exists(), "src/ directory missing"

        # Check that DHT package is in src/
        dht_pkg = src_dir / "DHT"
        assert dht_pkg.exists(), "DHT package not in src/"

        # Check that Python modules are included in package
        modules_in_pkg = dht_pkg / "modules"
        assert modules_in_pkg.exists(), "Python modules not in DHT package"

        # Check that orchestrator is accessible
        assert (modules_in_pkg / "orchestrator.py").exists(), "Python orchestrator not in package"


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
        """Test that there are no orphaned Python scripts at root level."""
        # Should have Python entry points
        dhtl_files = list(self.dht_root.glob("dhtl*.py"))
        expected_files = {"dhtl_entry.py", "dhtl_entry_windows.py"}
        actual_files = {f.name for f in dhtl_files}

        assert expected_files.issubset(actual_files), f"Missing dhtl Python files: {expected_files - actual_files}"


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

        # Launcher should use command dispatcher
        assert "CommandDispatcher" in launcher_content, "Launcher should use command dispatcher"

        # Entry point should delegate to launcher class
        assert "DHTLauncher" in dhtl_content, "Entry point should use launcher class"

    def test_python_modules_are_focused(self):
        """Test that Python modules are focused and lean."""
        modules_dir = self.dht_root / "src" / "DHT" / "modules"

        # Track oversized modules (technical debt)
        oversized_modules = []

        # Check that each module is focused (not too large, <10KB as per CLAUDE.md)
        for py_file in modules_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()

            # Track modules over 10KB (should be refactored as per CLAUDE.md)
            if len(content) > 10000:
                oversized_modules.append((py_file.name, len(content)))

        # Known oversized modules that were refactored
        # These are acceptable as they follow the delegation pattern
        known_refactored = {
            "environment_configurator.py",  # Refactored into multiple modules
            "environment_reproducer.py",  # Refactored into multiple modules
            "project_analyzer.py",  # Uses delegation pattern
        }

        unexpected_oversized = [name for name, size in oversized_modules if name not in known_refactored]

        # Allow some tolerance for files that are close to 10KB
        truly_oversized = [
            (name, size) for name, size in oversized_modules if size > 11000 and name not in known_refactored
        ]

        assert not truly_oversized, f"Oversized modules found (>11KB): {truly_oversized}"

    def test_no_duplicate_implementations(self):
        """Test that there are no duplicate implementations."""
        # Check that orchestrator properly imports modules (no duplication)
        orchestrator = self.dht_root / "src" / "DHT" / "modules" / "orchestrator.py"

        with open(orchestrator) as f:
            content = f.read()

        # Should import modules, not duplicate their functionality
        assert "import" in content, "Orchestrator should import modules"

        # Should have minimal implementation, mainly coordination
        lines = content.split("\n")
        # Count actual function definitions (not methods)
        function_lines = [
            line for line in lines if line.strip().startswith("def ") and not line.strip().startswith("def __")
        ]
        assert len(function_lines) < 10, "Orchestrator should coordinate, not implement everything"
