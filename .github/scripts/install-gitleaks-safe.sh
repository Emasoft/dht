#!/usr/bin/env bash
# Safe gitleaks installation script that prevents overwriting project files
# This script MUST extract gitleaks in /tmp to avoid overwriting README.md and LICENSE

set -euo pipefail

GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.23.1}"
TEMP_DIR="/tmp/gitleaks-install-$$"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

echo "Installing gitleaks v${GITLEAKS_VERSION} safely in temporary directory..."

# Create temporary directory for extraction
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Detect OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
    x86_64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Download URL
URL="https://github.com/zricethezav/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${OS}_${ARCH}.tar.gz"

echo "Downloading from: $URL"
echo "Extracting in: $TEMP_DIR (NOT in project directory)"

# Download and extract in temp directory
if command -v curl >/dev/null 2>&1; then
    curl -sSL "$URL" | tar xz
elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$URL" | tar xz
else
    echo "Error: Neither curl nor wget found"
    exit 1
fi

# Verify we got the binary
if [ ! -f "gitleaks" ]; then
    echo "Error: gitleaks binary not found after extraction"
    ls -la
    exit 1
fi

# Create install directory if needed
mkdir -p "$INSTALL_DIR"

# Move only the gitleaks binary to the install location
mv gitleaks "$INSTALL_DIR/gitleaks"
chmod +x "$INSTALL_DIR/gitleaks"

# Clean up temp directory
cd /
rm -rf "$TEMP_DIR"

echo "✅ Gitleaks installed safely to: $INSTALL_DIR/gitleaks"
echo "✅ No project files were overwritten"

# Verify installation
if "$INSTALL_DIR/gitleaks" version >/dev/null 2>&1; then
    echo "✅ Installation verified: $("$INSTALL_DIR/gitleaks" version)"
else
    echo "❌ Installation verification failed"
    exit 1
fi
