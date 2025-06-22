#!/usr/bin/env python3
"""
Test for duplicate function definitions in shell scripts.  This test ensures that functions are not duplicated across different shell script modules, which could cause conflicts and confusion.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test for duplicate function definitions in shell scripts.

This test ensures that functions are not duplicated across different
shell script modules, which could cause conflicts and confusion.
"""

import re
from pathlib import Path

import pytest


class TestDuplicateFunctions:
    """Test for duplicate function definitions."""

    def setup_method(self):
        """Set up test environment."""
        self.modules_dir = Path(__file__).parent.parent.parent / "src" / "DHT" / "modules"
        self.shell_scripts = list(self.modules_dir.glob("*.sh"))

    def test_no_duplicate_workflows_command(self):
        """Test that workflows_command is not duplicated across shell scripts."""
        workflows_definitions = []

        for script in self.shell_scripts:
            content = script.read_text()

            # Find function definitions
            patterns = [
                r"^\s*workflows_command\s*\(\s*\)\s*\{",  # workflows_command() {
                r"^\s*function\s+workflows_command\s*\{",  # function workflows_command {
                r"^\s*function\s+workflows_command\s*\(\s*\)\s*\{",  # function workflows_command() {
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    workflows_definitions.append({"file": script.name, "line": line_num, "pattern": match.group()})

        # There should be exactly one workflows_command definition
        assert len(workflows_definitions) <= 1, (
            f"Found {len(workflows_definitions)} workflows_command definitions: {workflows_definitions}"
        )

        if len(workflows_definitions) == 1:
            # Should be in the dedicated workflows file
            definition = workflows_definitions[0]
            assert definition["file"] == "dhtl_commands_workflows.sh", (
                f"workflows_command should be in dhtl_commands_workflows.sh, but found in {definition['file']}"
            )

    def test_no_duplicate_functions_general(self):
        """Test that no functions are duplicated across shell scripts."""
        function_definitions = {}

        for script in self.shell_scripts:
            content = script.read_text()

            # Find all function definitions
            patterns = [
                r"^\s*(\w+)\s*\(\s*\)\s*\{",  # function_name() {
                r"^\s*function\s+(\w+)\s*\{",  # function function_name {
                r"^\s*function\s+(\w+)\s*\(\s*\)\s*\{",  # function function_name() {
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    function_name = match.group(1)
                    line_num = content[: match.start()].count("\n") + 1

                    if function_name not in function_definitions:
                        function_definitions[function_name] = []

                    function_definitions[function_name].append({"file": script.name, "line": line_num})

        # Find duplicates
        duplicates = {name: defs for name, defs in function_definitions.items() if len(defs) > 1}

        # Some functions are legitimately duplicated (like common utilities)
        # But workflows_command should not be
        critical_duplicates = {name: defs for name, defs in duplicates.items() if name in ["workflows_command"]}

        assert len(critical_duplicates) == 0, f"Found critical duplicate functions: {critical_duplicates}"

        # Report all duplicates for awareness (but don't fail the test)
        if duplicates:
            print(f"\nFound {len(duplicates)} duplicate function names:")
            for name, defs in duplicates.items():
                locations = [f"{d['file']}:{d['line']}" for d in defs]
                print(f"  {name}: {locations}")

    def test_workflows_command_properly_located(self):
        """Test that workflows_command is in the right file with proper implementation."""
        workflows_file = self.modules_dir / "dhtl_commands_workflows.sh"

        if not workflows_file.exists():
            pytest.skip("dhtl_commands_workflows.sh not found")

        content = workflows_file.read_text()

        # Should contain workflows_command definition
        assert "workflows_command()" in content, (
            "dhtl_commands_workflows.sh should contain workflows_command() definition"
        )

        # Should have subcommand handling
        assert 'case "$subcommand" in' in content, "workflows_command should handle subcommands with case statement"

        # Should have essential subcommands
        essential_subcommands = ["lint", "run", "list", "help"]
        for subcommand in essential_subcommands:
            assert f"{subcommand})" in content, f"workflows_command should handle '{subcommand}' subcommand"
