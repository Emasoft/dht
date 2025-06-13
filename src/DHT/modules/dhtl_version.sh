#!/bin/bash
# Version Management Module
#
# This module provides functions for version management.
# It includes commands for creating git tags and handling version bumping.

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

# Function to create a Git tag
tag_command() {
    echo "🏷️ Creating Git tag..."
    
    # Process arguments
    local tag_name=""
    local tag_message=""
    local annotated=true
    local force=false
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name|-n)
                tag_name="$2"
                shift 2
                ;;
            --message|-m)
                tag_message="$2"
                shift 2
                ;;
            --lightweight|-l)
                annotated=false
                shift
                ;;
            --force|-f)
                force=true
                shift
                ;;
            *)
                # If not a known option, assume it's the tag name
                if [[ -z "$tag_name" ]]; then
                    tag_name="$1"
                    shift
                else
                    echo "❌ Unknown option: $1"
                    echo "Usage: dhtl tag [--name|-n <tag_name>] [--message|-m <message>] [--lightweight|-l] [--force|-f]"
                    return 1
                fi
                ;;
        esac
    done
    
    # Check if Git is available
    if ! command -v git &> /dev/null; then
        echo "❌ Git not found. Please install Git."
        return 1
    fi
    
    # Try to extract version from package files if tag_name is not provided
    if [[ -z "$tag_name" ]]; then
        # Try from pyproject.toml
        if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
            echo "🔄 Extracting version from pyproject.toml..."
            # Multiple patterns to match various version formats in pyproject.toml
            version=$(grep -E "version\s*=\s*[\"']([0-9]+\.[0-9]+\.[0-9]+)[\"']" "$PROJECT_ROOT/pyproject.toml" | sed -E 's/.*version\s*=\s*["\x27]([0-9\.]+)["\x27].*/\1/' | head -1)
            if [[ -n "$version" ]]; then
                tag_name="v$version"
                echo "📌 Using version from pyproject.toml: $version"
            fi
        fi
        
        # Try from package.json
        if [[ -z "$tag_name" && -f "$PROJECT_ROOT/package.json" ]]; then
            echo "🔄 Extracting version from package.json..."
            version=$(grep -E "\"version\":\s*\"([0-9]+\.[0-9]+\.[0-9]+)\"" "$PROJECT_ROOT/package.json" | sed -E 's/.*"version":\s*"([0-9\.]+)".*/\1/' | head -1)
            if [[ -n "$version" ]]; then
                tag_name="v$version"
                echo "📌 Using version from package.json: $version"
            fi
        fi
        
        # Try from __init__.py
        if [[ -z "$tag_name" ]]; then
            echo "🔄 Searching for version in Python files..."
            # Find files that might contain a version string
            for init_file in $(find "$PROJECT_ROOT" -name "__init__.py" | grep -v ".venv"); do
                version=$(grep -E "__version__\s*=\s*[\"']([0-9]+\.[0-9]+\.[0-9]+)[\"']" "$init_file" | sed -E 's/.*__version__\s*=\s*["\x27]([0-9\.]+)["\x27].*/\1/' | head -1)
                if [[ -n "$version" ]]; then
                    tag_name="v$version"
                    echo "📌 Using version from $init_file: $version"
                    break
                fi
            done
        fi
    fi
    
    # If still no tag_name, ask the user
    if [[ -z "$tag_name" ]]; then
        echo "❌ Could not determine tag name automatically."
        echo "Please specify a tag name with --name or as the first argument."
        return 1
    fi
    
    # Set up tag message if not provided
    if [[ -z "$tag_message" && "$annotated" = true ]]; then
        tag_message="Release $tag_name"
    fi
    
    # Create the tag
    local force_flag=""
    if [[ "$force" = true ]]; then
        force_flag="--force"
    fi
    
    if [[ "$annotated" = true ]]; then
        echo "🔄 Creating annotated tag $tag_name with message: $tag_message"
        git -C "$PROJECT_ROOT" tag $force_flag -a "$tag_name" -m "$tag_message"
    else
        echo "🔄 Creating lightweight tag $tag_name"
        git -C "$PROJECT_ROOT" tag $force_flag "$tag_name"
    fi
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Tag $tag_name created successfully."
        echo "📢 Use 'git push origin $tag_name' to push the tag to the remote repository."
        return 0
    else
        echo "❌ Failed to create tag $tag_name."
        return 1
    fi
}

