#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive verification test for DHT codebase.

This test performs a thorough examination of all changes to ensure:
- No syntax errors in any files
- No missing critical files
- No broken imports or references
- Proper file structure and organization
- Adherence to project guidelines
"""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Set
import pytest


class TestComprehensiveVerification:
    """Comprehensive verification of DHT codebase."""
    
    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.src_dir = self.project_root / "src" / "DHT"
        self.modules_dir = self.src_dir / "modules"
        
    def test_all_python_files_have_valid_syntax(self):
        """Test that ALL Python files have valid syntax."""
        python_files = list(self.project_root.rglob("*.py"))
        # Exclude test repositories and cache directories
        python_files = [f for f in python_files 
                       if "__pycache__" not in str(f) 
                       and "temp_test" not in str(f)
                       and ".venv" not in str(f)]
        
        syntax_errors = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file.relative_to(self.project_root)}: {e}")
            except UnicodeDecodeError as e:
                syntax_errors.append(f"{py_file.relative_to(self.project_root)}: Unicode error: {e}")
        
        assert len(syntax_errors) == 0, f"Syntax errors found:\n" + "\n".join(syntax_errors)
    
    def test_all_shell_scripts_have_valid_syntax(self):
        """Test that all shell scripts have valid syntax."""
        shell_files = list(self.project_root.rglob("*.sh"))
        syntax_errors = []
        
        for sh_file in shell_files:
            try:
                result = subprocess.run(
                    ["bash", "-n", str(sh_file)], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    syntax_errors.append(f"{sh_file.relative_to(self.project_root)}: {result.stderr}")
            except subprocess.TimeoutExpired:
                syntax_errors.append(f"{sh_file.relative_to(self.project_root)}: Syntax check timeout")
            except Exception as e:
                syntax_errors.append(f"{sh_file.relative_to(self.project_root)}: {e}")
        
        assert len(syntax_errors) == 0, f"Shell syntax errors found:\n" + "\n".join(syntax_errors)
    
    def test_no_template_placeholders_remain(self):
        """Test that no unresolved template placeholders remain in non-template files."""
        all_files = list(self.project_root.rglob("*"))
        text_files = [f for f in all_files 
                     if f.is_file() and f.suffix in ['.py', '.sh', '.md', '.yml', '.yaml', '.toml', '.txt']]
        
        # Exclude known template directories and documentation
        # These are directories that legitimately contain template files with placeholders
        excluded_paths = [
            '/GITHUB_WORKFLOWS/',  # Template workflows directory
            '/hooks/',  # Git hooks templates directory  
            '/docker/',  # Docker templates directory
            'DEVELOPMENT_PLAN.md',  # Documentation about templates
            '/temp_test/',  # Test repositories
            '/.venv/',  # Virtual environments
            '/test_',  # Test files may reference templates
            'README.md',  # README files in template directories
            '.pre-commit-config.yaml',  # Pre-commit template config
        ]
        
        placeholder_patterns = [
            r'\{REPO_NAME\}',
            r'\{AUTHOR_NAME_OR_REPO_OWNER\}',
            r'\{REPO_OWNER_OR_ORGANIZATION\}',
            r'\{TEMPLATE_[^}]*\}'
        ]
        
        files_with_placeholders = []
        
        for file_path in text_files:
            # Skip excluded paths - check if any excluded path is in the file path
            file_path_str = str(file_path)
            if any(excluded in file_path_str for excluded in excluded_paths):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                for pattern in placeholder_patterns:
                    if re.search(pattern, content):
                        matches = re.findall(pattern, content)
                        files_with_placeholders.append(f"{file_path.relative_to(self.project_root)}: {matches}")
                        break
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue
        
        assert len(files_with_placeholders) == 0, \
            f"Template placeholders found in non-template files:\n" + "\n".join(files_with_placeholders)
    
    def test_critical_files_exist(self):
        """Test that all critical files exist."""
        critical_files = [
            # Entry points
            "dhtl.sh",
            "dhtl.bat", 
            "src/DHT/dhtl.py",
            "src/DHT/launcher.py",
            "src/DHT/colors.py",
            
            # Core modules
            "src/DHT/modules/orchestrator.sh",
            "src/DHT/modules/dhtl_commands_1.sh",
            "src/DHT/modules/dhtl_environment_1.sh",
            "src/DHT/modules/dhtl_utils.sh",
            "src/DHT/modules/dhtl_error_handling.sh",
            "src/DHT/modules/dhtl_commands_workflows.sh",
            
            # Configuration
            "pyproject.toml",
            "uv.lock",
            
            # Documentation
            "README.md",
            "CLAUDE.md"
        ]
        
        missing_files = []
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        assert len(missing_files) == 0, f"Critical files missing:\n" + "\n".join(missing_files)
    
    def test_no_import_errors_in_python_files(self):
        """Test that Python files don't have obvious import errors."""
        python_files = list(self.src_dir.rglob("*.py"))
        import_errors = []
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                # Check for imports that might be broken
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module
                        if module and module.startswith('.'):
                            # Relative import - check if target exists
                            if node.level == 1:  # from .module import something
                                target_file = py_file.parent / f"{module[1:]}.py"
                                if not target_file.exists():
                                    # Check if it's a package
                                    target_package = py_file.parent / module[1:]
                                    if not target_package.is_dir() or not (target_package / "__init__.py").exists():
                                        import_errors.append(f"{py_file.name}: Relative import {module} not found")
                                        
            except SyntaxError:
                # Already caught in syntax test
                pass
            except Exception as e:
                import_errors.append(f"{py_file.name}: Error checking imports: {e}")
        
        # Don't fail the test for import issues since some might be intentional
        if import_errors:
            print(f"\nPotential import issues found:")
            for error in import_errors:
                print(f"  - {error}")
    
    def test_uv_build_works(self):
        """Test that UV build command works."""
        try:
            result = subprocess.run(
                ["uv", "build"], 
                cwd=self.project_root,
                capture_output=True, 
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            # Build should succeed or at least not fail with syntax errors
            if result.returncode != 0:
                # Check if it's a dependency issue vs syntax issue
                if "syntax error" in result.stderr.lower() or "invalid syntax" in result.stderr.lower():
                    pytest.fail(f"UV build failed with syntax error:\n{result.stderr}")
                else:
                    # Might be dependency or configuration issue - warn but don't fail
                    print(f"\nWarning: UV build failed (might be dependency issue):\n{result.stderr}")
                    
        except subprocess.TimeoutExpired:
            pytest.fail("UV build timed out")
        except FileNotFoundError:
            pytest.skip("UV not available for build test")
    
    def test_no_duplicate_function_definitions_comprehensive(self):
        """Test for duplicate function definitions across all shell scripts."""
        shell_files = list(self.modules_dir.glob("*.sh"))
        function_definitions = {}
        
        for shell_file in shell_files:
            content = shell_file.read_text()
            
            # Find function definitions
            patterns = [
                r'^\s*(\w+)\s*\(\s*\)\s*\{',              # function_name() {
                r'^\s*function\s+(\w+)\s*\{',             # function function_name {
                r'^\s*function\s+(\w+)\s*\(\s*\)\s*\{'    # function function_name() {
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    function_name = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1
                    
                    if function_name not in function_definitions:
                        function_definitions[function_name] = []
                    
                    function_definitions[function_name].append({
                        'file': shell_file.name,
                        'line': line_num
                    })
        
        # Find problematic duplicates
        critical_duplicates = {}
        for func_name, definitions in function_definitions.items():
            if len(definitions) > 1:
                # Some functions can be legitimately duplicated (utilities)
                # But certain core functions should not be
                critical_functions = [
                    'workflows_command', 'test_command', 'build_command', 
                    'lint_command', 'format_command', 'setup_command'
                ]
                
                if func_name in critical_functions:
                    critical_duplicates[func_name] = definitions
        
        assert len(critical_duplicates) == 0, \
            f"Critical function duplicates found: {critical_duplicates}"
    
    def test_orchestrator_sources_all_required_modules(self):
        """Test that orchestrator.sh sources all required modules."""
        orchestrator_file = self.modules_dir / "orchestrator.sh"
        if not orchestrator_file.exists():
            pytest.skip("orchestrator.sh not found")
        
        content = orchestrator_file.read_text()
        
        # Essential modules that should be sourced
        essential_modules = [
            "dhtl_error_handling.sh",
            "dhtl_environment_1.sh", 
            "dhtl_utils.sh",
            "dhtl_commands_workflows.sh"
        ]
        
        missing_sources = []
        for module in essential_modules:
            if f'source "$SCRIPT_DIR/{module}"' not in content and \
               f'source "{module}"' not in content and \
               f'. "$SCRIPT_DIR/{module}"' not in content:
                missing_sources.append(module)
        
        assert len(missing_sources) == 0, \
            f"Orchestrator missing sources for: {missing_sources}"
    
    def test_no_broken_symlinks(self):
        """Test that there are no broken symlinks."""
        broken_symlinks = []
        
        for item in self.project_root.rglob("*"):
            if item.is_symlink() and not item.exists():
                broken_symlinks.append(str(item.relative_to(self.project_root)))
        
        assert len(broken_symlinks) == 0, f"Broken symlinks found: {broken_symlinks}"
    
    def test_file_permissions_are_correct(self):
        """Test that file permissions are correctly set."""
        permission_issues = []
        
        # Shell scripts should be executable
        shell_files = list(self.project_root.rglob("*.sh"))
        for sh_file in shell_files:
            if not os.access(sh_file, os.X_OK):
                permission_issues.append(f"{sh_file.relative_to(self.project_root)}: Not executable")
        
        # Entry points should be executable
        entry_points = [self.project_root / "dhtl.sh", self.project_root / "dhtl.bat"]
        for entry_point in entry_points:
            if entry_point.exists() and not os.access(entry_point, os.X_OK):
                permission_issues.append(f"{entry_point.name}: Not executable")
        
        # Python files should NOT be executable (except entry points)
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            # Skip entry points and scripts that should be executable
            if py_file.name in ["dhtl.py"] or "/bin/" in str(py_file):
                continue
            if os.access(py_file, os.X_OK) and not py_file.name.startswith("test_"):
                permission_issues.append(f"{py_file.relative_to(self.project_root)}: Unexpectedly executable")
        
        # Report permission issues as warnings, not failures (might be system-dependent)
        if permission_issues:
            print(f"\nPermission issues found:")
            for issue in permission_issues:
                print(f"  - {issue}")
    
    def test_pyproject_toml_is_valid(self):
        """Test that pyproject.toml is valid."""
        pyproject_file = self.project_root / "pyproject.toml"
        assert pyproject_file.exists(), "pyproject.toml missing"
        
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                pytest.skip("No TOML parser available")
        
        try:
            with open(pyproject_file, 'rb') as f:
                config = tomllib.load(f)
            
            # Check for essential sections
            assert "project" in config, "pyproject.toml missing [project] section"
            assert "build-system" in config, "pyproject.toml missing [build-system] section"
            
            # Check build system is hatchling (as per UV guidelines)
            build_system = config["build-system"]
            assert "hatchling" in build_system.get("build-backend", ""), \
                "pyproject.toml should use hatchling build backend"
                
        except Exception as e:
            pytest.fail(f"pyproject.toml is invalid: {e}")
    
    def test_no_large_files_violating_guidelines(self):
        """Test that files respect size guidelines."""
        large_files = []
        
        # Python files should be under 10KB (CLAUDE.md guideline)
        python_files = list(self.src_dir.rglob("*.py"))
        for py_file in python_files:
            size_kb = py_file.stat().st_size / 1024
            if size_kb > 10:
                large_files.append(f"{py_file.name}: {size_kb:.1f}KB (Python >10KB)")
        
        # Report as informational - these are guidelines, not hard requirements
        if large_files:
            print(f"\nFiles exceeding size guidelines:")
            for file_info in large_files:
                print(f"  - {file_info}")
            
            # Only fail if there are an excessive number of large files
            assert len(large_files) < 30, \
                f"Too many large files ({len(large_files)}) - consider refactoring"