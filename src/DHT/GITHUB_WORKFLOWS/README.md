# GitHub Workflow Templates

This directory contains template GitHub workflow files that DHT can generate for projects.

## Important Note

These files contain template placeholders like `{REPO_NAME}` and `{REPO_OWNER_OR_ORGANIZATION}` that are meant to be replaced when DHT generates workflows for a specific project.

**These are NOT the actual workflows for DHT itself.** DHT's own workflows are located in `.github/workflows/`.

## Template Files

- `check_pypi_version.yml` - Template for checking PyPI package versions
- `docker-build-test.yml` - Template for Docker build and test workflows
- `docker-release.yml` - Template for Docker release workflows
- `pages.yml` - Template for GitHub Pages deployment
- `pre-commit.yml` - Template for pre-commit checks
- `release.yml` - Template for release workflows
- `ubuntu-tests.yml` - Template for Ubuntu test workflows
- `windows-tests.yml` - Template for Windows test workflows
- `windows_check_pypi_version.yml` - Template for Windows PyPI version checks

## Usage

When DHT initializes a new project or sets up CI/CD, it can use these templates to generate appropriate GitHub workflows with the placeholders replaced by actual project values.
