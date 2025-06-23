#!/usr/bin/env bash
# Verify that important project files haven't been overwritten by gitleaks

set -euo pipefail

echo "Verifying project files haven't been overwritten..."

# Check if README.md contains gitleaks content
if grep -q "gitleaks is a SAST tool" README.md 2>/dev/null; then
    echo "❌ ERROR: README.md has been overwritten with gitleaks README!"
    echo "This indicates gitleaks was extracted in the project root."
    exit 1
fi

# Check if LICENSE contains gitleaks license
if grep -q "gitleaks" LICENSE 2>/dev/null && grep -q "Zachary Rice" LICENSE 2>/dev/null; then
    echo "❌ ERROR: LICENSE has been overwritten with gitleaks LICENSE!"
    echo "This indicates gitleaks was extracted in the project root."
    exit 1
fi

# Check for other gitleaks files that shouldn't be in project root
GITLEAKS_FILES=("gitleaks" "gitleaks.exe" "gitleaks-darwin-amd64" "gitleaks-darwin-arm64" "gitleaks-linux-amd64" "gitleaks-linux-arm64")
for file in "${GITLEAKS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "❌ ERROR: Found gitleaks binary '$file' in project root!"
        echo "Gitleaks should be installed in ~/.local/bin or /usr/local/bin, not in project directory."
        exit 1
    fi
done

echo "✅ Project files are intact - no overwriting detected"
