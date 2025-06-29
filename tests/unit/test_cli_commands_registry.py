#!/usr/bin/env python3
"""
Test Cli Commands Registry module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial creation of comprehensive tests for CLI commands registry
# - Tests for command definition structure validation
# - Tests for platform-specific command filtering
# - Tests for category-based command retrieval
# - Tests for command format specifications
# - Tests for real command examples (git, python, docker, etc.)
# - Tests for nested category handling
# - Tests for edge cases and error handling
#

"""
Comprehensive test suite for the CLI commands registry module.

This test suite follows TDD methodology and provides comprehensive coverage for:
1. Command definition structure and validation
2. Platform-specific command filtering
3. Category-based command retrieval
4. Command format specifications
5. Real command examples and their configurations
6. Edge cases and error handling

The tests use minimal mocking and realistic command definitions to ensure
the registry behaves correctly in production environments.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add DHT modules to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from DHT.modules import cli_commands_registry


class TestCommandStructure:
    """Test suite for command definition structure validation"""

    @pytest.mark.unit
    def test_all_commands_have_required_fields(self) -> Any:
        """Test that all commands have required fields"""
        # All commands must have 'commands' dict and 'category'
        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            assert "commands" in cmd_def, f"{cmd_name} missing 'commands' field"
            assert isinstance(cmd_def["commands"], dict), f"{cmd_name} 'commands' must be dict"
            assert "category" in cmd_def, f"{cmd_name} missing 'category' field"
            assert len(cmd_def["commands"]) > 0, f"{cmd_name} has empty commands dict"

    @pytest.mark.unit
    def test_command_format_specifications(self) -> Any:
        """Test that format specifications are valid when present"""
        valid_formats = ["json", "auto", "yaml", "xml", "csv", "text"]

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            if "format" in cmd_def:
                assert cmd_def["format"] in valid_formats, f"{cmd_name} has invalid format: {cmd_def['format']}"

    @pytest.mark.unit
    def test_command_platforms_field(self) -> Any:
        """Test that platform restrictions are properly specified"""
        valid_platforms = ["macos", "linux", "windows"]

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            if "platforms" in cmd_def:
                assert isinstance(cmd_def["platforms"], list), f"{cmd_name} 'platforms' must be a list"
                for platform in cmd_def["platforms"]:
                    assert platform in valid_platforms, f"{cmd_name} has invalid platform: {platform}"

    @pytest.mark.unit
    def test_command_category_hierarchy(self) -> Any:
        """Test that categories follow expected hierarchy"""
        # Get all unique categories
        categories = set()
        for cmd_def in cli_commands_registry.CLI_COMMANDS.values():
            categories.add(cmd_def["category"])

        # Check that categories match system taxonomy categories
        expected_categories = [
            "version_control",
            "language_runtimes",
            "package_managers",
            "build_tools",
            "compilers",
            "containers_virtualization",
            "cloud_tools",
            "network_tools",
            "system_tools",
            "text_processing",
            "archive_managers",
            "ci_cd_tools",
            "database_tools",
            "documentation_tools",
            "hardware_info",
            "ide_editors",
            "monitoring_tools",
            "security_tools",
            "testing_tools",
        ]

        for category in categories:
            # Category should either be in expected list or be a subcategory
            base_category = category.split(".")[0]
            assert base_category in expected_categories, f"Unknown base category: {base_category} from {category}"


