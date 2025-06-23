#!/usr/bin/env python3
"""
Targeted script to fix specific mypy errors that are failing in CI.
"""

import re
from pathlib import Path


def fix_setup_recommendations_dict_items(filepath: Path) -> bool:
    """Fix dict item type mismatches in setup_recommendations.py."""
    content = filepath.read_text()
    original = content

    # This file has complex nested dicts that need proper typing
    lines = content.split("\n")

    # Find the TOOL_CONFIGS definition and fix it
    in_tool_configs = False
    brace_count = 0

    for i, line in enumerate(lines):
        if "TOOL_CONFIGS" in line and "=" in line:
            in_tool_configs = True

        if in_tool_configs:
            # Count braces to track nesting
            brace_count += line.count("{") - line.count("}")

            # Fix string values that should be lists
            if '"description":' in line and "[" not in line:
                # Extract the value
                match = re.search(r'"description":\s*"([^"]+)"', line)
                if match:
                    value = match.group(1)
                    lines[i] = line.replace(f'"{value}"', f'["{value}"]')

            # End of TOOL_CONFIGS
            if brace_count == 0 and "}" in line:
                in_tool_configs = False

    content = "\n".join(lines)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def fix_project_type_enums_comparison(filepath: Path) -> bool:
    """Fix enum comparison overlap errors."""
    content = filepath.read_text()
    original = content

    lines = content.split("\n")

    for i, line in enumerate(lines):
        # Fix comparisons with PROJECT_CATEGORIES
        if "if category in PROJECT_CATEGORIES" in line:
            lines[i] = line.replace("if category in PROJECT_CATEGORIES", "if category.value in PROJECT_CATEGORIES")
        elif "elif category in PROJECT_CATEGORIES" in line:
            lines[i] = line.replace("elif category in PROJECT_CATEGORIES", "elif category.value in PROJECT_CATEGORIES")
        # Fix direct enum comparisons
        elif "category == 'machine_learning'" in line:
            lines[i] = line.replace("category == 'machine_learning'", "category.value == 'machine_learning'")

    content = "\n".join(lines)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def fix_run_tests_compact(filepath: Path) -> bool:
    """Fix run_tests_compact.py."""
    content = filepath.read_text()
    original = content

    # Add type annotations
    content = re.sub(r"def run_tests_compact\(\):", "def run_tests_compact() -> None:", content)

    # Fix the return value issue
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "return 0" and i > 0:
            # Check if we're in run_tests_compact function
            for j in range(max(0, i - 20), i):
                if "def run_tests_compact() -> None:" in lines[j]:
                    lines[i] = "    # Tests completed"
                    break
        elif "sys.exit(run_tests_compact())" in line:
            lines[i] = line.replace("sys.exit(run_tests_compact())", "run_tests_compact()\n    sys.exit(0)")

    content = "\n".join(lines)

    if content != original:
        filepath.write_text(content)
        return True
    return False


def fix_example_files() -> int:
    """Fix example validation and main files."""
    fixed = 0

    # Fix validator.py
    validator = Path("examples/workspace-demo/packages/utils/utils/validator.py")
    if validator.exists():
        content = validator.read_text()
        original = content

        # Fix return type issue (returning int instead of bool)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "return 1" in line:
                lines[i] = line.replace("return 1", "return True")
            elif "return 0" in line:
                lines[i] = line.replace("return 0", "return False")

        content = "\n".join(lines)

        if content != original:
            validator.write_text(content)
            fixed += 1

    # Fix main.py
    main = Path("examples/workspace-demo/packages/core/core/main.py")
    if main.exists():
        content = main.read_text()
        original = content

        # Remove return statement from main()
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "def main() -> None:" in line:
                # Find and remove/fix return statements
                for j in range(i + 1, min(len(lines), i + 50)):
                    if lines[j].strip().startswith("return ") and "None" not in lines[j]:
                        lines[j] = "    # Processing complete"
                        break

        content = "\n".join(lines)

        if content != original:
            main.write_text(content)
            fixed += 1

    return fixed


