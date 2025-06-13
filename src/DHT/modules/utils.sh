#!/bin/bash
# Utils module

# ===== Direct Execution Prevention =====
# This script cannot be executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script is part of a modular system and cannot be executed directly." >&2
    echo "Please use the orchestrator script instead." >&2
    exit 1
fi

check_command_args() {
    # Check if process guardian should be disabled
    if [[ "$*" == *"--no-guardian"* ]]; then
        USE_GUARDIAN=false
        # Remove --no-guardian flag from arguments
        ARGS=()
        for arg in "$@"; do
            if [ "$arg" != "--no-guardian" ]; then
                ARGS+=("$arg")
            fi
        done
        set -- "${ARGS[@]}"
    fi
    
    # Check if quiet mode is enabled
    if [[ "$*" == *"--quiet"* ]]; then
        QUIET_MODE=true
        # Remove --quiet flag from arguments
        ARGS=()
        for arg in "$@"; do
            if [ "$arg" != "--quiet" ]; then
                ARGS+=("$arg")
            fi
        done
        set -- "${ARGS[@]}"
    fi
    
    return 0
}

format_command() {
    echo "🎨 Formatting code in project..."
    PROJECT_ROOT=$(find_project_root)
    
    # Try to detect which formatters are available
    USE_RUFF=false
    USE_BLACK=false
    USE_ISORT=false
    
    # Check for venv first
    VENV_DIR=$(find_virtual_env "$PROJECT_ROOT")
    if [ -z "$VENV_DIR" ]; then
        VENV_DIR="$PROJECT_ROOT/.venv"
    fi
    
    # Check for available formatters
    if [ -f "$VENV_DIR/bin/ruff" ]; then
        USE_RUFF=true
    elif command -v ruff &> /dev/null; then
        USE_RUFF=true
    fi
    
    if [ -f "$VENV_DIR/bin/black" ]; then
        USE_BLACK=true
    elif command -v black &> /dev/null; then
        USE_BLACK=true
    fi
    
    if [ -f "$VENV_DIR/bin/isort" ]; then
        USE_ISORT=true
    elif command -v isort &> /dev/null; then
        USE_ISORT=true
    fi
    
    # Format Python files
    FORMAT_ERRORS=0
    
    echo "🎨 Formatting Python files..."
    
    # First try ruff format
    if [ "$USE_RUFF" = true ]; then
        echo "🔄 Running ruff format..."
        ensure_process_guardian
        if [ -f "$VENV_DIR/bin/ruff" ]; then
            run_with_guardian "$VENV_DIR/bin/ruff" "ruff" "$PYTHON_MEM_LIMIT" format "$PROJECT_ROOT"
        else
            run_with_guardian ruff "ruff" "$PYTHON_MEM_LIMIT" format "$PROJECT_ROOT"
        fi
        
        if [ $? -ne 0 ]; then
            FORMAT_ERRORS=1
            echo "❌ Ruff format encountered errors."
        else
            echo "✅ Ruff format completed successfully."
        fi
    # Try black
    elif [ "$USE_BLACK" = true ]; then
        echo "🔄 Running black..."
        ensure_process_guardian
        if [ -f "$VENV_DIR/bin/black" ]; then
            run_with_guardian "$VENV_DIR/bin/black" "black" "$PYTHON_MEM_LIMIT" "$PROJECT_ROOT"
        else
            run_with_guardian black "black" "$PYTHON_MEM_LIMIT" "$PROJECT_ROOT"
        fi
        
        if [ $? -ne 0 ]; then
            FORMAT_ERRORS=1
            echo "❌ Black encountered errors."
        else
            echo "✅ Black completed successfully."
        fi
    fi
    
    # Run isort if available
    if [ "$USE_ISORT" = true ] && [ "$USE_RUFF" = false ]; then
        echo "🔄 Running isort..."
        ensure_process_guardian
        if [ -f "$VENV_DIR/bin/isort" ]; then
            run_with_guardian "$VENV_DIR/bin/isort" "isort" "$PYTHON_MEM_LIMIT" "$PROJECT_ROOT"
        else
            run_with_guardian isort "isort" "$PYTHON_MEM_LIMIT" "$PROJECT_ROOT"
        fi
        
        if [ $? -ne 0 ]; then
            FORMAT_ERRORS=1
            echo "❌ Isort encountered errors."
        else
            echo "✅ Isort completed successfully."
        fi
    fi
    
    # Exit with appropriate code
    if [ $FORMAT_ERRORS -eq 0 ]; then
        echo "✅ All formatting completed successfully."
        return 0
    else
        echo "⚠️ Some formatters encountered errors."
        return 1
    fi
}

file_exists_in_tree() {
    local dir="$1"
    local filename="$2"
    local max_depth="${3:-4}"  # Default max depth of 4
    
    if find "$dir" -maxdepth "$max_depth" -name "$filename" -type f -print -quit 2>/dev/null | grep -q .; then
        return 0
    else
        return 1
    fi
}

# lint_command is defined in dhtl_utils.sh - removing duplicate

