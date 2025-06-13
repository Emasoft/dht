#!/bin/bash
# dhtl_environment_3.sh - Environment_3 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to environment_3 functionality.
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

detect_active_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "$VIRTUAL_ENV"
    elif [[ -n "$CONDA_PREFIX" ]]; then
        echo "$CONDA_PREFIX"
    else
        echo ""
    fi
}

# Canonical version of detect_platform, enhanced from dhtl_platform.sh
detect_platform() {
    local os_name
    if [[ "$OSTYPE" == "darwin"* ]]; then
        os_name="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os_name="linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # These are Unix-like environments on Windows
        os_name="windows_unix"
    elif [[ "$OSTYPE" == "win32" ]]; then # For native Windows (e.g. cmd.exe, powershell)
        os_name="windows"
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        os_name="bsd" # Could be more specific if needed (freebsd, openbsd, netbsd)
    else
        os_name="unknown"
    fi
    echo "$os_name"
}

# --- Platform helper functions (from dhtl_platform.sh) ---
detect_architecture() {
    local arch=""
    if command -v uname &> /dev/null; then
        arch=$(uname -m)
    elif [[ "$PLATFORM" == "windows" ]]; then # Native Windows
        if [[ "$PROCESSOR_ARCHITECTURE" == "AMD64" || "$PROCESSOR_ARCHITEW6432" == "AMD64" ]]; then
            arch="x86_64"
        elif [[ "$PROCESSOR_ARCHITECTURE" == "x86" && -z "$PROCESSOR_ARCHITEW6432" ]]; then # Check if PROCESSOR_ARCHITEW6432 is empty for 32-bit on 64-bit OS
            arch="i386"
        elif [[ "$PROCESSOR_ARCHITECTURE" == "ARM64" ]]; then
            arch="aarch64"
        else
            arch="unknown"
        fi
    else
        arch="unknown"
    fi
    echo "$arch"
}

is_macos() { [[ "$PLATFORM" == "macos" ]]; return $?; }
is_linux() { [[ "$PLATFORM" == "linux" ]]; return $?; }
is_windows() { [[ "$PLATFORM" == "windows" || "$PLATFORM" == "windows_unix" ]]; return $?; }
is_bsd() { [[ "$PLATFORM" == "bsd" ]]; return $?; } # Generic BSD
is_unix() { [[ "$PLATFORM" == "macos" || "$PLATFORM" == "linux" || "$PLATFORM" == "bsd" || "$PLATFORM" == "windows_unix" ]]; return $?; }
is_arm() { local arch; arch=$(detect_architecture); [[ "$arch" == "arm"* || "$arch" == "aarch"* ]]; return $?; }
is_x86() { local arch; arch=$(detect_architecture); [[ "$arch" == "x86"* || "$arch" == "i386" || "$arch" == "i686" || "$arch" == "amd64" ]]; return $?; }

normalize_path() {
    local path="$1"
    if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then # Native Windows
        echo "$path" | sed 's|/|\\|g'
    else # Unix-like systems (including windows_unix)
        echo "$path" | sed 's|\\|/|g'
    fi
}
get_path_separator() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo "\\"; else echo "/"; fi; }
get_line_ending() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo -ne "\r\n"; else echo -ne "\n"; fi; } # Use echo -ne for literal newlines
get_executable_extension() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo ".exe"; else echo ""; fi; }
get_script_extension() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo ".bat"; else echo ".sh"; fi; }
get_home_directory() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo "$USERPROFILE"; else echo "$HOME"; fi; }
get_temp_directory() { if is_windows && [[ "$PLATFORM" != "windows_unix" ]]; then echo "$TEMP"; else echo "/tmp"; fi; }
# --- End Platform helper functions ---


