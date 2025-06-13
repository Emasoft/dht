#!/bin/bash
# dhtl_utils.sh - Utils module for DHT Launcher
# Contains utility functions like linting.

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of dhtl and cannot be executed directly." >&2
    echo "Please use the main dhtl.sh script instead." >&2
    exit 1
fi

# Check if we're being sourced by the main script
if [[ -z "$DHTL_SESSION_ID" ]]; then
    echo "ERROR: This script is being sourced outside of dhtl. This is not supported." >&2
    return 1 2>/dev/null || exit 1
fi


# ===== Functions =====

# Check if a file exists anywhere within a directory tree up to a certain depth.
# Usage: file_exists_in_tree <directory> <filename> [max_depth]
# Example: file_exists_in_tree "$PROJECT_ROOT" "pyproject.toml" 2
file_exists_in_tree() {
    local dir="$1"
    local filename="$2"
    local max_depth="${3:-4}"  # Default max depth of 4

    if [[ ! -d "$dir" ]]; then
        echo "⚠️ file_exists_in_tree: Directory '$dir' not found." >&2
        return 1
    fi
    if [[ -z "$filename" ]]; then
        echo "⚠️ file_exists_in_tree: Filename not provided." >&2
        return 1
    fi

    # Use find to locate the file efficiently
    # -print -quit makes find stop after the first match
    if find "$dir" -maxdepth "$max_depth" -name "$filename" -type f -print -quit 2>/dev/null | grep -q .; then
        return 0 # File found
    else
        return 1 # File not found
    fi
}

# NOTE: show_help removed (canonical version is in user_interface.sh)

