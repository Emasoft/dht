# DHT Docker Integration

DHT provides comprehensive Docker support for running tests, workflows, and development environments in isolated containers. This ensures consistent behavior across different platforms and makes it easy to reproduce issues.

## Features

- **Multi-stage Dockerfile** optimized for different use cases (runtime, testing, development)
- **uv integration** for fast dependency installation in containers
- **Docker Compose** configuration for easy service management
- **VS Code Dev Container** support for consistent development environments
- **GitHub Actions** integration for CI/CD in containers
- **Support for both Docker and Podman**

## Quick Start

### Using DHT Commands

```bash
# Build Docker images
dhtl docker build

# Run tests in Docker
dhtl docker test

# Run linting in Docker
dhtl docker lint

# Start interactive shell
dhtl docker shell

# Run GitHub workflows locally
dhtl docker workflow push
```

### Using Docker Compose

```bash
# Start all services
docker compose up

# Run tests
docker compose run --rm dht-test

# Start development environment
docker compose run --rm dht-dev

# Run linting
docker compose run --rm dht-lint
```

### Using Make

```bash
# Build all images
make docker-build

# Run tests
make docker-test

# Start development shell
make docker-shell

# Clean up
make docker-clean
```

## Docker Images

DHT provides multiple Docker images optimized for different use cases:

### Runtime Image (`dht:runtime`)
- Minimal production image
- Contains only runtime dependencies
- Used for running DHT commands in production

### Test Runner Image (`dht:test`)
- Based on runtime image
- Includes test dependencies (pytest, coverage)
- Optimized for running tests in CI/CD

### Development Image (`dht:dev`)
- Includes all development dependencies
- Contains development tools (vim, git, etc.)
- Used for development and debugging

## Docker Compose Services

### `dht` - Runtime Service
Basic service for running DHT commands.

```bash
docker compose run --rm dht dhtl build
```

### `dht-dev` - Development Service
Interactive development environment with all tools.

```bash
docker compose run --rm dht-dev
# or
make compose-dev
```

### `dht-test` - Test Runner Service
Automated test execution with coverage reporting.

```bash
docker compose run --rm dht-test
# or
make compose-test
```

### `dht-lint` - Linting Service
Code quality checks and linting.

```bash
docker compose run --rm dht-lint
```

### `dht-workflows` - Workflow Runner Service
Run GitHub Actions locally using act.

```bash
docker compose run --rm dht-workflows
```

## VS Code Dev Container

DHT includes a dev container configuration for VS Code:

1. Install the "Dev Containers" extension in VS Code
2. Open the DHT project folder
3. Click "Reopen in Container" when prompted
4. VS Code will build and start the development container

The dev container includes:
- Python with all DHT dependencies
- Pre-configured linting and formatting
- Git and GitHub CLI
- All VS Code extensions for Python development

## Environment Variables

### Build-time Variables
- `UV_COMPILE_BYTECODE=1` - Enable bytecode compilation for faster startup

### Runtime Variables
- `DHT_ENV` - Environment name (development, production, ci)
- `DHT_TEST_MODE=1` - Enable test mode
- `DHT_IN_DOCKER=1` - Indicates running inside Docker
- `UV_CACHE_DIR` - uv cache directory location

## Volumes

### Named Volumes
- `dht-cache` - Shared cache for uv and other tools
- `dht-test-results` - Test results and coverage reports

### Bind Mounts
- `./:/workspace` - Project files (read-only in production)
- `./:/app` - Project files (read-write in development)
- `/var/run/docker.sock` - Docker socket for Docker-in-Docker

## Advanced Usage

### Building with Custom Tags

```bash
# Build with custom tag
dhtl docker build --target runtime --tag myregistry/dht:latest

# Build without cache
docker build --no-cache -f Dockerfile --target runtime -t dht:runtime .
```

### Running with Custom Volumes

```bash
# Run with additional volume mounts
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.aws:/root/.aws:ro \
  dht:runtime \
  dhtl build
```

### Using with CI/CD

The Docker images can be used in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests in Docker
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace \
      -e CI=true \
      dht:test
```

### Docker-in-Docker Support

The containers support Docker-in-Docker for running workflows:

```bash
# Mount Docker socket
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  dht:runtime \
  dhtl docker test
```

## Troubleshooting

### Permission Issues
If you encounter permission issues, ensure the files are owned by the correct user:

```bash
# Fix permissions
docker compose run --rm --user root dht-dev chown -R dhtuser:dhtuser /app
```

### Cache Issues
Clear the Docker cache if you encounter stale dependency issues:

```bash
# Remove cache volume
docker volume rm dht-cache

# Rebuild without cache
make docker-build-nocache
```

### Platform-Specific Issues

#### macOS
- Ensure Docker Desktop is running
- File system performance can be improved with `:delegated` or `:cached` mount options

#### Windows
- Use WSL2 backend for better performance
- Ensure line endings are LF, not CRLF

#### Linux
- Add your user to the docker group: `sudo usermod -aG docker $USER`
- For rootless Podman, ensure subuid/subgid are configured

## Security Considerations

- The default user is non-root (`dhtuser`) for security
- Secrets should be passed via environment variables, not built into images
- Use `.dockerignore` to prevent sensitive files from being included
- For production, consider using multi-stage builds to minimize attack surface

## Performance Optimization

- uv caches are shared between builds for faster dependency installation
- Bytecode compilation is enabled for faster Python startup
- Layer caching is optimized in the Dockerfile
- Use BuildKit for improved build performance: `DOCKER_BUILDKIT=1 docker build ...`

## Integration with DHT Features

The Docker setup integrates seamlessly with DHT features:

- **Testing**: Full pytest suite with coverage reporting
- **Linting**: All linters (ruff, mypy, shellcheck, yamllint) are available
- **Workflows**: Act is installed for running GitHub Actions locally
- **Building**: uv is used for fast, deterministic builds
- **Development**: Full development environment with all tools

## Contributing

When adding new dependencies or tools:

1. Update the appropriate Dockerfile stage
2. Update docker-compose.yml if new services are needed
3. Document any new environment variables
4. Test the build on multiple platforms
5. Update this documentation