# Initialize environment and setup
dhtl_init_environment() {
    # Detect platform
    PLATFORM=$(detect_platform) # Uses the enhanced version now

    # Find project root
    PROJECT_ROOT=$(find_project_root) # From dhtl_environment_1.sh

    # Set up the virtual environment if needed - SKIP THIS IF SKIP_ENV_SETUP IS SET
    # setup_uv (from dhtl_init.sh) is the canonical way to create/manage venv
    if [[ -z "$DHTL_SKIP_ENV_SETUP" ]] && [ ! -d "$DEFAULT_VENV_DIR" ] && [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        log_info "Virtual environment not found or incomplete. Running 'dhtl setup' logic..."
        if function_exists "setup_uv"; then
            setup_uv "$PROJECT_ROOT" # setup_uv handles venv creation
        else
            log_warning "setup_uv function not found. Cannot automatically create venv."
        fi
    fi

    # Start the process guardian if not disabled
    if [[ -z "$DISABLE_GUARDIAN" || "$DISABLE_GUARDIAN" == "0" ]]; then
        if function_exists "ensure_process_guardian_running"; then
            ensure_process_guardian_running # From dhtl_guardian_X.sh
        else
            log_warning "ensure_process_guardian_running function not found."
        fi
    fi
}

# Perform cleanup when the script exits
dhtl_cleanup() {
    # Clean up any temporary files or processes
    if [[ -z "$DISABLE_GUARDIAN" || "$DISABLE_GUARDIAN" == "0" ]]; then
        # Note: We don't stop the process guardian here because it's meant to run persistently
        # But we could add any other cleanup tasks needed
        :
    fi

    # Print a message in verbose mode
    if [[ -z "$QUIET_MODE" || "$QUIET_MODE" == "0" ]]; then
        log_success "Cleanup completed"
    fi
}

# Function to execute the requested command
# This is the canonical command dispatcher.
dhtl_execute_command() {
    local cmd="$1"
    shift

    case "$cmd" in
        help) show_help; return $? ;;
        lint) lint_command "$@"; return $? ;;
        format) format_command "$@"; return $? ;;
        test) test_command "$@"; return $? ;;
        coverage) coverage_command "$@"; return $? ;;
        build) build_command "$@"; return $? ;;
        commit) commit_command "$@"; return $? ;;
        publish) publish_command "$@"; return $? ;;
        venv) # This command might be removed or call setup_uv
            if function_exists "setup_uv"; then
                log_info "Recreating virtual environment using 'setup_uv'..."
                setup_uv "$PROJECT_ROOT" # Pass project root
                return $?
            else
                log_error "setup_uv function not found. Cannot manage venv." $ERR_COMMAND_NOT_FOUND
                return $ERR_COMMAND_NOT_FOUND
            fi
            ;;
        install_tools) install_tools_command "$@"; return $? ;;
        setup_project) setup_project_command "$@"; return $? ;; # From dhtl_environment_1.sh
        workflows) workflows_command "$@"; return $? ;;
        act) act_command "$@"; return $? ;; # Legacy, redirects to workflows
        cicd-test) cicd_test_command "$@"; return $? ;; # Alias for workflows run
        rebase) rebase_command "$@"; return $? ;;
        node) node_command "$@"; return $? ;; # From dhtl_commands_standalone.sh
        python) python_command "$@"; return $? ;; # From dhtl_commands_standalone.sh
        run) run_command "$@"; return $? ;; # From dhtl_commands_standalone.sh
        script) script_command "$@"; return $? ;; # From dhtl_commands_standalone.sh
        guardian) guardian_command "$@"; return $? ;;
        setup) setup_command "$@"; return $? ;; # From dhtl_init.sh
        init) init_command "$@"; return $? ;; # From dhtl_init.sh
        clean) clean_command "$@"; return $? ;;
        env) env_command "$@"; return $? ;; # From dhtl_environment_2.sh
        diagnostics) diagnostics_command "$@"; return $? ;; # From dhtl_diagnostics.sh
        restore) restore_command "$@"; return $? ;; # From dhtl_commands_1.sh (restore_dependencies)
        selfcheck) selfcheck_command "$@"; return $? ;; # Placeholder, needs implementation
        test_dht) test_dht_command "$@"; return $? ;; # From dhtl_test.sh
        verify_dht) verify_dht_command "$@"; return $? ;; # From dhtl_test.sh
        tag) tag_command "$@"; return $? ;; # From dhtl_version.sh
        bump) bump_command "$@"; return $? ;; # From dhtl_version.sh
        clone) clone_command "$@"; return $? ;; # From dhtl_github.sh
        fork) fork_command "$@"; return $? ;; # From dhtl_github.sh
        *)
            log_error "Unknown command: $cmd" $ERR_INVALID_ARGUMENT
            show_help
            return $ERR_INVALID_ARGUMENT
            ;;
    esac
}
