#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration test for cloning a GitHub repo and setting it up with dhtl."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.mark.integration
@pytest.mark.network
class TestGitHubCloneSetup:
    """Test cloning a GitHub repo and setting it up with dhtl."""

    @pytest.fixture
    def test_repo_url(self) -> str:
        """Get test repository URL."""
        # Use a small, simple Python project for testing
        return "https://github.com/pypa/sampleproject.git"

    @pytest.fixture  
    def temp_workspace(self) -> Any:
        """Create temporary workspace for cloning."""
        with tempfile.TemporaryDirectory(prefix="dht_clone_test_") as tmpdir:
            yield Path(tmpdir)

    def test_clone_and_setup_github_repo(self, test_repo_url: str, temp_workspace: Path, test_config: Dict[str, Any], project_root: Path) -> None:
        """Test cloning a GitHub repo and setting it up with dhtl setup and build."""
        # Skip if in CI and slow tests are disabled
        if test_config["skip_slow_tests"]:
            pytest.skip("Skipping slow integration test")

        # Clone the repository
        clone_dir = temp_workspace / "sampleproject"
        result = subprocess.run(
            ["git", "clone", test_repo_url, str(clone_dir)],
            capture_output=True,
            text=True,
            timeout=test_config["timeout"] * 2  # Double timeout for network operations
        )
        assert result.returncode == 0, f"Git clone failed: {result.stderr}"
        assert clone_dir.exists(), "Clone directory not created"

        # Change to cloned directory
        os.chdir(clone_dir)

        # Run dhtl setup
        dhtl_path = project_root / "dhtl_entry.py"
        setup_result = subprocess.run(
            ["python", str(dhtl_path), "setup", "--quiet"],
            capture_output=True,
            text=True,
            timeout=test_config["timeout"] * 3
        )
        
        # Check setup results
        assert setup_result.returncode == 0, f"dhtl setup failed: {setup_result.stderr}"
        assert (clone_dir / ".venv").exists(), "Virtual environment not created"
        assert (clone_dir / ".dhtconfig").exists(), ".dhtconfig not created"
        
        # Run dhtl build
        build_result = subprocess.run(
            ["python", str(dhtl_path), "build"],
            capture_output=True,
            text=True,
            timeout=test_config["timeout"] * 3
        )
        
        # Check build results
        assert build_result.returncode == 0, f"dhtl build failed: {build_result.stderr}"
        assert (clone_dir / "dist").exists(), "dist directory not created"
        
        # Verify wheel was built
        dist_files = list((clone_dir / "dist").glob("*.whl"))
        assert len(dist_files) > 0, "No wheel files created"

    @pytest.mark.docker
    def test_clone_and_setup_in_docker(self, test_repo_url: str, test_config: Dict[str, Any], project_root: Path) -> None:
        """Test cloning and setup inside Docker container."""
        # This test runs the clone and setup inside a Docker container
        
        # Check if Docker is available
        docker_check = subprocess.run(["docker", "--version"], capture_output=True)
        if docker_check.returncode != 0:
            pytest.skip("Docker not available")

        # Build test image if needed
        build_result = subprocess.run(
            ["docker", "build", "-f", "Dockerfile", "--target", "test-runner", "-t", "dht:test", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for build
        )
        assert build_result.returncode == 0, f"Docker build failed: {build_result.stderr}"

        # Run the test inside Docker
        docker_cmd = [
            "docker", "run", "--rm",
            "-e", "DHT_TEST_PROFILE=docker",
            "-e", "DHT_TEST_MODE=1",
            "-v", f"{project_root}:/app",
            "dht:test",
            "bash", "-c",
            f"cd /tmp && git clone {test_repo_url} testproject && cd testproject && python /app/dhtl_entry.py setup --quiet && python /app/dhtl_entry.py build"
        ]
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=test_config["timeout"] * 10
        )
        
        assert result.returncode == 0, f"Docker test failed: {result.stderr}"
        assert "Successfully" in result.stdout or "built" in result.stdout.lower(), "Build did not complete successfully"

    def test_dhtl_regenerate_after_clone(self, test_repo_url: str, temp_workspace: Path, test_config: Dict[str, Any], project_root: Path) -> None:
        """Test regenerating environment from .dhtconfig after clone."""
        # First clone and setup
        clone_dir = temp_workspace / "sampleproject"
        subprocess.run(
            ["git", "clone", test_repo_url, str(clone_dir)],
            capture_output=True,
            timeout=test_config["timeout"] * 2
        )
        
        os.chdir(clone_dir)
        dhtl_path = project_root / "dhtl_entry.py"
        
        # Setup
        subprocess.run(
            ["python", str(dhtl_path), "setup", "--quiet"],
            capture_output=True,
            timeout=test_config["timeout"] * 3
        )
        
        # Remove .venv to simulate fresh clone with .dhtconfig
        import shutil
        shutil.rmtree(clone_dir / ".venv")
        
        # Run regenerate
        regenerate_result = subprocess.run(
            ["python", str(dhtl_path), "regenerate"],
            capture_output=True,
            text=True,
            timeout=test_config["timeout"] * 3
        )
        
        assert regenerate_result.returncode == 0, f"dhtl regenerate failed: {regenerate_result.stderr}"
        assert (clone_dir / ".venv").exists(), "Virtual environment not regenerated"
        
        # Verify environment works
        test_result = subprocess.run(
            ["python", str(dhtl_path), "test", "--version"],
            capture_output=True,
            text=True,
            timeout=test_config["timeout"]
        )
        assert test_result.returncode == 0, "Environment not functional after regeneration"