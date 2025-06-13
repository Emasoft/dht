#!/bin/bash
# dhtl_commands_2.sh - Commands_2 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_2 functionality.
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

test_command() {
    echo "🧪 Running tests on project..."
    PROJECT_ROOT=$(find_project_root)
    
    # Process flags
    FAST_MODE=false
    for arg in "$@"; do
        case "$arg" in
            --fast)
                FAST_MODE=true
                ;;
        esac
    done
    
    # Start the guardian process if needed
    ensure_process_guardian
    
    # Define timeout setting
    TIMEOUT=900  # 15 minutes
    
    # Set up proper paths
    VENV_DIR=$(find_virtual_env "$PROJECT_ROOT")
    if [ -z "$VENV_DIR" ]; then
        VENV_DIR="$PROJECT_ROOT/.venv"
    fi
    DHT_DIR="${DHT_DIR:-$PROJECT_ROOT/DHT}"
    
    # Set environment variables for testing
    export TEST_ENV="true"
    export PYTHONUTF8=1
    
    # Set optimizations to reduce memory usage
    export PYTHONOPTIMIZE=1         # Enable basic optimizations
    export PYTHONHASHSEED=0         # Fixed hash seed improves memory usage
    export PYTHONDONTWRITEBYTECODE=1 # Don't write .pyc files
    export PYTHONFAULTHANDLER=1     # Improved debugging with minimal overhead
    
    # First check for DHT/run_tests.sh (preferred method)
    DHT_TEST_SCRIPT="$DHT_DIR/run_tests.sh"
    if [ -f "$DHT_TEST_SCRIPT" ]; then
        echo "🔄 Using DHT test script..."
        
        # Create coverage directory if it doesn't exist
        mkdir -p "$PROJECT_ROOT/coverage_report"
        
        # Display system resource info
        echo "🔍 Detected system resources: $(nproc) CPU cores, $(free -m | awk '/^Mem:/{print $7}')MB available memory"
        CONCURRENT_PROCS=$(($(nproc) * 3 / 4))
        if [ "$CONCURRENT_PROCS" -lt 1 ]; then CONCURRENT_PROCS=1; fi
        TOTAL_MEM=$((PYTHON_MEM_LIMIT * CONCURRENT_PROCS))
        echo "⚙️ Configured limits: $CONCURRENT_PROCS concurrent processes, ${TOTAL_MEM}MB total memory"
        echo "🛡️ Running with Process Guardian (pytest, ${PYTHON_MEM_LIMIT}MB limit, $CONCURRENT_PROCS concurrent, ${TOTAL_MEM}MB total)"
        
        # Source the test script with proper environment setup
        # Set the SCRIPT_DIR variable required by run_tests.sh
        SCRIPT_DIR="$PROJECT_ROOT"
        
        if [ "$FAST_MODE" = true ]; then
            source "$DHT_TEST_SCRIPT" --fast
        else
            source "$DHT_TEST_SCRIPT"
        fi
        
        TEST_RESULT=$?
        
        # Report results
        if [ $TEST_RESULT -eq 0 ]; then
            echo "✅ Tests completed successfully!"
        else
            echo "❌ Tests failed with exit code $TEST_RESULT"
        fi
        
        return $TEST_RESULT
    fi
    
    # Fall back to project-specific run_tests.sh
    if [ -f "$PROJECT_ROOT/run_tests.sh" ]; then
        echo "🔄 Using project-specific test script..."
        SCRIPT_DIR="$PROJECT_ROOT"
        
        if [ "$FAST_MODE" = true ]; then
            source "$PROJECT_ROOT/run_tests.sh" --fast
        else
            source "$PROJECT_ROOT/run_tests.sh"
        fi
        
        TEST_RESULT=$?
        
        # Report results
        if [ $TEST_RESULT -eq 0 ]; then
            echo "✅ Tests completed successfully!"
        else
            echo "❌ Tests failed with exit code $TEST_RESULT"
        fi
        
        return $TEST_RESULT
    fi
    
    # Last resort: Direct pytest execution
    echo "🔄 No test script found, running pytest directly..."
    
    # Find pytest in virtual environment
    PYTEST_CMD=""
    if [ -f "$VENV_DIR/bin/pytest" ]; then
        PYTEST_CMD="$VENV_DIR/bin/pytest"
    elif command -v pytest &> /dev/null; then
        PYTEST_CMD="pytest"
    else
        echo "❌ pytest not found. Install it with: ./dhtl.sh install_tools"
        return 1
    fi
    
    # Find test directories
    TEST_DIRS=""
    if [ -d "$PROJECT_ROOT/tests" ]; then
        TEST_DIRS="$PROJECT_ROOT/tests"
    elif [ -d "$PROJECT_ROOT/test" ]; then
        TEST_DIRS="$PROJECT_ROOT/test"
    else
        echo "❌ No test directories found. Create a 'tests' directory first."
        return 1
    fi
    
    # Try to determine the package name
    PACKAGE_NAME=""
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        PACKAGE_NAME=$(grep -o 'name\s*=\s*"[^"]*"' "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2 | tr '-' '_')
    elif [ -f "$PROJECT_ROOT/setup.py" ]; then
        PACKAGE_NAME=$(grep -o 'name\s*=\s*"[^"]*"' "$PROJECT_ROOT/setup.py" | head -1 | cut -d'"' -f2 | tr '-' '_')
    fi
    
    # If no explicit package name, try to detect from src directory
    if [ -z "$PACKAGE_NAME" ]; then
        if [ -d "$PROJECT_ROOT/src" ]; then
            # Find first directory with __init__.py
            for dir in "$PROJECT_ROOT/src"/*; do
                if [ -d "$dir" ] && [ -f "$dir/__init__.py" ]; then
                    PACKAGE_NAME=$(basename "$dir")
                    break
                fi
            done
        else
            # Check in project root for package
            for dir in "$PROJECT_ROOT"/*; do
                if [ -d "$dir" ] && [ -f "$dir/__init__.py" ] && [[ "$dir" != *"test"* ]]; then
                    PACKAGE_NAME=$(basename "$dir")
                    break
                fi
            done
        fi
    fi
    
    # Make directory for reports
    mkdir -p "$PROJECT_ROOT/coverage_report"
    
    # Set up pytest arguments
    PYTEST_ARGS=(
        -v
        --html="$PROJECT_ROOT/report.html"
        --self-contained-html
        --durations=10
        --timeout=900
    )
    
    # Add coverage arguments if package name is found
    if [ -n "$PACKAGE_NAME" ]; then
        PYTEST_ARGS+=(
            "--cov=$PACKAGE_NAME"
            "--cov-report=term-missing:skip-covered"
            "--cov-report=html:$PROJECT_ROOT/coverage_report"
        )
        
        # Only enforce coverage in full test mode
        if [ "$FAST_MODE" = false ]; then
            PYTEST_ARGS+=("--cov-fail-under=80")
        fi
    fi
    
    # Add fast mode arguments if needed
    if [ "$FAST_MODE" = true ]; then
        echo "🔄 Running in fast mode - only critical tests"
        
        # Try to find critical tests
        CRITICAL_TESTS=(
            "test_cli_version"
            "test_cli_help"
            "test_cli_missing_filepath" 
            "test_cli_nonexistent_filepath"
            "test_translator_init_test_env"
            "test_basic"
            "test_version"
        )
        
        # Join tests with OR for pytest -k expression
        TESTS_EXPR=$(IFS=" or "; echo "${CRITICAL_TESTS[*]}")
        PYTEST_ARGS+=(-k "$TESTS_EXPR")
    fi
    
    # Run pytest with timeout
    echo "🧪 Running pytest with timeout of $TIMEOUT seconds..."
    timeout $TIMEOUT $PYTEST_CMD "${PYTEST_ARGS[@]}" $TEST_DIRS
    
    TEST_RESULT=$?
    
    # Report results
    if [ $TEST_RESULT -eq 0 ]; then
        echo "✅ Tests completed successfully!"
    elif [ $TEST_RESULT -eq 124 ]; then
        echo "❌ Tests timed out after $TIMEOUT seconds"
    else
        echo "❌ Tests failed with exit code $TEST_RESULT"
    fi
    
    return $TEST_RESULT
}