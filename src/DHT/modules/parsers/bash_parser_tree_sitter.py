#!/usr/bin/env python3
from __future__ import annotations

"""
bash_parser_tree_sitter.py - Tree-sitter based parsing for Bash scripts  This module contains all tree-sitter specific parsing functionality for Bash scripts.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
bash_parser_tree_sitter.py - Tree-sitter based parsing for Bash scripts

This module contains all tree-sitter specific parsing functionality for Bash scripts.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from bash_parser.py to reduce file size
# - Contains tree-sitter based parsing methods
#


import logging
from typing import Any

try:
    import tree_sitter
    import tree_sitter_bash

    TREE_SITTER_BASH_AVAILABLE = True
except ImportError:
    TREE_SITTER_BASH_AVAILABLE = False
    tree_sitter = None
    tree_sitter_bash = None

from .bash_parser_models import SHELL_KEYWORDS, TREE_SITTER_QUERIES
from .bash_parser_utils import BashParserUtils


class TreeSitterBashParser:
    """Tree-sitter based parser for Bash scripts."""

    def __init__(self) -> None:
        """Initialize tree-sitter parser."""
        self.logger = logging.getLogger(__name__)
        self.parser = None
        self.language_obj = None
        self.utils = BashParserUtils()

        if TREE_SITTER_BASH_AVAILABLE:
            try:
                # Get the Bash language object
                self.language_obj = tree_sitter.Language(tree_sitter_bash.language())
                # Create parser and set language
                self.parser = tree_sitter.Parser(self.language_obj)
                self.logger.info("Successfully initialized tree-sitter Bash parser")
            except Exception as e:
                self.logger.warning(f"Failed to initialize tree-sitter Bash parser: {e}")
                self.parser = None
                self.language_obj = None

    def is_available(self) -> bool:
        """Check if tree-sitter parser is available."""
        return self.parser is not None

    def parse_tree(self, content: str) -> Any | None:
        """Parse content using tree-sitter if available."""
        if not self.parser:
            return None

        try:
            if isinstance(content, str):
                content = content.encode("utf-8")
            return self.parser.parse(content)
        except Exception as e:
            self.logger.error(f"Tree-sitter parsing failed: {e}")
            return None

    def query_tree(self, tree: Any, query_string: str) -> list[Any]:
        """Query a tree-sitter tree."""
        if not tree or not self.language_obj:
            return []

        try:
            query = self.language_obj.query(query_string)
            captures = query.captures(tree.root_node)
            return captures
        except Exception as e:
            self.logger.error(f"Tree query failed: {e}")
            return []

    def extract_functions(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract function definitions using tree-sitter."""
        functions = []

        # Query for function definitions
        captures = self.query_tree(tree, TREE_SITTER_QUERIES["functions"])

        current_func = {}
        for node, capture_name in captures:
            if capture_name == "function":
                if current_func and "name" in current_func:
                    functions.append(current_func)
                current_func = {
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                }
            elif capture_name == "name":
                current_func["name"] = content[node.start_byte : node.end_byte]
            elif capture_name == "body":
                current_func["body"] = content[node.start_byte : node.end_byte]
                current_func["local_vars"] = self.utils.extract_local_vars_from_body(current_func["body"])

        if current_func:
            functions.append(current_func)

        # Also look for alternative function syntax
        alt_captures = self.query_tree(tree, TREE_SITTER_QUERIES["alt_functions"])
        current_func = {}
        for node, capture_name in alt_captures:
            if capture_name == "function":
                if current_func and "name" in current_func:
                    functions.append(current_func)
                current_func = {
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                }
            elif capture_name == "name":
                current_func["name"] = content[node.start_byte : node.end_byte]
            elif capture_name == "body":
                current_func["body"] = content[node.start_byte : node.end_byte]
                current_func["local_vars"] = self.utils.extract_local_vars_from_body(current_func["body"])

        if current_func and "name" in current_func:
            functions.append(current_func)

        return functions

    def extract_variables(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract variable assignments using tree-sitter."""
        variables = []

        captures = self.query_tree(tree, TREE_SITTER_QUERIES["variables"])

        current_var = {}
        for node, name in captures:
            if name == "assignment":
                if current_var:
                    variables.append(current_var)
                current_var = {"line": node.start_point[0] + 1}
            elif name == "name":
                current_var["name"] = content[node.start_byte : node.end_byte]
            elif name == "value":
                current_var["value"] = content[node.start_byte : node.end_byte]
                current_var["type"] = self.utils.infer_var_type(current_var["value"])

        if current_var:
            variables.append(current_var)

        return variables

    def extract_exports(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract exported variables using tree-sitter."""
        exports = []

        captures = self.query_tree(tree, TREE_SITTER_QUERIES["exports"])

        for node, name in captures:
            if name == "arg":
                arg_text = content[node.start_byte : node.end_byte]
                # Parse the export argument
                if "=" in arg_text:
                    var_name, var_value = arg_text.split("=", 1)
                    exports.append(
                        {
                            "name": var_name,
                            "value": var_value.strip("\"'"),
                            "line": node.start_point[0] + 1,
                        }
                    )
                else:
                    exports.append(
                        {
                            "name": arg_text,
                            "value": None,
                            "line": node.start_point[0] + 1,
                        }
                    )

        return exports

    def extract_sources(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract sourced files using tree-sitter."""
        sources = []

        captures = self.query_tree(tree, TREE_SITTER_QUERIES["sources"])

        for node, name in captures:
            if name == "file":
                file_path = content[node.start_byte : node.end_byte].strip("\"'")
                sources.append(
                    {
                        "path": file_path,
                        "line": node.start_point[0] + 1,
                        "resolved": self.utils.resolve_source_path(file_path),
                    }
                )

        return sources

    def extract_commands(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract command invocations using tree-sitter."""
        commands = []
        seen_commands = set()

        captures = self.query_tree(tree, TREE_SITTER_QUERIES["commands"])

        current_cmd = {}
        for node, capture_name in captures:
            if capture_name == "command":
                if current_cmd and "name" in current_cmd:
                    cmd_name = current_cmd["name"]
                    if cmd_name not in seen_commands:
                        seen_commands.add(cmd_name)
                        commands.append(current_cmd)
                current_cmd = {"line": node.start_point[0] + 1, "args": []}
            elif capture_name == "name":
                name_text = content[node.start_byte : node.end_byte]
                # Skip shell keywords
                if name_text not in SHELL_KEYWORDS:
                    current_cmd["name"] = name_text
            elif capture_name == "args" and "name" in current_cmd:
                arg_text = content[node.start_byte : node.end_byte]
                current_cmd["args"].append(arg_text)

        if current_cmd and "name" in current_cmd:
            cmd_name = current_cmd["name"]
            if cmd_name not in seen_commands:
                commands.append(current_cmd)

        return commands

    def extract_comments(self, tree: Any, content: str) -> list[dict[str, Any]]:
        """Extract comments using tree-sitter."""
        comments = []

        captures = self.query_tree(tree, TREE_SITTER_QUERIES["comments"])

        for node, _ in captures:
            comment_text = content[node.start_byte : node.end_byte]
            comments.append(
                {
                    "text": comment_text.lstrip("#").strip(),
                    "line": node.start_point[0] + 1,
                    "is_shebang": comment_text.startswith("#!"),
                }
            )

        return comments

    def extract_control_structures(self, tree: Any) -> dict[str, int]:
        """Count control structures using tree-sitter."""
        structures = {
            "if_statements": 0,
            "for_loops": 0,
            "while_loops": 0,
            "case_statements": 0,
            "functions": 0,
        }

        for structure_type, query in TREE_SITTER_QUERIES.items():
            if structure_type.endswith("_statements") or structure_type.endswith("_loops"):
                captures = self.query_tree(tree, query)
                structures[structure_type] = len(captures)

        # Count functions
        captures = self.query_tree(tree, TREE_SITTER_QUERIES["function_defs"])
        structures["functions"] = len(captures)

        return structures


# Export public API
__all__ = ["TreeSitterBashParser", "TREE_SITTER_BASH_AVAILABLE"]
