#!/bin/bash
# dhtl_commands_5.sh - Commands_5 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_5 functionality.
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

coverage_command() {
    log_info "📊 Running test coverage on project..."
    PROJECT_ROOT=$(find_project_root)
    # DHT_DIR is global

    local coverage_script="$DHT_DIR/run_coverage.sh"
    
    # Check if the run_coverage.sh script exists
    if [ ! -f "$coverage_script" ]; then
        log_error "Coverage script not found: $coverage_script" $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi
    
    # Make the script executable if it's not already
    if [ ! -x "$coverage_script" ]; then
        chmod +x "$coverage_script"
    fi
    
    # Ensure process guardian is running (if not disabled by --no-guardian)
    if [[ "${USE_GUARDIAN:-true}" == "true" ]]; then
        ensure_process_guardian # Assumes this function handles starting if necessary
    fi
    
    log_info "Coverage arguments: $*"
    
    # Run the coverage script with guardian protection
    run_with_guardian "$coverage_script" "script" "$DEFAULT_MEM_LIMIT" "$@"
    local coverage_result=$?
    
    if [ $coverage_result -ne 0 ]; then
        log_error "Coverage operation failed with exit code $coverage_result." $coverage_result
        return $coverage_result
    else
        log_success "Coverage operation completed successfully."
        
        # Check if HTML report was generated
        if [ -d "$PROJECT_ROOT/coverage_report" ] && [ -f "$PROJECT_ROOT/coverage_report/index.html" ]; then
            log_info "HTML Coverage report generated in: $PROJECT_ROOT/coverage_report"
            
            # Try to open the coverage report if available
            if command -v open &> /dev/null; then
                log_info "Opening coverage report..."
                open "$PROJECT_ROOT/coverage_report/index.html"
            elif command -v xdg-open &> /dev/null; then
                log_info "Opening coverage report..."
                xdg-open "$PROJECT_ROOT/coverage_report/index.html"
            elif command -v explorer &> /dev/null; then # For Windows Git Bash / WSL
                log_info "Opening coverage report..."
                # explorer needs a Windows-style path
                local report_path_win
                report_path_win=$(normalize_path "$PROJECT_ROOT/coverage_report/index.html")
                explorer.exe "$report_path_win"
            else
                log_info "Coverage report available at: $PROJECT_ROOT/coverage_report/index.html"
            fi
        fi
        
        # Recommend viewing on Codecov
        log_info "View online coverage reports at: https://codecov.io/gh/Emasoft/enchant_cli"
        
        return 0
    fi
}

publish_command() {
    log_info "🚀 Publishing to GitHub..."
    PROJECT_ROOT=$(find_project_root)
    
    # Process flags
    local skip_tests=false
    local skip_linters=false
    local skip_backup=false
    local publish_args=() # Store non-flag arguments for the script
    
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-linters)
                skip_linters=true
                shift
                ;;
            --no-backup)
                skip_backup=true
                shift
                ;;
            *)
                # Assume other args are for the publish script itself
                publish_args+=("$1")
                shift
                ;;
        esac
    done
    
    # Create backup unless skipped
    if [ "$skip_backup" = false ]; then
        if ! create_project_backup "publish"; then
            # create_project_backup handles user prompt if backup fails.
            # If it returns non-zero, it means user aborted or backup failed and user chose not to proceed.
            # However, create_project_backup returns 2 if backup failed but user wants to proceed.
            local backup_status=$?
            if [[ $backup_status -eq 1 ]]; then # User aborted
                log_error "Publish aborted due to backup failure." $ERR_GENERAL
                return $ERR_GENERAL
            elif [[ $backup_status -ne 0 && $backup_status -ne 2 ]]; then # Unexpected error
                log_error "Backup failed with unexpected status $backup_status. Aborting publish." $ERR_GENERAL
                return $ERR_GENERAL
            fi
            # If status is 0 (success) or 2 (failed but proceed), continue.
        fi
    else
        log_warning "Skipping backup as requested with --no-backup."
    fi
    
    # Check if publish_to_github.sh exists
    local publish_script_path=""
    if [ -f "$PROJECT_ROOT/publish_to_github.sh" ]; then
        publish_script_path="$PROJECT_ROOT/publish_to_github.sh"
    elif [ -f "$DHT_DIR/publish_to_github.sh" ]; then # Check in DHT_DIR as well
        publish_script_path="$DHT_DIR/publish_to_github.sh"
    else
        log_error "Could not find publish_to_github.sh script in project root or DHT directory." $ERR_FILE_NOT_FOUND
        return $ERR_FILE_NOT_FOUND
    fi
    
    # Prepare publish command with flags for the script
    local script_exec_args=()
    if [ "$skip_tests" = true ]; then
        script_exec_args+=("--skip-tests")
    fi
    if [ "$skip_linters" = true ]; then
        script_exec_args+=("--skip-linters")
    fi
    script_exec_args+=("${publish_args[@]}") # Add any other passthrough args

    # Run the publish script
    log_info "Running publish script: $publish_script_path ${script_exec_args[*]}"
    ensure_process_guardian # Assumes this function handles starting if necessary
    run_with_guardian "bash" "script" "$DEFAULT_MEM_LIMIT" "$publish_script_path" "${script_exec_args[@]}"
    
    local publish_result=$?
    if [ $publish_result -ne 0 ]; then
        log_error "Publish failed with exit code $publish_result." $publish_result
        return $publish_result
    else
        log_success "Project published to GitHub successfully."
        return 0
    fi
}