class TestPlatformFiltering:
    """Test suite for platform-specific command filtering"""

    @pytest.mark.unit
    @patch("DHT.modules.system_taxonomy.get_current_platform")
    def test_get_platform_specific_commands_macos(self, mock_platform) -> Any:
        """Test filtering commands for macOS platform"""
        mock_platform.return_value = "macos"

        commands = cli_commands_registry.get_platform_specific_commands("macos")

        # Should include brew
        assert "brew" in commands
        # Should not include apt
        assert "apt" not in commands
        # Should include cross-platform tools
        assert "git" in commands
        assert "python" in commands
        assert "docker" in commands

    @pytest.mark.unit
    @patch("DHT.modules.system_taxonomy.get_current_platform")
    def test_get_platform_specific_commands_linux(self, mock_platform) -> Any:
        """Test filtering commands for Linux platform"""
        mock_platform.return_value = "linux"

        commands = cli_commands_registry.get_platform_specific_commands("linux")

        # Should include apt
        assert "apt" in commands
        # Brew can be installed on Linux (Linuxbrew), so it should be included
        assert "brew" in commands
        # Should include cross-platform tools
        assert "git" in commands
        assert "python" in commands
        assert "docker" in commands

    @pytest.mark.unit
    @patch("DHT.modules.system_taxonomy.get_current_platform")
    def test_get_platform_specific_commands_windows(self, mock_platform) -> Any:
        """Test filtering commands for Windows platform"""
        mock_platform.return_value = "windows"

        commands = cli_commands_registry.get_platform_specific_commands("windows")

        # Should include choco
        assert "choco" in commands
        # Should not include apt or brew
        assert "apt" not in commands
        assert "brew" not in commands
        # Should include cross-platform tools
        assert "git" in commands
        assert "python" in commands

    @pytest.mark.unit
    def test_get_platform_specific_commands_uses_current_by_default(self) -> Any:
        """Test that platform filtering uses current platform by default"""
        # This test verifies the function works without explicit platform
        commands = cli_commands_registry.get_platform_specific_commands()

        # Should return a dict
        assert isinstance(commands, dict)
        # Should have some commands
        assert len(commands) > 0
        # Should include common tools
        assert "git" in commands or "python" in commands


class TestCategoryFiltering:
    """Test suite for category-based command retrieval"""

    @pytest.mark.unit
    def test_get_commands_by_category_version_control(self) -> Any:
        """Test retrieving version control commands"""
        commands = cli_commands_registry.get_commands_by_category("version_control")

        assert "git" in commands
        assert commands["git"]["category"] == "version_control"
        if "hg" in cli_commands_registry.CLI_COMMANDS:
            assert "hg" in commands
        if "svn" in cli_commands_registry.CLI_COMMANDS:
            assert "svn" in commands

    @pytest.mark.unit
    def test_get_commands_by_category_language_runtimes(self) -> Any:
        """Test retrieving language runtime commands"""
        commands = cli_commands_registry.get_commands_by_category("language_runtimes")

        assert "python" in commands
        assert "node" in commands
        assert commands["python"]["category"] == "language_runtimes"
        assert commands["node"]["category"] == "language_runtimes"

    @pytest.mark.unit
    def test_get_commands_by_category_nested(self) -> Any:
        """Test retrieving commands from nested categories"""
        # Test package_managers.system.macos
        commands = cli_commands_registry.get_commands_by_category("package_managers.system.macos")

        if "brew" in cli_commands_registry.CLI_COMMANDS:
            if cli_commands_registry.CLI_COMMANDS["brew"]["category"] == "package_managers.system.macos":
                assert "brew" in commands

    @pytest.mark.unit
    def test_get_commands_by_category_partial_match(self) -> Any:
        """Test that partial category matches work"""
        # Getting 'package_managers' should include all subcategories
        commands = cli_commands_registry.get_commands_by_category("package_managers")

        # Should include package managers from all subcategories
        package_managers = ["pip", "npm", "cargo", "brew", "apt", "choco"]
        found_any = False
        for pm in package_managers:
            if pm in commands:
                found_any = True
                assert commands[pm]["category"].startswith("package_managers")

        assert found_any, "Should find at least one package manager"

    @pytest.mark.unit
    def test_get_commands_by_category_nonexistent(self) -> Any:
        """Test retrieving commands from nonexistent category"""
        commands = cli_commands_registry.get_commands_by_category("nonexistent_category")

        assert isinstance(commands, dict)
        assert len(commands) == 0