# Run linters on the project (Python, Shell). Prioritizes pre-commit if configured.
# This is the canonical version.
lint_command() {
    echo "🔍 Running linters on project..."
    PROJECT_ROOT=$(find_project_root) # Use canonical function

    # Determine venv bin path
    VENV_DIR=$(find_virtual_env "$PROJECT_ROOT") # Use canonical function
    if [ -z "$VENV_DIR" ]; then VENV_DIR="$DEFAULT_VENV_DIR"; fi
    local venv_bin_path="$VENV_DIR/bin"
    local venv_scripts_path="$VENV_DIR/Scripts" # For Windows checks

    # --- Tool Availability Check ---
    local USE_PRECOMMIT=false
    local USE_RUFF=false
    local USE_BLACK=false # Keep for format check if ruff doesn't do it
    local USE_MYPY=false
    local USE_SHELLCHECK=false
    local PRECOMMIT_CMD=""
    local RUFF_CMD=""
    local BLACK_CMD=""
    local MYPY_CMD=""
    local SHELLCHECK_CMD=""

    # Check pre-commit first (preferred method)
    if [ -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
        if [ -x "$venv_bin_path/pre-commit" ]; then
            PRECOMMIT_CMD="$venv_bin_path/pre-commit"
            USE_PRECOMMIT=true
        elif [ -x "$venv_scripts_path/pre-commit.exe" ]; then
            PRECOMMIT_CMD="$venv_scripts_path/pre-commit.exe"
            USE_PRECOMMIT=true
        elif command -v pre-commit &>/dev/null; then
            PRECOMMIT_CMD="pre-commit"
            USE_PRECOMMIT=true
            echo "⚠️ Using global pre-commit."
        else
            echo "⚠️ .pre-commit-config.yaml found, but pre-commit command not found. Install it ('dhtl setup' or 'uv pip install pre-commit')."
        fi
    fi

    # Check individual linters if pre-commit isn't used/available
    if [ "$USE_PRECOMMIT" = false ]; then
        if [ -x "$venv_bin_path/ruff" ]; then RUFF_CMD="$venv_bin_path/ruff"; USE_RUFF=true;
        elif [ -x "$venv_scripts_path/ruff.exe" ]; then RUFF_CMD="$venv_scripts_path/ruff.exe"; USE_RUFF=true;
        elif command -v ruff &>/dev/null; then RUFF_CMD="ruff"; USE_RUFF=true; echo "⚠️ Using global ruff."; fi

        if [ -x "$venv_bin_path/black" ]; then BLACK_CMD="$venv_bin_path/black"; USE_BLACK=true;
        elif [ -x "$venv_scripts_path/black.exe" ]; then BLACK_CMD="$venv_scripts_path/black.exe"; USE_BLACK=true;
        elif command -v black &>/dev/null; then BLACK_CMD="black"; USE_BLACK=true; echo "⚠️ Using global black."; fi

        if [ -x "$venv_bin_path/mypy" ]; then MYPY_CMD="$venv_bin_path/mypy"; USE_MYPY=true;
        elif [ -x "$venv_scripts_path/mypy.exe" ]; then MYPY_CMD="$venv_scripts_path/mypy.exe"; USE_MYPY=true;
        elif command -v mypy &>/dev/null; then MYPY_CMD="mypy"; USE_MYPY=true; echo "⚠️ Using global mypy."; fi

        # Check for native shellcheck first
        if command -v shellcheck &>/dev/null; then
            SHELLCHECK_CMD="shellcheck"; USE_SHELLCHECK=true;
        # Fallback to shellcheck-py in venv
        elif [ -x "$venv_bin_path/shellcheck" ]; then
             SHELLCHECK_CMD="$venv_bin_path/shellcheck"; USE_SHELLCHECK=true; echo "ℹ️ Using shellcheck-py wrapper from venv."
        elif [ -x "$venv_scripts_path/shellcheck.exe" ]; then
             SHELLCHECK_CMD="$venv_scripts_path/shellcheck.exe"; USE_SHELLCHECK=true; echo "ℹ️ Using shellcheck-py wrapper from venv."
        else
             echo "⚠️ shellcheck command not found globally or in venv. Skipping shell script linting."
        fi
    fi

    # --- Execution ---
    local LINT_FAILED=0

    if [ "$USE_PRECOMMIT" = true ]; then
        echo "🔄 Running pre-commit hooks (preferred method)..."
        # Run pre-commit with guardian
        run_with_guardian "$PRECOMMIT_CMD" "precommit" "$PYTHON_MEM_LIMIT" run --all-files
        LINT_EXIT_CODE=$?
        if [ $LINT_EXIT_CODE -ne 0 ]; then
            LINT_FAILED=1
            echo "❌ Pre-commit checks failed with exit code $LINT_EXIT_CODE." >&2
            echo "   Please fix the issues reported above." >&2
        else
            echo "✅ Pre-commit checks passed successfully."
        fi
    else
        # Run individual linters if pre-commit wasn't used
        echo "ℹ️ No pre-commit config found or pre-commit command unavailable. Running individual linters..."

        local ran_any_linter=false
        # Ruff (Linter + Formatter Check)
        if [ "$USE_RUFF" = true ]; then
            ran_any_linter=true
            echo "🔄 Running ruff check..."
            run_with_guardian "$RUFF_CMD" "ruff" "$PYTHON_MEM_LIMIT" check "$PROJECT_ROOT"
            if [ $? -ne 0 ]; then LINT_FAILED=1; echo "❌ Ruff check found issues." >&2; fi
            echo "🔄 Running ruff format check..."
            run_with_guardian "$RUFF_CMD" "ruff" "$PYTHON_MEM_LIMIT" format --check "$PROJECT_ROOT"
             if [ $? -ne 0 ]; then LINT_FAILED=1; echo "❌ Ruff format check found issues. Run 'dhtl format'." >&2; fi
        fi

        # Black (Formatter Check - only if Ruff didn't run format check)
        if [ "$USE_BLACK" = true ] && { [ "$USE_RUFF" = false ] || ! "$RUFF_CMD" --version | grep -q "format"; }; then
             ran_any_linter=true
             echo "🔄 Running black format check..."
             run_with_guardian "$BLACK_CMD" "black" "$PYTHON_MEM_LIMIT" --check "$PROJECT_ROOT"
             if [ $? -ne 0 ]; then LINT_FAILED=1; echo "❌ Black format check found issues. Run 'dhtl format'." >&2; fi
        fi

        # MyPy (Type Checking)
        if [ "$USE_MYPY" = true ]; then
             ran_any_linter=true
             echo "🔄 Running mypy type check..."
             # Point mypy to the src directory or specific packages if configured
             local mypy_target="$PROJECT_ROOT/src"
             if [ ! -d "$mypy_target" ]; then mypy_target="$PROJECT_ROOT"; fi # Fallback to root
             run_with_guardian "$MYPY_CMD" "mypy" "$PYTHON_MEM_LIMIT" "$mypy_target"
             if [ $? -ne 0 ]; then LINT_FAILED=1; echo "❌ MyPy found type issues." >&2; fi
        fi

        # ShellCheck
        if [ "$USE_SHELLCHECK" = true ]; then
            ran_any_linter=true
            echo "🔄 Running shellcheck..."
            local sh_files
            # Find shell scripts, excluding venv and .git
            sh_files=$(find "$PROJECT_ROOT" -path "$PROJECT_ROOT/.git" -prune -o -path "$PROJECT_ROOT/.venv" -prune -o -path "$PROJECT_ROOT/.venv_windows" -prune -o -name "*.sh" -type f -print)
            if [ -n "$sh_files" ]; then
                 # Use xargs to handle multiple files safely
                 # Use run_with_guardian for each file? Or run shellcheck once?
                 # Running once is more efficient. Use guardian for the overall check.
                 echo "$sh_files" | xargs run_with_guardian "$SHELLCHECK_CMD" "shellcheck" "$DEFAULT_MEM_LIMIT" --severity=error --external-sources
                 if [ $? -ne 0 ]; then LINT_FAILED=1; echo "❌ ShellCheck found issues." >&2; fi
            else
                 echo "ℹ️ No shell scripts found to check."
            fi
        fi

        if [ "$ran_any_linter" = false ]; then
             echo "⚠️ No recognized linters (pre-commit, ruff, black, mypy, shellcheck) found or configured."
             echo "   Consider running 'dhtl setup' or installing linters manually."
        fi
    fi

    # Final result
    if [ $LINT_FAILED -eq 0 ]; then
        echo "✅ All linting checks passed successfully."
        return 0
    else
        echo "❌ Linting failed. Please review the errors above." >&2
        return 1
    fi
}
