# Changelog

All notable changes to DHT (Development Helper Toolkit) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-10

### Added
- Initial release of DHT as a Python CLI package
- Global `dhtl` command installation via pip
- Python CLI wrapper around existing bash scripts
- Support for PyPI distribution
- Comprehensive project type detection (Python, Node.js, Rust, Go, C++, Java, .NET)
- Universal build system with automatic detection
- GitHub Actions integration with act and actionlint
- Workflow management commands: `dhtl workflows lint/run/test`
- Container-based workflow execution
- UV package manager integration for fast Python dependency management
- Prefect-based task orchestration
- Tree-sitter parsing for code analysis
- Rich terminal output with progress indicators
- Cross-platform support (macOS, Linux, Windows via Git Bash/WSL)
- Deterministic environment reproduction
- GitHub CLI integration for repository operations
- Comprehensive test suite
- Project initialization and setup commands
- Linting, formatting, and testing workflows
- Version management and git integration

### Changed
- Migrated from pure bash implementation to Python CLI
- Restructured commands for better clarity (e.g., `dhtl act` → `dhtl workflows`)
- Improved error handling and user feedback
- Enhanced cross-platform compatibility

### Security
- Local-only container configurations
- Secure secrets management
- Isolated virtual environments

## [0.1.0] - 2024-05-01 (Pre-release)

### Added
- Initial bash-based implementation
- Basic command structure
- Virtual environment management
- Simple project detection

---

For detailed commit history, see: https://github.com/yourusername/dht/commits/main