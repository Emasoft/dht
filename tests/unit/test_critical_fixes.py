#!/usr/bin/env python3
"""
Test for critical fixes identified in comprehensive verification. This uses TDD to identify and fix critical issues.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Test for critical fixes identified in comprehensive verification.
This uses TDD to identify and fix critical issues.
"""

import re
from pathlib import Path

import pytest


class TestCriticalFixes:
    """Test critical fixes for issues found in verification."""

    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.src_dir = self.project_root / "src" / "DHT"
        self.modules_dir = self.src_dir / "modules"

    def test_no_duplicate_lint_command(self):
        """Test that lint_command is not duplicated."""
        utils_file = self.modules_dir / "utils.sh"
        dhtl_utils_file = self.modules_dir / "dhtl_utils.sh"

        duplicates = []

        for file_path in [utils_file, dhtl_utils_file]:
            if file_path.exists():
                content = file_path.read_text()
                if re.search(r"^\s*lint_command\s*\(\s*\)\s*\{", content, re.MULTILINE):
                    duplicates.append(file_path.name)

        assert len(duplicates) <= 1, (
            f"lint_command defined in multiple files: {duplicates}. Should only be in one file."
        )

    def test_github_workflows_are_templates(self):
        """Test that GitHub workflow template files have proper placeholders."""
        workflow_dir = self.src_dir / "GITHUB_WORKFLOWS"

        if not workflow_dir.exists():
            pytest.skip("GitHub workflows directory not found")

        template_files = []

        for workflow_file in workflow_dir.glob("*.yml"):
            content = workflow_file.read_text()
            # These should be TEMPLATES with placeholders
            if "{REPO_NAME}" in content:
                template_files.append(workflow_file.name)

        # Most workflow files should be templates with placeholders
        assert len(template_files) > 0, (
            "GitHub workflow template files should contain {REPO_NAME} placeholders for user project generation"
        )

    def test_precommit_config_is_template(self):
        """Test that pre-commit config is a proper template."""
        precommit_file = self.src_dir / "hooks" / ".pre-commit-config.yaml"

        if not precommit_file.exists():
            pytest.skip("Pre-commit config not found")

        content = precommit_file.read_text()
        # This should be a TEMPLATE with placeholders for user projects
        assert "{REPO_NAME}" in content, "Pre-commit config should contain {REPO_NAME} placeholder as it's a template"

    def test_our_test_files_dont_use_real_placeholders(self):
        """Test that our test files use escaped or example placeholders."""
        test_files = [
            self.project_root / "tests" / "unit" / "test_template_files.py",
            self.project_root / "tests" / "unit" / "test_comprehensive_verification.py",
        ]

        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                # These should be in strings as examples, not actual placeholders
                raw_placeholders = re.findall(r'(?<!")(\{REPO_NAME\})(?!")', content)
                assert len(raw_placeholders) == 0, f"{test_file.name} has unescaped placeholders: {raw_placeholders}"
