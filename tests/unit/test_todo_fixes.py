#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test that all TODO fixes have been properly implemented.

This test verifies that:
- include_secrets functionality works in diagnostic reporters
- system_taxonomy handles nested categories and language package managers
- dhtl_regenerate_poc.sh has version check implemented
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestTodoFixes:
    """Test all TODO fixes are properly implemented."""
    
    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.src_dir = self.project_root / "src" / "DHT"
        
    def test_include_secrets_implemented_in_diagnostic_reporter(self):
        """Test that include_secrets functionality is implemented."""
        # Import the module
        sys.path.insert(0, str(self.src_dir))
        try:
            from diagnostic_reporter import build_bible
            
            # Mock os.environ to test the functionality
            test_env = {
                'PATH': '/usr/bin:/bin',
                'HOME': '/home/test',
                'USER': 'testuser',
                'AWS_ACCESS_KEY': 'secret_key',
                'GITHUB_TOKEN': 'secret_token',
                'API_KEY': 'secret_api',
                'DATABASE_PASSWORD': 'secret_pass',
                'NORMAL_VAR': 'normal_value'
            }
            
            with patch.dict('os.environ', test_env, clear=True):
                # Test with include_secrets=False
                bible_no_secrets = build_bible(include_secrets=False)
                assert 'environment' in bible_no_secrets
                assert 'variables' in bible_no_secrets['environment']
                
                env_vars = bible_no_secrets['environment']['variables']
                
                # Check that sensitive vars are redacted
                assert env_vars['AWS_ACCESS_KEY'] == '[REDACTED]'
                assert env_vars['GITHUB_TOKEN'] == '[REDACTED]'
                assert env_vars['API_KEY'] == '[REDACTED]'
                assert env_vars['DATABASE_PASSWORD'] == '[REDACTED]'
                
                # Check that normal vars are not redacted
                assert env_vars['PATH'] == '/usr/bin:/bin'
                assert env_vars['HOME'] == '/home/test'
                assert env_vars['USER'] == 'testuser'
                assert env_vars['NORMAL_VAR'] == 'normal_value'
                
                # Test with include_secrets=True
                bible_with_secrets = build_bible(include_secrets=True)
                env_vars_with_secrets = bible_with_secrets['environment']['variables']
                
                # Check that all vars are included without redaction
                assert env_vars_with_secrets['AWS_ACCESS_KEY'] == 'secret_key'
                assert env_vars_with_secrets['GITHUB_TOKEN'] == 'secret_token'
                assert env_vars_with_secrets['API_KEY'] == 'secret_api'
                assert env_vars_with_secrets['DATABASE_PASSWORD'] == 'secret_pass'
                
        finally:
            # Clean up sys.path
            sys.path.pop(0)
    
    def test_system_taxonomy_handles_language_package_managers(self):
        """Test that system_taxonomy includes language package managers."""
        # Import the module
        sys.path.insert(0, str(self.src_dir / "modules"))
        try:
            from system_taxonomy import get_relevant_categories
            
            # Test that language package managers are included
            categories = get_relevant_categories('darwin')  # Test on macOS
            
            # Check that package_managers category exists
            assert 'package_managers' in categories
            
            pm_category = categories['package_managers']
            assert 'categories' in pm_category
            
            # Check that language subcategory is included
            assert 'language' in pm_category['categories']
            
            language_pm = pm_category['categories']['language']
            
            # Language subcategory has a different structure
            # Package managers are stored as lists under language names
            assert 'python' in language_pm
            assert 'javascript' in language_pm
            
            # Check that language package managers are present
            expected_language_pms = ['pip', 'npm', 'cargo', 'gem', 'composer']
            
            # Collect all package managers from all languages
            all_pms = []
            for lang, pm_list in language_pm.items():
                if lang != 'description' and isinstance(pm_list, list):
                    all_pms.extend(pm_list)
            
            # At least some language package managers should be present
            assert any(pm in all_pms for pm in expected_language_pms)
            
        finally:
            sys.path.pop(0)
    
    def test_system_taxonomy_handles_nested_categories(self):
        """Test that get_tool_fields handles nested categories."""
        # Import the module
        sys.path.insert(0, str(self.src_dir / "modules"))
        try:
            from system_taxonomy import get_tool_fields
            
            # Test nested category tool lookup
            # pip is in package_managers -> language -> pip
            fields = get_tool_fields('package_managers', 'pip')
            
            # Should find pip fields even though it's in a nested subcategory
            assert len(fields) > 0
            assert 'version' in fields
            
            # Test with a system package manager (also nested)
            fields = get_tool_fields('package_managers', 'brew')
            if fields:  # brew might not be in the taxonomy
                assert 'version' in fields
            
        finally:
            sys.path.pop(0)
    
    def test_dhtl_regenerate_poc_version_check_implemented(self):
        """Test that version check is implemented in dhtl_regenerate_poc.sh."""
        script_path = self.src_dir / "modules" / "dhtl_regenerate_poc.sh"
        
        # Read the script content
        content = script_path.read_text()
        
        # Check that TODO is gone
        assert "# TODO: Implement version check" not in content
        
        # Check that version check code is present
        assert "CURRENT_DHT_VERSION=" in content
        assert "dhtl version" in content
        assert "DHT version mismatch" in content
        assert "✓ DHT version" in content
        
        # Verify the implementation has proper structure
        assert "if [[ -z \"$CURRENT_DHT_VERSION\" ]]; then" in content
        assert "elif [[ \"$CURRENT_DHT_VERSION\" != \"$DHT_VERSION\" ]]; then" in content
    
    def test_no_todos_remain(self):
        """Test that no TODO comments remain in the fixed files."""
        files_to_check = [
            self.src_dir / "diagnostic_reporter.py",
            self.src_dir / "diagnostic_reporter_old.py", 
            self.src_dir / "modules" / "system_taxonomy.py",
            self.src_dir / "modules" / "dhtl_regenerate_poc.sh"
        ]
        
        todos_found = []
        
        for file_path in files_to_check:
            content = file_path.read_text()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if 'TODO:' in line and 'for future upgrades' not in line:
                    # Skip the XXXX pattern which is not a TODO
                    if 'additional_info_XXXX' in line:
                        continue
                    todos_found.append(f"{file_path.name}:{i}: {line.strip()}")
        
        assert len(todos_found) == 0, f"TODOs still found:\n" + "\n".join(todos_found)