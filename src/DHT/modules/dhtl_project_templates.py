#!/usr/bin/env python3
"""
dhtl_project_templates.py - Project template content for dhtl commands  This module contains templates for project files like .gitignore, LICENSE, etc.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtl_project_templates.py - Project template content for dhtl commands

This module contains templates for project files like .gitignore, LICENSE, etc.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtl_commands_init.py to reduce file size
# - Contains project file templates (.gitignore, LICENSE, CI/CD)
#

from datetime import datetime


def get_python_gitignore() -> str:
    """Get standard Python .gitignore content."""
    return """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
ENV/
env/
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv (commented out as we create .python-version)
# .python-version

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# UV
uv.lock
"""


def get_mit_license(author_name: str | None = None) -> str:
    """Get MIT license template."""
    year = datetime.now().year
    author = author_name or "Your Name"

    return f"""MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def get_apache_license(author_name: str | None = None) -> str:
    """Get Apache 2.0 license template."""
    year = datetime.now().year
    author = author_name or "Your Name"

    return f"""Copyright {year} {author}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


def get_github_actions_ci() -> str:
    """Get GitHub Actions CI/CD workflow template."""
    return """name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v2

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        uv sync --dev

    - name: Lint with ruff
      run: |
        uv run ruff check .
        uv run ruff format --check .

    - name: Type check with mypy
      run: |
        uv run mypy .

    - name: Test with pytest
      run: |
        uv run pytest -v --cov=./ --cov-report=xml
"""


__all__ = ["get_python_gitignore", "get_mit_license", "get_apache_license", "get_github_actions_ci"]
