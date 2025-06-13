#!/bin/bash
# DHT Initialization Module
#
# This module provides functions for initializing DHT in any project.
# It sets up the DHT directory structure and creates necessary files.

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

# Function to install project dependencies using uv
# Ensures dev dependencies from requirements-dev.txt (or pyproject.toml) and tox are installed.
# Priority: uv.lock -> pyproject.toml[dev] -> requirements-dev.txt -> requirements.txt
install_project_dependencies() {
    local target_dir="$1"
    local venv_path="$target_dir/.venv" # Assumes standard venv location
    local venv_python="$venv_path/bin/python"
    local pyproject_file="$target_dir/pyproject.toml"
    local lock_file="$target_dir/uv.lock"
    local req_dev_file="$target_dir/requirements-dev.txt"
    local req_file="$target_dir/requirements.txt"

    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found at $venv_path. Cannot install dependencies." $ERR_ENVIRONMENT
        log_error "Run 'dhtl setup' or 'dhtl init' first."
        return $ERR_ENVIRONMENT
    fi

    # Ensure Python interpreter exists in venv
    if [[ ! -x "$venv_python" ]]; then
        if [[ -x "$venv_path/Scripts/python.exe" ]]; then # Windows Git Bash/WSL
            venv_python="$venv_path/Scripts/python.exe"
        else
            log_error "Python interpreter not found in virtual environment: $venv_python" $ERR_ENVIRONMENT
            log_error "The virtual environment might be corrupted or incomplete."
            return $ERR_ENVIRONMENT
        fi
    fi
    log_debug "Using Python from venv: $venv_python"

    # Get the uv command path (use helper from dhtl_uv.sh)
    local UV_CMD
    UV_CMD=$(get_uv_command "$venv_path") # Pass venv path
    if [[ -z "$UV_CMD" ]]; then
        log_error "uv command not found. Cannot install dependencies." $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi
    log_debug "Using uv command: $UV_CMD"

    log_info "Installing/updating project dependencies..."

    local install_success=false
    local install_method=""

    # 1. Try syncing with uv.lock (most preferred)
    if [[ -f "$lock_file" ]]; then
        log_info "📦 Attempting to sync dependencies from $lock_file using uv..."
        if "$UV_CMD" sync --locked -p "$venv_python"; then
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
        if "$UV_CMD" pip install -p "$venv_python" -e ".[dev]"; then
             log_success "Development dependencies installed/updated from $pyproject_file."
             install_success=true
             install_method="uv pip install -e .[dev]"
        else
            log_warning "Failed to install dev dependencies from $pyproject_file."
        fi
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
            # Mark as success, but dev tools might be missing
            install_success=true
            install_method="uv pip install -r requirements.txt"
            log_warning "Note: Only core dependencies from requirements.txt were installed. Dev tools might be missing."
        else
            log_warning "Failed to install dependencies from $req_file."
        fi
    fi

    # Report if no dependency source was found or successful
    if [[ "$install_success" = false ]]; then
         log_error "No suitable dependency file found or installation failed (checked uv.lock, pyproject.toml, requirements-dev.txt, requirements.txt)." $ERR_FILE_NOT_FOUND
         # Allow continuing to install tox, but return failure later
    else
        log_info "Dependencies installed via: $install_method"
    fi

    # Always try to install/update pip itself
    log_info "📦 Ensuring pip is installed/updated in the venv using uv..."
    if "$UV_CMD" pip install -p "$venv_python" --upgrade pip; then
        log_success "pip installed/updated successfully in the venv."
    else
        log_warning "Failed to install/update pip in the venv. Some operations might fail."
    fi

    # Always try to install tox
    log_info "📦 Ensuring tox is installed using uv..."
    if "$UV_CMD" pip install -p "$venv_python" tox; then
        log_success "tox installed/updated successfully."
    else
        log_warning "Failed to install tox. Ensure 'tox' is in your dev dependencies or install manually."
        # Do not fail the whole process just for tox
    fi

    # Install dependencies needed by diagnostic_reporter.py
    log_info "📦 Ensuring dependencies for diagnostics reporter..."
    local reporter_deps=("psutil" "distro" "requests" "gitpython" "pyyaml")
    for dep in "${reporter_deps[@]}"; do
        if ! "$UV_CMD" pip install -p "$venv_python" "$dep"; then
            log_warning "Failed to install diagnostic dependency '$dep'."
            # Don't fail the whole setup for this, but warn
        fi
    done

    if [[ "$install_success" = true ]]; then
        log_success "Project dependencies setup complete."
        return 0
    else
        log_error "Failed to install primary project dependencies." $ERR_MISSING_DEPENDENCY
        return $ERR_MISSING_DEPENDENCY
    fi
}

