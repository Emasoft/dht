#!/bin/bash
# Guardian Command Module
#
# Implements the guardian command with status/start/stop functionality
# for the DHT Process Guardian.

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

# Guardian command function
guardian_command() {
    # Parse subcommand from arguments
    local subcommand="${1:-status}"

    case "$subcommand" in
        status)
            guardian_status
            ;;
        start)
            start_guardian
            ;;
        stop)
            stop_guardian
            ;;
        restart)
            stop_guardian
            start_guardian
            ;;
        help)
            show_guardian_help
            ;;
        *)
            log_error "Unknown guardian subcommand: $subcommand" $ERR_INVALID_ARGUMENT
            show_guardian_help
            return $ERR_INVALID_ARGUMENT
            ;;
    esac
}

# Function to check guardian status
guardian_status() {
    log_info "Checking Process Guardian status..."
    
    # Define guardian files
    local guardian_internal_dir="$DHT_DIR/.process_guardian"
    local pid_file="$guardian_internal_dir/process_watchdog.pid"
    
    # Check if guardian directory exists
    if [ ! -d "$guardian_internal_dir" ]; then
        log_info "Process Guardian not initialized."
        log_info "You can start it with: dhtl guardian start"
        return 0
    fi
    
    # Check if PID file exists
    if [ ! -f "$pid_file" ]; then
        log_info "Process Guardian is not running."
        log_info "You can start it with: dhtl guardian start"
        return 0
    fi
    
    # Read PID from file
    local current_pid
    current_pid=$(cat "$pid_file")
    
    # Check if process is running
    if ps -p "$current_pid" > /dev/null 2>&1; then
        log_success "Process Guardian is running with PID: $current_pid"
        
        # Get additional information if available
        if [ -f "$guardian_internal_dir/active_nodes.txt" ]; then
            local active_count
            active_count=$(wc -l < "$guardian_internal_dir/active_nodes.txt" 2>/dev/null || echo "0")
            log_info "Active processes: $active_count"
        fi
        
        if [ -f "$guardian_internal_dir/active_py_scripts.txt" ]; then
            local py_scripts_count
            py_scripts_count=$(wc -l < "$guardian_internal_dir/active_py_scripts.txt" 2>/dev/null || echo "0")
            log_info "Active Python scripts: $py_scripts_count"
        fi
        
        return 0
    else
        log_warning "Process Guardian PID file exists but process is not running."
        log_info "Cleaning up stale PID file..."
        rm -f "$pid_file"
        log_info "You can start the guardian with: dhtl guardian start"
        return 1
    fi
}

# Function to start the guardian
start_guardian() {
    log_info "Starting Process Guardian..."
    
    local guardian_internal_dir="$DHT_DIR/.process_guardian"
    local pid_file="$guardian_internal_dir/process_watchdog.pid"
    
    # Create guardian directory if it doesn't exist
    mkdir -p "$guardian_internal_dir"
    
    if [ -f "$pid_file" ]; then
        local current_pid
        current_pid=$(cat "$pid_file")
        if ps -p "$current_pid" > /dev/null 2>&1; then
            log_success "Process Guardian is already running with PID: $current_pid"
            return 0
        else
            log_info "Removing stale PID file..."
            rm -f "$pid_file"
        fi
    fi
    
    # Check for the watchdog script
    local watchdog_script_path="$DHT_DIR/process-guardian-watchdog.py"
    if [ ! -f "$watchdog_script_path" ]; then
        log_error "Process Guardian watchdog script not found: $watchdog_script_path" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi
    
    # Ensure Python is available
    local current_python_cmd
    current_python_cmd=$(get_python_cmd)
    if [[ -z "$current_python_cmd" ]]; then
        log_error "Python not found. Cannot start Process Guardian." $ERR_COMMAND_NOT_FOUND
        return $ERR_COMMAND_NOT_FOUND
    fi
    
    # Ensure psutil is installed
    if ! "$current_python_cmd" -c "import psutil" &>/dev/null; then
        log_info "Installing psutil for Process Guardian..."
        # Use uv_pip_install from dhtl_uv.sh (assumes dhtl_uv.sh is sourced)
        if function_exists "uv_pip_install"; then
            if ! uv_pip_install "psutil"; then
                log_warning "Failed to install psutil using uv_pip_install."
                log_warning "Process Guardian may not work correctly."
            fi
        else
            log_warning "uv_pip_install function not found. Cannot install psutil automatically."
            log_warning "Process Guardian may not work correctly."
        fi
    fi
    
    # Start the watchdog in the background
    "$current_python_cmd" "$watchdog_script_path" start &>/dev/null &
    sleep 1 # Give it a moment to start and write PID file
    
    # Check if it started successfully
    if [ -f "$pid_file" ]; then
        local new_pid
        new_pid=$(cat "$pid_file")
        if ps -p "$new_pid" > /dev/null 2>&1; then
            log_success "Process Guardian started successfully with PID: $new_pid"
            return 0
        fi
    fi
    
    log_error "Failed to start Process Guardian." $ERR_UNEXPECTED
    return $ERR_UNEXPECTED
}

# Function to stop the guardian
stop_guardian() {
    log_info "Stopping Process Guardian..."
    
    local guardian_internal_dir="$DHT_DIR/.process_guardian"
    local pid_file="$guardian_internal_dir/process_watchdog.pid"
    
    if [ ! -f "$pid_file" ]; then
        log_info "Process Guardian is not running."
        return 0
    fi
    
    local current_pid
    current_pid=$(cat "$pid_file")
    if ! ps -p "$current_pid" > /dev/null 2>&1; then
        log_info "Removing stale PID file..."
        rm -f "$pid_file"
        log_info "Process Guardian is not running."
        return 0
    fi
    
    # Try graceful shutdown first
    log_info "Sending SIGTERM to Process Guardian (PID: $current_pid)..."
    kill -TERM "$current_pid" 2>/dev/null
    
    # Wait a bit for it to shut down
    sleep 2
    
    # Check if it's still running
    if ps -p "$current_pid" > /dev/null 2>&1; then
        log_info "Process Guardian still running, sending SIGKILL..."
        kill -KILL "$current_pid" 2>/dev/null
        sleep 1
    fi
    
    # Final check and cleanup
    if ps -p "$current_pid" > /dev/null 2>&1; then
        log_warning "Failed to kill Process Guardian (PID: $current_pid)."
        return 1
    else
        log_success "Process Guardian stopped successfully."
        rm -f "$pid_file"
        return 0
    fi
}

# Show help for guardian command
show_guardian_help() {
    # Using direct echo for help text is standard and fine.
    echo "Process Guardian Command Usage:"
    echo "  dhtl guardian [subcommand]"
    echo ""
    echo "Subcommands:"
    echo "  status   - Show the current status of the Process Guardian"
    echo "  start    - Start the Process Guardian"
    echo "  stop     - Stop the Process Guardian"
    echo "  restart  - Restart the Process Guardian"
    echo "  help     - Show this help message"
}
