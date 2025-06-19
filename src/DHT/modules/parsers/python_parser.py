#!/usr/bin/env python3
"""
python_parser.py - Python file parser using AST

This module provides comprehensive Python file parsing using the built-in AST module.
It extracts imports, functions, classes, and dependencies from Python source files.
"""

import ast
import logging
from pathlib import Path
from typing import Any

from .base_parser import BaseParser


class PythonParser(BaseParser):
    """
    Parser for Python source files using AST.

    Extracts:
    - Import statements and dependencies
    - Function definitions with signatures
    - Class definitions with methods
    - Module-level variables
    - Docstrings and comments
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """
        Parse a Python file and extract comprehensive information.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary containing parsed information
        """
        content = self.read_file_safe(file_path)
        if content is None:
            return {"error": f"Could not read file {file_path}"}

        try:
            tree = ast.parse(content, filename=str(file_path))

            return {
                "file_metadata": self.get_file_metadata(file_path),
                "imports": self._extract_imports(tree),
                "dependencies": self._extract_dependencies(tree),
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "module_variables": self._extract_module_variables(tree),
                "docstring": ast.get_docstring(tree),
                "has_main": self._has_main_block(tree),
                "decorators_used": self._extract_decorators(tree),
                "async_functions": self._extract_async_functions(tree),
                "type_hints": self._extract_type_hints(tree),
            }
        except SyntaxError as e:
            return {
                "error": f"Syntax error in {file_path}: {e}",
                "line": e.lineno,
                "offset": e.offset,
            }
        except Exception as e:
            return {"error": f"Failed to parse {file_path}: {e}"}

    def extract_dependencies(self, file_path: Path) -> list[str]:
        """Extract unique dependencies from imports"""
        content = self.read_file_safe(file_path)
        if content is None:
            return []

        try:
            tree = ast.parse(content)
            return list(self._extract_dependencies(tree))
        except Exception:
            return []

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract all import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno if hasattr(node, "lineno") else None,
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from",
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "level": node.level,  # Relative import level
                            "line": node.lineno if hasattr(node, "lineno") else None,
                        }
                    )

        return imports

    def _extract_dependencies(self, tree: ast.AST) -> list[str]:
        """Extract unique package dependencies from imports"""
        dependencies = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get base package name
                    base_package = alias.name.split(".")[0]
                    dependencies.add(base_package)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get base package name
                    base_package = node.module.split(".")[0]
                    dependencies.add(base_package)

        # Filter out standard library modules (basic heuristic)
        stdlib_modules = {
            "os",
            "sys",
            "time",
            "datetime",
            "json",
            "math",
            "re",
            "random",
            "collections",
            "itertools",
            "functools",
            "typing",
            "pathlib",
            "subprocess",
            "threading",
            "multiprocessing",
            "asyncio",
            "logging",
            "unittest",
            "pytest",
            "argparse",
            "configparser",
            "csv",
            "sqlite3",
            "http",
            "urllib",
            "socket",
            "email",
            "html",
            "xml",
            "ast",
        }

        return sorted(list(dependencies - stdlib_modules))

    def _extract_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract function definitions"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                func_info = {
                    "name": node.name,
                    "line": node.lineno if hasattr(node, "lineno") else None,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node),
                    "args": self._extract_arguments(node.args),
                    "decorators": [
                        self._get_decorator_name(d) for d in node.decorator_list
                    ],
                    "returns": self._extract_annotation(node.returns)
                    if node.returns
                    else None,
                    "is_method": self._is_method(node),
                    "complexity": self._calculate_complexity(node),
                }
                functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract class definitions"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno if hasattr(node, "lineno") else None,
                    "docstring": ast.get_docstring(node),
                    "bases": [self._get_name(base) for base in node.bases],
                    "decorators": [
                        self._get_decorator_name(d) for d in node.decorator_list
                    ],
                    "methods": self._extract_class_methods(node),
                    "attributes": self._extract_class_attributes(node),
                    "is_dataclass": self._is_dataclass(node),
                    "metaclass": self._get_metaclass(node),
                }
                classes.append(class_info)

        return classes

    def _extract_arguments(self, args: ast.arguments) -> dict[str, Any]:
        """Extract function arguments"""
        arg_info = {
            "args": [],
            "vararg": None,
            "kwarg": None,
            "defaults": [],
            "kwonlyargs": [],
            "kw_defaults": [],
        }

        # Regular arguments
        for arg in args.args:
            arg_info["args"].append(
                {
                    "name": arg.arg,
                    "annotation": self._extract_annotation(arg.annotation)
                    if arg.annotation
                    else None,
                }
            )

        # Default values
        if args.defaults:
            arg_info["defaults"] = [self._get_value(d) for d in args.defaults]

        # *args
        if args.vararg:
            arg_info["vararg"] = {
                "name": args.vararg.arg,
                "annotation": self._extract_annotation(args.vararg.annotation)
                if args.vararg.annotation
                else None,
            }

        # **kwargs
        if args.kwarg:
            arg_info["kwarg"] = {
                "name": args.kwarg.arg,
                "annotation": self._extract_annotation(args.kwarg.annotation)
                if args.kwarg.annotation
                else None,
            }

        # Keyword-only arguments
        for arg in args.kwonlyargs:
            arg_info["kwonlyargs"].append(
                {
                    "name": arg.arg,
                    "annotation": self._extract_annotation(arg.annotation)
                    if arg.annotation
                    else None,
                }
            )

        if args.kw_defaults:
            arg_info["kw_defaults"] = [
                self._get_value(d) if d else None for d in args.kw_defaults
            ]

        return arg_info

    def _extract_class_methods(self, class_node: ast.ClassDef) -> list[dict[str, Any]]:
        """Extract methods from a class"""
        methods = []

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                method_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node),
                    "decorators": [
                        self._get_decorator_name(d) for d in node.decorator_list
                    ],
                    "is_static": self._has_decorator(node, "staticmethod"),
                    "is_class": self._has_decorator(node, "classmethod"),
                    "is_property": self._has_decorator(node, "property"),
                    "is_private": node.name.startswith("_"),
                    "is_dunder": node.name.startswith("__")
                    and node.name.endswith("__"),
                }
                methods.append(method_info)

        return methods

    def _extract_class_attributes(
        self, class_node: ast.ClassDef
    ) -> list[dict[str, Any]]:
        """Extract class attributes"""
        attributes = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                attributes.append(
                    {
                        "name": node.target.id,
                        "annotation": self._extract_annotation(node.annotation),
                        "value": self._get_value(node.value) if node.value else None,
                        "line": node.lineno,
                    }
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(
                            {
                                "name": target.id,
                                "annotation": None,
                                "value": self._get_value(node.value),
                                "line": node.lineno,
                            }
                        )

        return attributes

    def _extract_module_variables(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract module-level variables"""
        variables = []

        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                variables.append(
                    {
                        "name": node.target.id,
                        "annotation": self._extract_annotation(node.annotation),
                        "value": self._get_value(node.value) if node.value else None,
                        "line": node.lineno,
                    }
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(
                            {
                                "name": target.id,
                                "annotation": None,
                                "value": self._get_value(node.value),
                                "line": node.lineno,
                                "is_constant": target.id.isupper(),
                            }
                        )

        return variables

    def _extract_decorators(self, tree: ast.AST) -> list[str]:
        """Extract all unique decorators used in the file"""
        decorators = set()

        for node in ast.walk(tree):
            if hasattr(node, "decorator_list"):
                for decorator in node.decorator_list:
                    decorators.add(self._get_decorator_name(decorator))

        return sorted(list(decorators))

    def _extract_async_functions(self, tree: ast.AST) -> list[str]:
        """Extract names of async functions"""
        async_funcs = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_funcs.append(node.name)

        return async_funcs

    def _extract_type_hints(self, tree: ast.AST) -> dict[str, int]:
        """Extract statistics about type hints usage"""
        stats = {
            "annotated_args": 0,
            "annotated_returns": 0,
            "annotated_variables": 0,
            "total_functions": 0,
            "total_variables": 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                stats["total_functions"] += 1
                if node.returns:
                    stats["annotated_returns"] += 1
                for arg in node.args.args:
                    if arg.annotation:
                        stats["annotated_args"] += 1
            elif isinstance(node, ast.AnnAssign):
                stats["annotated_variables"] += 1
                stats["total_variables"] += 1
            elif isinstance(node, ast.Assign):
                stats["total_variables"] += len(node.targets)

        return stats

    def _extract_annotation(self, annotation: ast.AST | None) -> str | None:
        """Extract type annotation as string"""
        if annotation is None:
            return None

        try:
            return ast.unparse(annotation)
        except AttributeError:
            # Fallback for Python < 3.9
            return self._get_name(annotation)

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name as string"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_name(decorator.func)
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        else:
            return str(decorator)

    def _get_name(self, node: ast.AST) -> str:
        """Get name from various AST nodes"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        else:
            try:
                return ast.unparse(node)
            except Exception:
                return str(node)

    def _get_value(self, node: ast.AST | None) -> Any:
        """Extract value from AST node"""
        if node is None:
            return None

        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._get_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._get_value(k): self._get_value(v)
                for k, v in zip(node.keys, node.values, strict=False)
            }
        elif isinstance(node, ast.Set):
            return {self._get_value(elt) for elt in node.elts}
        elif isinstance(node, ast.Tuple):
            return tuple(self._get_value(elt) for elt in node.elts)
        elif isinstance(node, ast.Name):
            return node.id
        else:
            try:
                return ast.unparse(node)
            except Exception:
                return str(node)

    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is a method (has self/cls as first arg)"""
        if not node.args.args:
            return False

        first_arg = node.args.args[0].arg
        return first_arg in ("self", "cls")

    def _has_decorator(self, node: ast.FunctionDef, decorator_name: str) -> bool:
        """Check if function has specific decorator"""
        for decorator in node.decorator_list:
            if self._get_decorator_name(decorator) == decorator_name:
                return True
        return False

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """Check if class is a dataclass"""
        return self._has_decorator(node, "dataclass") or self._has_decorator(
            node, "dataclasses.dataclass"
        )

    def _get_metaclass(self, node: ast.ClassDef) -> str | None:
        """Extract metaclass if specified"""
        for keyword in node.keywords:
            if keyword.arg == "metaclass":
                return self._get_name(keyword.value)
        return None

    def _has_main_block(self, tree: ast.AST) -> bool:
        """Check if file has if __name__ == '__main__' block"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    if (
                        isinstance(node.test.left, ast.Name)
                        and node.test.left.id == "__name__"
                    ):
                        if any(isinstance(op, ast.Eq) for op in node.test.ops):
                            if any(
                                isinstance(comp, ast.Constant)
                                and comp.value == "__main__"
                                for comp in node.test.comparators
                            ):
                                return True
        return False

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity of a function.
        This is a simplified version that counts decision points.
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each and/or adds a decision point
                complexity += len(child.values) - 1

        return complexity
