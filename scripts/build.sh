#!/usr/bin/env bash
# Build script for DHT using uv

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building DHT toolkit with uv...${NC}"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Ensure we're in a virtual environment
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate || {
        echo -e "${RED}Failed to activate virtual environment. Run 'uv venv' first.${NC}"
        exit 1
    }
fi

# Sync dependencies
echo -e "${YELLOW}Syncing dependencies...${NC}"
uv sync --all-extras

# Run tests before building
echo -e "${YELLOW}Running tests...${NC}"
uv run pytest tests/ -v || {
    echo -e "${RED}Tests failed. Fix tests before building.${NC}"
    exit 1
}

# Build both sdist and wheel with constraints
echo -e "${YELLOW}Building distributions...${NC}"
uv build --sdist --wheel --build-constraint build-constraints.txt

# Verify the build
echo -e "${YELLOW}Verifying build...${NC}"
# Check for wheel files
wheel_count=$(find dist -name "*.whl" 2>/dev/null | wc -l)
sdist_count=$(find dist -name "*.tar.gz" 2>/dev/null | wc -l)

if [[ $wheel_count -gt 0 ]] && [[ $sdist_count -gt 0 ]]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "${GREEN}Distributions created in dist/:${NC}"
    ls -la dist/
else
    echo -e "${RED}Build failed - distributions not created${NC}"
    exit 1
fi

# Optional: Check wheel contents
echo -e "${YELLOW}Checking wheel contents...${NC}"
for wheel in dist/*.whl; do
    if [[ -f "$wheel" ]]; then
        unzip -l "$wheel" | head -20
        break
    fi
done

echo -e "${GREEN}Build complete!${NC}"
