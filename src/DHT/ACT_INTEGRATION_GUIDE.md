# DHT Act Integration Guide

## Overview

DHT integrates [act](https://github.com/nektos/act) to enable local testing of GitHub Actions workflows. This allows developers to:

- **Test workflows locally** before pushing to GitHub
- **Debug CI/CD pipelines** without commit-push cycles
- **Run workflows in isolated containers** for reproducibility
- **Save time and resources** by catching issues early

## Architecture

### Components

1. **act_integration.py** - Core Python module that manages act
2. **dhtl_commands_act.sh** - Shell command interface for DHT
3. **Container integration** - Works with Podman/Docker for isolation
4. **gh extension support** - Integrates with GitHub CLI

### How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   dhtl act  │────▶│ act_integration│────▶│  Container  │
│  (command)  │     │   (Python)     │     │  (Podman)   │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                      │
                            ▼                      ▼
                    ┌──────────────┐     ┌─────────────┐
                    │.github/      │     │  GitHub     │
                    │ workflows/   │     │  Actions    │
                    └──────────────┘     │  Runner     │
                                        └─────────────┘
```

## Installation

### 1. Install Container Runtime (Recommended: Podman)

**macOS:**
```bash
brew install podman
```

**Linux:**
```bash
sudo apt-get install podman  # Debian/Ubuntu
sudo dnf install podman       # Fedora/RHEL
```

### 2. Install act

**Using gh extension (Recommended):**
```bash
gh extension install https://github.com/nektos/gh-act
```

**Standalone installation:**
```bash
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Using DHT helper:**
```bash
dhtl install-act
```

## Usage

### Basic Commands

```bash
# List all workflows
dhtl act --list

# Run push event (default)
dhtl act

# Run specific event
dhtl act pull_request

# Run specific job
dhtl act -j test

# Setup only (create config files)
dhtl act --setup-only
```

### Advanced Usage

```bash
# Test all workflows
dhtl workflow test

# Run with specific event
dhtl act -e release

# CI/CD test alias
dhtl cicd-test
```

## Configuration

DHT creates project-specific act configuration in `.venv/dht-act/`:

```
.venv/
└── dht-act/
    ├── .actrc         # Act configuration
    ├── .secrets       # Local secrets (git-ignored)
    ├── .env          # Environment variables
    └── rootless/     # Container configs
        ├── containers.conf
        └── storage.conf
```

### .actrc Configuration

```bash
# Container options
--container-architecture linux/amd64
--platform ubuntu-latest
--pull=false

# Use local project directory
--bind

# Container runtime (auto-detected)
--container-daemon-socket unix:///path/to/socket

# Runner image
--image catthehacker/ubuntu:act-latest
```

### Secrets Management

Edit `.venv/dht-act/.secrets`:
```bash
GITHUB_TOKEN=your_personal_access_token
NPM_TOKEN=your_npm_token
DOCKER_USERNAME=your_username
DOCKER_PASSWORD=your_password
```

**Important:** Never commit secrets! They're automatically git-ignored.

## Container Isolation

### Rootless Containers (Podman)

DHT prefers Podman for rootless container execution:

- No daemon required
- Runs as regular user
- Isolated storage in project
- No system-wide configuration

### Docker Support

If Docker is available, DHT will use it with appropriate isolation:

- Bind mounts limited to project directory
- Separate network namespace
- Resource limits applied

## Integration with DHT Build

When you run `dhtl build`, DHT automatically:

1. Detects GitHub workflows
2. Suggests testing with act
3. Shows workflow summary

Example output:
```
✅ Build completed successfully!
⏱️  Total time: 45.3s
📦 Artifacts: 2

🎬 GitHub Actions detected!
Found 3 workflow(s):
  • Python Tests (python-tests.yml)
  • Release (release.yml)
  • CodeQL Analysis (codeql.yml)

💡 Tip: Use dhtl act to test workflows locally
```

## Workflow Examples

### Python Project
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install -e .
          pytest
```

Test locally:
```bash
dhtl act push -j test
```

### Multi-Platform Build
```yaml
name: Build
on: [push]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - run: make build
```

Test specific platform:
```bash
dhtl act push -j build -P ubuntu-latest
```

## Troubleshooting

### Common Issues

1. **"No container runtime found"**
   - Install Podman or Docker
   - Ensure daemon is running (Docker only)

2. **"Permission denied"**
   - Use Podman for rootless operation
   - Check socket permissions

3. **"Workflow failed locally but works on GitHub"**
   - Check secrets configuration
   - Verify network access
   - Some GitHub-specific features may not work locally

### Debug Mode

```bash
# Verbose output
dhtl act -v

# Keep containers after run
dhtl act --reuse

# Shell into container
dhtl act -j test --container-options "--entrypoint /bin/bash"
```

## Best Practices

1. **Test before push**: Always run `dhtl act` before pushing
2. **Use secrets file**: Store credentials in `.venv/dht-act/.secrets`
3. **Version control workflows**: Keep `.github/workflows/` in git
4. **Rootless when possible**: Use Podman for better security
5. **Cache dependencies**: Use act's caching for faster runs

## Benefits

### For Developers
- ⚡ Fast feedback loop
- 🐛 Debug workflows locally
- 💰 Save CI/CD minutes
- 🔒 Test with production-like environment

### For Teams
- 📋 Standardized testing process
- 🔄 Reproducible CI/CD
- 🛡️ Catch issues before production
- 📚 Self-documenting workflows

## Limitations

Some GitHub Actions features don't work locally:
- GitHub Pages deployment
- Release creation
- Issue/PR operations
- Repository secrets (use local secrets)
- Some GitHub-hosted runner tools

## Future Enhancements

Planned features:
- Matrix build visualization
- Workflow dependency graphs
- Performance profiling
- Cache management UI
- Integration with DHT task system

## Summary

DHT's act integration brings GitHub Actions to your local development environment, enabling:

- **Immediate feedback** on workflow changes
- **Cost savings** on CI/CD minutes
- **Debugging capabilities** for complex workflows
- **Consistent environment** across local and remote

Run `dhtl act` to start testing your workflows locally!
