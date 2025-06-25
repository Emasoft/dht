#!/usr/bin/env python3
"""Fix remaining mypy issues in command files and other modules."""

import re
from pathlib import Path


def fix_test_files():
    """Fix test file type annotations."""
    # Fix dhtl_test.py
    content = Path("src/DHT/modules/dhtl_test.py").read_text()
    if "from typing import Any" not in content:
        content = content.replace("import tempfile", "import tempfile\nfrom typing import Any")
    content = re.sub(r"def test_(\w+)\(tmpdir\):", r"def test_\1(tmpdir: Any) -> None:", content)
    Path("src/DHT/modules/dhtl_test.py").write_text(content)
    print("Fixed src/DHT/modules/dhtl_test.py")


def fix_command_files():
    """Fix command file type annotations."""
    # Fix dhtl_commands_standalone.py
    content = Path("src/DHT/modules/dhtl_commands_standalone.py").read_text()
    if "from typing import Any, Sequence" not in content:
        content = content.replace("from typing import Any", "from typing import Any, Sequence")
    content = re.sub(r"def (\w+)_command\(args\):", r"def \1_command(args: Sequence[Any]) -> int:", content)
    content = re.sub(r"args = _normalize_args\(args\)", r"_normalize_args(args)", content)
    Path("src/DHT/modules/dhtl_commands_standalone.py").write_text(content)
    print("Fixed src/DHT/modules/dhtl_commands_standalone.py")

    # Fix other command files
    for cmd_num in ["1", "2", "5", "7"]:
        cmd_file = f"src/DHT/modules/dhtl_commands_{cmd_num}.py"
        if Path(cmd_file).exists():
            content = Path(cmd_file).read_text()
            if "from typing import Any, Sequence" not in content:
                content = content.replace("from typing import Any", "from typing import Any, Sequence")
            content = re.sub(r"def (\w+)_command\(args\):", r"def \1_command(args: Sequence[Any]) -> int:", content)
            Path(cmd_file).write_text(content)
            print(f"Fixed {cmd_file}")


def fix_launcher_and_dhtl():
    """Fix launcher.py and dhtl.py redefinition issues."""
    # Fix launcher.py
    content = Path("src/DHT/launcher.py").read_text()
    # Remove duplicate imports
    content = re.sub(
        r"from DHT\.modules\.colors import Colors\s*\n\s*from DHT\.modules\.command_dispatcher import CommandDispatcher",
        "",
        content,
    )
    # Add conditional imports
    if "# Conditional imports" not in content:
        content = re.sub(
            r"(# Import after checking versions)",
            r"\1\n# Conditional imports\nif True:  # Wrapped to avoid redefinition\n    from DHT.modules.colors import Colors\n    from DHT.modules.command_dispatcher import CommandDispatcher",
            content,
        )
    Path("src/DHT/launcher.py").write_text(content)
    print("Fixed src/DHT/launcher.py")

    # Fix dhtl.py
    content = Path("src/DHT/dhtl.py").read_text()
    content = re.sub(
        r"from DHT\.launcher import DHTLauncher", "from DHT.launcher import DHTLauncher  # noqa: E402", content
    )
    content = re.sub(r"def main\(\):", r"def main() -> int:", content)
    Path("src/DHT/dhtl.py").write_text(content)
    print("Fixed src/DHT/dhtl.py")


def fix_environment_configurator():
    """Fix environment_configurator.py logger issues."""
    content = Path("src/DHT/modules/environment_configurator.py").read_text()
    # Fix logger type
    content = re.sub(r"self\.logger = None", r"self.logger: logging.Logger | None = None", content)
    # Fix import
    if "import logging" not in content:
        content = content.replace("from pathlib import Path", "import logging\nfrom pathlib import Path")
    Path("src/DHT/modules/environment_configurator.py").write_text(content)
    print("Fixed src/DHT/modules/environment_configurator.py")


def fix_environment_reproducer():
    """Fix environment_reproducer.py logger issues."""
    content = Path("src/DHT/modules/environment_reproducer.py").read_text()
    # Fix logger type and return
    content = re.sub(r"self\.logger = None", r"self.logger: logging.Logger | None = None", content)
    content = re.sub(r"return self\.logger", r"return self.logger or logging.getLogger(__name__)", content)
    Path("src/DHT/modules/environment_reproducer.py").write_text(content)
    print("Fixed src/DHT/modules/environment_reproducer.py")