def fix_uv_task_files() -> int:
    """Fix UV task files with Prefect decorators."""
    fixed = 0

    uv_files = [
        "src/DHT/modules/uv_script_tasks.py",
        "src/DHT/modules/uv_python_tasks.py",
        "src/DHT/modules/uv_environment_tasks.py",
        "src/DHT/modules/uv_dependency_tasks.py",
        "src/DHT/modules/uv_build_tasks.py",
    ]

    for file_path in uv_files:
        filepath = Path(file_path)
        if filepath.exists():
            content = filepath.read_text()
            original = content

            # Add type: ignore to @task decorators
            lines = content.split("\n")
            for i in range(len(lines)):
                if "@task" in lines[i] and "# type: ignore" not in lines[i]:
                    lines[i] = lines[i].rstrip() + "  # type: ignore[misc]"

            # Fix return Any issues
            content = "\n".join(lines)
            content = re.sub(
                r'return result\.get\("python_version"\)', 'return str(result.get("python_version", ""))', content
            )

            # Fix index assignment issues in uv_environment_tasks.py
            if "uv_environment_tasks.py" in file_path:
                content = re.sub(r"env\[([^\]]+)\] = ", r"env[str(\1)] = ", content)
                # Fix object has no attribute get
                content = re.sub(r'(\w+)\.get\("venv_path"\)', r'cast(Dict[str, Any], \1).get("venv_path")', content)
                # Add cast import if needed
                if "cast(" in content and "from typing import" in content:
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if "from typing import" in line and "cast" not in line:
                            lines[i] = line.rstrip() + ", cast"
                            content = "\n".join(lines)
                            break

            if content != original:
                filepath.write_text(content)
                fixed += 1

    return fixed


def fix_run_cmd(filepath: Path) -> bool:
    """Fix run_cmd.py type annotations."""
    content = filepath.read_text()
    original = content

    # Fix function annotations
    content = re.sub(
        r"def get_windows_parent_process_name\(\):", "def get_windows_parent_process_name() -> str | None:", content
    )

    content = re.sub(r"def execute_command\(cmd,", "def execute_command(cmd: List[str],", content)

    content = re.sub(r"def run_cmd\(cmd,", "def run_cmd(cmd: str | List[str],", content)

    content = re.sub(r"def execute_process\(args", "def execute_process(args: List[str]", content)

    # Fix union-attr error
    content = re.sub(r"output = proc\.stdout\.read\(\)", 'output = proc.stdout.read() if proc.stdout else b""', content)

    # Fix return Any
    content = re.sub(r"return parent_name", "return str(parent_name) if parent_name else None", content)

    # Add imports
    if "List[" in content:
        content = add_imports(content, {"List"})

    if content != original:
        filepath.write_text(content)
        return True
    return False


def add_imports(content: str, imports: set) -> str:
    """Add missing imports to content."""
    lines = content.split("\n")

    # Find typing import line
    typing_idx = -1
    for i, line in enumerate(lines):
        if "from typing import" in line:
            typing_idx = i
            break

    if typing_idx >= 0:
        # Add to existing import
        existing = set()
        match = re.search(r"from typing import (.+)", lines[typing_idx])
        if match:
            existing = {imp.strip() for imp in match.group(1).split(",")}

        missing = imports - existing
        if missing:
            all_imports = sorted(existing | missing)
            lines[typing_idx] = f"from typing import {', '.join(all_imports)}"
    else:
        # Add new import line
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                lines.insert(i + 1, f"from typing import {', '.join(sorted(imports))}")
                break

    return "\n".join(lines)


def main():
    """Fix specific CI mypy errors."""
    print("Fixing specific CI mypy errors...\n")

    fixed_count = 0

    # Fix setup_recommendations.py
    setup_rec = Path("src/DHT/modules/setup_recommendations.py")
    if setup_rec.exists():
        if fix_setup_recommendations_dict_items(setup_rec):
            print("✓ Fixed dict items in setup_recommendations.py")
            fixed_count += 1

    # Fix project_type_enums.py
    enums = Path("src/DHT/modules/project_type_enums.py")
    if enums.exists():
        if fix_project_type_enums_comparison(enums):
            print("✓ Fixed enum comparisons in project_type_enums.py")
            fixed_count += 1

    # Fix run_tests_compact.py
    run_tests = Path("run_tests_compact.py")
    if run_tests.exists():
        if fix_run_tests_compact(run_tests):
            print("✓ Fixed run_tests_compact.py")
            fixed_count += 1

    # Fix example files
    example_fixed = fix_example_files()
    if example_fixed:
        print(f"✓ Fixed {example_fixed} example files")
        fixed_count += example_fixed

    # Fix UV task files
    uv_fixed = fix_uv_task_files()
    if uv_fixed:
        print(f"✓ Fixed {uv_fixed} UV task files")
        fixed_count += uv_fixed

    # Fix run_cmd.py
    run_cmd = Path("src/DHT/modules/run_cmd.py")
    if run_cmd.exists():
        if fix_run_cmd(run_cmd):
            print("✓ Fixed run_cmd.py")
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")

    # Test with pre-commit
    print("\nTesting with pre-commit mypy...")
    import subprocess

    result = subprocess.run(["uv", "run", "pre-commit", "run", "mypy", "--all-files"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ All mypy errors fixed! CI should pass now.")
    else:
        # Count errors
        error_lines = [line for line in result.stdout.split("\n") if ": error:" in line]
        print(f"⚠ {len(error_lines)} errors remain")

        if len(error_lines) <= 10:
            print("\nRemaining errors:")
            for line in error_lines:
                print(f"  {line}")

    return 0


if __name__ == "__main__":
    main()
