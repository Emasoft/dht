# Deploy Project in Container - Design Document

## Overview
The `dhtl deploy_project_in_container` command will automatically build and deploy any Python project into a Docker container with a properly configured UV environment, allowing users to run the application and tests from within the container.

## Architecture

### Command Flow
```
deploy_project_in_container
├── Pre-flight checks
│   ├── Docker availability check
│   ├── Docker daemon status
│   └── Project validation
├── Project analysis
│   ├── Detect project type (web app, CLI, library)
│   ├── Find main entry points
│   ├── Detect test frameworks (pytest, playwright, puppeteer)
│   ├── Identify Python version requirements
│   └── Analyze dependencies
├── Dockerfile generation
│   ├── Select appropriate base image
│   ├── Configure UV installation
│   ├── Set up project structure
│   ├── Install dependencies
│   └── Configure entry points
├── Container operations
│   ├── Build Docker image
│   ├── Create and start container
│   ├── Execute application (if applicable)
│   ├── Run test suites
│   └── Collect results
└── Results presentation
    ├── Format test results as table
    ├── Display application output
    └── Provide container access info
```

### Key Components

#### 1. Docker Manager (`docker_manager.py`)
- Check Docker installation and daemon status
- Build images with progress tracking
- Manage container lifecycle
- Handle volume mounts and port mappings
- Stream logs and output

#### 2. Dockerfile Generator (`dockerfile_generator.py`)
- Generate Dockerfiles based on project analysis
- Support multiple Python versions
- Configure UV environment
- Handle different project types (web, CLI, library)
- Set up test environments

#### 3. Container Test Runner (`container_test_runner.py`)
- Execute pytest with coverage
- Run Playwright tests
- Run Puppeteer tests
- Capture and parse results
- Format output as tables

#### 4. Deploy Command (`deploy_command.py`)
- Main command implementation
- Orchestrate the deployment flow
- Handle errors gracefully
- Provide user feedback

### Dockerfile Template Structure
```dockerfile
# Base image with Python
FROM python:3.x-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies with UV
RUN uv sync --all-extras

# Build project
RUN uv build

# Expose ports (if web app)
EXPOSE 8000

# Set entry point
CMD ["uv", "run", "python", "main.py"]
```

### Test Execution Strategy

#### pytest
```bash
docker exec container_name uv run pytest -v --tb=short --color=yes
```

#### Playwright
```bash
# Install browsers in container
docker exec container_name uv run playwright install chromium
# Run tests
docker exec container_name uv run pytest tests/e2e -v
```

#### Puppeteer
```bash
docker exec container_name uv run python -m pytest tests/puppeteer -v
```

### Results Formatting

Test results will be displayed as a formatted table:
```
┌─────────────────────────┬────────┬──────────┬─────────┐
│ Test Suite              │ Passed │ Failed   │ Skipped │
├─────────────────────────┼────────┼──────────┼─────────┤
│ Unit Tests (pytest)     │ 45     │ 2        │ 3       │
│ E2E Tests (Playwright)  │ 12     │ 0        │ 1       │
│ UI Tests (Puppeteer)    │ 8      │ 1        │ 0       │
└─────────────────────────┴────────┴──────────┴─────────┘
```

### Error Handling

1. **Docker Not Installed**
   - Provide installation instructions for the platform
   - Suggest alternative deployment methods

2. **Build Failures**
   - Display build logs
   - Suggest fixes for common issues
   - Provide debugging commands

3. **Test Failures**
   - Show detailed test output
   - Provide access to container for debugging
   - Suggest running tests locally first

### Security Considerations

- Use non-root user in container
- Limit container resources
- Use specific Python versions (not latest)
- Scan for vulnerabilities
- Isolate test environments

### Implementation Plan

1. **Phase 1: Core Infrastructure**
   - Docker detection and validation
   - Basic Dockerfile generation
   - Simple container management

2. **Phase 2: Project Analysis**
   - Detect project types
   - Find entry points
   - Analyze dependencies

3. **Phase 3: Test Integration**
   - pytest support
   - Playwright support
   - Puppeteer support

4. **Phase 4: Results & UX**
   - Format results as tables
   - Progress indicators
   - Error messages

### Usage Examples

```bash
# Deploy and run application
dhtl deploy_project_in_container

# Deploy and run specific tests
dhtl deploy_project_in_container --run-tests

# Deploy with specific Python version
dhtl deploy_project_in_container --python 3.11

# Deploy and keep container running
dhtl deploy_project_in_container --detach
```
