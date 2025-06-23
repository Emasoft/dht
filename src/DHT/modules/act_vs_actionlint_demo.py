#!/usr/bin/env python3
"""
Demo showing the difference between actionlint and act.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created demo to show the difference between act and actionlint
# - Shows actionlint for static analysis vs act for execution
#

"""
Demo showing the difference between actionlint and act.
"""

import subprocess
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


# Example workflow with a deliberate syntax error
WORKFLOW_WITH_ERROR = """
name: Example Workflow
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          echo "Running tests..."
          # Missing closing quote below
          echo "This has a syntax error
          pytest tests/
      - name: Invalid action reference
        uses: actions/does-not-exist@v1
"""

# Example valid workflow
VALID_WORKFLOW = """
name: Valid Workflow
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          echo "Running tests..."
          echo "All tests passed!"
      - name: Build
        run: |
          echo "Building project..."
          echo "Build complete!"
"""


def demo_actionlint_vs_act() -> None:
    """Demonstrate the difference between actionlint and act."""

    console.print(
        Panel.fit(
            "🎯 Act vs Actionlint Demo\n\n"
            "This demo shows the fundamental difference between:\n"
            "• actionlint: Static analysis (finds errors without running)\n"
            "• act: Execution (actually runs the workflow)",
            style="bold blue",
        )
    )

    # Create a temporary directory for the demo
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        workflows_dir = tmpdir_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        # Test 1: Workflow with errors
        console.print("\n[yellow]📝 Test 1: Workflow with syntax errors[/yellow]")

        error_workflow = workflows_dir / "error.yml"
        with open(error_workflow, "w") as f:
            f.write(WORKFLOW_WITH_ERROR)

        console.print("\nWorkflow content:")
        console.print(Syntax(WORKFLOW_WITH_ERROR, "yaml", line_numbers=True))

        # Run actionlint
        console.print("\n[cyan]🔍 Running actionlint (static analysis):[/cyan]")
        try:
            result = subprocess.run(["actionlint", str(error_workflow)], capture_output=True, text=True)
            if result.returncode != 0:
                console.print("[red]❌ Actionlint found errors:[/red]")
                console.print(result.stdout)
            else:
                console.print("[green]✅ No errors found[/green]")
        except FileNotFoundError:
            console.print("[yellow]⚠️  actionlint not installed[/yellow]")
            console.print("   Would detect: unclosed quote, invalid action reference")

        # Try to run with act
        console.print("\n[cyan]🚀 Trying to run with act:[/cyan]")
        console.print("[red]❌ Act would fail to parse the workflow due to syntax errors[/red]")
        console.print("   Act cannot execute workflows with syntax errors")

        # Test 2: Valid workflow
        console.print("\n\n[yellow]📝 Test 2: Valid workflow[/yellow]")

        valid_workflow = workflows_dir / "valid.yml"
        with open(valid_workflow, "w") as f:
            f.write(VALID_WORKFLOW)

        console.print("\nWorkflow content:")
        console.print(Syntax(VALID_WORKFLOW, "yaml", line_numbers=True))

        # Run actionlint
        console.print("\n[cyan]🔍 Running actionlint (static analysis):[/cyan]")
        try:
            result = subprocess.run(["actionlint", str(valid_workflow)], capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✅ No syntax errors found[/green]")
                console.print("   Actionlint confirms the workflow syntax is valid")
            else:
                console.print(f"[red]Unexpected errors: {result.stdout}[/red]")
        except FileNotFoundError:
            console.print("[yellow]⚠️  actionlint not installed[/yellow]")
            console.print("   Would report: workflow syntax is valid")

        # Show what act would do
        console.print("\n[cyan]🚀 What act would do:[/cyan]")
        console.print("[green]✅ Act would execute this workflow:[/green]")
        console.print("   1. Spin up ubuntu-latest container")
        console.print("   2. Check out repository code")
        console.print("   3. Execute 'echo \"Running tests...\"'")
        console.print("   4. Execute 'echo \"All tests passed!\"'")
        console.print("   5. Execute 'echo \"Building project...\"'")
        console.print("   6. Execute 'echo \"Build complete!\"'")

        # Summary
        console.print(
            Panel.fit(
                "📊 Summary:\n\n"
                "• Actionlint: Found syntax errors without running anything\n"
                "  - Fast (milliseconds)\n"
                "  - No Docker/containers needed\n"
                "  - Catches errors before execution\n\n"
                "• Act: Would actually run the workflow commands\n"
                "  - Slower (seconds to minutes)\n"
                "  - Requires Docker/Podman\n"
                "  - Tests actual execution\n\n"
                "💡 Best practice: Use actionlint first, then act",
                style="bold green",
            )
        )


def show_dht_usage() -> None:
    """Show how DHT uses both tools."""
    console.print("\n[bold cyan]🔧 DHT Integration:[/bold cyan]\n")

    console.print("1. Check syntax with actionlint:")
    console.print("   [dim]dhtl act --lint[/dim]")
    console.print("   → Fast validation, catches syntax errors\n")

    console.print("2. Run workflows with act:")
    console.print("   [dim]dhtl act[/dim]")
    console.print("   → Actually executes the workflow locally\n")

    console.print("3. Run in container for isolation:")
    console.print("   [dim]dhtl act --container[/dim]")
    console.print("   → Runs act inside a container for complete isolation\n")

    console.print("[dim]Note: The user was confused thinking actionlint runs workflows.[/dim]")
    console.print("[dim]In fact, actionlint only validates syntax, act runs workflows.[/dim]")


if __name__ == "__main__":
    demo_actionlint_vs_act()
    show_dht_usage()
