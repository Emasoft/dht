#!/usr/bin/env python3
"""
Test template files for syntax errors and proper functionality.  This test verifies that files containing template placeholders are either: 1. Properly configured with actual values 2. Not executed as Python modules (and thus safe to have placeholders) 3. Removed if unused by DHT

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test template files for syntax errors and proper functionality.

This test verifies that files containing template placeholders are either:
1. Properly configured with actual values
2. Not executed as Python modules (and thus safe to have placeholders)
3. Removed if unused by DHT
"""

import ast
import re
from pathlib import Path
from typing import Any

import pytest


class TestTemplateFiles:
    """Test template files functionality."""

    def setup_method(self) -> Any:
        """Set up test environment."""
        self.dht_modules_dir = Path(__file__).parent.parent.parent / "src" / "DHT" / "modules"
        self.template_files = [
            "blame.py",
            "clean_metadata.py",
            "homepage.py",
            "issues.py",
            "logo_svg.py",
            "my_models.py",
            "dl_icons.py",
        ]

    def test_template_files_removed(self) -> Any:
        """Test that template files with syntax errors have been removed."""
        for filename in self.template_files:
            file_path = self.dht_modules_dir / filename
            assert not file_path.exists(), f"Template file {filename} should have been removed"

    def test_no_template_files_remaining(self) -> Any:
        """Test that no template files with syntax errors remain in modules directory."""
        # Get all Python files in the modules directory
        python_files = list(self.dht_modules_dir.glob("*.py"))

        placeholder_patterns = [r"\{REPO_NAME\}", r"\{AUTHOR_NAME_OR_REPO_OWNER\}", r"\{TEMPLATE_"]

        for py_file in python_files:
            try:
                content = py_file.read_text()

                # Check if file contains template placeholders
                has_placeholders = any(re.search(pattern, content) for pattern in placeholder_patterns)

                if has_placeholders:
                    pytest.fail(
                        f"File {py_file.name} still contains template placeholders and should be removed or fixed"
                    )

                # All remaining Python files should have valid syntax
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"File {py_file.name} has invalid Python syntax: {e}")

            except UnicodeDecodeError:
                # Skip binary files
                continue

    def test_template_files_removed_successfully(self) -> Any:
        """Test that template files have been successfully removed."""
        blame_path = self.dht_modules_dir / "blame.py"

        # File should not exist anymore
        assert not blame_path.exists(), "blame.py should have been removed"

        # All template files should be gone
        for filename in self.template_files:
            file_path = self.dht_modules_dir / filename
            assert not file_path.exists(), f"Template file {filename} should have been removed"

    def test_template_files_not_imported_by_dht(self) -> Any:
        """Test that template files are not imported by DHT modules."""
        # Get all Python files in the modules directory
        python_files = list(self.dht_modules_dir.glob("*.py"))

        # Check imports in each file
        for py_file in python_files:
            if py_file.name in self.template_files:
                continue  # Skip the template files themselves

            try:
                content = py_file.read_text()

                # Check for imports of template files
                for template_file in self.template_files:
                    module_name = template_file.replace(".py", "")

                    # These patterns would indicate the template is being imported
                    import_patterns = [
                        f"import {module_name}",
                        f"from {module_name}",
                        f"from .{module_name}",
                        f"import .{module_name}",
                    ]

                    for pattern in import_patterns:
                        assert pattern not in content, f"File {py_file.name} imports template file {template_file}"

            except UnicodeDecodeError:
                # Skip binary files
                continue

    def test_orchestrator_py_imports_template_files(self) -> Any:
        """Test whether orchestrator.py tries to import template files."""
        orchestrator_path = self.dht_modules_dir / "orchestrator.py"
        if not orchestrator_path.exists():
            pytest.skip("orchestrator.py not found")

        content = orchestrator_path.read_text()

        # Check if any template files are imported
        for template_file in self.template_files:
            module_name = template_file.replace(".py", "")
            import_patterns = [f"import {module_name}", f"from {module_name}", f"from .{module_name}"]
            for pattern in import_patterns:
                assert pattern not in content, f"orchestrator.py should not import template file {template_file}"

    def test_template_files_issue_resolved(self) -> Any:
        """Test that template files issue has been resolved."""
        # This test documents that the template files issue has been resolved
        # The files with placeholders have been removed since they were unused

        # Verify no template files remain
        remaining_template_files = []
        for filename in self.template_files:
            file_path = self.dht_modules_dir / filename
            if file_path.exists():
                remaining_template_files.append(filename)

        # Document the resolution
        assert len(remaining_template_files) == 0, (
            f"All template files should have been removed, but found: {remaining_template_files}"
        )

        print("\n✅ Template files issue resolved:")
        print(f"  - Removed {len(self.template_files)} unused template files with syntax errors")
        print("  - All Python files in modules/ directory now have valid syntax")
        print("  - No more template placeholders causing issues")
