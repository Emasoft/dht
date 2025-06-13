#!/bin/bash
# dhtl_commands_7.sh - Commands_7 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_7 functionality.
# It is sourced by the main dhtl.sh orchestrator and should not be modified manually.
# To make changes, modify the original dhtl.sh and regenerate the modules.
#
# DO NOT execute this file directly.


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

build_command() {
    echo "📦 Building Python package..."
    PROJECT_ROOT=$(find_project_root)
    
    # Process flags
    SKIP_CHECKS=false
    for arg in "$@"; do
        case "$arg" in
            --no-checks)
                SKIP_CHECKS=true
                ;;
        esac
    done
    
    # Run linters first unless skipped
    if [ "$SKIP_CHECKS" = false ]; then
        echo "🔍 Running linters before build..."
        # Call the canonical lint_command from utils.sh
        if function_exists "lint_command"; then
            lint_command
            if [ $? -ne 0 ]; then
                echo "❌ Linting failed. Fix the issues before building."
                echo "   Run with --no-checks to skip linting."
                return 1
            fi
        else
            log_warning "lint_command not found. Skipping lint checks."
        fi
    else
        echo "⚠️ Skipping linting checks as requested."
    fi
    
    # Check for venv
    VENV_DIR=$(find_virtual_env "$PROJECT_ROOT")
    if [ -z "$VENV_DIR" ]; then
        VENV_DIR="$PROJECT_ROOT/.venv"
    fi
    
    # Clean old builds
    echo "🧹 Cleaning old build artifacts..."
    rm -rf "$PROJECT_ROOT/dist"
    rm -rf "$PROJECT_ROOT/build"
    find "$PROJECT_ROOT" -maxdepth 3 -type d -name "*.egg-info" -exec rm -rf {} +
    
    # Ensure we're using the project's venv
    if function_exists "ensure_venv_activated"; then
        ensure_venv_activated "$PROJECT_ROOT"
    fi
    
    # Determine build command
    BUILD_CMD=""
    
    # Check for UV in venv or globally
    UV_CMD=$(command -v uv || echo "$VENV_DIR/bin/uv")
    if [ -x "$UV_CMD" ] || command -v uv &> /dev/null; then
        echo "🔄 Building with uv..."
        # Use run_in_venv to ensure correct environment
        if function_exists "run_in_venv"; then
            run_in_venv "$PROJECT_ROOT" uv build
        else
            BUILD_CMD="uv build"
        fi
    elif [ -f "$VENV_DIR/bin/pip" ]; then
        echo "🔄 Building with setuptools..."
        BUILD_CMD="$VENV_DIR/bin/pip wheel --no-deps -w dist/ ."
    elif command -v uv &> /dev/null; then
        echo "🔄 Building with global uv..."
        BUILD_CMD="uv build"
    else
        echo "❌ No build tools found. Install uv or pip."
        return 1
    fi
    
    # Run the build
    echo "🔄 Building package..."
    ensure_process_guardian
    run_with_guardian $BUILD_CMD "build" "$PYTHON_MEM_LIMIT"
    
    BUILD_RESULT=$?
    if [ $BUILD_RESULT -ne 0 ]; then
        echo "❌ Build failed with exit code $BUILD_RESULT."
        return $BUILD_RESULT
    else
        echo "✅ Build completed successfully."
        echo "📦 Package created in: $PROJECT_ROOT/dist/"
        # List the built files
        find "$PROJECT_ROOT/dist" -type f
        return 0
    fi
}

# NOTE: check_command_args removed. Canonical version is in dhtl_utils.sh
# NOTE: restore_command removed. Canonical version is in dhtl_commands_1.sh (restore_dependencies)

run_python_dev_command() {
    local script_path=$1
    shift

    ensure_process_guardian
    # Use python-dev-wrapper.sh for Python dev scripts if available
    if [ -f "$DHT_DIR/python-dev-wrapper.sh" ] && [ "$USE_GUARDIAN" = true ]; then
        echo "🐍 Running Python dev script with wrapper"
        "$DHT_DIR/python-dev-wrapper.sh" "$script_path" "$@"
    else
        # Fallback to running with generic guardian
        if [[ "$script_path" == *.py ]]; then
            run_with_guardian "$PYTHON_CMD" "python" "$PYTHON_MEM_LIMIT" "$script_path" "$@"
        else
            # For non-Python scripts in DHT
            run_with_guardian "$script_path" "script" "$DEFAULT_MEM_LIMIT" "$@"
        fi
    fi
}

# NOTE: test_command_duplicate removed. Canonical version is in dhtl_commands_2.sh
