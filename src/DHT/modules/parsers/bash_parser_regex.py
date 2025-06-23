#!/usr/bin/env python3
from __future__ import annotations

"""
bash_parser_regex.py - Regex-based fallback parsing for Bash scripts  This module provides regex-based parsing as a fallback when tree-sitter is not available.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
bash_parser_regex.py - Regex-based fallback parsing for Bash scripts

This module provides regex-based parsing as a fallback when tree-sitter is not available.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from bash_parser.py to reduce file size
# - Contains regex-based fallback parsing methods
#


import re
from typing import Any

from .bash_parser_models import COMMON_COMMANDS, REGEX_PATTERNS
from .bash_parser_utils import BashParserUtils


class RegexBashParser:
    """Regex-based fallback parser for Bash scripts."""

    def __init__(self) -> None:
        """Initialize regex parser."""
        self.utils = BashParserUtils()

    def extract_functions(self, content: str) -> list[dict[str, Any]]:
        """Extract functions using regex (fallback)."""
        functions = []

        # Split content into lines for easier processing
        lines = content.splitlines()

        # Track brace depth to find function boundaries
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for function definitions
            match1 = re.match(REGEX_PATTERNS["function_def1"], line)
            match2 = re.match(REGEX_PATTERNS["function_def2"], line)

            if match1 or match2:
                func_name = match1.group(1) if match1 else match2.group(1)
                start_line = i + 1  # 1-based line number

                # Find the matching closing brace
                brace_count = 1
                func_lines = []
                j = i + 1

                while j < len(lines) and brace_count > 0:
                    func_line = lines[j]
                    func_lines.append(func_line)

                    # Count braces (simple approach - doesn't handle strings/comments perfectly)
                    brace_count += func_line.count("{") - func_line.count("}")
                    j += 1

                # Extract function body
                if func_lines and func_lines[-1].strip() == "}":
                    func_body = "\n".join(func_lines[:-1])
                else:
                    func_body = "\n".join(func_lines)

                functions.append(
                    {
                        "name": func_name,
                        "body": func_body,
                        "line": start_line,
                        "local_vars": self.utils.extract_local_vars_from_body(func_body),
                    }
                )

                # Skip past this function
                i = j - 1

            i += 1

        return functions

    def extract_variables(self, content: str) -> list[dict[str, Any]]:
        """Extract variable assignments using regex."""
        variables = []

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(REGEX_PATTERNS["variable_assignment"], line.strip())
            if match and not line.strip().startswith("#"):
                var_name = match.group(1)
                var_value = match.group(2).strip("\"'")

                variables.append(
                    {
                        "name": var_name,
                        "value": var_value,
                        "line": line_num,
                        "type": self.utils.infer_var_type(var_value),
                    }
                )

        return variables

    def extract_exports(self, content: str) -> list[dict[str, Any]]:
        """Extract exported variables using regex."""
        exports = []

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(REGEX_PATTERNS["export_statement"], line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2).strip("\"'") if match.group(2) else None

                exports.append({"name": var_name, "value": var_value, "line": line_num})

        return exports

    def extract_sources(self, content: str) -> list[dict[str, Any]]:
        """Extract sourced files using regex."""
        sources = []

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(REGEX_PATTERNS["source_statement"], line)
            if match:
                file_path = match.group(1).strip("\"'")
                sources.append(
                    {
                        "path": file_path,
                        "line": line_num,
                        "resolved": self.utils.resolve_source_path(file_path),
                    }
                )

        return sources

    def extract_commands(self, content: str) -> list[dict[str, Any]]:
        """Extract command invocations using regex."""
        commands = []
        seen_commands = set()

        # Look for lines that appear to be command invocations
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check if line starts with a common command
            for cmd in COMMON_COMMANDS:
                if line.startswith(cmd + " ") or line == cmd:
                    if cmd not in seen_commands:
                        seen_commands.add(cmd)

                        # Extract arguments
                        args = []
                        if len(line) > len(cmd):
                            args_str = line[len(cmd) :].strip()
                            # Simple argument splitting (doesn't handle quotes perfectly)
                            args = args_str.split()

                        commands.append(
                            {
                                "name": cmd,
                                "line": line_num,
                                "args": args,
                            }
                        )
                    break

        return commands

    def extract_comments(self, content: str) -> list[dict[str, Any]]:
        """Extract comments using regex."""
        lines = content.splitlines()
        return self.utils.extract_comments_from_lines(lines)

    def extract_control_structures(self, content: str) -> dict[str, int]:
        """Count control structures using regex."""
        structures = {
            "if_statements": 0,
            "for_loops": 0,
            "while_loops": 0,
            "case_statements": 0,
            "functions": 0,
        }

        # Count different structures
        structures["if_statements"] = len(re.findall(r"\bif\s+", content))
        structures["for_loops"] = len(re.findall(r"\bfor\s+", content))
        structures["while_loops"] = len(re.findall(r"\bwhile\s+", content))
        structures["case_statements"] = len(re.findall(r"\bcase\s+", content))

        # Count functions (both syntaxes)
        func_count1 = len(re.findall(REGEX_PATTERNS["function_def1"], content, re.MULTILINE))
        func_count2 = len(re.findall(REGEX_PATTERNS["function_def2"], content, re.MULTILINE))
        structures["functions"] = func_count1 + func_count2

        return structures


# Export public API
__all__ = ["RegexBashParser"]
