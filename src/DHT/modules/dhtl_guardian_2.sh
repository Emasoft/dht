#!/bin/bash
# dhtl_guardian_2.sh - Guardian_2 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to guardian_2 functionality.
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

ensure_process_guardian() {
    if [[ "${USE_GUARDIAN:-true}" == "true" ]] && [[ -f "$DHT_DIR/process-guardian-watchdog.py" ]]; then
        # Make sure .process_guardian directory exists
        local guardian_internal_dir="$DHT_DIR/.process_guardian" # Renamed to avoid conflict with global GUARDIAN_DIR if any
        local pid_file="$guardian_internal_dir/process_watchdog.pid"
        
        mkdir -p "$guardian_internal_dir"
        
        # Determine Python command
        local current_python_cmd
        current_python_cmd=$(get_python_cmd) # Use canonical function
        if [[ -z "$current_python_cmd" ]]; then
            log_warning "Python not found. Cannot ensure psutil or start process guardian."
            return 1 # Cannot proceed without Python
        fi

        # Ensure psutil is installed for process guardian
        # VENV_DIR should be globally available from dhtl.sh
        if ! "$current_python_cmd" -c "import psutil" &>/dev/null; then
            log_info "Installing psutil for process guardian..."
            # Use uv_pip_install from dhtl_uv.sh (assumes dhtl_uv.sh is sourced)
            if function_exists "uv_pip_install"; then
                if ! uv_pip_install "psutil"; then
                    log_warning "Failed to install psutil using uv_pip_install."
                    log_warning "Process guardian may not work correctly."
                fi
            else
                log_warning "uv_pip_install function not found. Cannot install psutil automatically."
                log_warning "Process guardian may not work correctly."
            fi
        fi
        
        # Check if watchdog is already running
        if [ ! -f "$pid_file" ]; then
            log_info "Starting Process Guardian Watchdog..."
            # Use run_with_guardian to start the watchdog, though it's a light process
            # For simplicity here, directly calling python. If issues, wrap with run_with_guardian.
            "$current_python_cmd" "$DHT_DIR/process-guardian-watchdog.py" start &>/dev/null &
            sleep 1  # Give it a moment to start and create PID file
            
            # Verify guardian started successfully
            if [ ! -f "$pid_file" ]; then
                log_warning "Process Guardian PID file not found after start attempt."
                log_warning "Guardian may not have started properly. Continuing without active guardian checks for this command."
            else
                log_debug "Process Guardian Watchdog started (PID file: $pid_file)."
            fi
        else
            log_debug "Process Guardian Watchdog already running (PID file: $pid_file)."
        fi
    elif [[ "${USE_GUARDIAN:-true}" == "true" ]]; then
        log_debug "Process guardian watchdog script not found at $DHT_DIR/process-guardian-watchdog.py. Guardian disabled."
    else
        log_debug "Process guardian is disabled by USE_GUARDIAN=false."
    fi
}