# Function to set up/update the virtual environment and aliases for an existing project
# Usage: setup_command [target_dir]
setup_command() {
    local target_dir="${1:-$PROJECT_ROOT}" # Default to current project root if not provided

    # Ensure target_dir is an absolute path
    if [[ "$target_dir" != /* ]]; then
        target_dir="$(realpath "$target_dir")"
    fi

    log_info "🛠️ Running DHT Setup for project at $target_dir..."

    # Step 0: Run diagnostics to gather info and generate report
    if function_exists "run_diagnostics"; then
        if ! run_diagnostics; then
             log_warning "Diagnostics failed. Setup might be incomplete or based on defaults."
             # Continue setup, but be aware info might be missing
        fi
    else
         log_warning "Diagnostics module not found. Skipping environment report generation."
    fi

    # Step 1: Ensure uv is installed and set up the virtual environment
    # setup_uv also creates the venv if it doesn't exist.
    if ! setup_uv "$target_dir"; then
        log_error "Failed to set up uv or virtual environment. Aborting setup." $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi
    log_success "uv setup and virtual environment verified/created."

    # Step 2: Install/update project development dependencies into the venv
    if ! install_project_dependencies "$target_dir"; then
        log_warning "Failed to install all project dependencies. Some tools might not be available."
        # Continue, as alias creation might still be useful
    fi

    # Step 3: Install pre-commit hooks if config exists
    if [[ -f "$target_dir/.pre-commit-config.yaml" ]]; then
        log_info "Installing pre-commit hooks..."
        local venv_path="$target_dir/.venv" # Standard venv location
        local precommit_cmd="$venv_path/bin/pre-commit"
        if [[ ! -x "$precommit_cmd" ]]; then precommit_cmd="$venv_path/Scripts/pre-commit.exe"; fi

        if [[ -x "$precommit_cmd" ]]; then
             # Run pre-commit install within the project directory
             (cd "$target_dir" && "$precommit_cmd" install)
             if [[ $? -eq 0 ]]; then
                 log_success "Pre-commit hooks installed successfully."
             else
                 log_warning "Failed to install pre-commit hooks."
             fi
        else
             log_warning "pre-commit command not found in venv. Skipping hook installation."
             log_warning "Run 'dhtl setup' again after ensuring pre-commit is in dev dependencies."
        fi
    fi

    # Step 4: Create/update dhtl alias scripts inside the venv
    if create_dhtl_alias_scripts "$target_dir"; then
        log_success "dhtl alias scripts created/updated in the virtual environment."
    else
        log_error "Failed to create dhtl alias scripts." $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT # Alias creation is critical for 'dhtl' command usability
    fi

    # Step 5: Handle Secrets (Check and Instruct)
    if function_exists "check_and_instruct_secrets"; then
        check_and_instruct_secrets "$target_dir"
    else
        log_warning "Secrets management function not found. Skipping secrets check."
    fi

    log_success "DHT Setup completed successfully for $target_dir."
    echo "   Virtual Environment: $target_dir/.venv (or .venv_windows)"
    echo "   To use the 'dhtl' alias, activate the environment:"
    echo "   e.g., source \"$target_dir/.venv/bin/activate\""
    echo "   (or equivalent for your shell/OS)"
}


# Function to initialize DHT in a new or existing project
# Usage: init_command [target_dir]
init_command() {
    local target_dir="${1:-.}" # Default to current directory

    # Create absolute path for target_dir
    if [[ "$target_dir" != /* ]]; then
        target_dir="$(realpath "$target_dir")"
    fi

    log_info "🚀 Initializing DHT in $target_dir..."

    # Create DHT structure within the target project
    local target_dht_dir="$target_dir/DHT"
    mkdir -p "$target_dht_dir/modules"
    mkdir -p "$target_dht_dir/tests/unit"
    mkdir -p "$target_dht_dir/tests/integration"
    log_success "DHT directory structure created at $target_dht_dir."

    # Create the project root dhtl launcher script(s) if they don't exist
    create_launcher_script "$target_dir"

    # Copy essential modules to the new project's DHT directory
    copy_essential_modules "$target_dir"

    # Create a basic test framework for DHT itself within the new project
    create_test_framework "$target_dir"

    # Create DHT configuration files (READMEs) in the new project's DHT directory
    create_dht_config "$target_dir"

    # Initialize git in the target directory if not already initialized
    init_git "$target_dir"

    # Create initial project structure (src, tests, pyproject.toml, etc.) if needed
    create_project_structure "$target_dir"

    # Create default tox.ini if it doesn't exist
    _create_default_tox_ini "$target_dir"

    # Create default GitHub workflows if they don't exist
    _create_github_workflows "$target_dir"

    # Set up uv and the virtual environment for the target project
    if ! setup_uv "$target_dir"; then
        log_error "Failed during uv setup for the project. Aborting initialization." $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi

    # Install project development dependencies (including tox) into the new venv
    if ! install_project_dependencies "$target_dir"; then
        log_warning "Failed to install project dependencies. Please check logs and run 'dhtl setup' later."
        # Decide if this is a fatal error for init - let's allow it to continue for now
    fi

    # Install pre-commit hooks if config exists
    if [[ -f "$target_dir/.pre-commit-config.yaml" ]]; then
        log_info "Installing pre-commit hooks..."
        local venv_path="$target_dir/.venv" # Standard venv location
        local precommit_cmd="$venv_path/bin/pre-commit"
        if [[ ! -x "$precommit_cmd" ]]; then precommit_cmd="$venv_path/Scripts/pre-commit.exe"; fi

        if [[ -x "$precommit_cmd" ]]; then
             (cd "$target_dir" && "$precommit_cmd" install)
             if [[ $? -eq 0 ]]; then log_success "Pre-commit hooks installed successfully."; else log_warning "Failed to install pre-commit hooks."; fi
        else
             log_warning "pre-commit command not found in venv. Skipping hook installation."
        fi
    fi

    # Create dhtl alias scripts within the new virtual environment
    if create_dhtl_alias_scripts "$target_dir"; then
         log_success "dhtl alias scripts created/updated."
    else
        log_error "Failed to create dhtl alias scripts." $ERR_ENVIRONMENT
        # Decide if this is a fatal error for init - let's allow it to continue
    fi

    # Run diagnostics for the new project *after* setting up venv and installing deps
    if function_exists "run_diagnostics"; then
        if ! run_diagnostics; then
             log_warning "Diagnostics failed during init. Environment report might be incomplete."
        fi
    else
         log_warning "Diagnostics module not found. Skipping environment report generation during init."
    fi

    # Handle Secrets (Check and Instruct)
    if function_exists "check_and_instruct_secrets"; then
        check_and_instruct_secrets "$target_dir"
    else
        log_warning "Secrets management function not found. Skipping secrets check."
    fi

    log_success "DHT initialized successfully in $target_dir"
    echo "   Virtual environment created at $target_dir/.venv (or .venv_windows)"
    echo "   Activate it using: source \"$target_dir/.venv/bin/activate\""
    echo "   Then you can use the 'dhtl' command."
}

# ---------------------------------------------------------------------
# Creates the dhtl alias scripts inside the virtual environment directories
# Assumes the virtual environment exists at $proj_dir/.venv or $proj_dir/.venv_windows
create_dhtl_alias_scripts() {
    local proj_dir="$1"
    local dhtl_script_path_relative='DHT/dhtl.sh' # Relative path from project root

    log_info "Setting up 'dhtl' alias to point to '\$PROJECT_ROOT/$dhtl_script_path_relative'"

    local created_posix=false
    local created_windows=false

    # --- POSIX (.venv) -------------------------------------------------
    local posix_venv_bin="$proj_dir/.venv/bin"
    if [[ -d "$posix_venv_bin" ]]; then
        local act_dir="$posix_venv_bin/activate.d"
        mkdir -p "$act_dir"
        log_debug "Creating Posix alias script: $act_dir/dhtl_alias.sh"
        cat >"$act_dir/dhtl_alias.sh"<<EOSH
#!/usr/bin/env bash
# Auto-generated by DHT: exposes the \`dhtl\` alias after venv activation.

# Unalias and clear hash before defining to ensure it's fresh
unalias dhtl 2>/dev/null || true
hash -d dhtl 2>/dev/null || true   # zsh fix

# Determine PROJECT_ROOT dynamically based on the venv's location
# Assumes the .venv is at the root of the project.
_OLD_PWD_DHTL="\$(pwd)"
# shellcheck disable=SC2164 # Error handling is implicit with set -e
cd -- "\$( dirname "\${BASH_SOURCE[0]}" )/../.." &>/dev/null
_PROJECT_ROOT_DHTL="\$(pwd -P)" # -P to resolve symlinks, ensuring canonical path
# shellcheck disable=SC2164 # Error handling is implicit with set -e
cd -- "\$_OLD_PWD_DHTL" &>/dev/null
unset _OLD_PWD_DHTL # Clean up temporary variable

# Define the alias
alias dhtl="\${_PROJECT_ROOT_DHTL}/$dhtl_script_path_relative"

# Source project-specific secrets if .env file exists
if [ -f "\$_PROJECT_ROOT_DHTL/.env" ]; then
    # shellcheck source=/dev/null
    set -a # Automatically export all variables
    source "\$_PROJECT_ROOT_DHTL/.env"
    set +a
fi
unset _PROJECT_ROOT_DHTL # Clean up temporary variable

# Attempt to export the alias for subshells if supported (Bash specific)
# This makes 'dhtl' available in scripts run from the activated shell.
if [[ -n "\$BASH_VERSION" ]]; then
    export -f dhtl 2>/dev/null || true
fi
EOSH
        chmod +x "$act_dir/dhtl_alias.sh"
        created_posix=true
    else
        log_debug "Posix venv directory not found: $posix_venv_bin. Skipping Posix alias."
    fi

    # --- Windows (.venv_windows) --------------------------------------
    local win_venv_scripts="$proj_dir/.venv_windows/Scripts"
    if [[ -d "$win_venv_scripts" ]]; then
        local win_activate_d_dir="$win_venv_scripts/activate.d"
        mkdir -p "$win_activate_d_dir"

        # alias bash (Git-Bash / WSL)
        log_debug "Creating Git Bash alias script: $win_activate_d_dir/dhtl_alias.sh"
        cat >"$win_activate_d_dir/dhtl_alias.sh"<<EOSH
#!/usr/bin/env bash
# Auto-generated by DHT: exposes the \`dhtl\` alias after venv activation (Windows Git Bash).
unalias dhtl 2>/dev/null || true
hash -d dhtl 2>/dev/null || true

_OLD_PWD_DHTL="\$(pwd)"
# shellcheck disable=SC2164
cd -- "\$( dirname "\${BASH_SOURCE[0]}" )/../.." &>/dev/null
_PROJECT_ROOT_DHTL="\$(pwd -P)"
# shellcheck disable=SC2164
cd -- "\$_OLD_PWD_DHTL" &>/dev/null
unset _OLD_PWD_DHTL

alias dhtl="\${_PROJECT_ROOT_DHTL}/$dhtl_script_path_relative"

# Source project-specific secrets if .env file exists
if [ -f "\$_PROJECT_ROOT_DHTL/.env" ]; then
    # shellcheck source=/dev/null
    set -a # Automatically export all variables
    source "\$_PROJECT_ROOT_DHTL/.env"
    set +a
fi
unset _PROJECT_ROOT_DHTL

if [[ -n "\$BASH_VERSION" ]]; then
    export -f dhtl 2>/dev/null || true
fi
EOSH
        chmod +x "$win_activate_d_dir/dhtl_alias.sh"

        # alias batch (cmd / powershell) - points to DHT/dhtl.bat
        local dhtl_bat_path_relative='DHT\\dhtl.bat' # Relative path using backslashes
        log_debug "Creating Windows Batch alias script: $win_venv_scripts/dhtl_alias.bat"
        # Use %~dp0 which expands to the directory of the batch script (.venv_windows/Scripts/)
        # Then navigate up two levels to the project root.
        cat >"$win_venv_scripts/dhtl_alias.bat"<<EOBAT
@echo off
doskey dhtl="%~dp0..\\..\\$dhtl_bat_path_relative" %*
EOBAT
        created_windows=true
    else
        log_debug "Windows venv directory not found: $win_venv_scripts. Skipping Windows alias."
    fi

    # Return success if at least one alias type was created
    if [[ "$created_posix" = true || "$created_windows" = true ]]; then
        return 0
    else
        # If neither venv type was found, it's likely an issue
        log_error "Failed to create alias scripts: Neither Posix nor Windows venv structure found." $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi
}

# Function to create the dhtl launcher script(s) at the project root
create_launcher_script() {
    local target_dir="$1" # Project root
    local launcher_path_sh="$target_dir/dhtl.sh"
    local launcher_path_bat="$target_dir/dhtl.bat"
    local dht_script_rel_sh="DHT/dhtl.sh" # Relative path to main script
    local dht_script_rel_bat="DHT\\dhtl.bat" # Relative path for batch

    log_info "Creating project root dhtl launcher script(s)..."

    # Create dhtl.sh (for Unix-like systems)
    cat > "$launcher_path_sh" << EOF
#!/bin/bash
# Project Root DHT Launcher
# This script calls the main DHT toolkit script located in the DHT subdirectory.

set -e

# Determine the directory containing this script (the project root)
PROJECT_ROOT_DIR="\$( cd -- "\$(dirname "\${BASH_SOURCE[0]}")" &> /dev/null && pwd )"
# Path to the main DHT script relative to the project root
DHT_MAIN_SCRIPT="\$PROJECT_ROOT_DIR/$dht_script_rel_sh"

if [[ ! -f "\$DHT_MAIN_SCRIPT" ]]; then
    echo "❌ ERROR: Main DHT script not found at \$DHT_MAIN_SCRIPT" >&2
    echo "   DHT might not be correctly initialized in this project." >&2
    echo "   Try running the setup command from your DHT installation:" >&2
    echo "   path/to/your/dht/dhtl.sh setup \"\$PROJECT_ROOT_DIR\"" >&2
    exit 1
fi

# Execute the main DHT script, passing all arguments
# Use exec to replace this process with the target script
exec "\$DHT_MAIN_SCRIPT" "\$@"
EOF
    chmod +x "$launcher_path_sh"
    log_success "Created $launcher_path_sh"

    # Create dhtl.bat (for Windows CMD/PowerShell)
    # Check if we are likely on Windows or a Unix env that might need it (like Git Bash)
    if [[ "$PLATFORM" == "windows_unix" || "$PLATFORM" == "windows" || -n "$WINDIR" ]]; then
        log_info "Creating project root dhtl.bat launcher script for Windows at $launcher_path_bat..."
        cat > "$launcher_path_bat" << 'EOF'
@echo off
:: Project Root DHT Launcher for Windows
:: This script calls the main DHT toolkit script located in the DHT subdirectory.

setlocal

:: Determine the directory containing this script (the project root)
set "PROJECT_ROOT_DIR=%~dp0"
:: Remove trailing backslash if present
if "%PROJECT_ROOT_DIR:~-1%"=="\" set "PROJECT_ROOT_DIR=%PROJECT_ROOT_DIR:~0,-1%"

:: Path to the main DHT batch script relative to the project root
set "DHT_MAIN_SCRIPT_BAT=%PROJECT_ROOT_DIR%\DHT\dhtl.bat"
set "DHT_MAIN_SCRIPT_SH=%PROJECT_ROOT_DIR%\DHT\dhtl.sh"

if exist "%DHT_MAIN_SCRIPT_BAT%" (
    call "%DHT_MAIN_SCRIPT_BAT%" %*
    exit /b %ERRORLEVEL%
) else if exist "%DHT_MAIN_SCRIPT_SH%" (
    echo Attempting to run with Bash: %DHT_MAIN_SCRIPT_SH%
    bash "%DHT_MAIN_SCRIPT_SH%" %*
    exit /b %ERRORLEVEL%
) else (
    echo ERROR: Main DHT script not found at %DHT_MAIN_SCRIPT_BAT% or %DHT_MAIN_SCRIPT_SH%
    echo DHT might not be correctly initialized in this project.
    exit /b 1
)

endlocal
EOF
        log_success "Created $launcher_path_bat"
    fi
}

# Function to copy essential modules to a new project's DHT directory
copy_essential_modules() {
    local target_dir="$1" # Project root where DHT will be placed
    local target_dht_modules_dir="$target_dir/DHT/modules"
    # current_modules_dir is the modules dir of the *running* dhtl script
    local current_modules_dir="$MODULES_DIR"

    log_info "Copying essential modules to $target_dht_modules_dir..."
    mkdir -p "$target_dht_modules_dir"

    # List of essential modules needed for a minimal functional DHT instance
    # This list should align with the updated orchestrator.sh
    local essential_modules=(
        "orchestrator.sh"
        "dhtl_error_handling.sh"
        "dhtl_environment_1.sh"
        "dhtl_environment_3.sh"
        "environment.sh"
        "dhtl_utils.sh"
        "dhtl_guardian_1.sh"
        "dhtl_guardian_2.sh"
        "dhtl_guardian_command.sh"
        "dhtl_uv.sh"
        "dhtl_diagnostics.sh"
        "dhtl_secrets.sh"
        "dhtl_init.sh" # This module itself
        "user_interface.sh"
        "dhtl_commands_1.sh" # restore
        "dhtl_commands_8.sh" # clean
        "dhtl_environment_2.sh" # env
        # Add other core command modules if they are considered essential for a new project
        "dhtl_commands_standalone.sh" # script, python, node, run
        "dhtl_test.sh" # test_dht, verify_dht
        "dhtl_version.sh" # tag, bump
    )

    local copy_failed=false
    for module_to_copy in "${essential_modules[@]}"; do
        local source_module_path="$current_modules_dir/$module_to_copy"
        local target_module_path="$target_dht_modules_dir/$module_to_copy"

        if [[ -f "$source_module_path" ]]; then
            # Check if source and target are the same file to prevent 'cp: ... are the same file' error
            if [[ "$source_module_path" -ef "$target_module_path" ]]; then
                log_debug "  Skipping copy for $module_to_copy (source and target are the same file)."
            elif cp "$source_module_path" "$target_module_path"; then
                 log_debug "  Copied $module_to_copy"
            else
                 log_error "  Failed to copy $module_to_copy"
                 copy_failed=true
            fi
        else
            # Only warn if the module is expected to exist in the source DHT
            if [[ " ${essential_modules[*]} " =~ " ${module_to_copy} " ]]; then
                 log_warning "  Essential module $module_to_copy not found in source $current_modules_dir."
                 copy_failed=true # Treat missing essential module as failure
            fi
        fi
    done

    # Ensure a basic orchestrator exists, listing only the essentials we tried to copy
    local target_orchestrator="$target_dht_modules_dir/orchestrator.sh"
    log_debug "Creating/Updating orchestrator: $target_orchestrator"
    # This orchestrator template should match the one in the main orchestrator.sh
    # for consistency, listing only the modules that are truly essential for a *new* project.
    # The main orchestrator.sh in the source DHT repo will list *all* modules.
    cat > "$target_orchestrator" << EOF
#!/bin/bash
# Orchestrator for dhtl.sh (basic version for new projects)

SCRIPT_DIR="\$( cd -- "\$( dirname "\${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Import essential modules (adjust list if essential_modules changes)
source "\$SCRIPT_DIR/dhtl_error_handling.sh"
source "\$SCRIPT_DIR/dhtl_environment_1.sh"
source "\$SCRIPT_DIR/dhtl_environment_3.sh"
source "\$SCRIPT_DIR/environment.sh"
source "\$SCRIPT_DIR/dhtl_utils.sh"
source "\$SCRIPT_DIR/dhtl_guardian_1.sh"
source "\$SCRIPT_DIR/dhtl_guardian_2.sh"
source "\$SCRIPT_DIR/dhtl_guardian_command.sh"
source "\$SCRIPT_DIR/dhtl_uv.sh"
source "\$SCRIPT_DIR/dhtl_diagnostics.sh"
source "\$SCRIPT_DIR/dhtl_secrets.sh"
source "\$SCRIPT_DIR/dhtl_init.sh"
source "\$SCRIPT_DIR/user_interface.sh"
source "\$SCRIPT_DIR/dhtl_commands_1.sh" # restore
source "\$SCRIPT_DIR/dhtl_commands_8.sh" # clean
source "\$SCRIPT_DIR/dhtl_environment_2.sh" # env
source "\$SCRIPT_DIR/dhtl_commands_standalone.sh" # script, python, node, run
source "\$SCRIPT_DIR/dhtl_test.sh" # test_dht, verify_dht
source "\$SCRIPT_DIR/dhtl_version.sh" # tag, bump

# Add other modules here as the project evolves or more are copied.
# Example: source "\$SCRIPT_DIR/dhtl_commands_2.sh" # test
EOF

    if [[ "$copy_failed" = true ]]; then
        log_error "Failed to copy one or more essential modules." $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi

    log_success "Essential modules copied."
    return 0
}

# Function to create a basic test framework for DHT itself
create_test_framework() {
    local target_dir="$1" # Project root
    local tests_dir="$target_dir/DHT/tests" # Tests for DHT itself

    log_info "Creating DHT test framework in $tests_dir..."
    mkdir -p "$tests_dir/unit"
    mkdir -p "$tests_dir/integration"

    # Create conftest.py
    local conftest_path="$tests_dir/conftest.py"
    log_debug "Creating $conftest_path"
    cat > "$conftest_path" << 'EOF'
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add the DHT directory to sys.path to allow imports from DHT modules if needed
# This assumes conftest.py is in DHT/tests/
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def project_root():
    """Returns the project root directory (parent of DHT)."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def temp_dir_session_scoped(tmp_path_factory):
    """Create a temporary directory for tests that is cleaned up after session."""
    temp_dir = tmp_path_factory.mktemp("dht_tests_")
    yield temp_dir
    # tmp_path_factory handles cleanup

@pytest.fixture
def mock_project_dir(temp_dir_session_scoped):
    """Create a mock project directory with basic structure within a temp dir."""
    project_dir = Path(temp_dir_session_scoped) / "mock_project"
    project_dir.mkdir(exist_ok=True)

    # Create basic project structure
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "DHT").mkdir(exist_ok=True) # For testing dhtl init within mock

    # Create some mock files
    (project_dir / "pyproject.toml").touch()
    (project_dir / "README.md").touch()

    yield project_dir

@pytest.fixture
def mock_dht_env(monkeypatch, project_root):
    """Set up environment variables for DHT testing."""
    dht_dir = project_root / "DHT"
    monkeypatch.setenv("DHTL_SESSION_ID", "test_session_123")
    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("DHTL_DIR", str(dht_dir)) # dhtl.sh is in DHT
    monkeypatch.setenv("DHT_DIR", str(dht_dir))
    monkeypatch.setenv("DEFAULT_VENV_DIR", str(project_root / ".venv"))
    monkeypatch.setenv("DHTL_SKIP_ENV_SETUP", "1")
    monkeypatch.setenv("SKIP_ENV_CHECK", "1")
    monkeypatch.setenv("IN_DHTL", "1")
    monkeypatch.setenv("DEBUG_MODE", "true") # Enable debug for more output

    # Ensure PATH includes potential venv bin if tests need it
    venv_bin = project_root / ".venv" / "bin"
    if venv_bin.is_dir():
        monkeypatch.setenv("PATH", f"{venv_bin}:{os.environ.get('PATH', '')}", prepend=":")

    return os.environ.copy()

def pytest_sessionfinish(session, exitstatus):
    """Print a summary of test results at the end of the session."""
    try:
        reporter = session.config.pluginmanager.getplugin('terminalreporter')
        if reporter: # Reporter might not be available in all contexts (e.g. collection error)
            passed = len(reporter.stats.get('passed', []))
            failed = len(reporter.stats.get('failed', []))
            skipped = len(reporter.stats.get('skipped', []))

            print("\n📊 DHT Test Summary")
            print(f"Total Tests: {passed + failed + skipped}")
            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"⏩ Skipped: {skipped}")
    except Exception as e:
        print(f"\nError generating test summary: {e}")

EOF

    # Create pytest.ini
    local pytest_ini_path="$tests_dir/pytest.ini"
    log_debug "Creating $pytest_ini_path"
    cat > "$pytest_ini_path" << 'EOF'
[pytest]
testpaths = unit integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    bash: marks tests that depend on bash functionality
    process: marks tests related to process guardian functionality
    windows: marks tests specific to Windows
    macos: marks tests specific to macOS
    linux: marks tests specific to Linux
addopts = -v --color=yes
filterwarnings =
    ignore::DeprecationWarning
EOF

    # Create a sample unit test file
    local sample_test_path="$tests_dir/unit/test_core_presence.py"
    log_debug "Creating $sample_test_path"
    cat > "$sample_test_path" << 'EOF'
import os
import pytest
from pathlib import Path

def test_dht_core_files_exist(project_root):
    """Test that essential DHT core files exist."""
    dht_dir = project_root / "DHT"
    assert dht_dir.is_dir(), f"DHT directory {dht_dir} does not exist"

    modules_dir = dht_dir / "modules"
    assert modules_dir.is_dir(), f"DHT modules directory {modules_dir} does not exist"

    core_files = ["dhtl.sh", "modules/orchestrator.sh", "modules/dhtl_init.sh"]
    for f_path in core_files:
        assert (dht_dir / f_path).is_file(), f"Essential DHT file {dht_dir / f_path} does not exist"

    # Check for the project root launcher script as well
    launcher_script_project_root = project_root / "dhtl.sh"
    assert launcher_script_project_root.is_file(), f"Project root launcher {launcher_script_project_root} does not exist"
EOF
    log_success "DHT test framework created."
}

# Function to create DHT configuration files (READMEs)
create_dht_config() {
    local target_dir="$1" # Project root
    local dht_dir="$target_dir/DHT"
    local dht_readme_path="$dht_dir/README.md"
    local uv_commands_path="$dht_dir/uv_commands.md"

    log_info "Creating DHT configuration files (READMEs)..."
    mkdir -p "$dht_dir"

    # Create the README.md file for DHT directory
    log_debug "Creating $dht_readme_path"
    cat > "$dht_readme_path" << 'EOF'
# Development Helper Toolkit (DHT)

This directory contains the core scripts and modules for the Development Helper Toolkit (DHT).
DHT is a portable, project-independent toolkit that provides standardized development workflows,
environment management, and project automation.

## Structure

- `dhtl.sh`: The main launcher script for DHT. All commands are run through this.
- `dhtl.bat`: Windows batch wrapper for `dhtl.sh`.
- `modules/`: Contains various shell script modules that provide DHT's functionality.
  - `orchestrator.sh`: Loads all other modules.
  - `dhtl_init.sh`: Handles project initialization (`dhtl init`) and setup (`dhtl setup`).
  - `dhtl_uv.sh`: Manages Python virtual environments and dependencies using `uv`.
  - `dhtl_diagnostics.sh`: Gathers environment information and generates reports.
  - `dhtl_secrets.sh`: Handles detection and setup of required secrets.
  - ... and many others for linting, testing, building, etc.
- `tests/`: Contains tests for DHT itself (pytest for Python parts, BATS/shell for scripts).
- `.dht_environment_report.json`: Machine-readable report of the project environment (generated by `dhtl setup` or `dhtl env`).

## Usage

DHT is typically invoked via the `dhtl` alias (available when a DHT-managed virtual environment
is activated) or by running the launcher script from the project root (`./dhtl.sh` or `dhtl.bat`).

```bash
# From an activated virtual environment:
dhtl <command> [options]

# From the project root:
./dhtl.sh <command> [options]  # macOS/Linux/Git Bash
.\dhtl.bat <command> [options] # Windows CMD/PowerShell
```

### Key Commands

- `dhtl init`: Initializes DHT in a new or existing project. Creates necessary configs,
  sets up a virtual environment, installs dev tools, and runs diagnostics.
- `dhtl setup`: Sets up or updates the virtual environment, installs dev tools, runs diagnostics,
  configures the `dhtl` alias, and checks/instructs on secrets for the current project.
- `dhtl env`: Runs diagnostics and displays environment information.
- `dhtl test_dht`: Runs DHT's internal self-tests.
- `dhtl help`: Shows available commands.

Refer to the main project `README.md` or run `dhtl help` for a full list of commands.
EOF

    # Create UV integration documentation
    log_debug "Creating $uv_commands_path"
    cat > "$uv_commands_path" << 'EOF'
# `uv` Commands and Workflows Reference

This project uses `uv` (from Astral) for Python packaging and project management.
`uv` is an extremely fast Python package installer and resolver, written in Rust,
and is designed as a drop-in replacement for `pip` and `pip-tools`.

DHT integrates `uv` for:
- Creating and managing virtual environments (`dhtl setup`, `dhtl init`).
- Installing and syncing dependencies (`dhtl setup`, `dhtl init`).
- Potentially running tools (`dhtl uv tool run ...` if `dhtl_uv.sh` implements it).

## Common `uv` Commands (for manual use if needed)

You can also use `uv` directly if the virtual environment is activated.

### Virtual Environment Management

```bash
# Create a virtual environment (DHT typically uses .venv)
# Specify python version if needed, e.g., --python 3.11
uv venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Dependency Management

(Assuming `pyproject.toml` is your source of truth)

```bash
# Install dependencies from pyproject.toml (equivalent to pip install -e .)
uv pip install -e .

# Install dev dependencies defined in [project.optional-dependencies]
uv pip install -e ".[dev]"

# Add a new dependency
# 1. Manually add 'package-name' to pyproject.toml [project.dependencies]
# 2. Install it into the venv:
uv pip install package-name
# 3. Update the lock file (optional but recommended)
uv lock

# Sync environment with lock file (installs based on lock)
uv sync --locked

# Update all dependencies in lock file
uv lock --upgrade

# Update specific packages in lock file
uv lock --upgrade-package package-name --upgrade-package another-package
```

### Other Useful Commands

```bash
# Clean the global uv cache
uv cache clean

# List installed packages in the current venv
uv pip list

# Show details about an installed package
uv pip show package-name
```

For more information, refer to the official `uv` documentation:
[https://astral.sh/docs/uv](https://astral.sh/docs/uv)
EOF
    log_success "DHT configuration files created."
}

# Function to initialize git repository if needed
init_git() {
    local target_dir="$1"

    log_info "Checking git initialization in $target_dir..."

    if [[ -d "$target_dir/.git" ]]; then
        log_success "Git already initialized."
        return 0
    fi

    if ! command -v git &> /dev/null; then
        log_warning "Git command not found. Skipping git initialization."
        return 1 # Return error as git is usually expected
    fi

    log_info "Initializing git repository in $target_dir..."
    if git -C "$target_dir" init; then
        log_success "Git repository initialized."
    else
        log_error "Failed to initialize git repository." $ERR_GENERAL
        return $ERR_GENERAL
    fi

    local gitignore_path="$target_dir/.gitignore"
    if [[ ! -f "$gitignore_path" ]]; then
        log_debug "Creating .gitignore..."
        # Use the .gitignore content provided by the user if available, else default
        if [[ -f "$PROJECT_ROOT/.gitignore" && "$target_dir" != "$PROJECT_ROOT" ]]; then
             cp "$PROJECT_ROOT/.gitignore" "$gitignore_path"
             log_success ".gitignore copied from project."
        else
            # Default .gitignore content
            cat > "$gitignore_path" << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
src/*.egg-info/ # Explicitly ignore egg-info in src
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
coverage_report/ # HTML coverage report dir
report.html # HTML test report file

# Translations
*.mo
*.pot
*.po

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/ # Typically user-uploaded files

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# Environments
.env
.venv/
.venv_windows/
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# VS Code settings
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# AI Assistant & Tool Caches/Logs
.aider*
*.aider.chat.*
*.aider.tags.cache*
.aider.chat.history.md
.aider.input.history
.aider.tags.cache.v*
# report.html # Already covered by test reports section
.claude/

# Ruff Cache
.ruff_cache/

# macOS specific files
.DS_Store
**/.DS_Store

# Custom
*.orig
*.bak
*.swp
*.swo
*~
_setup* # Files starting with _setup

# Backup directories (but keep the README)
backups/*
!backups/
!backups/README.md

# Lock files (keep uv.lock in repo for reproducibility)
# uv.lock # Keep this commented - we want to track the lock file

# Test samples (ignore all by default, explicitly allow needed ones)
tests/samples/*
!tests/samples/
!tests/samples/.gitkeep
# !tests/samples/test_sample.txt # Example: Allow specific sample

# Examples directory - track only the README
examples/*
!examples/
!examples/README.md

# Changelog files (Track these)
# Keep changelog files in version control
# .chglog/ directory with templates should be committed
# CHANGELOG.md should be committed when generated

# DHT specific files (ensure these are ignored within DHT dir)
/DHT/.dht_cache/
/DHT/.dhtconfig
/DHT/.process_guardian/
/DHT/.dht_environment_report.json

# Temporary files from scripts
temp_commands.sh
temp/
EOF
            log_success "Default .gitignore created."
        fi
    else
        log_info ".gitignore already exists."
    fi
    return 0
}

# Function to create initial project structure (src, tests, basic pyproject.toml)
create_project_structure() {
    local target_dir="$1"
    local project_name
    project_name=$(basename "$target_dir") # Use directory name as default project name
    # Sanitize for Python package name (lowercase, replace hyphens/spaces with underscores)
    project_name=$(echo "$project_name" | tr '[:upper:]' '[:lower:]' | sed 's/[- ]/_/g' | sed 's/[^a-z0-9_]//g')
    if [[ -z "$project_name" ]]; then project_name="my_project"; fi # Fallback if name is invalid

    log_info "Checking project structure in $target_dir (using package name: $project_name)..."

    # Create src directory and basic package structure
    local src_pkg_dir="$target_dir/src/$project_name"
    if [[ ! -d "$src_pkg_dir" ]]; then
        log_debug "Creating src/$project_name structure..."
        mkdir -p "$src_pkg_dir"
        if [[ ! -f "$src_pkg_dir/__init__.py" ]]; then
            # Extract version from pyproject.toml if possible, else default
            local init_version="0.1.0"
            if [[ -f "$target_dir/pyproject.toml" ]]; then
                 local found_version
                 found_version=$(grep -oP '(?<=^version\s*=\s*")[^"]+' "$target_dir/pyproject.toml" | head -1)
                 if [[ -n "$found_version" ]]; then init_version="$found_version"; fi
            fi
            cat > "$src_pkg_dir/__init__.py" << EOF
"""$project_name package."""
__version__ = "$init_version"
EOF
        fi
        log_success "src/$project_name structure created."
    else
        log_info "src/$project_name structure already exists."
    fi

    # Create tests directory
    local tests_dir="$target_dir/tests"
    if [[ ! -d "$tests_dir" ]]; then
        log_debug "Creating tests directory..."
        mkdir -p "$tests_dir"
        if [[ ! -f "$tests_dir/__init__.py" ]]; then
            touch "$tests_dir/__init__.py"
        fi
        local test_file_path="$tests_dir/test_basic.py"
        if [[ ! -f "$test_file_path" ]]; then
            cat > "$test_file_path" << EOF
"""Basic tests for the $project_name project."""
import pytest

def test_import_project():
    """Test that the main project package can be imported."""
    try:
        import $project_name
        assert hasattr($project_name, "__version__")
        print(f"Imported $project_name version: {\$project_name.__version__}")
    except ImportError as e:
        pytest.fail(f"Failed to import project '$project_name': {e}")

# You can add more basic tests here
EOF
        fi
        log_success "tests directory structure created."
    else
        log_info "tests directory structure already exists."
    fi

    # Create docs directory
    if [[ ! -d "$target_dir/docs" ]]; then
        mkdir -p "$target_dir/docs"
        log_success "docs directory created."
    fi

    # Create basic README.md if it doesn't exist
    local readme_path="$target_dir/README.md"
    if [[ ! -f "$readme_path" ]];then
        log_debug "Creating README.md..."
        # Use project name from pyproject.toml if available, else default
        local readme_title="$project_name"
        if [[ -f "$target_dir/pyproject.toml" ]]; then
             local found_name
             found_name=$(grep -oP '(?<=^name\s*=\s*")[^"]+' "$target_dir/pyproject.toml" | head -1)
             if [[ -n "$found_name" ]]; then readme_title="$found_name"; fi
        fi
        cat > "$readme_path" << EOF
# $readme_title

A new Python project.

## Development

This project uses DHT (Development Helper Toolkit) and \`uv\` for environment and task management.

1.  **Setup Environment**:
    If you just cloned this project, run:
    \`\`\`bash
    ./DHT/dhtl.sh setup
    # or if DHT is in a different location, run its dhtl.sh setup path/to/this/project
    \`\`\`
    This will create a \`.venv\` with all dependencies.

2.  **Activate Environment**:
    \`\`\`bash
    source .venv/bin/activate
    \`\`\`

3.  **Run tasks using DHTL**:
    \`\`\`bash
    dhtl test      # Run project tests
    dhtl lint      # Lint code
    dhtl format    # Format code
    dhtl build     # Build package
    dhtl --help    # See all commands
    \`\`\`

See [DHT/README.md](DHT/README.md) for more details.

## Usage

\`\`\`python
# Example usage
\`\`\`
EOF
        log_success "README.md created."
    else
        log_info "README.md already exists."
    fi

    # Create basic pyproject.toml if it doesn't exist
    local pyproject_path="$target_dir/pyproject.toml"
    if [[ ! -f "$pyproject_path" ]]; then
        log_debug "Creating pyproject.toml..."
        cat > "$pyproject_path" << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$project_name"
version = "0.1.0" # Managed by bump-my-version or similar
description = "A new Python project: $project_name"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
readme = { file = "README.md", content-type = "text/markdown" }
requires-python = ">=3.9" # Match DHT's typical Python version
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License", # Choose your license
    "Operating System :: OS Independent",
]
dependencies = [
    # Add your project's core dependencies here
    # e.g., "requests>=2.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "black>=24.0", # Code formatter
    "ruff>=0.2.0",   # Linter & Formatter
    "mypy>=1.0.0",   # Type checker
    "tox",           # Test automation
    "uv",            # Explicitly list if project scripts depend on it
    "pre-commit",
    "bump-my-version",
    # Add other dev tools
]

[project.scripts]
# my-script = "$project_name.module:main_function"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
# include = ["$project_name*"] # Optional: if you want to be more specific
# exclude = ["$project_name.tests*"] # Optional

[tool.black]
line-length = 88 # Or your preferred length
# target-version = ["py39", "py310", "py311", "py312"] # Black auto-detects now

[tool.ruff]
line-length = 88 # Match black
target-version = "py39"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "RUF"] # Common selections
ignore = ["E501"] # Example: ignore line too long if handled by formatter

[tool.ruff.lint.isort]
known-first-party = ["$project_name"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true # Start with this, tighten later if needed
# Add other mypy settings
EOF
        log_success "pyproject.toml created."
    else
        log_info "pyproject.toml already exists."
    fi
    log_success "Project structure checked/created."
}

# Function to set up uv (install uv, create venv, run uv lock)
# Ensures uv is available and sets up the project's virtual environment.
setup_uv() {
    local target_dir="$1" # This is the project root
    local venv_path="$target_dir/.venv" # Standard venv location for the project
    local python_version_file="$target_dir/.python-version"

    log_info "Setting up uv for project at $target_dir..."

    # Check if uv is available globally or install it
    if ! command -v uv &> /dev/null; then
        log_info "uv command not found. Attempting to install uv globally..."
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            # Attempt to source profile to make uv available in current shell
            # shellcheck source=/dev/null
            source "$HOME/.cargo/env" || source "$HOME/.profile" || true
            if ! command -v uv &> /dev/null; then
                 log_error "Failed to install uv or make it available in PATH." $ERR_COMMAND_NOT_FOUND
                 log_error "Please install uv manually: https://astral.sh/docs/uv/install"
                 return $ERR_COMMAND_NOT_FOUND
            fi
            log_success "uv installed globally."
        else
            log_error "Failed to install uv globally using curl script." $ERR_GENERAL
            return $ERR_GENERAL
        fi
    else
        log_success "uv is already available."
    fi

    # Determine the Python interpreter to use for the venv
    local python_to_use
    local python_version_arg=""
    # Check for .python-version file
    if [[ -f "$python_version_file" ]]; then
        python_to_use=$(head -n 1 "$python_version_file" | xargs) # Read first line, trim whitespace
        if [[ -n "$python_to_use" ]]; then
            log_info "Found .python-version, requesting Python $python_to_use for venv."
            python_version_arg="-p $python_to_use"
        else
            log_warning ".python-version file is empty. Using default Python."
            python_to_use=$(get_python_cmd) # Use default python3/python
        fi
    else
        python_to_use=$(get_python_cmd) # Use default python3/python
    fi

    if [[ -z "$python_to_use" && -z "$python_version_arg" ]]; then
        log_error "Cannot find a suitable Python interpreter (python3 or python)." $ERR_ENVIRONMENT
        return $ERR_ENVIRONMENT
    fi
    log_info "Using Python interpreter specification: ${python_version_arg:-$python_to_use}"

    # Create a virtual environment if it doesn't exist
    if [[ ! -d "$venv_path" ]]; then
        log_info "Creating virtual environment at $venv_path using uv..."
        # Use -p to specify the Python interpreter uv should use to create the venv
        # shellcheck disable=SC2086 # We want word splitting for $python_version_arg
        # Use uv_create_venv from dhtl_uv.sh
        if uv_create_venv "$venv_path" "$python_to_use"; then # Pass python_to_use as specifier
            log_success "Virtual environment created at $venv_path."
        else
            log_error "Failed to create virtual environment at $venv_path using ${python_version_arg:-$python_to_use}." $ERR_ENVIRONMENT
            log_error "Ensure the requested Python version is available to uv or try without .python-version."
            return $ERR_ENVIRONMENT
        fi
    else
        log_info "Virtual environment already exists at $venv_path."
        # Optionally, could check if venv is compatible and offer to recreate
    fi

    # Check if pyproject.toml exists and run uv lock/sync
    local pyproject_path="$target_dir/pyproject.toml"
    if [[ -f "$pyproject_path" ]]; then
        log_info "Checking/creating uv.lock from $pyproject_path..."
        local original_dir
        original_dir=$(pwd)
        # Change to target directory because uv lock/sync work relative to CWD
        cd "$target_dir" || { log_error "Failed to cd to $target_dir" $ERR_GENERAL; return $ERR_GENERAL; }

        # Resolve the uv command to use (venv or global)
        local resolved_uv_cmd
        resolved_uv_cmd=$(get_uv_command "$venv_path")
        if [[ -z "$resolved_uv_cmd" ]]; then
            log_error "uv command not found after setup attempts. Cannot proceed with uv lock/sync."
            cd "$original_dir" || exit 1
            return $ERR_COMMAND_NOT_FOUND
        fi

        # Run uv lock to generate/update the lock file based on pyproject.toml
        if "$resolved_uv_cmd" lock --quiet; then
            log_success "uv.lock created/updated successfully."
        else
            log_warning "Failed to create/update uv.lock. Check pyproject.toml for errors."
            # This might not be fatal, but dependencies might not be locked correctly.
        fi

        # Run uv sync to ensure the venv matches the lock file (or pyproject.toml if lock failed)
        log_info "Syncing virtual environment with project dependencies..."
        if "$resolved_uv_cmd" sync --quiet -p "$venv_path/bin/python"; then # Specify python for sync
            log_success "Virtual environment synced with project dependencies."
        else
            log_error "Failed to sync virtual environment." $ERR_ENVIRONMENT
            cd "$original_dir" || exit 1 # Go back before failing
            return $ERR_ENVIRONMENT
        fi

        cd "$original_dir" || { log_error "Failed to cd back to $original_dir" $ERR_GENERAL; return $ERR_GENERAL; }
    else
        log_info "No pyproject.toml found in $target_dir. Skipping uv lock and sync."
    fi

    log_success "uv setup completed for $target_dir."
    return 0
}

# NOTE: check_and_instruct_secrets removed. Canonical version is in dhtl_secrets.sh

# Function to create a default tox.ini file if it doesn't exist
_create_default_tox_ini() {
    local target_dir="$1"
    local tox_ini_path="$target_dir/tox.ini"

    if [[ -f "$tox_ini_path" ]]; then
        log_info "$tox_ini_path already exists. Skipping creation."
        return 0
    fi

    # Determine project name for tox config
    local project_name_tox="my_project" # Default
    if [[ -f "$target_dir/pyproject.toml" ]]; then
        local found_name
        found_name=$(grep -oP '(?<=^name\s*=\s*")[^"]+' "$target_dir/pyproject.toml" | head -1 | tr '-' '_')
        if [[ -n "$found_name" ]]; then project_name_tox="$found_name"; fi
    else
        project_name_tox=$(basename "$target_dir" | tr '[:upper:]' '[:lower:]' | sed 's/[- ]/_/g' | sed 's/[^a-z0-9_]//g')
        if [[ -z "$project_name_tox" ]]; then project_name_tox="my_project"; fi
    fi
    local src_dir_tox="src/$project_name_tox"

    log_debug "Creating default $tox_ini_path..."
    # Use the content from the provided tox.ini file as a template
    # Use variables directly in the heredoc
    cat > "$tox_ini_path" << EOF
[tox]
envlist = py39, py310, py311, py312, py313
isolated_build = True
requires =
    tox-uv>=0.8.1
    tox>=4.11.4

[testenv]
deps =
    pytest>=7.3.1
    pytest-cov>=4.1.0
    pytest-timeout>=2.1.0
    pytest-xdist>=3.3.1
commands =
    pytest {posargs:tests} --cov=${project_name_tox} --cov-report=term --cov-report=xml --timeout=900

[testenv:lint]
deps =
    ruff>=0.3.0
    black>=23.3.0
commands =
    ruff check .
    ruff format --check .

[testenv:typecheck]
deps =
    mypy>=1.0.0
commands =
    mypy ${src_dir_tox}

[testenv:docs]
deps =
    mkdocs>=1.4.0
    mkdocs-material>=8.5.0
commands =
    mkdocs build
EOF

    log_success "Created default $tox_ini_path."
}

# Function to create default GitHub workflow files if they don't exist
_create_github_workflows() {
    local target_dir="$1"
    local workflows_dir="$target_dir/.github/workflows"
    local tests_workflow_path="$workflows_dir/tests.yml"
    local publish_workflow_path="$workflows_dir/publish.yml"

    if [[ -f "$tests_workflow_path" && -f "$publish_workflow_path" ]]; then
        log_info "GitHub workflow files already exist. Skipping creation."
        return 0
    fi

    log_info "Creating default GitHub workflow files in $workflows_dir..."
    mkdir -p "$workflows_dir"

    # --- tests.yml ---
    if [[ ! -f "$tests_workflow_path" ]]; then
        log_debug "Creating $tests_workflow_path..."
        cat > "$tests_workflow_path" << 'EOF'
# Basic GitHub Actions workflow for running tests using DHTL

name: Run Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch: # Allow manual triggering

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv globally (for setup)
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Set up DHT environment
      run: ./DHT/dhtl.sh setup
      shell: bash # Ensure bash is used for setup

    - name: Activate environment and Run Tests
      run: |
        source .venv/bin/activate # Adjust for Windows if needed later
        dhtl test --cov-report=xml # Generate XML coverage for Codecov
      shell: bash

    - name: Upload coverage reports to Codecov
      uses: codecov/codecov-action@v4
      with:
        token: ${{ secrets.CODECOV_TOKEN }} # Use CODECOV_TOKEN
        files: ./coverage_report/coverage.xml # Path to XML report
        fail_ci_if_error: true
EOF
        log_success "Created $tests_workflow_path."
    else
        log_info "$tests_workflow_path already exists."
    fi

    # --- publish.yml ---
    if [[ ! -f "$publish_workflow_path" ]]; then
        log_debug "Creating $publish_workflow_path..."
        cat > "$publish_workflow_path" << 'EOF'
# Basic GitHub Actions workflow for building and publishing to PyPI using DHTL

name: Publish to PyPI

on:
  release:
    types: [ published ] # Trigger when a GitHub release is published on GitHub
  workflow_dispatch: # Allow manual triggering

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: release # Optional: Use GitHub environments for protection rules
    permissions:
      id-token: write # Required for trusted publishing

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11" # Use a specific Python version for publishing

    - name: Install uv globally (for setup)
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Set up DHT environment and Build package
      run: |
        ./DHT/dhtl.sh setup
        source .venv/bin/activate
        dhtl build --no-checks # Build the package (skip local checks, assume tests passed)
      shell: bash

    - name: Publish package to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      # No API token needed here, uses OIDC trusted publishing
EOF
        log_success "Created $publish_workflow_path."
    else
        log_info "$publish_workflow_path already exists."
    fi

    log_success "Default GitHub workflows created/verified."
}
