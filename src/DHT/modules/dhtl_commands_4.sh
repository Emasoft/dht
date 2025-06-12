#!/bin/bash
# dhtl_commands_4.sh - Commands_4 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_4 functionality.
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

rebase_command() {
    echo "🔄 Resetting local repository to match GitHub head..."
    PROJECT_ROOT=$(find_project_root)
    
    # Process flags
    SKIP_BACKUP=false
    
    for arg in "$@"; do
        case "$arg" in
            --no-backup)
                SKIP_BACKUP=true
                ;;
        esac
    done
    
    # Create backup unless skipped
    if [ "$SKIP_BACKUP" = false ]; then
        echo "🔄 Creating backup of project directory..."
        BACKUP_NAME="project_backup_$(date +%Y%m%d_%H%M%S).zip"
        BACKUP_PATH="${HOME}/${BACKUP_NAME}"
        
        # Check if zip command is available
        if command -v zip &> /dev/null; then
            # Create zip backup excluding .git, __pycache__, and other large directories
            (cd "$PROJECT_ROOT" && zip -r "$BACKUP_PATH" . -x "*.git*" "*__pycache__*" "*.venv*" "*.coverage*" "*.pytest_cache*" "*.mypy_cache*" "*.ruff_cache*" "node_modules/*" "dist/*" "build/*")
            
            if [ $? -eq 0 ]; then
                echo "✅ Backup created at: $BACKUP_PATH"
            else
                echo "⚠️ Backup creation failed. Recommend aborting or using --no-backup."
                read -p "Continue anyway? (y/N): " CONTINUE
                if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
                    echo "❌ Operation aborted."
                    return 1
                fi
            fi
        else
            echo "⚠️ Zip command not found. Cannot create backup."
            read -p "Continue without backup? (y/N): " CONTINUE
            if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
                echo "❌ Operation aborted."
                return 1
            fi
        fi
    else
        echo "⚠️ Skipping backup as requested with --no-backup."
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        echo "❌ Git not found. Please install git."
        return 1
    fi
    
    # Check if we're in a git repository
    if ! git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree &> /dev/null; then
        echo "❌ Not in a git repository. Initialize a git repository first."
        return 1
    fi
    
    # Show git status before reset
    echo "📊 Current git status before reset:"
    git -C "$PROJECT_ROOT" status --short
    
    # Fetch from remote
    echo "🔄 Fetching latest changes from remote..."
    git -C "$PROJECT_ROOT" fetch origin
    
    # Find current branch
    CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current)
    if [ -z "$CURRENT_BRANCH" ]; then
        CURRENT_BRANCH="main"  # Default to main if not on a branch
    fi
    
    # Reset to origin/CURRENT_BRANCH
    echo "🔄 Resetting to origin/$CURRENT_BRANCH..."
    git -C "$PROJECT_ROOT" reset --hard "origin/$CURRENT_BRANCH"
    
    # Clean untracked files
    echo "🧹 Cleaning untracked files..."
    git -C "$PROJECT_ROOT" clean -fd
    
    # Show git status after reset
    echo "📊 Current git status after reset:"
    git -C "$PROJECT_ROOT" status
    
    echo "✅ Local repository has been reset to match origin/$CURRENT_BRANCH."
    echo "   If you had important untracked files, they can be found in the backup:"
    echo "   $BACKUP_PATH"
    
    return 0
}
