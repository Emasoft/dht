#!/usr/bin/env python3
"""
bash_parser_models.py - Data models and constants for Bash parser  This module contains data models, constants, and common patterns used by the Bash parser.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
bash_parser_models.py - Data models and constants for Bash parser

This module contains data models, constants, and common patterns used by the Bash parser.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from bash_parser.py to reduce file size
# - Contains constants and common patterns for bash parsing
#

from __future__ import annotations

# Common commands to look for in scripts
COMMON_COMMANDS: set[str] = {
    "git",
    "docker",
    "npm",
    "pip",
    "python",
    "node",
    "make",
    "gcc",
    "curl",
    "wget",
    "apt-get",
    "yum",
    "brew",
    "cargo",
    "go",
    "mvn",
    "gradle",
    "rake",
    "bundle",
    "composer",
    "yarn",
    "pnpm",
    "uv",
    "apt",
    "dpkg",
    "rpm",
    "pacman",
    "emerge",
    "zypper",
    "dnf",
    "javac",
    "rustc",
    "clang",
    "g++",
    "dotnet",
    "sbt",
    "lein",
    "pod",
    "flutter",
    "react-native",
    "ng",
    "vue",
    "gatsby",
    "webpack",
    "parcel",
    "rollup",
    "tsc",
    "babel",
    "eslint",
    "pytest",
    "jest",
    "mocha",
    "rspec",
    "phpunit",
    "junit",
}

# Shell keywords to skip when extracting commands
SHELL_KEYWORDS: set[str] = {
    "if",
    "then",
    "else",
    "elif",
    "fi",
    "for",
    "while",
    "do",
    "done",
    "case",
    "esac",
    "function",
    "return",
    "break",
    "continue",
    "export",
    "source",
    ".",
    "eval",
    "exec",
    "exit",
    "set",
    "unset",
    "shift",
    "trap",
    "wait",
    "jobs",
    "bg",
    "fg",
    "disown",
    "suspend",
    "true",
    "false",
    "test",
    "[",
    "[[",
    "]]",
    "]",
    "echo",
    "printf",
    "read",
    "cd",
    "pwd",
    "pushd",
    "popd",
    "dirs",
    "history",
    "alias",
    "unalias",
    "type",
    "which",
    "command",
    "builtin",
    "enable",
    "help",
}

# File extensions for shell scripts
SHELL_EXTENSIONS: set[str] = {".sh", ".bash", ".zsh", ".ksh", ".fish", ".ash", ".dash"}

# Common shell script names without extensions
SHELL_SCRIPT_NAMES: set[str] = {
    "bashrc",
    "bash_profile",
    "zshrc",
    "profile",
    "bash_aliases",
    "bash_functions",
    "bash_logout",
    "inputrc",
    "dircolors",
}

# Patterns for different types of variable values
ARRAY_PATTERN = r"^\s*\(\s*.*\s*\)\s*$"
PATH_PATTERN = r"^[/~].*|.*\.\.?/.*"
NUMBER_PATTERN = r"^\s*-?\d+(\.\d+)?\s*$"
BOOLEAN_PATTERN = r"^\s*(true|false|yes|no|on|off|1|0)\s*$"

# Tree-sitter queries for Bash parsing
TREE_SITTER_QUERIES = {
    "functions": """
        (function_definition
            name: (word) @name
            body: (compound_statement) @body) @function
    """,
    "alt_functions": """
        (command
            name: (command_name (word) @keyword)
            (#eq? @keyword "function")
            . (word) @name
            . (compound_statement) @body) @function
    """,
    "variables": """
        (variable_assignment
            name: (variable_name) @name
            value: (_) @value) @assignment
    """,
    "exports": """
        (command
            name: (command_name (word) @cmd)
            (#eq? @cmd "export")
            argument: (_) @arg) @export
    """,
    "sources": """
        (command
            name: (command_name (word) @cmd)
            (#match? @cmd "^(source|\\.)$")
            argument: (_) @file) @source
    """,
    "commands": """
        (command
            name: (command_name) @name
            argument: (_)* @args) @command
    """,
    "comments": """
        (comment) @comment
    """,
    "if_statements": "(if_statement) @item",
    "for_loops": "(for_statement) @item",
    "while_loops": "(while_statement) @item",
    "case_statements": "(case_statement) @item",
    "function_defs": "(function_definition) @item",
}

# Regex patterns for fallback parsing
REGEX_PATTERNS = {
    "function_def1": r"^\s*(\w+)\s*\(\s*\)\s*\{",
    "function_def2": r"^\s*function\s+(\w+)\s*\{",
    "variable_assignment": r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$",
    "export_statement": r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.*))?",
    "source_statement": r"^\s*(?:source|\.)\s+([^\s;|&]+)",
    "shebang": r"^#!\s*(\S+)",
    "local_var": r"^\s*local\s+(?:-[a-zA-Z]+\s+)?([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.*))?",
    "command_call": r"^\s*(\w+)(?:\s+(.*))?$",
}

# Export public API
__all__ = [
    "COMMON_COMMANDS",
    "SHELL_KEYWORDS",
    "SHELL_EXTENSIONS",
    "SHELL_SCRIPT_NAMES",
    "ARRAY_PATTERN",
    "PATH_PATTERN",
    "NUMBER_PATTERN",
    "BOOLEAN_PATTERN",
    "TREE_SITTER_QUERIES",
    "REGEX_PATTERNS",
]
