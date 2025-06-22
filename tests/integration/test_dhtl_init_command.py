#!/usr/bin/env python3
"""
Integration tests for dhtl init command.  Tests the dhtl init command using real UV and following TDD principles.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Integration tests for dhtl init command.

Tests the dhtl init command using real UV and following TDD principles.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial test suite for dhtl init command
# - Tests real UV init functionality
# - Follows UV documentation best practices
# - No mocking - uses real commands
#

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below


class TestDhtlInitCommand:
    """Test dhtl init command implementation."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def uv_available(self) -> bool:
        """Check if UV is available."""
        return shutil.which("uv") is not None

    def test_init_new_project_basic(self, temp_dir, uv_available):
        """Test initializing a new Python project with basic settings."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "test-project"
        project_path = temp_dir / project_name

        # Run dhtl init command
        # Note: The command doesn't exist yet - TDD approach
        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(path=str(project_path), name=project_name, python="3.11")

        # Verify the command succeeded
        assert result["success"] is True
        # Normalize path for comparison (macOS has /var -> /private/var symlink)
        expected_path = Path(result["path"]).resolve()
        assert result["message"] == f"Initialized project '{project_name}' at {expected_path}"

        # Verify project structure
        assert project_path.exists()
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".python-version").exists()
        assert (project_path / ".gitignore").exists()

        # Verify pyproject.toml content
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        assert pyproject["project"]["name"] == project_name
        assert "version" in pyproject["project"]
        assert pyproject["project"]["requires-python"] == ">=3.11"

        # Verify .python-version content
        python_version = (project_path / ".python-version").read_text().strip()
        assert python_version == "3.11"

    def test_init_with_package_structure(self, temp_dir, uv_available):
        """Test initializing a project as a package (not just scripts)."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "my-package"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(
            path=str(project_path),
            name=project_name,
            package=True,  # Create as package
            python="3.11",
        )

        assert result["success"] is True

        # Verify package structure
        package_dir = project_path / project_name.replace("-", "_")
        assert package_dir.exists()
        assert (package_dir / "__init__.py").exists()
        assert (package_dir / "py.typed").exists()  # For type checking

        # Verify build system in pyproject.toml
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        assert "build-system" in pyproject
        assert pyproject["build-system"]["requires"] == ["hatchling"]
        assert pyproject["build-system"]["build-backend"] == "hatchling.build"

    def test_init_with_dev_dependencies(self, temp_dir, uv_available):
        """Test initializing with common development dependencies."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "dev-project"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(
            path=str(project_path),
            name=project_name,
            python="3.11",
            with_dev=True,  # Add common dev dependencies
        )

        assert result["success"] is True

        # Verify dev dependencies in pyproject.toml
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        assert "optional-dependencies" in pyproject["project"]
        dev_deps = pyproject["project"]["optional-dependencies"]["dev"]

        # Should include common dev tools
        assert any("pytest" in dep for dep in dev_deps)
        assert any("ruff" in dep for dep in dev_deps)
        assert any("mypy" in dep for dep in dev_deps)
        assert any("black" in dep for dep in dev_deps)

    def test_init_existing_directory(self, temp_dir, uv_available):
        """Test initializing in an existing directory."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_path = temp_dir / "existing-project"
        project_path.mkdir()

        # Add some existing files
        (project_path / "existing_file.py").write_text("# Existing code")

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(path=str(project_path), python="3.11")

        assert result["success"] is True

        # Verify existing files are preserved
        assert (project_path / "existing_file.py").exists()
        assert (project_path / "existing_file.py").read_text() == "# Existing code"

        # Verify new files are created
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / ".python-version").exists()

    def test_init_with_author_info(self, temp_dir, uv_available):
        """Test initializing with author information."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "authored-project"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(
            path=str(project_path), name=project_name, python="3.11", author="Test Author", email="test@example.com"
        )

        assert result["success"] is True

        # Verify author info in pyproject.toml
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        authors = pyproject["project"]["authors"]
        assert len(authors) > 0
        assert authors[0]["name"] == "Test Author"
        assert authors[0]["email"] == "test@example.com"

    def test_init_with_license(self, temp_dir, uv_available):
        """Test initializing with license selection."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "licensed-project"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(path=str(project_path), name=project_name, python="3.11", license="MIT")

        assert result["success"] is True

        # Verify license in pyproject.toml
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        assert pyproject["project"]["license"] == {"text": "MIT"}

        # Verify LICENSE file exists
        assert (project_path / "LICENSE").exists()

    def test_init_idempotent(self, temp_dir, uv_available):
        """Test that init is idempotent (safe to run multiple times)."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "idempotent-project"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        # First init
        result1 = commands.init(path=str(project_path), name=project_name, python="3.11")
        assert result1["success"] is True

        # Modify a file to test preservation
        readme_path = project_path / "README.md"
        original_content = readme_path.read_text()
        readme_path.write_text(original_content + "\n\n## Custom Section")

        # Second init
        result2 = commands.init(path=str(project_path), name=project_name, python="3.11")

        assert result2["success"] is True
        assert "already initialized" in result2["message"].lower()

        # Verify custom content is preserved
        assert "## Custom Section" in readme_path.read_text()

    def test_init_with_github_actions(self, temp_dir, uv_available):
        """Test initializing with GitHub Actions CI/CD."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_name = "ci-project"
        project_path = temp_dir / project_name

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(
            path=str(project_path),
            name=project_name,
            python="3.11",
            with_ci="github",  # Add GitHub Actions
        )

        assert result["success"] is True

        # Verify GitHub Actions workflow
        workflow_path = project_path / ".github" / "workflows" / "test.yml"
        assert workflow_path.exists()

        workflow_content = workflow_path.read_text()
        assert "uses: astral-sh/setup-uv" in workflow_content
        assert "uv sync" in workflow_content
        assert "uv run pytest" in workflow_content

    def test_init_from_requirements_txt(self, temp_dir, uv_available):
        """Test initializing from existing requirements.txt."""
        if not uv_available:
            pytest.skip("UV is not installed")

        project_path = temp_dir / "legacy-project"
        project_path.mkdir()

        # Create requirements.txt
        requirements = """
requests>=2.28.0
click>=8.0.0
pydantic>=2.0.0
"""
        (project_path / "requirements.txt").write_text(requirements.strip())

        from DHT.modules.dhtl_commands import DHTLCommands

        commands = DHTLCommands()

        result = commands.init(path=str(project_path), python="3.11", from_requirements=True)

        assert result["success"] is True

        # Verify dependencies were imported
        with open(project_path / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        deps = pyproject["project"]["dependencies"]
        assert any("requests" in dep for dep in deps)
        assert any("click" in dep for dep in deps)
        assert any("pydantic" in dep for dep in deps)
