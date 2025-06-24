#!/usr/bin/env python3
"""
base_parser.py - Base class for all DHT file parsers  This module provides the abstract base class for all language and file parsers. It includes Prefect integration for task-based parallel processing.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
base_parser.py - Base class for all DHT file parsers

This module provides the abstract base class for all language and file parsers.
It includes Prefect integration for task-based parallel processing.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None

try:
    import tree_sitter

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from prefect import get_run_logger, task


class BaseParser(ABC):
    """
    Base class for all file parsers in DHT.

    This class provides:
    - Common interface for all parsers
    - Prefect task integration
    - Tree-sitter support for language parsers
    - Error handling and logging
    """

    def __init__(self, language: str | None = None) -> None:
        """
        Initialize the parser.

        Args:
            language: Tree-sitter language name if applicable
        """
        self.language = language
        self.parser: Any | None = None
        self.language_obj: Any | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

        if language and TREE_SITTER_AVAILABLE:
            try:
                self._init_tree_sitter(language)
            except Exception as e:
                self.logger.warning(f"Failed to initialize tree-sitter for {language}: {e}")

    def _init_tree_sitter(self, language: str) -> None:
        """Initialize tree-sitter parser for the given language"""
        # Look for compiled language library
        lib_paths = [
            Path(__file__).parent.parent.parent / "build" / "languages.so",
            Path.cwd() / "build" / "languages.so",
            Path.home() / ".dht" / "build" / "languages.so",
        ]

        for lib_path in lib_paths:
            if lib_path.exists():
                try:
                    language_obj = tree_sitter.Language(str(lib_path), language)
                    self.parser = tree_sitter.Parser()
                    self.parser.set_language(language_obj)
                    self.language_obj = language_obj
                    self.logger.info(f"Initialized tree-sitter for {language} from {lib_path}")
                    return
                except Exception as e:
                    self.logger.debug(f"Failed to load {language} from {lib_path}: {e}")

        raise RuntimeError(f"Could not find tree-sitter language library for {language}")

    @abstractmethod
    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """
        Parse a file and extract structured information.

        Args:
            file_path: Path to the file to parse

        Returns:
            Dictionary containing parsed information
        """
        pass

    @abstractmethod
    def extract_dependencies(self, file_path: Path) -> Any:
        """
        Extract dependencies from a file.

        Args:
            file_path: Path to the file to parse

        Returns:
            Dependencies (format depends on parser implementation)
        """
        pass

    def extract_imports(self, file_path: Path) -> list[str]:
        """
        Extract import statements from a file.
        Default implementation returns empty list.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of import statements
        """
        return []

    def extract_functions(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Extract function definitions from a file.
        Default implementation returns empty list.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of function definitions with metadata
        """
        return []

    def extract_classes(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Extract class definitions from a file.
        Default implementation returns empty list.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of class definitions with metadata
        """
        return []

    @task(
        name="parse-file",
        description="Parse a file with appropriate parser",
        retries=2,
        retry_delay_seconds=5,
    )  # type: ignore[misc]
    def parse_with_prefect(self, file_path: str | Path) -> dict[str, Any]:
        """
        Prefect task wrapper for parsing files.

        Args:
            file_path: Path to the file to parse

        Returns:
            Dictionary containing parsed information
        """
        logger = get_run_logger()
        file_path = Path(file_path)

        logger.info(f"Parsing {file_path} with {self.__class__.__name__}")

        try:
            result = self.parse_file(file_path)
            logger.info(f"Successfully parsed {file_path}")
            return result
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {
                "error": str(e),
                "file_path": str(file_path),
                "parser": self.__class__.__name__,
            }

    def read_file_safe(self, file_path: Path, encoding: str = "utf-8") -> str | None:
        """
        Safely read file contents with error handling.

        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)

        Returns:
            File contents or None if error
        """
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None

    def parse_tree_sitter(self, content: str | bytes) -> Any | None:
        """
        Parse content using tree-sitter if available.

        Args:
            content: File content to parse

        Returns:
            Tree-sitter tree or None
        """
        if not self.parser:
            return None

        # Convert to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        try:
            return self.parser.parse(content_bytes)
        except Exception as e:
            self.logger.error(f"Tree-sitter parsing failed: {e}")
            return None

    def query_tree(self, tree: Any, query_string: str) -> list[Any]:
        """
        Query a tree-sitter tree.

        Args:
            tree: Tree-sitter tree
            query_string: Query string in tree-sitter query language

        Returns:
            List of captures
        """
        if not tree or not self.language_obj:
            return []

        try:
            query = self.language_obj.query(query_string)
            captures = query.captures(tree.root_node)
            return list(captures)  # Ensure we return a list
        except Exception as e:
            self.logger.error(f"Tree query failed: {e}")
            return []

    @staticmethod
    def load_json(file_path: Path) -> dict[str, Any]:
        """Load and parse JSON file"""
        try:
            with open(file_path) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            raise ValueError(f"Failed to parse JSON from {file_path}: {e}") from e

    @staticmethod
    def load_yaml(file_path: Path) -> dict[str, Any]:
        """Load and parse YAML file"""
        try:
            with open(file_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to parse YAML from {file_path}: {e}") from e

    @staticmethod
    def load_toml(file_path: Path) -> dict[str, Any]:
        """Load and parse TOML file"""
        try:
            import toml  # type: ignore
        except ImportError as e:
            raise ImportError("toml package required for TOML parsing. Install with: pip install toml") from e

        try:
            with open(file_path) as f:
                data: dict[str, Any] = toml.load(f)
                return data
        except Exception as e:
            raise ValueError(f"Failed to parse TOML from {file_path}: {e}") from e

    def get_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """
        Get basic file metadata.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata
        """
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
