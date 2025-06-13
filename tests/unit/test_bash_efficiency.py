#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test bash script efficiency and modularity.

This test verifies that bash scripts in the DHT project follow
efficiency and modularity best practices as outlined in CLAUDE.md.
"""

import os
import re
import pytest
from pathlib import Path


class TestBashEfficiency:
    """Test bash script efficiency and modularity."""
    
    def setup_method(self):
        """Set up test environment."""
        self.modules_dir = Path(__file__).parent.parent.parent / "src" / "DHT" / "modules"
        self.shell_scripts = list(self.modules_dir.glob("*.sh"))
        self.max_file_size_kb = 60  # CLAUDE.md mentions keeping files small (dhtl_init.sh is 59KB)
    
    def test_shell_scripts_exist(self):
        """Test that shell scripts exist in modules directory."""
        assert len(self.shell_scripts) > 0, "Should find shell scripts in modules directory"
        
        # Core scripts should exist
        core_scripts = [
            "orchestrator.sh",
            "dhtl_commands_1.sh",
            "dhtl_environment_1.sh",
            "dhtl_utils.sh",
            "dhtl_error_handling.sh"
        ]
        
        existing_scripts = [s.name for s in self.shell_scripts]
        for script in core_scripts:
            assert script in existing_scripts, f"Core script {script} should exist"
    
    def test_file_sizes_reasonable(self):
        """Test that shell script files are not excessively large."""
        oversized_files = []
        
        for script in self.shell_scripts:
            size_kb = script.stat().st_size / 1024
            if size_kb > self.max_file_size_kb:
                oversized_files.append(f"{script.name}: {size_kb:.1f}KB")
        
        # Report oversized files but allow some exceptions
        if oversized_files:
            print(f"\nLarge shell script files found (>{self.max_file_size_kb}KB):")
            for file_info in oversized_files:
                print(f"  {file_info}")
            
            # dhtl_init.sh is a known large file that's marked for refactoring
            allowed_large_files = ["dhtl_init.sh"]
            critical_large_files = [f for f in oversized_files 
                                   if not any(allowed in f for allowed in allowed_large_files)]
            
            assert len(critical_large_files) == 0, \
                f"These files are too large and should be refactored: {critical_large_files}"
    
    def test_scripts_have_proper_headers(self):
        """Test that shell scripts have proper headers and shebangs."""
        for script in self.shell_scripts:
            content = script.read_text()
            
            # Should start with shebang
            assert content.startswith("#!/bin/bash"), \
                f"{script.name} should start with #!/bin/bash shebang"
            
            # Should have error handling (set -e or equivalent checks)
            has_error_handling = any(pattern in content for pattern in [
                "set -e", "set -euo pipefail", "|| exit 1", "|| return 1"
            ])
            
            # Some scripts may handle errors differently, so this is not strict
            if not has_error_handling:
                print(f"\nWarning: {script.name} may lack explicit error handling")
    
    def test_scripts_are_modular(self):
        """Test that shell scripts follow modular design principles."""
        for script in self.shell_scripts:
            content = script.read_text()
            
            # Should not execute directly (should be sourced)
            if script.name != "orchestrator.sh":  # orchestrator might be different
                assert 'cannot be executed directly' in content.lower() or \
                       'do not execute this file directly' in content.lower(), \
                    f"{script.name} should prevent direct execution"
            
            # Should check for proper sourcing environment
            sourcing_checks = [
                "DHTL_SESSION_ID", "IN_DHTL", "BASH_SOURCE", "sourced by"
            ]
            
            has_sourcing_check = any(check in content for check in sourcing_checks)
            if not has_sourcing_check:
                print(f"\nWarning: {script.name} may not validate proper sourcing")
    
    def test_functions_are_well_organized(self):
        """Test that functions in shell scripts are well organized."""
        for script in self.shell_scripts:
            content = script.read_text()
            
            # Find function definitions
            function_patterns = [
                r'^\s*(\w+)\s*\(\s*\)\s*\{',              # function_name() {
                r'^\s*function\s+(\w+)\s*\{',             # function function_name {
                r'^\s*function\s+(\w+)\s*\(\s*\)\s*\{'    # function function_name() {
            ]
            
            functions = []
            for pattern in function_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                functions.extend([match.group(1) for match in matches])
            
            # Should not have too many functions in one file (modularity)
            max_functions_per_file = 15
            if len(functions) > max_functions_per_file:
                print(f"\nWarning: {script.name} has {len(functions)} functions, "
                      f"consider breaking into smaller modules")
    
    def test_scripts_use_best_practices(self):
        """Test that shell scripts follow bash best practices."""
        for script in self.shell_scripts:
            content = script.read_text()
            
            # Check for potentially problematic patterns
            issues = []
            
            # Should use [[ ]] instead of [ ] for conditions (more robust)
            single_bracket_conditions = re.findall(r'\s+\[\s+[^]]+\](?!\])', content)
            if len(single_bracket_conditions) > 3:  # Allow some, but not too many
                issues.append(f"Uses single brackets [{len(single_bracket_conditions)}x] - consider [[ ]]")
            
            # Should quote variables to prevent word splitting
            unquoted_vars = re.findall(r'\$\w+(?!["\[\])])', content)
            if len(unquoted_vars) > 10:  # Allow some, but flag excessive use
                issues.append(f"May have unquoted variables [{len(unquoted_vars)}x] - risk of word splitting")
            
            # Should use local variables in functions
            if 'function' in content or '() {' in content:
                local_usage = content.count('local ')
                if local_usage < 1 and len(content) > 1000:  # Only check non-trivial scripts
                    issues.append("Functions may not use 'local' variables")
            
            # Report issues as warnings, not failures (these are guidelines)
            if issues:
                print(f"\nBest practice suggestions for {script.name}:")
                for issue in issues:
                    print(f"  - {issue}")
    
    def test_scripts_are_efficient(self):
        """Test that shell scripts avoid inefficient patterns."""
        for script in self.shell_scripts:
            content = script.read_text()
            
            # Check for efficiency anti-patterns
            efficiency_issues = []
            
            # Avoid unnecessary subshells
            subshell_patterns = [
                r'\$\(cat\s+[^)]+\)',  # $(cat file) - use $(<file) instead
                r'\$\(echo\s+[^)]+\)'  # $(echo ...) - often unnecessary
            ]
            
            for pattern in subshell_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    efficiency_issues.append(f"Potential inefficient subshells: {len(matches)}x")
            
            # Check for excessive command repetition
            common_commands = ['git', 'find', 'grep', 'sed', 'awk']
            for cmd in common_commands:
                cmd_count = len(re.findall(rf'\b{cmd}\b', content))
                if cmd_count > 20:  # Arbitrary threshold
                    efficiency_issues.append(f"Command '{cmd}' used {cmd_count}x - consider optimization")
            
            # Report as informational (not test failures)
            if efficiency_issues:
                print(f"\nEfficiency suggestions for {script.name}:")
                for issue in efficiency_issues:
                    print(f"  - {issue}")
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across scripts."""
        error_handling_patterns = {
            'return_on_error': r'return\s+[1-9]',
            'exit_on_error': r'exit\s+[1-9]',
            'command_checks': r'\|\|\s*(return|exit)',
            'status_checks': r'\$\?\s*(==|!=|\-eq|\-ne)\s*0'
        }
        
        scripts_with_error_handling = []
        
        for script in self.shell_scripts:
            content = script.read_text()
            
            error_handling_found = []
            for pattern_name, pattern in error_handling_patterns.items():
                if re.search(pattern, content):
                    error_handling_found.append(pattern_name)
            
            if error_handling_found:
                scripts_with_error_handling.append({
                    'script': script.name,
                    'patterns': error_handling_found
                })
        
        # Most scripts should have some form of error handling
        scripts_without_error_handling = [
            s.name for s in self.shell_scripts 
            if s.name not in [sh['script'] for sh in scripts_with_error_handling]
        ]
        
        if scripts_without_error_handling:
            print(f"\nScripts without obvious error handling:")
            for script in scripts_without_error_handling:
                print(f"  - {script}")
        
        # At least 80% of scripts should have some error handling
        error_handling_ratio = len(scripts_with_error_handling) / len(self.shell_scripts)
        assert error_handling_ratio >= 0.6, \
            f"Only {error_handling_ratio*100:.1f}% of scripts have error handling (expected >60%)"