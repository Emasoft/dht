#!/usr/bin/env python3
"""
setup_tree_sitter.py - Set up tree-sitter with Bash grammar for the project  This script ensures that: 1. tree-sitter Python package is installed 2. tree-sitter-bash grammar is cloned and properly configured 3. A compiled language library is built and ready for use  Usage:

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
setup_tree_sitter.py - Set up tree-sitter with Bash grammar for the project

This script ensures that:
1. tree-sitter Python package is installed
2. tree-sitter-bash grammar is cloned and properly configured
3. A compiled language library is built and ready for use

Usage:
    python setup_tree_sitter.py

The script is idempotent and can be run multiple times without issues.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def ensure_tree_sitter_installed() -> None:
    """Ensure the tree-sitter Python package is installed"""
    try:
        import tree_sitter

        # Get version if available, otherwise just acknowledge it's installed
        try:
            version = tree_sitter.__version__
            version_str = f"(version: {version})"
        except AttributeError:
            version_str = "(version information not available)"

        print(f"✅ tree-sitter Python package is installed {version_str}")
        return True  # type: ignore[return-value]
    except ImportError:
        print("❌ tree-sitter Python package is not installed")
        try:
            print("🔄 Installing tree-sitter Python package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tree-sitter"])
            import tree_sitter

            print("✅ tree-sitter Python package installed successfully")
            return True  # type: ignore[return-value]
        except Exception as e:
            print(f"❌ Failed to install tree-sitter Python package: {e}")
            return False  # type: ignore[return-value]


def ensure_build_directory(project_root):
    """Ensure the build directory exists"""
    build_dir = project_root / "build"
    if not build_dir.exists():
        print(f"🔄 Creating build directory at {build_dir}")
        build_dir.mkdir(exist_ok=True)
    else:
        print(f"✅ Build directory already exists at {build_dir}")
    return build_dir


def ensure_tree_sitter_bash(project_root) -> None:
    """Ensure tree-sitter-bash grammar is cloned and set up"""
    ts_bash_dir = project_root / "tree-sitter-bash"

    # Check for valid repository structure
    parser_file = ts_bash_dir / "src" / "parser.c"
    is_valid_repo = ts_bash_dir.exists() and parser_file.exists()

    if not is_valid_repo:
        print(f"🔄 Setting up tree-sitter-bash at {ts_bash_dir}")

        # Remove directory if it exists but is incomplete
        if ts_bash_dir.exists():
            print("🔄 Removing incomplete tree-sitter-bash directory")
            shutil.rmtree(ts_bash_dir)

        # Clone the repository
        try:
            print("🔄 Cloning tree-sitter-bash repository...")
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/tree-sitter/tree-sitter-bash.git",
                    str(ts_bash_dir),
                ]
            )

            # Verify the clone worked correctly
            if not (ts_bash_dir / "src" / "parser.c").exists():
                print("❌ Cloned repository is missing expected structure")
                return False  # type: ignore[return-value]

            print("✅ tree-sitter-bash repository cloned successfully")
        except Exception as e:
            print(f"❌ Failed to clone tree-sitter-bash repository: {e}")
            return False  # type: ignore[return-value]
    else:
        print("✅ tree-sitter-bash directory already exists and contains expected files")

    return True  # type: ignore[return-value]


def build_language_library(project_root) -> None:
    """Build the language library using tree-sitter"""
    try:
        import tree_sitter
        from tree_sitter import Language

        build_dir = project_root / "build"
        ts_bash_dir = project_root / "tree-sitter-bash"

        # For newer tree-sitter versions, we try to use tree_sitter_languages
        try:
            import importlib.util

            if importlib.util.find_spec("tree_sitter_bash") is not None:
                print("✅ tree-sitter-bash Python bindings already installed")
                return True  # type: ignore[return-value]
        except ImportError:
            pass

        # Try newer API with Language.build
        lib_path = build_dir / "languages.so"

        # Check if library exists and is up to date
        if lib_path.exists():
            print(f"✅ Language library already exists at {lib_path}")
            # Validate that it works
            try:
                language = tree_sitter.Language(str(lib_path), "bash")
                print("✅ Successfully loaded Bash language from existing library")
                return True  # type: ignore[return-value]
            except Exception:
                print("❌ Existing language library is invalid. Rebuilding...")
                if lib_path.exists():
                    lib_path.unlink()

        # Build the library - try different methods based on version
        print(f"🔄 Building language library at {lib_path}")

        # Try the newer API first
        try:
            Language.build(str(lib_path), [str(ts_bash_dir)])
        except AttributeError:
            # Fall back to older API
            try:
                Language.build_library(str(lib_path), [str(ts_bash_dir)])
            except Exception as e:
                print(f"❌ Neither Language.build nor Language.build_library available: {e}")
                print("🔄 Attempting to use pre-installed tree-sitter-bash bindings...")

                # Try to install tree-sitter-bash as a package
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "tree-sitter-bash"])
                    # Verify installation using importlib
                    import importlib.util

                    if importlib.util.find_spec("tree_sitter_bash") is not None:
                        print("✅ Successfully installed tree-sitter-bash Python bindings")
                        return True  # type: ignore[return-value]
                    else:
                        print("❌ tree-sitter-bash installation verification failed")
                        return False  # type: ignore[return-value]
                except Exception as install_error:
                    print(f"❌ Failed to install tree-sitter-bash: {install_error}")
                    return False  # type: ignore[return-value]

        # Validate the built library
        try:
            language = tree_sitter.Language(str(lib_path), "bash")
            print("✅ Successfully built and loaded Bash language library")
            return True  # type: ignore[return-value]
        except Exception as e:
            print(f"❌ Failed to load the built language library: {e}")
            return False  # type: ignore[return-value]

    except ImportError:
        print("❌ tree-sitter Python package is not installed")
        return False  # type: ignore[return-value]
    except Exception as e:
        print(f"❌ Failed to build language library: {e}")
        return False  # type: ignore[return-value]


def test_bash_parsing(project_root) -> None:
    """Test if bash parsing works with a simple example"""
    try:
        import tree_sitter

        lib_path = project_root / "build" / "languages.so"
        language = tree_sitter.Language(str(lib_path), "bash")

        parser = tree_sitter.Parser()
        parser.set_language(language)

        # Sample bash function to parse
        bash_code = """
        #!/bin/bash

        hello_world() {
            echo "Hello, world!"
            return 0
        }

        hello_world
        """

        tree = parser.parse(bytes(bash_code, "utf8"))
        root_node = tree.root_node

        print("\n🔍 Testing Bash parsing...")
        print(f"Tree type: {root_node.type}")
        print("Tree structure (simplified):")
        print(f"  - Root node: {root_node.type}")

        function_nodes = []
        for child in root_node.children:
            print(f"  - Child node: {child.type}")
            if child.type == "function_definition":
                function_nodes.append(child)

        if function_nodes:
            print("✅ Successfully identified function definitions in Bash code")
            for func in function_nodes:
                for part in func.children:
                    if part.type == "word":
                        func_name = bash_code[part.start_byte : part.end_byte]
                        print(f"    Function name: {func_name}")
            return True  # type: ignore[return-value]
        else:
            print("❌ Failed to identify function definitions in Bash code")
            return False  # type: ignore[return-value]

    except Exception as e:
        print(f"❌ Failed to test Bash parsing: {e}")
        return False  # type: ignore[return-value]


def main() -> None:
    """Main function"""
    print("🚀 Setting up tree-sitter with Bash grammar...")

    # Get project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Ensure tree-sitter Python package is installed
    if not ensure_tree_sitter_installed():
        print("❌ Failed to set up tree-sitter. Exiting.")
        sys.exit(1)

    # Ensure build directory exists
    ensure_build_directory(project_root)

    # Ensure tree-sitter-bash grammar is set up
    if not ensure_tree_sitter_bash(project_root):
        print("❌ Failed to set up tree-sitter-bash grammar. Exiting.")
        sys.exit(1)

    # Build language library
    if not build_language_library(project_root):
        print("❌ Failed to build language library. Exiting.")
        sys.exit(1)

    # Test bash parsing
    if not test_bash_parsing(project_root):
        print("❌ Bash parsing test failed. Setup may not be complete.")
        sys.exit(1)

    print("\n✅ tree-sitter with Bash grammar is set up successfully!")
    print("You can now use the bash_parser.py and extract_functions.py scripts")


if __name__ == "__main__":
    main()
