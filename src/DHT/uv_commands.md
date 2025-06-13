# `uv` Commands and Workflows Reference

This project uses `uv` (from Astral) for Python packaging and project management.
`uv` is an extremely fast Python package installer and resolver, written in Rust,
and is designed as a drop-in replacement for `pip` and `pip-tools`.

DHT integrates `uv` for:
- Creating and managing virtual environments (`dhtl setup`, `dhtl init`).
- Installing and syncing dependencies (`dhtl setup`, `dhtl init`).
- Potentially running tools (`dhtl uv tool run ...` if `dhtl_uv.sh` implements it).

## Common `uv` Commands (for manual use if needed)

You can also use `uv` directly if the virtual environment is activated.

### Virtual Environment Management

```bash
# Create a virtual environment (DHT typically uses .venv)
# Specify python version if needed, e.g., --python 3.11
uv venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Dependency Management

(Assuming `pyproject.toml` is your source of truth)

```bash
# Install dependencies from pyproject.toml (equivalent to pip install -e .)
uv pip install -e .

# Install dev dependencies defined in [project.optional-dependencies]
uv pip install -e ".[dev]"

# Add a new dependency
# 1. Manually add 'package-name' to pyproject.toml [project.dependencies]
# 2. Install it into the venv:
uv pip install package-name
# 3. Update the lock file (optional but recommended)
uv lock

# Sync environment with lock file (installs based on lock)
uv sync --locked

# Update all dependencies in lock file
uv lock --upgrade

# Update specific packages in lock file
uv lock --upgrade-package package-name --upgrade-package another-package
```

### Other Useful Commands

```bash
# Clean the global uv cache
uv cache clean

# List installed packages in the current venv
uv pip list

# Show details about an installed package
uv pip show package-name
```

For more information, refer to the official `uv` documentation:
[https://astral.sh/docs/uv](https://astral.sh/docs/uv)
