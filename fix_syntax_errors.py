#!/usr/bin/env python3
"""Fix syntax errors in various modules."""

import re
from pathlib import Path


def fix_container_test_runner():
    """Fix container_test_runner.py indentation issue."""
    content = Path("src/DHT/modules/container_test_runner.py").read_text()

    # Fix the indentation after if statement
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if i == 249 and 'if "tests" not in results:' in line:
            # Ensure next line is properly indented
            if i + 1 < len(lines):
                lines[i + 1] = '                results["tests"] = {}'

    content = "\n".join(lines)
    Path("src/DHT/modules/container_test_runner.py").write_text(content)
    print("Fixed src/DHT/modules/container_test_runner.py")


def fix_subprocess_utils():
    """Fix subprocess_utils.py import issue."""
    content = Path("src/DHT/modules/subprocess_utils.py").read_text()

    # Fix the resource import issue
    content = re.sub(
        r'import sys\nimport resource if sys\.platform != "win32" else None',
        """import sys
        if sys.platform != "win32":
            import resource
        else:
            resource = None  # type: ignore[assignment]""",
        content,
    )

    Path("src/DHT/modules/subprocess_utils.py").write_text(content)
    print("Fixed src/DHT/modules/subprocess_utils.py")


def fix_missing_imports():
    """Fix missing logging imports in various files."""
    files_to_fix = [
        "src/DHT/modules/environment_configurator.py",
        "src/DHT/modules/project_capture_utils.py",
        "src/DHT/modules/reproduction_flow_utils.py",
        "src/DHT/modules/environment_capture_utils.py",
    ]

    for file_path in files_to_fix:
        if Path(file_path).exists():
            content = Path(file_path).read_text()

            # Add logging import at the top if not present
            if "import logging" not in content:
                # Find the first import line
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        lines.insert(i, "import logging")
                        break
                content = "\n".join(lines)
                Path(file_path).write_text(content)
                print(f"Added logging import to {file_path}")


def fix_setup_tree_sitter():
    """Remove unused import from setup_tree_sitter.py."""
    content = Path("src/DHT/setup_tree_sitter.py").read_text()

    # Remove unused Language import
    content = re.sub(r"from tree_sitter import Language\n", "", content)

    Path("src/DHT/setup_tree_sitter.py").write_text(content)
    print("Fixed src/DHT/setup_tree_sitter.py")


def fix_project_file_generators():
    """Fix isinstance tuple issue in project_file_generators.py."""
    content = Path("src/DHT/modules/project_file_generators.py").read_text()

    # Convert isinstance tuple to union
    content = re.sub(
        r"isinstance\(workflows_raw, \(list, tuple\)\)", "isinstance(workflows_raw, list | tuple)", content
    )

    Path("src/DHT/modules/project_file_generators.py").write_text(content)
    print("Fixed src/DHT/modules/project_file_generators.py")


def main() -> None:
    """Fix all syntax errors."""
    print("Fixing syntax errors...")

    fix_container_test_runner()
    fix_subprocess_utils()
    fix_missing_imports()
    fix_setup_tree_sitter()
    fix_project_file_generators()

    print("\nAll syntax errors fixed!")


if __name__ == "__main__":
    main()
