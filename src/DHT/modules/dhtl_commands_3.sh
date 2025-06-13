#!/bin/bash
# dhtl_commands_3.sh - Commands_3 module for DHT Launcher
#
# Generated on: 2025-05-02 23:31:20
# Generator: extract_dhtl_modules.py
#
# This file contains functions related to commands_3 functionality.
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

commit_command() {
    echo "💾 Committing changes to git..."
    PROJECT_ROOT=$(find_project_root)
    
    # Process flags and message
    SKIP_CHECKS=false
    SKIP_BACKUP=false
    COMMIT_MSG=""
    
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --no-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --no-backup)
                SKIP_BACKUP=true
                shift
                ;;
            *)
                # Assume anything else is part of the commit message
                if [ -z "$COMMIT_MSG" ]; then
                    COMMIT_MSG="$1"
                else
                    COMMIT_MSG="$COMMIT_MSG $1"
                fi
                shift
                ;;
        esac
    done
    
    # Check if commit message was provided
    if [ -z "$COMMIT_MSG" ]; then
        echo "❌ No commit message provided."
        echo "Usage: ./dhtl.sh commit \"Your commit message\" [--no-checks] [--no-backup]"
        return 1
    fi
    
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
                echo "⚠️ Backup creation failed. Consider using --no-backup if you don't need a backup."
                echo "   Continuing with commit operation..."
            fi
        else
            echo "⚠️ Zip command not found. Cannot create backup."
            echo "   Consider installing zip or using --no-backup."
            echo "   Continuing with commit operation..."
        fi
    else
        echo "⚠️ Skipping backup as requested with --no-backup."
    fi
    
    # Run linters first unless skipped
    if [ "$SKIP_CHECKS" = false ]; then
        echo "🔍 Running linters before commit..."
        # Call the canonical lint_command from utils.sh
        if function_exists "lint_command"; then
            lint_command
            if [ $? -ne 0 ]; then
                echo "❌ Linting failed. Fix the issues before committing."
                echo "   Run with --no-checks to skip linting."
                return 1
            fi
        else
            log_warning "lint_command not found. Skipping lint checks."
        fi
    else
        echo "⚠️ Skipping linting checks as requested."
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
    
    # Show git status
    echo "📊 Current git status:"
    git -C "$PROJECT_ROOT" status --short
    
    # Commit changes
    echo "🔄 Committing changes with message: $COMMIT_MSG"
    if [ "$SKIP_CHECKS" = true ]; then
        # Add [skip-linters] tag to commit message if checks were skipped
        COMMIT_MSG="$COMMIT_MSG [skip-linters]"
    fi
    
    # Add all changes and commit
    git -C "$PROJECT_ROOT" add .
    git -C "$PROJECT_ROOT" commit -m "$COMMIT_MSG"
    
    COMMIT_RESULT=$?
    if [ $COMMIT_RESULT -ne 0 ]; then
        echo "❌ Commit failed with exit code $COMMIT_RESULT."
        return $COMMIT_RESULT
    else
        echo "✅ Changes committed successfully."
        echo "📊 Current git status:"
        git -C "$PROJECT_ROOT" status
        return 0
    fi
}

# NOTE: lint_command removed. Canonical version is in dhtl_utils.sh
