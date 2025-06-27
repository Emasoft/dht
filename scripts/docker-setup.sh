#!/usr/bin/env bash
# Docker setup script for DHT
# This script helps users get started with Docker in DHT

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Main script
print_info "DHT Docker Setup Script"
print_info "======================"
echo

# Check for Docker or Podman
CONTAINER_RUNTIME=""
if check_command docker; then
    CONTAINER_RUNTIME="docker"
    print_success "Docker found"
elif check_command podman; then
    CONTAINER_RUNTIME="podman"
    print_success "Podman found"
else
    print_error "Neither Docker nor Podman found!"
    echo "Please install one of the following:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Podman: https://podman.io/getting-started/installation"
    exit 1
fi

# Check if runtime is running
print_info "Checking if $CONTAINER_RUNTIME is running..."
if $CONTAINER_RUNTIME version &> /dev/null; then
    print_success "$CONTAINER_RUNTIME is running"
else
    print_error "$CONTAINER_RUNTIME is not running!"
    if [[ "$CONTAINER_RUNTIME" == "docker" ]]; then
        echo "Please start Docker Desktop or the Docker daemon"
    else
        echo "Please start the Podman service"
    fi
    exit 1
fi

# Check for docker-compose
print_info "Checking for docker-compose..."
COMPOSE_COMMAND=""
if [[ "$CONTAINER_RUNTIME" == "docker" ]]; then
    if docker compose version &> /dev/null; then
        COMPOSE_COMMAND="docker compose"
        print_success "Docker Compose (v2) found"
    elif check_command docker-compose; then
        COMPOSE_COMMAND="docker-compose"
        print_success "docker-compose found"
    else
        print_warning "docker-compose not found"
        echo "Install with: pip install docker-compose"
    fi
elif check_command podman-compose; then
    COMPOSE_COMMAND="podman-compose"
    print_success "podman-compose found"
else
    print_warning "podman-compose not found"
    echo "Install with: pip install podman-compose"
fi

# Build images
echo
print_info "Building Docker images..."
echo "This may take a few minutes on first run..."

# Build runtime image
print_info "Building runtime image..."
if $CONTAINER_RUNTIME build -f Dockerfile --target runtime -t dht:runtime .; then
    print_success "Runtime image built successfully"
else
    print_error "Failed to build runtime image"
    exit 1
fi

# Build test image
print_info "Building test image..."
if $CONTAINER_RUNTIME build -f Dockerfile --target test-runner -t dht:test .; then
    print_success "Test image built successfully"
else
    print_error "Failed to build test image"
    exit 1
fi

# Build development image
print_info "Building development image..."
if $CONTAINER_RUNTIME build -f Dockerfile --target development -t dht:dev .; then
    print_success "Development image built successfully"
else
    print_error "Failed to build development image"
    exit 1
fi

# Test the setup
echo
print_info "Testing Docker setup..."
if $CONTAINER_RUNTIME run --rm dht:runtime dhtl --version; then
    print_success "Docker setup is working!"
else
    print_error "Docker setup test failed"
    exit 1
fi

# Show available commands
echo
print_success "Docker setup complete!"
echo
echo "Available commands:"
echo "  dhtl docker build    - Build Docker images"
echo "  dhtl docker test     - Run tests in Docker"
echo "  dhtl docker lint     - Run linting in Docker"
echo "  dhtl docker shell    - Start development shell"
echo "  dhtl docker workflow - Run GitHub workflows locally"
echo
echo "Or use docker-compose:"
if [[ -n "$COMPOSE_COMMAND" ]]; then
    echo "  $COMPOSE_COMMAND up         - Start all services"
    echo "  $COMPOSE_COMMAND run dht-test - Run tests"
    echo "  $COMPOSE_COMMAND run dht-dev  - Start dev environment"
else
    echo "  (Install docker-compose or podman-compose for compose support)"
fi
echo
echo "See docs/DOCKER.md for more information"
