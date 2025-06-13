#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bash_parser.py - Bash script parser using tree-sitter

This module provides comprehensive Bash script parsing using tree-sitter.
It extracts functions, variables, sourced files, and commands from shell scripts.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    import tree_sitter
    import tree_sitter_bash

    TREE_SITTER_BASH_AVAILABLE = True
except ImportError:
    TREE_SITTER_BASH_AVAILABLE = False

from .base_parser import BaseParser


class BashParser(BaseParser):
    """
    Parser for Bash shell scripts using tree-sitter.

    Extracts:
    - Function definitions
    - Variable declarations and exports
    - Sourced files
    - Commands and their arguments
    - Comments and documentation
    - Control structures
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = None
        self.language_obj = None

        # Initialize tree-sitter with bash language
        if TREE_SITTER_BASH_AVAILABLE:
            try:
                # Get the Bash language object
                self.language_obj = tree_sitter.Language(tree_sitter_bash.language())
                # Create parser and set language
                self.parser = tree_sitter.Parser(self.language_obj)
                self.logger.info("Successfully initialized tree-sitter Bash parser")
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize tree-sitter Bash parser: {e}"
                )
                self.logger.info("Will use regex-based parsing as fallback")
                self.parser = None
                self.language_obj = None
        else:
            self.logger.warning(
                "tree-sitter-bash not available, using regex-based parsing"
            )
            self.parser = None
            self.language_obj = None

    def parse_tree_sitter(self, content: str) -> Optional[Any]:
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

    def query_tree(self, tree: Any, query_string: str) -> List[Any]:
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

    def read_file_safe(self, file_path: Path, encoding: str = "utf-8") -> Optional[str]:
        """Safely read file contents with error handling."""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file metadata."""
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "permissions": oct(stat.st_mode),
            "absolute_path": str(file_path.absolute()),
            "name": file_path.name,
            "extension": file_path.suffix,
        }

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Bash script and extract comprehensive information.

        Args:
            file_path: Path to the Bash script

        Returns:
            Dictionary containing parsed information
        """
        content = self.read_file_safe(file_path)
        if content is None:
            return {"error": f"Could not read file {file_path}"}

        # Use tree-sitter if available, otherwise fall back to regex
        if self.parser:
            try:
                tree = self.parse_tree_sitter(content)
                if tree:
                    return {
                        "file_metadata": self.get_file_metadata(file_path),
                        "functions": self._extract_functions_ts(tree, content),
                        "variables": self._extract_variables_ts(tree, content),
                        "exports": self._extract_exports_ts(tree, content),
                        "sourced_files": self._extract_sources_ts(tree, content),
                        "commands": self._extract_commands_ts(tree, content),
                        "shebang": self._extract_shebang(content),
                        "comments": self._extract_comments_ts(tree, content),
                        "dependencies": self._extract_dependencies_from_content(
                            content
                        ),
                        "control_structures": self._extract_control_structures_ts(
                            tree, content
                        ),
                    }
            except Exception as e:
                self.logger.warning(f"Tree-sitter parsing failed for {file_path}: {e}")
                self.logger.info("Falling back to regex-based parsing")

        # Fall back to regex parsing
        return self._parse_with_regex(content, file_path)

    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract external command dependencies"""
        content = self.read_file_safe(file_path)
        if content is None:
            return []

        return self._extract_dependencies_from_content(content)

    def _extract_functions_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions using tree-sitter"""
        functions = []

        # Query for function definitions
        query_string = """
        (function_definition
            name: (word) @name
            body: (compound_statement) @body) @function
        """

        captures = self.query_tree(tree, query_string)

        # Group captures by function
        current_func = {}
        for node, name in captures:
            if name == "function":
                if current_func:
                    functions.append(current_func)
                current_func = {
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte,
                }
            elif name == "name" and current_func is not None:
                current_func["name"] = content[node.start_byte : node.end_byte]
            elif name == "body" and current_func is not None:
                current_func["body"] = content[node.start_byte : node.end_byte]
                # Extract local variables within function
                current_func["local_vars"] = self._extract_local_vars_from_body(
                    current_func["body"]
                )

        if current_func:
            functions.append(current_func)

        # Also look for alternative function syntax: function name() { ... }
        alt_query = """
        (command
            name: (command_name (word) @keyword)
            (#eq? @keyword "function")
            . (word) @name
            . (compound_statement) @body) @function
        """

        alt_captures = self.query_tree(tree, alt_query)
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
                current_func["local_vars"] = self._extract_local_vars_from_body(
                    current_func["body"]
                )

        if current_func and "name" in current_func:
            functions.append(current_func)

        return functions

    def _extract_variables_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract variable assignments using tree-sitter"""
        variables = []

        # Query for variable assignments
        query_string = """
        (variable_assignment
            name: (variable_name) @name
            value: (_) @value) @assignment
        """

        captures = self.query_tree(tree, query_string)

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
                current_var["type"] = self._infer_var_type(current_var["value"])

        if current_var:
            variables.append(current_var)

        return variables

    def _extract_exports_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract exported variables using tree-sitter"""
        exports = []

        # Query for export commands
        query_string = """
        (command
            name: (command_name (word) @cmd)
            (#eq? @cmd "export")
            argument: (_) @arg) @export
        """

        captures = self.query_tree(tree, query_string)

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

    def _extract_sources_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract sourced files using tree-sitter"""
        sources = []

        # Query for source/. commands
        query_string = """
        (command
            name: (command_name (word) @cmd)
            (#match? @cmd "^(source|\\.)$")
            argument: (_) @file) @source
        """

        captures = self.query_tree(tree, query_string)

        for node, name in captures:
            if name == "file":
                file_path = content[node.start_byte : node.end_byte].strip("\"'")
                sources.append(
                    {
                        "path": file_path,
                        "line": node.start_point[0] + 1,
                        "resolved": self._resolve_source_path(file_path),
                    }
                )

        return sources

    def _extract_commands_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract command invocations using tree-sitter"""
        commands = []
        seen_commands = set()

        # Query for command invocations
        query_string = """
        (command
            name: (command_name) @name
            argument: (_)* @args) @command
        """

        captures = self.query_tree(tree, query_string)

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
                if name_text not in {
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
                }:
                    current_cmd["name"] = name_text
            elif capture_name == "args" and "name" in current_cmd:
                arg_text = content[node.start_byte : node.end_byte]
                current_cmd["args"].append(arg_text)

        if current_cmd and "name" in current_cmd:
            cmd_name = current_cmd["name"]
            if cmd_name not in seen_commands:
                commands.append(current_cmd)

        return commands

    def _extract_comments_ts(self, tree: Any, content: str) -> List[Dict[str, Any]]:
        """Extract comments using tree-sitter"""
        comments = []

        # Query for comments
        query_string = """
        (comment) @comment
        """

        captures = self.query_tree(tree, query_string)

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

    def _extract_control_structures_ts(self, tree: Any, content: str) -> Dict[str, int]:
        """Count control structures using tree-sitter"""
        structures = {
            "if_statements": 0,
            "for_loops": 0,
            "while_loops": 0,
            "case_statements": 0,
            "functions": 0,
        }

        # Query for different control structures
        queries = {
            "if_statements": "(if_statement) @item",
            "for_loops": "(for_statement) @item",
            "while_loops": "(while_statement) @item",
            "case_statements": "(case_statement) @item",
            "functions": "(function_definition) @item",
        }

        for structure_type, query in queries.items():
            captures = self.query_tree(tree, query)
            structures[structure_type] = len(captures)

        return structures

    def _parse_with_regex(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Fallback regex-based parsing when tree-sitter is not available"""
        return {
            "file_metadata": self.get_file_metadata(file_path),
            "functions": self._extract_functions_regex(content),
            "variables": self._extract_variables_regex(content),
            "exports": self._extract_exports_regex(content),
            "sourced_files": self._extract_sources_regex(content),
            "commands": self._extract_commands_regex(content),
            "shebang": self._extract_shebang(content),
            "comments": self._extract_comments_regex(content),
            "dependencies": self._extract_dependencies_from_content(content),
            "parser_type": "regex",
        }

    def _extract_functions_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract functions using regex (fallback)"""
        functions = []

        # Split content into lines for easier processing
        lines = content.splitlines()

        # Track brace depth to find function boundaries
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for function definitions
            # Pattern 1: name() {
            match1 = re.match(r"^\s*(\w+)\s*\(\s*\)\s*\{", line)
            # Pattern 2: function name {
            match2 = re.match(r"^\s*function\s+(\w+)\s*\{", line)

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

                # Extract function body (excluding the last closing brace line if it only contains })
                if func_lines and func_lines[-1].strip() == "}":
                    func_body = "\n".join(func_lines[:-1])
                else:
                    func_body = "\n".join(func_lines)

                functions.append(
                    {
                        "name": func_name,
                        "body": func_body,
                        "line": start_line,
                        "local_vars": self._extract_local_vars_from_body(func_body),
                    }
                )

                # Skip past this function
                i = j - 1

            i += 1

        return functions

    def _extract_variables_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract variable assignments using regex"""
        variables = []

        # Match variable assignments: VAR=value
        var_pattern = r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(var_pattern, line.strip())
            if match and not line.strip().startswith("#"):
                var_name = match.group(1)
                var_value = match.group(2).strip("\"'")

                variables.append(
                    {
                        "name": var_name,
                        "value": var_value,
                        "line": line_num,
                        "type": self._infer_var_type(var_value),
                    }
                )

        return variables

    def _extract_exports_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract exported variables using regex"""
        exports = []

        # Match export statements
        export_pattern = r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.*))?"

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(export_pattern, line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2).strip("\"'") if match.group(2) else None

                exports.append({"name": var_name, "value": var_value, "line": line_num})

        return exports

    def _extract_sources_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract sourced files using regex"""
        sources = []

        # Match source or . commands - fixed to properly match . command
        source_pattern = r"^\s*(?:source|\.)\s+([^\s;|&]+)"

        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.match(source_pattern, line)
            if match:
                file_path = match.group(1).strip("\"'")
                sources.append(
                    {
                        "path": file_path,
                        "line": line_num,
                        "resolved": self._resolve_source_path(file_path),
                    }
                )

        return sources

    def _extract_commands_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract command invocations using regex"""
        commands = []
        seen_commands = set()

        # Common commands to look for
        common_commands = {
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
        }

        for cmd in common_commands:
            if cmd in content and cmd not in seen_commands:
                seen_commands.add(cmd)
                commands.append({"name": cmd, "found": True})

        return commands

    def _extract_comments_regex(self, content: str) -> List[Dict[str, Any]]:
        """Extract comments using regex"""
        comments = []

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line.startswith("#"):
                comments.append(
                    {
                        "text": line[1:].strip(),
                        "line": line_num,
                        "is_shebang": line.startswith("#!"),
                    }
                )

        return comments

    def _extract_shebang(self, content: str) -> Optional[str]:
        """Extract shebang line"""
        lines = content.splitlines()
        if lines and lines[0].startswith("#!"):
            return lines[0]
        return None

    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """Extract external command dependencies from content"""
        dependencies = set()

        # Common external commands
        external_commands = {
            "curl",
            "wget",
            "git",
            "docker",
            "npm",
            "yarn",
            "pip",
            "python",
            "node",
            "ruby",
            "perl",
            "java",
            "gcc",
            "g++",
            "make",
            "cmake",
            "apt-get",
            "yum",
            "dnf",
            "pacman",
            "brew",
            "port",
            "snap",
            "systemctl",
            "service",
            "mysql",
            "psql",
            "mongo",
            "redis-cli",
            "aws",
            "gcloud",
            "az",
            "kubectl",
            "helm",
            "terraform",
            "ansible",
        }

        # Look for command invocations
        for cmd in external_commands:
            # Check if command is used (not in comments)
            # Escape special regex characters in command name
            escaped_cmd = re.escape(cmd)
            pattern = rf"\b{escaped_cmd}\b"
            for line in content.splitlines():
                if not line.strip().startswith("#") and re.search(pattern, line):
                    dependencies.add(cmd)
                    break

        return sorted(list(dependencies))

    def _extract_local_vars_from_body(self, body: str) -> List[str]:
        """Extract local variable declarations from function body"""
        local_vars = []
        seen_vars = set()

        # Match local variable declarations
        # Pattern 1: local var=value
        # Pattern 2: local var
        # Pattern 3: local -a var (array declaration)
        # Pattern 4: local var=$(command)
        local_patterns = [
            r"^\s*local\s+(?:-[a-zA-Z]\s+)?([A-Za-z_][A-Za-z0-9_]*)",
            r"local\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
        ]

        for line in body.splitlines():
            for pattern in local_patterns:
                matches = re.findall(pattern, line)
                for var_name in matches:
                    if var_name not in seen_vars:
                        seen_vars.add(var_name)
                        local_vars.append(var_name)

        return local_vars

    def _infer_var_type(self, value: str) -> str:
        """Infer variable type from its value"""
        value = value.strip()

        # Array
        if value.startswith("(") and value.endswith(")"):
            return "array"

        # Boolean-like (check before number)
        if value.lower() in ("true", "false", "0", "1"):
            return "boolean"

        # Number
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return "number"

        # Path
        if value.startswith("/") or value.startswith("~"):
            return "path"

        # Command substitution
        if value.startswith("$(") or value.startswith("`"):
            return "command_substitution"

        # Variable reference
        if value.startswith("$"):
            return "variable_reference"

        return "string"

    def _resolve_source_path(self, path: str) -> Optional[str]:
        """Try to resolve a sourced file path"""
        # This is a simple implementation - in practice would need more logic
        if path.startswith("/"):
            return path if Path(path).exists() else None

        # Relative path - would need context of script location
        return None
