#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created universal build detection system
# - Supports Python, Node.js, Rust, Go, C++, Docker, and more
# - Returns appropriate build commands for each project type
# 

"""
Universal build detection for DHT.
Detects project type and returns appropriate build commands.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class BuildConfig:
    """Build configuration for a project."""
    project_type: str
    build_tool: str
    build_commands: List[str]
    artifacts_path: Optional[str] = None
    pre_build_commands: List[str] = None
    post_build_commands: List[str] = None
    notes: str = ""


class UniversalBuildDetector:
    """Detects project type and provides build configuration."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        
    def detect_build_config(self) -> Optional[BuildConfig]:
        """
        Detect project type and return build configuration.
        
        Returns:
            BuildConfig if build is possible, None if no build needed
        """
        # Check for various project types in order of specificity
        
        # Python projects
        if (self.project_path / "setup.py").exists():
            return self._python_setuptools_config()
        elif (self.project_path / "pyproject.toml").exists():
            return self._python_pyproject_config()
        
        # Node.js/JavaScript projects
        elif (self.project_path / "package.json").exists():
            return self._nodejs_config()
        
        # Rust projects
        elif (self.project_path / "Cargo.toml").exists():
            return self._rust_config()
        
        # Go projects
        elif (self.project_path / "go.mod").exists():
            return self._go_config()
        
        # C++ projects
        elif (self.project_path / "CMakeLists.txt").exists():
            return self._cmake_config()
        elif (self.project_path / "Makefile").exists():
            return self._makefile_config()
        
        # Docker projects
        elif (self.project_path / "Dockerfile").exists():
            return self._docker_config()
        
        # Gradle (Java/Kotlin/Android)
        elif (self.project_path / "build.gradle").exists() or (self.project_path / "build.gradle.kts").exists():
            return self._gradle_config()
        
        # Maven (Java)
        elif (self.project_path / "pom.xml").exists():
            return self._maven_config()
        
        # .NET projects
        elif any(self.project_path.glob("*.csproj")) or any(self.project_path.glob("*.sln")):
            return self._dotnet_config()
        
        # No build configuration found
        return None
    
    def _python_setuptools_config(self) -> BuildConfig:
        """Python project with setup.py."""
        return BuildConfig(
            project_type="python",
            build_tool="setuptools",
            build_commands=["python -m build"],
            artifacts_path="dist",
            pre_build_commands=["pip install --upgrade build"],
            notes="Python project with setup.py"
        )
    
    def _python_pyproject_config(self) -> BuildConfig:
        """Python project with pyproject.toml."""
        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return None
            
        # Parse pyproject.toml to determine project type
        import tomllib
        with open(pyproject_path, "rb") as f:
            try:
                pyproject = tomllib.load(f)
            except (AttributeError, tomllib.TOMLDecodeError):
                # Fallback for older Python without tomllib
                import toml
                pyproject = toml.load(pyproject_path)
        
        # Check for Poetry
        if "tool" in pyproject and "poetry" in pyproject["tool"]:
            poetry_config = pyproject["tool"]["poetry"]
            
            # Check if it has packages defined (library)
            if "packages" in poetry_config or "py-modules" in poetry_config:
                return BuildConfig(
                    project_type="python-lib",
                    build_tool="poetry",
                    build_commands=["poetry build"],
                    artifacts_path="dist",
                    notes="Python Poetry library (has packages)"
                )
            
            # Check for explicit scripts (application)
            elif "scripts" in poetry_config:
                return BuildConfig(
                    project_type="python-app",
                    build_tool="poetry",
                    build_commands=[],
                    notes="Python Poetry application (has scripts, no packages)"
                )
            
            # Default Poetry project - check for src layout
            elif (self.project_path / "src").exists():
                return BuildConfig(
                    project_type="python-lib",
                    build_tool="poetry",
                    build_commands=["poetry build"],
                    artifacts_path="dist",
                    notes="Python Poetry library (src layout)"
                )
            else:
                # Application by default
                return BuildConfig(
                    project_type="python-app",
                    build_tool="poetry",
                    build_commands=[],
                    notes="Python Poetry application"
                )
        
        # Check for setuptools with pyproject.toml
        project_config = pyproject.get("project", {})
        
        # Heuristics to determine lib vs app:
        # 1. Has 'packages' or 'py-modules' -> library
        # 2. Has 'scripts' or 'gui-scripts' -> could be either
        # 3. Has src/ directory with package -> library
        # 4. Has single main.py or app.py -> application
        
        # Check for package indicators
        has_packages = False
        if "packages" in project_config or "py-modules" in project_config:
            has_packages = True
        elif (self.project_path / "src").exists():
            # Check if src contains Python packages
            for item in (self.project_path / "src").iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    has_packages = True
                    break
        
        # Check for main application files
        has_main = any((self.project_path / name).exists() 
                      for name in ["main.py", "app.py", "__main__.py"])
        
        if has_packages and not has_main:
            # Pure library
            return BuildConfig(
                project_type="python-lib",
                build_tool="pyproject",
                build_commands=["python -m build"],
                artifacts_path="dist",
                pre_build_commands=["pip install --upgrade build"],
                notes="Python library project (pyproject.toml)"
            )
        elif has_main and not has_packages:
            # Pure application
            return BuildConfig(
                project_type="python-app",
                build_tool="pyproject",
                build_commands=[],
                notes="Python application (no packages to distribute)"
            )
        else:
            # Mixed or unclear - default to library behavior
            return BuildConfig(
                project_type="python",
                build_tool="pyproject",
                build_commands=["python -m build"],
                artifacts_path="dist",
                pre_build_commands=["pip install --upgrade build"],
                notes="Python project with pyproject.toml"
            )
    
    def _nodejs_config(self) -> BuildConfig:
        """Node.js/JavaScript project."""
        package_json_path = self.project_path / "package.json"
        build_commands = []
        
        if package_json_path.exists():
            with open(package_json_path) as f:
                package_data = json.load(f)
                scripts = package_data.get("scripts", {})
                
                # Check for common build scripts
                if "build" in scripts:
                    build_commands = ["npm run build"]
                elif "compile" in scripts:
                    build_commands = ["npm run compile"]
                elif "dist" in scripts:
                    build_commands = ["npm run dist"]
                    
                # Check if it's an Electron app
                if "electron" in package_data.get("devDependencies", {}):
                    if "dist" in scripts:
                        build_commands = ["npm run dist"]
                    else:
                        build_commands = ["npm run build", "electron-builder"]
                    
                    return BuildConfig(
                        project_type="electron",
                        build_tool="electron-builder",
                        build_commands=build_commands,
                        artifacts_path="dist",
                        pre_build_commands=["npm install"],
                        notes="Electron desktop application"
                    )
        
        if not build_commands:
            # No build script - might be a library or simple app
            return BuildConfig(
                project_type="nodejs",
                build_tool="npm",
                build_commands=[],
                notes="Node.js project - check package.json scripts"
            )
        
        return BuildConfig(
            project_type="nodejs",
            build_tool="npm",
            build_commands=build_commands,
            artifacts_path="dist",
            pre_build_commands=["npm install"],
            notes="Node.js project with build script"
        )
    
    def _rust_config(self) -> BuildConfig:
        """Rust project."""
        return BuildConfig(
            project_type="rust",
            build_tool="cargo",
            build_commands=["cargo build --release"],
            artifacts_path="target/release",
            notes="Rust project"
        )
    
    def _go_config(self) -> BuildConfig:
        """Go project."""
        # Try to determine the output binary name
        module_name = "app"
        go_mod_path = self.project_path / "go.mod"
        if go_mod_path.exists():
            with open(go_mod_path) as f:
                first_line = f.readline().strip()
                if first_line.startswith("module "):
                    module_name = first_line.split()[-1].split("/")[-1]
        
        return BuildConfig(
            project_type="go",
            build_tool="go",
            build_commands=[f"go build -o {module_name}"],
            artifacts_path=".",
            notes="Go project"
        )
    
    def _cmake_config(self) -> BuildConfig:
        """CMake C++ project."""
        return BuildConfig(
            project_type="cpp",
            build_tool="cmake",
            build_commands=[
                "mkdir -p build",
                "cd build && cmake ..",
                "cd build && make"
            ],
            artifacts_path="build",
            notes="CMake C++ project"
        )
    
    def _makefile_config(self) -> BuildConfig:
        """Makefile-based project."""
        return BuildConfig(
            project_type="make",
            build_tool="make",
            build_commands=["make"],
            artifacts_path=".",
            notes="Makefile-based project"
        )
    
    def _docker_config(self) -> BuildConfig:
        """Docker/Container project."""
        # Import container handler
        from container_build_handler import get_container_build_info
        
        container_info = get_container_build_info(self.project_path)
        
        if not container_info["can_build"]:
            # No container runtime available
            return BuildConfig(
                project_type="container",
                build_tool="none",
                build_commands=[],
                notes=f"Container project - {container_info['reason']}",
                pre_build_commands=[
                    f"echo '{container_info['recommendation']}'"
                ]
            )
        
        # Container build is possible
        return BuildConfig(
            project_type="container",
            build_tool=container_info["builder"],
            build_commands=container_info["commands"],
            notes=f"Container project using {container_info['builder']} ({'rootless' if container_info['rootless'] else 'requires daemon'})"
        )
    
    def _gradle_config(self) -> BuildConfig:
        """Gradle project (Java/Kotlin)."""
        return BuildConfig(
            project_type="gradle",
            build_tool="gradle",
            build_commands=["./gradlew build"],
            artifacts_path="build/libs",
            notes="Gradle project"
        )
    
    def _maven_config(self) -> BuildConfig:
        """Maven project (Java)."""
        return BuildConfig(
            project_type="maven",
            build_tool="maven",
            build_commands=["mvn package"],
            artifacts_path="target",
            notes="Maven project"
        )
    
    def _dotnet_config(self) -> BuildConfig:
        """NET project."""
        return BuildConfig(
            project_type="dotnet",
            build_tool="dotnet",
            build_commands=["dotnet build --configuration Release"],
            artifacts_path="bin/Release",
            notes=".NET project"
        )
    
    def get_build_summary(self) -> Dict[str, any]:
        """Get a summary of the build configuration."""
        config = self.detect_build_config()
        
        if not config:
            return {
                "can_build": False,
                "reason": "No recognized build configuration found",
                "suggestions": [
                    "This appears to be a script or application without build requirements",
                    "If this should be packaged, add appropriate build configuration",
                    "For Python: add setup.py or pyproject.toml",
                    "For Node.js: add build script to package.json",
                ]
            }
        
        if not config.build_commands:
            return {
                "can_build": False,
                "project_type": config.project_type,
                "build_tool": config.build_tool,
                "reason": config.notes,
                "suggestions": [
                    "This appears to be an application, not a library",
                    "Applications typically don't need build artifacts",
                    "Use 'dhtl run' to execute the application",
                ]
            }
        
        return {
            "can_build": True,
            "project_type": config.project_type,
            "build_tool": config.build_tool,
            "build_commands": config.build_commands,
            "artifacts_path": config.artifacts_path,
            "notes": config.notes
        }


def main():
    """Test the build detector."""
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
    
    detector = UniversalBuildDetector(project_path)
    summary = detector.get_build_summary()
    
    print(f"Build Detection for: {project_path}")
    print("=" * 60)
    
    if summary["can_build"]:
        print("✅ Build possible!")
        print(f"Project Type: {summary['project_type']}")
        print(f"Build Tool: {summary['build_tool']}")
        print(f"Commands: {summary['build_commands']}")
        if summary.get("artifacts_path"):
            print(f"Artifacts: {summary['artifacts_path']}")
    else:
        print("❌ No build needed")
        print(f"Reason: {summary['reason']}")
        if summary.get("suggestions"):
            print("\nSuggestions:")
            for suggestion in summary["suggestions"]:
                print(f"  - {suggestion}")


if __name__ == "__main__":
    main()