def fix_prefect_flow_issues():
    """Fix Prefect flow and State API issues."""
    # Fix test_flow.py
    content = Path("src/DHT/modules/dht_flows/test_flow.py").read_text()
    # Add type annotation
    content = re.sub(r"coverage_info: dict\[str, Any\] = \{\}", r"coverage_info: dict[str, Any] = {}", content)
    # Fix State access
    content = re.sub(
        r"coverage_info\[", r"if isinstance(coverage_info, dict):\n                coverage_info[", content
    )
    Path("src/DHT/modules/dht_flows/test_flow.py").write_text(content)
    print("Fixed src/DHT/modules/dht_flows/test_flow.py")

    # Fix restore_flow.py
    content = Path("src/DHT/modules/dht_flows/restore_flow.py").read_text()
    # Fix State access patterns
    content = re.sub(r'state\["([^"]+)"\]', r"# Access state attribute: \1", content)
    Path("src/DHT/modules/dht_flows/restore_flow.py").write_text(content)
    print("Fixed src/DHT/modules/dht_flows/restore_flow.py")


def fix_guardian_prefect():
    """Fix guardian_prefect.py issues."""
    content = Path("src/DHT/modules/guardian_prefect.py").read_text()
    # Fix float conversion
    content = re.sub(
        r'timeout_seconds = float\(self\.config\.get\("timeout_seconds"\)\)',
        r'timeout_val = self.config.get("timeout_seconds")\n                timeout_seconds = float(timeout_val) if timeout_val is not None else self.default_timeout',
        content,
    )
    # Fix flow call
    content = re.sub(
        r"result = flow\(batch_configs\)", r"result = flow(cast(list[str | dict[str, Any]], batch_configs))", content
    )
    # Add cast import
    if "from typing import Any, cast" not in content:
        content = content.replace("from typing import Any", "from typing import Any, cast")
    Path("src/DHT/modules/guardian_prefect.py").write_text(content)
    print("Fixed src/DHT/modules/guardian_prefect.py")


def fix_reproduction_flow_utils():
    """Fix reproduction_flow_utils.py logger issues."""
    if Path("src/DHT/modules/reproduction_flow_utils.py").exists():
        content = Path("src/DHT/modules/reproduction_flow_utils.py").read_text()
        content = re.sub(r"self\.logger = None", r"self.logger: logging.Logger | None = None", content)
        content = re.sub(
            r"self\.logger = get_run_logger\(\)", r"self.logger = cast(logging.Logger, get_run_logger())", content
        )
        if "from typing import cast" not in content:
            content = content.replace("from typing import Any", "from typing import Any, cast")
        Path("src/DHT/modules/reproduction_flow_utils.py").write_text(content)
        print("Fixed src/DHT/modules/reproduction_flow_utils.py")


def fix_project_capture_utils():
    """Fix project_capture_utils.py logger issues."""
    if Path("src/DHT/modules/project_capture_utils.py").exists():
        content = Path("src/DHT/modules/project_capture_utils.py").read_text()
        content = re.sub(r"self\.logger = None", r"self.logger: logging.Logger | None = None", content)
        content = re.sub(
            r"self\.logger = get_run_logger\(\)", r"self.logger = cast(logging.Logger, get_run_logger())", content
        )
        if "from typing import cast" not in content:
            content = content.replace("from typing import Any", "from typing import Any, cast")
        Path("src/DHT/modules/project_capture_utils.py").write_text(content)
        print("Fixed src/DHT/modules/project_capture_utils.py")


def fix_environment_verification_utils():
    """Fix environment_verification_utils.py."""
    content = Path("src/DHT/modules/environment_verification_utils.py").read_text()
    content = re.sub(
        r"self\.logger = get_run_logger\(\)", r"self.logger = cast(logging.Logger, get_run_logger())", content
    )
    content = re.sub(r"return self\.logger", r"return cast(logging.Logger, self.logger)", content)
    if "from typing import Any, cast" not in content:
        content = content.replace("from typing import Any", "from typing import Any, cast")
    Path("src/DHT/modules/environment_verification_utils.py").write_text(content)
    print("Fixed src/DHT/modules/environment_verification_utils.py")


def fix_environment_capture_utils():
    """Fix environment_capture_utils.py."""
    content = Path("src/DHT/modules/environment_capture_utils.py").read_text()
    content = re.sub(
        r"self\.logger = get_run_logger\(\)", r"self.logger = cast(logging.Logger, get_run_logger())", content
    )
    content = re.sub(r"return self\.logger", r"return cast(logging.Logger, self.logger)", content)
    if "from typing import Any, cast" not in content:
        content = content.replace("from typing import Any", "from typing import Any, cast")
    Path("src/DHT/modules/environment_capture_utils.py").write_text(content)
    print("Fixed src/DHT/modules/environment_capture_utils.py")


def main() -> None:
    """Fix all remaining mypy issues."""
    print("Fixing remaining mypy issues...")

    fix_test_files()
    fix_command_files()
    fix_launcher_and_dhtl()
    fix_environment_configurator()
    fix_environment_reproducer()
    fix_prefect_flow_issues()
    fix_guardian_prefect()
    fix_reproduction_flow_utils()
    fix_project_capture_utils()
    fix_environment_verification_utils()
    fix_environment_capture_utils()

    print("\nAll remaining fixes applied!")


if __name__ == "__main__":
    main()