# Function to bump version using bump-my-version
bump_command() {
    echo "🔄 Bumping version..."
    
    # Process arguments
    local part="minor"  # Default to minor version bump
    local dry_run=false
    local commit=true
    local tag=true
    local allow_dirty=true
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            major|minor|patch|pre|dev|release|final)
                part="$1"
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --no-commit)
                commit=false
                shift
                ;;
            --no-tag)
                tag=false
                shift
                ;;
            --no-dirty)
                allow_dirty=false
                shift
                ;;
            *)
                echo "❌ Unknown option: $1"
                echo "Usage: dhtl bump [major|minor|patch|pre|dev|release|final] [--dry-run] [--no-commit] [--no-tag] [--no-dirty]"
                return 1
                ;;
        esac
    done
    
    # Find uv command
    local uv_cmd=""
    if [[ -f "$PROJECT_ROOT/.venv/bin/uv" ]]; then
        uv_cmd="$PROJECT_ROOT/.venv/bin/uv"
    elif command -v uv &> /dev/null; then
        uv_cmd="uv"
    fi
    
    # Check if bump-my-version is available via uv
    if [[ -n "$uv_cmd" ]]; then
        echo "🔄 Using bump-my-version via uv tool run..."
        
        # Build the command arguments
        local cmd_args=("bump" "$part")
        if [[ "$dry_run" = true ]]; then
            cmd_args+=("--dry-run")
        fi
        if [[ "$commit" = true ]]; then
            cmd_args+=("--commit")
        else
            cmd_args+=("--no-commit")
        fi
        if [[ "$tag" = true ]]; then
            cmd_args+=("--tag")
        else
            cmd_args+=("--no-tag")
        fi
        if [[ "$allow_dirty" = true ]]; then
            cmd_args+=("--allow-dirty")
        fi
        
        # Run bump-my-version
        "$uv_cmd" tool run bump-my-version "${cmd_args[@]}"
        exit_code=$?
        
        # Report result
        if [[ $exit_code -ne 0 ]]; then
            echo "❌ Version bumping failed."
            return 1
        fi
        
        # Always sync dependencies after version bump to ensure consistency
        if [[ -f "$PROJECT_ROOT/uv.lock" && "$dry_run" = false ]]; then
            echo "🔄 Syncing dependencies after version bump..."
            "$uv_cmd" sync || echo "⚠️ Warning: uv sync failed after version bump"
        fi
        
        return 0
    fi
    
    # Check if bump2version or bumpversion is available directly
    if command -v bump2version &> /dev/null; then
        echo "🔄 Using bump2version directly..."
        
        # Build the command arguments
        local cmd_args=("$part")
        if [[ "$dry_run" = true ]]; then
            cmd_args+=("--dry-run")
        fi
        if [[ "$commit" = true ]]; then
            cmd_args+=("--commit")
        else
            cmd_args+=("--no-commit")
        fi
        if [[ "$tag" = true ]]; then
            cmd_args+=("--tag")
        else
            cmd_args+=("--no-tag")
        fi
        if [[ "$allow_dirty" = true ]]; then
            cmd_args+=("--allow-dirty")
        fi
        
        # Run bump2version
        bump2version "${cmd_args[@]}"
        exit_code=$?
        
        # Report result
        if [[ $exit_code -ne 0 ]]; then
            echo "❌ Version bumping failed."
            return 1
        fi
        
        return 0
    elif command -v bumpversion &> /dev/null; then
        echo "🔄 Using bumpversion directly..."
        
        # Build the command arguments
        local cmd_args=("$part")
        if [[ "$dry_run" = true ]]; then
            cmd_args+=("--dry-run")
        fi
        if [[ "$commit" = true ]]; then
            cmd_args+=("--commit")
        else
            cmd_args+=("--no-commit")
        fi
        if [[ "$tag" = true ]]; then
            cmd_args+=("--tag")
        else
            cmd_args+=("--no-tag")
        fi
        if [[ "$allow_dirty" = true ]]; then
            cmd_args+=("--allow-dirty")
        fi
        
        # Run bumpversion
        bumpversion "${cmd_args[@]}"
        exit_code=$?
        
        # Report result
        if [[ $exit_code -ne 0 ]]; then
            echo "❌ Version bumping failed."
            return 1
        fi
        
        return 0
    fi
    
    # If we get here, no version bumping tool is available
    echo "❌ No version bumping tool found. Please install uv and bump-my-version:"
    echo "   dhtl uv tool install bump-my-version"
    return 1
}