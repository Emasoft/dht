#!/bin/bash
# dhtl_commands_1.sh - Commands_1 module for DHT Launcher
# Contains dependency restoration logic.

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

# Restore project dependencies using uv.
# Assumes the virtual environment exists and uv is available (handled by 'dhtl setup').
# Priority: uv.lock -> pyproject.toml[dev] -> requirements-dev.txt -> requirements.txt
restore_dependencies() {
    log_info "Restoring project dependencies..."

    # Ensure PROJECT_ROOT is set
    if [[ -z "$PROJECT_ROOT" ]]; then
        PROJECT_ROOT=$(find_project_root)
        if [[ -z "$PROJECT_ROOT" ]]; then
             log_error "Could not determine project root." $ERR_ENVIRONMENT
             return $ERR_ENVIRONMENT
        fi
    fi
    log_debug "Project root: $PROJECT_ROOT"

    # Find the virtual environment
    VENV_DIR=$(find_virtual_env "$PROJECT_ROOT") # Use canonical function
    if [ -z "$VENV_DIR" ]; then
        VENV_DIR="$DEFAULT_VENV_DIR" # Use globally set default
    fi
    log_debug "Using virtual environment: $VENV_DIR"

    # Ensure venv exists - if not, tell user to run setup
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment directory not found: $VENV_DIR." $ERR_ENVIRONMENT
        log_error "Run 'dhtl setup' first to create the environment and install tools."
        return $ERR_ENVIRONMENT
    fi

    # Get the uv command path (use helper from dhtl_uv.sh)
    local UV_CMD
    UV_CMD=$(get_uv_command "$VENV_DIR")
    if [[ -z "$UV_CMD" ]]; then
        log_error "uv command not found in venv or PATH. Cannot restore dependencies." $ERR_COMMAND_NOT_FOUND
        log_error "Run 'dhtl setup' to ensure uv is installed correctly."
        return $ERR_COMMAND_NOT_FOUND
    fi
    log_debug "Using uv command: $UV_CMD"

    # Activate virtual environment if not already active (best effort)
    local active_venv
    active_venv=$(detect_active_venv)
    if [[ "$active_venv" != "$VENV_DIR"* ]]; then
        local activate_script="$VENV_DIR/bin/activate"
        if [[ ! -f "$activate_script" ]]; then activate_script="$VENV_DIR/Scripts/activate"; fi # Windows check

        if [[ -f "$activate_script" ]]; then
            # shellcheck source=/dev/null
            source "$activate_script"
            log_success "Activated virtual environment: $VENV_DIR"
        else
            log_warning "Could not find activation script for $VENV_DIR. Dependencies might not install correctly if venv isn't active."
            # Continue anyway, uv might handle it if paths are correct
        fi
    fi

    # Determine Python executable within the venv for uv commands
    local venv_python="$VENV_DIR/bin/python"
    if [[ ! -x "$venv_python" ]]; then
        if [[ -x "$VENV_DIR/Scripts/python.exe" ]]; then # Windows Git Bash/WSL
            venv_python="$VENV_DIR/Scripts/python.exe"
        else
            log_error "Python interpreter not found in virtual environment: $venv_python" $ERR_ENVIRONMENT
            return $ERR_ENVIRONMENT
        fi
    fi

    # --- Dependency Installation Logic ---
    local install_success=false
    local install_method=""
    local pyproject_file="$PROJECT_ROOT/pyproject.toml"
    local lock_file="$PROJECT_ROOT/uv.lock"
    local req_dev_file="$PROJECT_ROOT/requirements-dev.txt"
    local req_file="$PROJECT_ROOT/requirements.txt"

    # 1. Try syncing with uv.lock (most preferred)
    if [[ -f "$lock_file" ]]; then
        log_info "📦 Attempting to sync dependencies from $lock_file using uv..."
        # Run sync from project root, specifying python interpreter
        if (cd "$PROJECT_ROOT" && "$UV_CMD" sync --locked -p "$venv_python"); then
            log_success "Dependencies synced successfully from $lock_file."
            install_success=true
            install_method="uv sync --locked"
        else
            log_warning "Failed to sync with $lock_file. Will try other methods."
        fi
    fi

    # 2. Try installing from pyproject.toml (editable + dev extras)
    if [[ "$install_success" = false ]] && [[ -f "$pyproject_file" ]]; then
        log_info "📦 Attempting to install dev dependencies from $pyproject_file using uv..."
        # Change to project directory to use relative path for editable install
        local original_dir
        original_dir=$(pwd)
        pushd "$PROJECT_ROOT" > /dev/null || { log_error "Failed to cd to $PROJECT_ROOT"; return 1; }
        if "$UV_CMD" pip install -p "$venv_python" -e ".[dev]"; then
             log_success "Development dependencies installed/updated from $pyproject_file."
             install_success=true
             install_method="uv pip install -e .[dev]"
        else
            log_warning "Failed to install dev dependencies from $pyproject_file."
        fi
        popd > /dev/null || { log_error "Failed to cd back from $PROJECT_ROOT"; return 1; } # Return to original directory
    fi

    # 3. Try installing from requirements-dev.txt (fallback)
    if [[ "$install_success" = false ]] && [[ -f "$req_dev_file" ]]; then
        log_info "📦 Attempting to install dependencies from $req_dev_file using uv..."
        if "$UV_CMD" pip install -p "$venv_python" -r "$req_dev_file"; then
            log_success "Development dependencies installed/updated from $req_dev_file."
            install_success=true
            install_method="uv pip install -r requirements-dev.txt"
        else
            log_warning "Failed to install dependencies from $req_dev_file."
        fi
    fi

    # 4. Try installing from requirements.txt (last resort for core deps)
    if [[ "$install_success" = false ]] && [[ -f "$req_file" ]]; then
        log_info "📦 Attempting to install core dependencies from $req_file using uv..."
        if "$UV_CMD" pip install -p "$venv_python" -r "$req_file"; then
            log_success "Core dependencies installed/updated from $req_file."
            install_success=true
            install_method="uv pip install -r requirements.txt"
            log_warning "Note: Only core dependencies from requirements.txt were installed. Dev tools might be missing."
        else
            log_warning "Failed to install dependencies from $req_file."
        fi
    fi

    # Install dependencies needed by diagnostic_reporter.py
    log_info "📦 Ensuring dependencies for diagnostics reporter..."
    local reporter_deps=("psutil" "distro" "requests" "gitpython" "pyyaml")
    local dep_install_failed=0
    for dep in "${reporter_deps[@]}"; do
        if ! "$UV_CMD" pip install -p "$venv_python" "$dep"; then
            log_warning "Failed to install diagnostic dependency '$dep'."
            dep_install_failed=1
        fi
    done
    if [[ $dep_install_failed -eq 0 ]]; then
        log_success "Diagnostic reporter dependencies ensured."
    fi


    # Report final status
    if [[ "$install_success" = true ]]; then
        log_success "Dependencies restored successfully (Method: $install_method)."
        # Re-installing DHT tools is likely redundant if pyproject/req-dev was used,
        # but we can ensure psutil/requests are present for DHT core functionality.
        log_info "Ensuring core DHT dependencies (psutil, requests) are present..."
        if ! "$UV_CMD" pip install -p "$venv_python" psutil requests; then
             log_warning "Failed to ensure core DHT dependencies."
             # Don't fail the whole restore for this minor check
        fi
        return 0
    else
        log_error "Failed to restore primary project dependencies." $ERR_MISSING_DEPENDENCY
        log_error "Checked: uv.lock, pyproject.toml, requirements-dev.txt, requirements.txt"
        log_error "Try running 'dhtl setup' to ensure the environment and tools are correctly configured."
        return $ERR_MISSING_DEPENDENCY
    fi
}

# Command alias for restore_dependencies
restore_command() {
    restore_dependencies
    return $?
}
