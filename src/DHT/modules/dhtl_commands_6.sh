#!/bin/bash
# dhtl_commands_6.sh - Commands_6 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_6 functionality.
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

create_project_backup() {
    local operation=$1  # The type of operation (rebase, commit, publish)
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="${HOME}/project_backup_${TIMESTAMP}.zip"
    
    echo "⚠️ CRITICAL: Creating backup of the entire project to protect untracked files..."
    echo "📦 Backup location: $BACKUP_PATH"
    
    # Make sure PROJECT_ROOT is set
    if [ -z "${PROJECT_ROOT}" ]; then
        echo "❌ Error: PROJECT_ROOT is not set. Cannot create backup."
        return 1
    fi
    
    # Create backup based on platform
    if [[ "$PLATFORM" == "macos" || "$PLATFORM" == "linux" ]]; then
        zip -r "$BACKUP_PATH" "$PROJECT_ROOT" || {
            echo "❌ Backup failed! Would you like to proceed with $operation anyway? (y/N): "
            read -r PROCEED_WITHOUT_BACKUP
            if [ "$PROCEED_WITHOUT_BACKUP" != "y" ] && [ "$PROCEED_WITHOUT_BACKUP" != "Y" ]; then
                echo "❌ $operation aborted."
                return 1
            fi
            return 2  # Indicate backup failed but operation should proceed
        }
    elif [[ "$PLATFORM" == "windows_unix" ]]; then
        # For Git Bash/WSL on Windows
        if command -v powershell &> /dev/null; then
            powershell -command "Compress-Archive -Path '$PROJECT_ROOT' -DestinationPath '$BACKUP_PATH'" || {
                echo "❌ Backup failed! Would you like to proceed with $operation anyway? (y/N): "
                read -r PROCEED_WITHOUT_BACKUP
                if [ "$PROCEED_WITHOUT_BACKUP" != "y" ] && [ "$PROCEED_WITHOUT_BACKUP" != "Y" ]; then
                    echo "❌ $operation aborted."
                    return 1
                fi
                return 2  # Indicate backup failed but operation should proceed
            }
        else
            # Fallback to zip if powershell not available
            zip -r "$BACKUP_PATH" "$PROJECT_ROOT" || {
                echo "❌ Backup failed! Would you like to proceed with $operation anyway? (y/N): "
                read -r PROCEED_WITHOUT_BACKUP
                if [ "$PROCEED_WITHOUT_BACKUP" != "y" ] && [ "$PROCEED_WITHOUT_BACKUP" != "Y" ]; then
                    echo "❌ $operation aborted."
                    return 1
                fi
                return 2  # Indicate backup failed but operation should proceed
            }
        fi
    else
        # Generic fallback
        zip -r "$BACKUP_PATH" "$PROJECT_ROOT" || {
            echo "❌ Backup failed! Would you like to proceed with $operation anyway? (y/N): "
            read -r PROCEED_WITHOUT_BACKUP
            if [ "$PROCEED_WITHOUT_BACKUP" != "y" ] && [ "$PROCEED_WITHOUT_BACKUP" != "Y" ]; then
                echo "❌ $operation aborted."
                return 1
            fi
            return 2  # Indicate backup failed but operation should proceed
        }
    fi
    
    echo "✅ Backup created successfully: $BACKUP_PATH"
    return 0
}

# NOTE: format_command removed. Canonical version is in dhtl_utils.sh
