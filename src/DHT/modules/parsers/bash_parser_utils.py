#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bash_parser_utils.py - Utility functions for Bash parser

This module contains utility functions used by both tree-sitter and regex parsers.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from bash_parser.py to reduce file size
# - Contains utility functions for type inference, path resolution, etc.
#

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from .bash_parser_models import (
    ARRAY_PATTERN, PATH_PATTERN, NUMBER_PATTERN, BOOLEAN_PATTERN,
    REGEX_PATTERNS, COMMON_COMMANDS
)


class BashParserUtils:
    """Utility functions for Bash parsing."""
    
    def infer_var_type(self, value: str) -> str:
        """Infer the type of a bash variable from its value."""
        value = value.strip()
        
        # Check for arrays
        if re.match(ARRAY_PATTERN, value):
            return "array"
        
        # Check for numbers
        if re.match(NUMBER_PATTERN, value):
            return "number"
        
        # Check for booleans
        if re.match(BOOLEAN_PATTERN, value, re.IGNORECASE):
            return "boolean"
        
        # Check for paths
        if re.match(PATH_PATTERN, value):
            return "path"
        
        # Check if it's empty
        if not value or value in ('""', "''"):
            return "empty"
        
        # Default to string
        return "string"
    
    def extract_local_vars_from_body(self, body: str) -> List[str]:
        """Extract local variable declarations from function body."""
        local_vars = []
        
        for line in body.splitlines():
            match = re.match(REGEX_PATTERNS["local_var"], line)
            if match:
                local_vars.append(match.group(1))
        
        return local_vars
    
    def resolve_source_path(self, path: str) -> Optional[str]:
        """Try to resolve a sourced file path."""
        # Remove quotes if present
        path = path.strip("\"'")
        
        # Handle special cases
        if path.startswith("$"):
            # Variable expansion - can't resolve statically
            return None
        
        # Try different path resolutions
        path_candidates = []
        
        # Absolute path
        if path.startswith("/"):
            path_candidates.append(Path(path))
        else:
            # Relative paths
            path_candidates.extend([
                Path(path),
                Path.cwd() / path,
                Path.home() / path,
            ])
            
            # Common bash config locations
            if not path.startswith("."):
                path_candidates.extend([
                    Path("/etc") / path,
                    Path("/usr/share") / path,
                    Path("/usr/local/share") / path,
                ])
        
        # Check which paths exist
        for candidate in path_candidates:
            if candidate.exists():
                return str(candidate.resolve())
        
        return None
    
    def extract_shebang(self, content: str) -> Optional[str]:
        """Extract shebang from script content."""
        lines = content.splitlines()
        if lines and lines[0].startswith("#!"):
            match = re.match(REGEX_PATTERNS["shebang"], lines[0])
            if match:
                return match.group(1)
        return None
    
    def extract_dependencies_from_content(self, content: str) -> Dict[str, List[str]]:
        """Extract potential dependencies from script content."""
        dependencies = {
            "commands": [],
            "packages": [],
            "files": [],
        }
        
        # Look for command usage
        for cmd in COMMON_COMMANDS:
            if re.search(rf'\b{cmd}\b', content):
                dependencies["commands"].append(cmd)
        
        # Look for package installation commands
        apt_pattern = r'apt(?:-get)?\s+install\s+([^\s;|&]+)'
        yum_pattern = r'yum\s+install\s+([^\s;|&]+)'
        brew_pattern = r'brew\s+install\s+([^\s;|&]+)'
        pip_pattern = r'pip\d?\s+install\s+([^\s;|&]+)'
        
        for pattern in [apt_pattern, yum_pattern, brew_pattern, pip_pattern]:
            for match in re.finditer(pattern, content):
                package = match.group(1).strip()
                if package and package not in dependencies["packages"]:
                    dependencies["packages"].append(package)
        
        return dependencies
    
    def extract_comments_from_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract comments from lines of code."""
        comments = []
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for comments
            if line.strip().startswith("#"):
                comment_text = line.strip()[1:].strip()
                comments.append({
                    "text": comment_text,
                    "line": line_num,
                    "is_shebang": line.strip().startswith("#!"),
                })
            else:
                # Check for inline comments
                if "#" in line and not self._is_in_string(line, line.index("#")):
                    comment_start = line.index("#")
                    comment_text = line[comment_start + 1:].strip()
                    comments.append({
                        "text": comment_text,
                        "line": line_num,
                        "is_shebang": False,
                        "is_inline": True,
                    })
        
        return comments
    
    def _is_in_string(self, line: str, position: int) -> bool:
        """Check if a position in a line is inside a string."""
        # Simple check - count quotes before position
        before = line[:position]
        single_quotes = before.count("'") - before.count("\\'")
        double_quotes = before.count('"') - before.count('\\"')
        
        # If odd number of quotes, we're inside a string
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)


# Export public API
__all__ = ["BashParserUtils"]