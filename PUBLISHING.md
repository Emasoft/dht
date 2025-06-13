# Publishing DHT to PyPI

This guide explains how to publish DHT (Development Helper Toolkit) to the Python Package Index (PyPI).

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. Test PyPI account (optional): https://test.pypi.org/account/register/
3. Install build tools:
   ```bash
   pip install build twine
   ```

## Pre-Publishing Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update version in `dhtl_cli.py`
- [ ] Update version in `DHT/__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Run tests: `dhtl test_dht`
- [ ] Ensure all files are committed

## Building the Package

1. Clean previous builds:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

2. Build the package:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/dht-toolkit-1.0.0.tar.gz` (source distribution)
   - `dist/dht_toolkit-1.0.0-py3-none-any.whl` (wheel)

## Testing on Test PyPI (Recommended)

1. Upload to Test PyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```

2. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dht-toolkit
   ```

3. Verify the command works:
   ```bash
   dhtl --version
   ```

## Publishing to PyPI

1. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

2. Verify on PyPI: https://pypi.org/project/dht-toolkit/

3. Test installation:
   ```bash
   pip install dht-toolkit
   ```

## Post-Publishing

1. Create a GitHub release with the same version
2. Update documentation
3. Announce the release

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Troubleshooting

### Common Issues

1. **Name already taken**: The name `dht` might be taken. We use `dht-toolkit` instead.

2. **Missing files**: Ensure `MANIFEST.in` includes all necessary files.

3. **Import errors**: Test the package locally with:
   ```bash
   pip install -e .
   ```

4. **Platform-specific issues**: The bash scripts need to be included properly.

## Versioning

Follow semantic versioning:
- MAJOR.MINOR.PATCH
- 1.0.0 - Initial release
- 1.0.1 - Bug fixes
- 1.1.0 - New features (backward compatible)
- 2.0.0 - Breaking changes