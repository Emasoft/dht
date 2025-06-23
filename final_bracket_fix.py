#!/usr/bin/env python3
"""
Final comprehensive bracket fixer.
"""

import re
from pathlib import Path


def comprehensive_bracket_fix(file_path: Path) -> int:
    """Fix all bracket issues comprehensively."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        fixes = 0
        new_lines = []

        for _i, line in enumerate(lines):
            original_line = line

            # Fix dict[str, Any]] -> dict[str, Any]
            line = re.sub(r"(dict\[[^\]]+\])\](\s*[,\):\|])", r"\1\2", line)

            # Fix list[str]] -> list[str]
            line = re.sub(r"(list\[[^\]]+\])\](\s*[,\):\|])", r"\1\2", line)

            # Fix set[Any]] -> set[Any]
            line = re.sub(r"(set\[[^\]]+\])\](\s*[,\):\|])", r"\1\2", line)

            # Fix tuple[...]] -> tuple[...]
            line = re.sub(r"(tuple\[[^\]]+\])\](\s*[,\):\|])", r"\1\2", line)

            # Fix Any]]] -> Any]
            line = re.sub(r"(Any)\]\]\]", r"\1]", line)
            line = re.sub(r"(Any)\]\]", r"\1]", line)

            # Fix function definitions with unbalanced brackets
            if "def " in line and line.strip().endswith(":"):
                # Count brackets
                open_brackets = line.count("[")
                close_brackets = line.count("]")
                open_parens = line.count("(")
                close_parens = line.count(")")

                # Fix missing closing brackets
                if open_brackets > close_brackets:
                    missing = open_brackets - close_brackets
                    line = line.rstrip(":\n") + "]" * missing + ":\n"

                # Fix extra closing brackets
                elif close_brackets > open_brackets:
                    # Remove extra brackets
                    extra = close_brackets - open_brackets
                    for _ in range(extra):
                        line = re.sub(r"\](\s*[,\):])", r"\1", line, count=1)

            if line != original_line:
                fixes += 1

            new_lines.append(line)

        if fixes > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

        return fixes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main() -> None:
    src_path = Path("src/DHT")
    python_files = list(src_path.rglob("*.py"))

    print(f"Processing {len(python_files)} Python files...")

    total_fixed = 0
    for file_path in python_files:
        fixes = comprehensive_bracket_fix(file_path)
        if fixes:
            print(f"Fixed {fixes} issues in: {file_path}")
            total_fixed += fixes

    print(f"\nTotal fixes: {total_fixed}")


if __name__ == "__main__":
    main()