class TestCommandFormats:
    """Test suite for command format specifications"""

    @pytest.mark.unit
    def test_json_format_commands(self) -> Any:
        """Test commands that output JSON"""
        json_commands = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            if cmd_def.get("format") == "json":
                json_commands.append(cmd_name)

        # Common commands that output JSON
        expected_json_commands = ["pip", "npm", "docker"]

        for expected in expected_json_commands:
            if expected in cli_commands_registry.CLI_COMMANDS:
                if cli_commands_registry.CLI_COMMANDS[expected].get("format") == "json":
                    assert expected in json_commands

    @pytest.mark.unit
    def test_auto_format_commands(self) -> Any:
        """Test commands with auto format detection"""
        auto_commands = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            if cmd_def.get("format") == "auto":
                auto_commands.append(cmd_name)

        # Should have some auto-format commands
        assert len(auto_commands) > 0

    @pytest.mark.unit
    def test_commands_with_json_output_flag(self) -> Any:
        """Test commands that have JSON output via flags"""
        json_capable = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            for _cmd_key, cmd_str in cmd_def["commands"].items():
                if "--json" in cmd_str or "-j" in cmd_str:
                    json_capable.append(cmd_name)
                    break

        # Commands like pip, npm often have --json flags
        if "pip" in cli_commands_registry.CLI_COMMANDS:
            pip_commands = cli_commands_registry.CLI_COMMANDS["pip"]["commands"]
            # Check if any pip command uses JSON
            has_json = any("--json" in cmd or "inspect" in cmd for cmd in pip_commands.values())
            if has_json:
                assert "pip" in json_capable


class TestRealCommandExamples:
    """Test suite for real command examples"""

    @pytest.mark.unit
    def test_git_command_definition(self) -> Any:
        """Test git command is properly defined"""
        assert "git" in cli_commands_registry.CLI_COMMANDS

        git_cmd = cli_commands_registry.CLI_COMMANDS["git"]
        assert git_cmd["category"] == "version_control"
        assert "version" in git_cmd["commands"]

        # Git version command
        assert "--version" in git_cmd["commands"]["version"]

    @pytest.mark.unit
    def test_python_command_definition(self) -> Any:
        """Test python command is properly defined"""
        assert "python" in cli_commands_registry.CLI_COMMANDS

        python_cmd = cli_commands_registry.CLI_COMMANDS["python"]
        assert python_cmd["category"] == "language_runtimes"
        assert "version" in python_cmd["commands"]

        # Python version command
        version_cmd = python_cmd["commands"]["version"]
        assert "--version" in version_cmd or "-V" in version_cmd

    @pytest.mark.unit
    def test_docker_command_definition(self) -> Any:
        """Test docker command is properly defined"""
        assert "docker" in cli_commands_registry.CLI_COMMANDS

        docker_cmd = cli_commands_registry.CLI_COMMANDS["docker"]
        assert docker_cmd["category"] == "containers_virtualization"
        assert "version" in docker_cmd["commands"]

        # Docker should have info command
        if "info" in docker_cmd["commands"]:
            assert "info" in docker_cmd["commands"]["info"]

    @pytest.mark.unit
    def test_package_manager_definitions(self) -> Any:
        """Test package managers are properly defined"""
        package_managers = {
            "pip": "package_managers.language.python",
            "npm": "package_managers.language.javascript",
            "cargo": "package_managers.language.rust",
        }

        for pm, _expected_category in package_managers.items():
            if pm in cli_commands_registry.CLI_COMMANDS:
                pm_cmd = cli_commands_registry.CLI_COMMANDS[pm]
                # Category should match or at least start with package_managers
                assert pm_cmd["category"].startswith("package_managers"), f"{pm} should be in package_managers category"

    @pytest.mark.unit
    def test_cloud_tool_definitions(self) -> Any:
        """Test cloud tools are properly defined"""
        cloud_tools = ["aws", "gcloud", "az"]

        found_cloud_tools = []
        for tool in cloud_tools:
            if tool in cli_commands_registry.CLI_COMMANDS:
                found_cloud_tools.append(tool)
                tool_cmd = cli_commands_registry.CLI_COMMANDS[tool]
                assert tool_cmd["category"] == "cloud_tools"
                assert "version" in tool_cmd["commands"]

        # Should have at least one cloud tool defined
        assert len(found_cloud_tools) > 0


