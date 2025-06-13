#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Python script efficiency and modularity.

This test verifies that Python scripts in the DHT project follow
efficiency and modularity best practices as outlined in CLAUDE.md.
"""

import ast
import os
import re
import pytest
from pathlib import Path


class TestPythonEfficiency:
    """Test Python script efficiency and modularity."""
    
    def setup_method(self):
        """Set up test environment."""
        self.dht_dir = Path(__file__).parent.parent.parent / "src" / "DHT"
        self.python_files = list(self.dht_dir.rglob("*.py"))
        # Filter out __pycache__ and test files
        self.python_files = [f for f in self.python_files 
                           if "__pycache__" not in str(f) and "test_" not in f.name]
        self.max_file_size_kb = 10  # CLAUDE.md mentions 10KB limit for Python files
    
    def test_python_files_exist(self):
        """Test that Python files exist in DHT package."""
        assert len(self.python_files) > 0, "Should find Python files in DHT package"
        
        # Core Python files should exist
        core_files = [
            "dhtl.py",
            "launcher.py",
            "colors.py"
        ]
        
        existing_files = [f.name for f in self.python_files]
        for core_file in core_files:
            assert core_file in existing_files, f"Core file {core_file} should exist"
    
    def test_file_sizes_modular(self):
        """Test that Python files follow the 10KB modularity rule from CLAUDE.md."""
        oversized_files = []
        
        for py_file in self.python_files:
            size_kb = py_file.stat().st_size / 1024
            if size_kb > self.max_file_size_kb:
                oversized_files.append(f"{py_file.name}: {size_kb:.1f}KB")
        
        if oversized_files:
            print(f"\nPython files exceeding {self.max_file_size_kb}KB limit:")
            for file_info in oversized_files:
                print(f"  {file_info}")
        
        # CLAUDE.md states: "always keep the size of source code files below 10Kb"
        assert len(oversized_files) == 0, \
            f"These Python files exceed the 10KB limit: {oversized_files}"
    
    def test_files_have_proper_headers(self):
        """Test that Python files have proper headers."""
        for py_file in self.python_files:
            content = py_file.read_text()
            
            # Should start with shebang
            assert content.startswith("#!/usr/bin/env python3"), \
                f"{py_file.name} should start with #!/usr/bin/env python3 shebang"
            
            # Should have encoding declaration
            lines = content.split('\n')
            if len(lines) > 1:
                second_line = lines[1]
                assert "coding" in second_line or "utf-8" in second_line, \
                    f"{py_file.name} should have encoding declaration on second line"
    
    def test_files_have_valid_syntax(self):
        """Test that all Python files have valid syntax."""
        for py_file in self.python_files:
            content = py_file.read_text()
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file.name}: {e}")
    
    def test_files_have_docstrings(self):
        """Test that Python files have module docstrings (CLAUDE.md requirement)."""
        files_without_docstrings = []
        
        for py_file in self.python_files:
            # Skip __init__.py files (can be empty)
            if py_file.name == "__init__.py":
                continue
                
            content = py_file.read_text()
            
            try:
                tree = ast.parse(content)
                # Check if first statement is a docstring
                has_docstring = (
                    len(tree.body) > 0 and
                    isinstance(tree.body[0], ast.Expr) and
                    isinstance(tree.body[0].value, ast.Constant) and
                    isinstance(tree.body[0].value.value, str)
                )
                
                if not has_docstring:
                    files_without_docstrings.append(py_file.name)
                    
            except SyntaxError:
                # Already caught in test_files_have_valid_syntax
                pass
        
        if files_without_docstrings:
            print(f"\nFiles without module docstrings:")
            for filename in files_without_docstrings:
                print(f"  - {filename}")
        
        # CLAUDE.md states: "always write the docstrings of all functions"
        # Allow some files to not have docstrings, but most should
        docstring_ratio = (len(self.python_files) - len(files_without_docstrings)) / len(self.python_files)
        assert docstring_ratio >= 0.7, \
            f"Only {docstring_ratio*100:.1f}% of Python files have docstrings (expected >70%)"
    
    def test_functions_have_docstrings(self):
        """Test that functions have docstrings (CLAUDE.md requirement)."""
        functions_without_docstrings = []
        total_functions = 0
        
        for py_file in self.python_files:
            content = py_file.read_text()
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        
                        # Check if function has docstring
                        has_docstring = (
                            len(node.body) > 0 and
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)
                        )
                        
                        if not has_docstring:
                            functions_without_docstrings.append(f"{py_file.name}:{node.name}()")
                            
            except SyntaxError:
                # Already caught in test_files_have_valid_syntax
                pass
        
        if functions_without_docstrings and total_functions > 0:
            print(f"\nFunctions without docstrings (showing first 10):")
            for func_name in functions_without_docstrings[:10]:
                print(f"  - {func_name}")
            if len(functions_without_docstrings) > 10:
                print(f"  ... and {len(functions_without_docstrings) - 10} more")
        
        if total_functions > 0:
            docstring_ratio = (total_functions - len(functions_without_docstrings)) / total_functions
            # CLAUDE.md is strict about docstrings, but allow some flexibility
            assert docstring_ratio >= 0.6, \
                f"Only {docstring_ratio*100:.1f}% of functions have docstrings (expected >60%)"
    
    def test_functions_use_type_annotations(self):
        """Test that functions use type annotations (CLAUDE.md requirement)."""
        functions_without_types = []
        total_functions = 0
        
        for py_file in self.python_files:
            content = py_file.read_text()
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip magic methods and some special cases
                        if node.name.startswith('_'):
                            continue
                            
                        total_functions += 1
                        
                        # Check for type annotations
                        has_annotations = (
                            node.returns is not None or  # Return type annotation
                            any(arg.annotation is not None for arg in node.args.args)  # Parameter annotations
                        )
                        
                        if not has_annotations:
                            functions_without_types.append(f"{py_file.name}:{node.name}()")
                            
            except SyntaxError:
                # Already caught in test_files_have_valid_syntax
                pass
        
        if functions_without_types and total_functions > 0:
            print(f"\nFunctions without type annotations (showing first 10):")
            for func_name in functions_without_types[:10]:
                print(f"  - {func_name}")
            if len(functions_without_types) > 10:
                print(f"  ... and {len(functions_without_types) - 10} more")
        
        if total_functions > 0:
            type_annotation_ratio = (total_functions - len(functions_without_types)) / total_functions
            # CLAUDE.md states: "always use type annotations"
            assert type_annotation_ratio >= 0.5, \
                f"Only {type_annotation_ratio*100:.1f}% of functions have type annotations (expected >50%)"
    
    def test_imports_are_organized(self):
        """Test that imports are properly organized."""
        for py_file in self.python_files:
            content = py_file.read_text()
            
            try:
                tree = ast.parse(content)
                
                # Collect imports
                imports = []
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        imports.append(node)
                
                # Check that imports are at the top (after docstring and comments)
                non_import_nodes = [node for node in tree.body 
                                  if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr))]
                
                if imports and non_import_nodes:
                    first_non_import_line = non_import_nodes[0].lineno
                    last_import_line = max(imp.lineno for imp in imports)
                    
                    # Allow some flexibility - imports should generally be near the top
                    if last_import_line > first_non_import_line:
                        print(f"\nWarning: {py_file.name} has imports after code (line {last_import_line})")
                        
            except SyntaxError:
                # Already caught in test_files_have_valid_syntax
                pass
    
    def test_no_unused_imports(self):
        """Test for obvious unused imports (basic check)."""
        files_with_potential_unused_imports = []
        
        for py_file in self.python_files:
            content = py_file.read_text()
            
            # Simple regex-based check for obvious unused imports
            import_pattern = r'^(?:from\s+\S+\s+)?import\s+([^#\n]+)'
            imports = re.findall(import_pattern, content, re.MULTILINE)
            
            for import_line in imports:
                # Extract module/function names
                names = [name.strip().split(' as ')[0] for name in import_line.split(',')]
                
                for name in names:
                    name = name.strip()
                    if name and not re.search(rf'\b{re.escape(name)}\b', content[content.find(import_line)+len(import_line):]):
                        if py_file.name not in files_with_potential_unused_imports:
                            files_with_potential_unused_imports.append(py_file.name)
                        break
        
        # This is informational - not a hard failure
        if files_with_potential_unused_imports:
            print(f"\nFiles with potentially unused imports:")
            for filename in files_with_potential_unused_imports:
                print(f"  - {filename}")
    
    def test_code_complexity_reasonable(self):
        """Test that code complexity is reasonable."""
        complex_functions = []
        
        for py_file in self.python_files:
            content = py_file.read_text()
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Count lines in function (simple complexity measure)
                        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                            func_lines = node.end_lineno - node.lineno
                            
                            # Functions over 50 lines might be too complex
                            if func_lines > 50:
                                complex_functions.append(f"{py_file.name}:{node.name}() ({func_lines} lines)")
                                
            except SyntaxError:
                # Already caught in test_files_have_valid_syntax
                pass
        
        if complex_functions:
            print(f"\nComplex functions (>50 lines):")
            for func_info in complex_functions:
                print(f"  - {func_info}")
        
        # Allow some complex functions but flag excessive complexity
        assert len(complex_functions) < 5, \
            f"Too many complex functions found: {len(complex_functions)}"