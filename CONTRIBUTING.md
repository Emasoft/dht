# Contributing to DHT

Thank you for your interest in contributing to the Development Helper Toolkit (DHT)!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/dht.git
   cd dht
   ```
3. Set up development environment:
   ```bash
   ./dhtl.py init
   ```

## Development Workflow

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Test your changes:
   ```bash
   dhtl test_dht  # Run DHT's test suite
   dhtl test      # Run project tests
   ```

4. Lint and format:
   ```bash
   dhtl lint --fix
   dhtl format
   ```

### Submitting Changes

1. Commit with descriptive message:
   ```bash
   git commit -m "feat: add new feature X"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request

## Coding Standards

### Python Code
- Follow PEP 8
- Use type hints
- Add docstrings (Google style)
- Maximum line length: 120 characters

### Shell Scripts
- Use shellcheck for validation
- Add error handling
- Document complex logic
- Maintain cross-platform compatibility

### Documentation
- Update README.md for new features
- Add/update docstrings
- Include examples
- Update CHANGELOG.md

## Testing

### Running Tests
```bash
# All tests
dhtl test_dht

# Python tests only
pytest DHT/tests/

# Shell script tests
./DHT/tests/test_dhtl_basic.sh
```

### Writing Tests
- Use pytest for Python code
- Include unit and integration tests
- Test edge cases
- Maintain high coverage

## Project Structure

```
dht/
├── dhtl.py            # Python CLI entry point
├── dhtl_cli.py        # PyPI wrapper (for global install)
├── DHT/
│   ├── modules/       # Core functionality
│   │   ├── *.py      # Python modules
│   │   └── *.sh      # Shell modules
│   └── tests/         # Test suite
├── pyproject.toml     # Package configuration
└── README.md          # Documentation
```

## Types of Contributions

### Bug Reports
- Use GitHub Issues
- Include reproduction steps
- Specify environment details
- Add error messages/logs

### Feature Requests
- Discuss in GitHub Issues first
- Explain use case
- Consider implementation approach

### Code Contributions
- Fix bugs
- Add features
- Improve documentation
- Add tests
- Enhance performance

## Communication

- GitHub Issues: Bug reports and feature requests
- Pull Requests: Code contributions
- Discussions: General questions and ideas

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
