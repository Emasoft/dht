#!/usr/bin/env python3
"""Fix import statements in test files."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix import statements in a single test file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix various import patterns
    replacements = [
        # Direct DHT imports
        (r'^from DHT\.modules import (.+)$', r'from modules import \1', re.MULTILINE),
        (r'^from DHT\.modules\.(.+) import (.+)$', r'from modules.\1 import \2', re.MULTILINE),
        (r'^from DHT import (.+)$', r'import \1', re.MULTILINE),
        (r'^import DHT\.(.+)$', r'import \1', re.MULTILINE),
        
        # Fix specific common patterns
        (r'from DHT\.diagnostic_reporter_v2 import', r'from diagnostic_reporter_v2 import'),
        (r'from DHT\.modules\.parsers\.(.+) import', r'from modules.parsers.\1 import'),
        (r'from DHT\.modules\.dht_flows\.(.+) import', r'from modules.dht_flows.\1 import'),
        (r'from DHT\.modules\.dht_flows import', r'from modules.dht_flows import'),
        
        # Fix more complex imports
        (r'from DHT\.modules\.(.+)$', r'from modules.\1', re.MULTILINE),
        (r'DHT\.modules\.', r'modules.'),
        (r'DHT\.diagnostic_reporter_v2', r'diagnostic_reporter_v2'),
        
        # Fix patch decorators
        (r"@patch\('DHT\.modules\.(.+?)'\)", r"@patch('modules.\1')"),
        (r"@patch\('DHT\.(.+?)'\)", r"@patch('\1')"),
        (r'@patch\("DHT\.modules\.(.+?)"\)', r'@patch("modules.\1")'),
        (r'@patch\("DHT\.(.+?)"\)', r'@patch("\1")'),
    ]
    
    for pattern, replacement, *flags in replacements:
        if flags:
            content = re.sub(pattern, replacement, content, *flags)
        else:
            content = re.sub(pattern, replacement, content)
    
    # Only write if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix imports in all test files."""
    test_dir = Path("DHT/tests/unit")
    fixed_files = []
    
    for test_file in test_dir.glob("*.py"):
        if test_file.name == "__init__.py":
            continue
            
        print(f"Checking {test_file.name}...")
        if fix_imports_in_file(test_file):
            fixed_files.append(test_file.name)
            print(f"  ✓ Fixed imports in {test_file.name}")
    
    print(f"\nFixed {len(fixed_files)} files:")
    for f in fixed_files:
        print(f"  - {f}")

if __name__ == "__main__":
    main()