class TestCommandPatterns:
    """Test suite for command pattern detection"""

    @pytest.mark.unit
    def test_commands_with_error_redirect(self) -> Any:
        """Test detection of commands that redirect stderr"""
        error_redirect_commands = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            for cmd_str in cmd_def["commands"].values():
                if "2>&1" in cmd_str:
                    error_redirect_commands.append(cmd_name)
                    break

        # Some commands redirect stderr to stdout
        assert isinstance(error_redirect_commands, list)

    @pytest.mark.unit
    def test_commands_with_environment_vars(self) -> Any:
        """Test detection of commands that use environment variables"""
        env_var_commands = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            for cmd_str in cmd_def["commands"].values():
                if "$" in cmd_str or "%" in cmd_str:
                    env_var_commands.append(cmd_name)
                    break

        # Some commands might use environment variables
        assert isinstance(env_var_commands, list)

    @pytest.mark.unit
    def test_commands_with_pipes(self) -> Any:
        """Test detection of commands that use pipes"""
        piped_commands = []

        for cmd_name, cmd_def in cli_commands_registry.CLI_COMMANDS.items():
            for cmd_str in cmd_def["commands"].values():
                if "|" in cmd_str:
                    piped_commands.append(cmd_name)
                    break

        # Some complex commands might use pipes
        assert isinstance(piped_commands, list)


class TestEdgeCases:
    """Test suite for edge cases and error handling"""

    @pytest.mark.unit
    def test_empty_platform_string(self) -> Any:
        """Test handling of empty platform string"""
        commands = cli_commands_registry.get_platform_specific_commands("")

        # Should return all commands or use current platform
        assert isinstance(commands, dict)
        assert len(commands) > 0

    @pytest.mark.unit
    def test_invalid_platform_string(self) -> Any:
        """Test handling of invalid platform string"""
        commands = cli_commands_registry.get_platform_specific_commands("invalid_os")

        # Should handle gracefully
        assert isinstance(commands, dict)
        # Should at least return cross-platform commands
        if "git" in cli_commands_registry.CLI_COMMANDS:
            assert "git" in commands

    @pytest.mark.unit
    def test_none_category(self) -> Any:
        """Test handling of None category"""
        commands = cli_commands_registry.get_commands_by_category(None)

        assert isinstance(commands, dict)
        assert len(commands) == 0

    @pytest.mark.unit
    def test_command_with_multiple_categories(self) -> Any:
        """Test commands that might belong to multiple categories"""
        # For example, python is both a runtime and has package management
        if "python" in cli_commands_registry.CLI_COMMANDS:
            python_cmd = cli_commands_registry.CLI_COMMANDS["python"]
            assert "category" in python_cmd
            # Should have one primary category
            assert isinstance(python_cmd["category"], str)


# Module-level test
@pytest.mark.unit
def test_module_exports() -> Any:
    """Test that module exports expected functions"""
    assert hasattr(cli_commands_registry, "CLI_COMMANDS")
    assert hasattr(cli_commands_registry, "get_platform_specific_commands")
    assert hasattr(cli_commands_registry, "get_commands_by_category")

    # CLI_COMMANDS should be a dict
    assert isinstance(cli_commands_registry.CLI_COMMANDS, dict)

    # Functions should be callable
    assert callable(cli_commands_registry.get_platform_specific_commands)
    assert callable(cli_commands_registry.get_commands_by_category)
