#!/usr/bin/env python3
from __future__ import annotations

"""
dhtl_commands_deploy.py - Implementation of dhtl deploy_project_in_container command  This module implements the deploy command functionality extracted from dhtl_commands.py

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtl_commands_deploy.py - Implementation of dhtl deploy_project_in_container command

This module implements the deploy command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted deploy_project_in_container command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#


import logging
import os
from pathlib import Path
from typing import Any

from prefect import task
from prefect.cache_policies import NO_CACHE

from DHT.modules.container_test_runner import ContainerTestRunner, TestFramework
from DHT.modules.docker_manager import DockerManager
from DHT.modules.dockerfile_generator import DockerfileGenerator


class DeployCommand:
    """Implementation of dhtl deploy_project_in_container command."""

    def __init__(self):
        """Initialize deploy command."""
        self.logger = logging.getLogger(__name__)

    @task(name="deploy_project_in_container", cache_policy=NO_CACHE)
    def deploy_project_in_container(
        self,
        project_path: str | None = None,
        run_tests: bool = True,
        python_version: str | None = None,
        detach: bool = False,
        port_mapping: dict[str, int] | None = None,
        environment: dict[str, str] | None = None,
        multi_stage: bool = False,
        production: bool = False,
    ) -> dict[str, Any]:
        """
        Deploy project in a Docker container with UV environment.

        Args:
            project_path: Path to project (defaults to current directory)
            run_tests: Run tests after deployment
            python_version: Python version to use (auto-detected if not specified)
            detach: Run container in background
            port_mapping: Custom port mapping
            environment: Environment variables
            multi_stage: Use multi-stage Dockerfile
            production: Use production optimizations

        Returns:
            Result dictionary with deployment info and test results
        """
        # Use current directory if not specified
        if project_path is None:
            project_path = os.getcwd()

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Project path does not exist: {project_path}"}

        # Initialize components
        docker_mgr = DockerManager()
        dockerfile_gen = DockerfileGenerator()
        test_runner = ContainerTestRunner()

        try:
            # Check Docker requirements
            docker_mgr.check_docker_requirements()

            # Analyze project
            self.logger.info(f"Analyzing project: {project_path}")
            project_info = dockerfile_gen.analyze_project(project_path)

            # Override Python version if specified
            if python_version:
                project_info["python_version"] = python_version

            # Generate image tag
            project_name = project_info.get("name", project_path.name)
            image_tag = f"dht-{project_name}:latest"
            container_name = f"dht-{project_name}-container"

            # Check for existing Dockerfile
            dockerfile_path = project_path / "Dockerfile"
            if dockerfile_path.exists():
                self.logger.info("Using existing Dockerfile")
                dockerfile_content = dockerfile_path.read_text()
            else:
                # Generate Dockerfile
                self.logger.info("Generating Dockerfile...")
                dockerfile_content = dockerfile_gen.generate_dockerfile(
                    project_info, multi_stage=multi_stage, production=production
                )

                # Save generated Dockerfile
                dockerfile_path.write_text(dockerfile_content)
                self.logger.info(f"Saved Dockerfile to: {dockerfile_path}")

            # Build Docker image
            self.logger.info(f"Building Docker image: {image_tag}")
            success, build_logs = docker_mgr.build_image(project_path, image_tag, dockerfile=str(dockerfile_path))

            if not success:
                return {"success": False, "error": "Failed to build Docker image", "build_logs": build_logs}

            # Prepare port mapping
            if port_mapping is None and project_info.get("ports"):
                port_mapping = {}
                for port in project_info["ports"]:
                    # Check if port is available
                    if docker_mgr.is_port_available(port):
                        port_mapping[f"{port}/tcp"] = port
                    else:
                        # Try alternative port
                        alt_port = port + 10000
                        if docker_mgr.is_port_available(alt_port):
                            port_mapping[f"{port}/tcp"] = alt_port
                            self.logger.warning(f"Port {port} in use, using {alt_port}")

            # Clean up existing container
            docker_mgr.cleanup_containers(container_name)

            # Run container
            self.logger.info(f"Running container: {container_name}")
            container = docker_mgr.run_container(
                image=image_tag,
                name=container_name,
                ports=port_mapping,
                environment=environment,
                detach=detach,
                remove=False,  # Keep for testing
            )

            # Get container info
            container_info = docker_mgr.get_container_info(container_name)

            result = {
                "success": True,
                "message": "Successfully deployed project in container",
                "image_tag": image_tag,
                "container_name": container_name,
                "container_id": container_info["id"],
                "ports": container_info["ports"],
                "status": container_info["status"],
            }

            # Run tests if requested
            if run_tests and project_info.get("has_tests"):
                self.logger.info("Running tests in container...")

                # Determine which test frameworks to use
                frameworks = [TestFramework.PYTEST]  # Default

                deps = [d.lower() for d in project_info.get("dependencies", [])]
                if "playwright" in deps:
                    frameworks.append(TestFramework.PLAYWRIGHT)
                if "puppeteer" in deps or "pyppeteer" in deps:
                    frameworks.append(TestFramework.PUPPETEER)

                # Run tests
                test_results = test_runner.run_all_tests(container_name, frameworks)

                # Format results
                result["test_results"] = test_results
                result["test_summary"] = test_runner.format_results_table(test_results)

                # Add to console output
                print(result["test_summary"])

                # Save detailed results
                results_path = project_path / "container_test_results.json"
                test_runner.save_results(test_results, results_path)
                result["test_results_file"] = str(results_path)

            # If not detached, provide access info
            if not detach and port_mapping:
                result["access_info"] = []
                for container_port, host_port in container_info["ports"].items():
                    if "8000" in container_port:
                        result["access_info"].append(f"Web app: http://localhost:{host_port}")
                    else:
                        result["access_info"].append(f"Port {container_port} -> localhost:{host_port}")

            # Provide helpful commands
            result["commands"] = {
                "logs": f"docker logs -f {container_name}",
                "shell": f"docker exec -it {container_name} /bin/bash",
                "stop": f"docker stop {container_name}",
                "remove": f"docker rm {container_name}",
                "cleanup": f"dhtl cleanup_containers --prefix dht-{project_name}",
            }

            return result

        except Exception as e:
            self.logger.error(f"Deployment error: {e}")
            return {"success": False, "error": str(e)}


# Export the command class
__all__ = ["DeployCommand"]
