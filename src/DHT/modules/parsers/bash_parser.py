#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bash_parser.py - Bash script parser using tree-sitter

This module provides comprehensive Bash script parsing using tree-sitter.
It extracts functions, variables, sourced files, and commands from shell scripts.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to extract functionality into separate modules
# - Reduced file size by delegating to specialized parsers
#

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_parser import BaseParser
from .bash_parser_tree_sitter import TreeSitterBashParser, TREE_SITTER_BASH_AVAILABLE
from .bash_parser_regex import RegexBashParser
from .bash_parser_utils import BashParserUtils


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
        """Initialize the Bash parser."""
        self.logger = logging.getLogger(__name__)
        self.utils = BashParserUtils()
        
        # Initialize parsers
        self.tree_sitter_parser = TreeSitterBashParser()
        self.regex_parser = RegexBashParser()
        
        # Log parser availability
        if self.tree_sitter_parser.is_available():
            self.logger.info("Using tree-sitter parser for Bash scripts")
        else:
            self.logger.info("Using regex-based parser for Bash scripts")
    
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
                self.logger.error(f"Failed to read file {file_path}: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Bash script and extract all information.
        
        Args:
            file_path: Path to the Bash script
            
        Returns:
            Dictionary containing parsed information
        """
        self.logger.debug(f"Parsing Bash script: {file_path}")
        
        # Read file content
        content = self.read_file_safe(file_path)
        if content is None:
            return self._empty_result(file_path)
        
        # Try tree-sitter parsing first
        if self.tree_sitter_parser.is_available():
            tree = self.tree_sitter_parser.parse_tree(content)
            if tree:
                return self._parse_with_tree_sitter(tree, content, file_path)
        
        # Fall back to regex parsing
        return self._parse_with_regex(content, file_path)
    
    def _parse_with_tree_sitter(
        self, tree: Any, content: str, file_path: Path
    ) -> Dict[str, Any]:
        """Parse using tree-sitter."""
        return {
            "file_metadata": self.get_file_metadata(file_path),
            "functions": self.tree_sitter_parser.extract_functions(tree, content),
            "variables": self.tree_sitter_parser.extract_variables(tree, content),
            "exports": self.tree_sitter_parser.extract_exports(tree, content),
            "sourced_files": self.tree_sitter_parser.extract_sources(tree, content),
            "commands": self.tree_sitter_parser.extract_commands(tree, content),
            "shebang": self.utils.extract_shebang(content),
            "comments": self.tree_sitter_parser.extract_comments(tree, content),
            "control_structures": self.tree_sitter_parser.extract_control_structures(tree),
            "dependencies": self.utils.extract_dependencies_from_content(content),
            "parser_type": "tree-sitter",
        }
    
    def _parse_with_regex(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Fallback regex-based parsing when tree-sitter is not available."""
        return {
            "file_metadata": self.get_file_metadata(file_path),
            "functions": self.regex_parser.extract_functions(content),
            "variables": self.regex_parser.extract_variables(content),
            "exports": self.regex_parser.extract_exports(content),
            "sourced_files": self.regex_parser.extract_sources(content),
            "commands": self.regex_parser.extract_commands(content),
            "shebang": self.utils.extract_shebang(content),
            "comments": self.regex_parser.extract_comments(content),
            "control_structures": self.regex_parser.extract_control_structures(content),
            "dependencies": self.utils.extract_dependencies_from_content(content),
            "parser_type": "regex",
        }
    
    def _empty_result(self, file_path: Path) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            "file_metadata": self.get_file_metadata(file_path),
            "functions": [],
            "variables": [],
            "exports": [],
            "sourced_files": [],
            "commands": [],
            "shebang": None,
            "comments": [],
            "control_structures": {
                "if_statements": 0,
                "for_loops": 0,
                "while_loops": 0,
                "case_statements": 0,
                "functions": 0,
            },
            "dependencies": {"commands": [], "packages": [], "files": []},
            "parser_type": "none",
            "error": "Failed to read file",
        }
    
    def extract_imports(self, file_path: Path) -> List[str]:
        """
        Extract imports/sources from a Bash script.
        
        Args:
            file_path: Path to the Bash script
            
        Returns:
            List of sourced file paths
        """
        result = self.parse(file_path)
        return [source["path"] for source in result.get("sourced_files", [])]
    
    def extract_exports(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract exported variables from a Bash script.
        
        Args:
            file_path: Path to the Bash script
            
        Returns:
            Dictionary of exported variables
        """
        result = self.parse(file_path)
        exports = {}
        
        for export in result.get("exports", []):
            exports[export["name"]] = export.get("value")
        
        return exports
    
    def extract_functions(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract function definitions from a Bash script.
        
        Args:
            file_path: Path to the Bash script
            
        Returns:
            List of function definitions
        """
        result = self.parse(file_path)
        return result.get("functions", [])
    
    def extract_dependencies(self, file_path: Path) -> Dict[str, List[str]]:
        """
        Extract dependencies from a Bash script.
        
        Args:
            file_path: Path to the Bash script
            
        Returns:
            Dictionary of dependencies
        """
        result = self.parse(file_path)
        return result.get("dependencies", {"commands": [], "packages": [], "files": []})


# Export public API
__all__ = ["BashParser"]