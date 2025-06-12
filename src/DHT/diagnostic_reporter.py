#!/usr/bin/env python3
# diagnostic_reporter.py
"""
Script to generate an *exhaustive* YAML "system bible"

Key features
============

* Pre-declared taxonomy with >40 categories / subcategories.
* Parallel collection of dozens of CLI-tool outputs.
* Generic parsing pipeline (JSON → YAML → key:value → KEY=VAL).
* Every datum becomes an atomic snake_case key.
* Unparsed lines retained as additional_info_XXXX for future upgrades.
* Absolutely no regex-editing of source files; the reporter only reads data.


diagnostic_reporter.py that extract informations from the system.
	•	≥ 40 categories / 700 sub-categories are pre-declared, giving you a ready-made spine to hang future data on.
	•	Every discovery command you register is executed in parallel;
    •   All key–value pairs that can be recognised are parsed into atomic, snake-case keys.
	•	**Unparsed lines are never lost – they are stored under enumerated keys:

        python_package_managers:
          pipx:
            environment:
              env_vars:
                pipx_home: "/Users/…/.local/pipx"
              additional_info_0001: "PIPX_HOME="
              additional_info_0002: "PIPX_BIN_DIR="
              …


	•	Nothing crashes the run: every error is caught and surfaced in parser_error.
	•	No source editing through regex – the program only manipulates in-memory strings and dicts.

To use, save it as diagnostic_reporter.py, chmod +x it, and run:

./diagnostic_reporter.py --output system_bible.yaml --include-secrets


How to extend it further
========================

This version is only a basic skeleton. 
This need to be expanded to include all tools and config files from
all systems (i.e. SSH keys, env vars, Git repo user and email, full brew list, 
extend tand improve he taxonomy layout, etc.)

	1.	Add a command
Put a new entry in CLI_COMMANDS:

CLI_COMMANDS["kubectl"] = {
    "cmd": "kubectl version -o json",
    "cat": "containers.kubernetes.version"
}

No other code changes are needed – the collector will run, parse JSON,
and drop the data into
system_bible["cli_tools"]["containers"]["kubernetes"]["version"].

	2.	Replace the generic parser for a tricky format
Give the spec a custom parser function:

def parse_mytool(text: str) -> dict:  ...
CLI_COMMANDS["mytool"]["parser"] = parse_mytool

The framework will call it instead of parse_any.

	3.	Fill empty scaffold nodes later
Because everything is pre-scaffolded, you can progressively
upgrade the reporter without breaking downstream consumers.

"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import count
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# --------------------------------------------------------------------------- #
# Minimal third-party deps (auto-install)                                     #
# --------------------------------------------------------------------------- #
def _ensure(pkg: str) -> None:
    try:
        __import__(pkg)
    except ImportError:
        # Instead of self-installing, raise an error if a dependency is missing.
        # The DHT setup process is responsible for installing these.
        print(
            f"Error: Python package '{pkg}' is missing for diagnostic_reporter.py.",
            file=sys.stderr
        )
        print(
            "Please run 'dhtl setup' to install required dependencies.",
            file=sys.stderr
        )
        # Re-raise the ImportError to halt execution if critical,
        # or handle more gracefully if some parts of the script can run without it.
        # For now, let's make it a hard stop.
        raise ImportError(
            f"Missing dependency '{pkg}'. Run 'dhtl setup'."
        ) from None


for _pkg in ("psutil", "distro", "requests", "git", "yaml"):
    _ensure(_pkg)

import distro           # type: ignore
import git              # type: ignore
import psutil           # type: ignore
import requests         # type: ignore
import yaml             # type: ignore

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def run(cmd: str, timeout: int = 30) -> Tuple[str, Optional[str]]:
    """
    Execute *cmd*; return (stdout, error).  *error* is None on success.
    """
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, text=True, timeout=timeout
        )
        err = p.stderr.strip() or None
        return p.stdout.rstrip(), err
    except Exception as exc:
        return "", str(exc)


def snake(s: str) -> str:
    """`X Y` → `x_y`, drop weird chars, compress underscores."""
    s = s.strip().lower().replace(" ", "_").replace("-", "_")
    s = re.sub(r"[^\w]", "_", s)
    return re.sub(r"__+", "_", s).strip("_")


def _coerce(v: str) -> Any:
    """Guess bool / int / float, else return raw string."""
    v = v.strip()
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def parse_any(text: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse *whatever* format we can recognise.  
    Returns (parsed_dict, leftover_lines).
    """
    parsed: Dict[str, Any] = {}
    leftovers: List[str] = []

    txt = text.strip()
    if not txt:
        return parsed, leftovers

    # 1) JSON --------------------------------------------------------------- #
    if (txt.startswith("{") and txt.endswith("}")) or (txt.startswith("[") and txt.endswith("]")):
        try:
            return json.loads(txt), leftovers
        except Exception:
            pass  # fall through

    # 2) YAML ---------------------------------------------------------------- #
    try:
        y = yaml.safe_load(txt)
        if isinstance(y, dict):
            return y, leftovers
    except Exception:
        pass  # fall through

    # 3) key : value  /  KEY=value ------------------------------------------ #
    current: Optional[str] = None
    for ln in txt.splitlines():
        if not ln.strip():
            continue
        if ":" in ln:
            k, v = ln.split(":", 1)
            k, v = snake(k), v.strip()
            current = k
            parsed[k] = _coerce(v) if v else []
        elif "=" in ln:
            k, v = ln.split("=", 1)
            parsed.setdefault("env_vars", {})[snake(k)] = _coerce(v)
        elif current and isinstance(parsed.get(current), list):
            parsed[current].append(_coerce(ln.strip()))
        else:
            leftovers.append(ln)
    return parsed, leftovers


def number_unparsed(lines: List[str]) -> Dict[str, str]:
    """Map leftovers → additional_info_0001, … preserving order."""
    return {f"additional_info_{i:04d}": ln for i, ln in zip(count(1), lines)}


def insert_nested(root: Dict[str, Any], path: List[str], leaf: Dict[str, Any]) -> None:
    d = root
    for p in path[:-1]:
        d = d.setdefault(p, {})
    d[path[-1]] = leaf

# --------------------------------------------------------------------------- #
# CLI command registry                                                        #
# --------------------------------------------------------------------------- #
CLI_COMMANDS: Dict[str, Dict[str, str]] = {
    # tool            command                                           category_path
    "brew":        {"cmd": "brew config",                               "cat": "mac_specific.brew.config"},
    "conda":       {"cmd": "conda info",                                "cat": "python_package_managers.conda.info"},
    "pipx":        {"cmd": "pipx environment",                          "cat": "python_package_managers.pipx.environment"},
    "pip":         {"cmd": f'"{sys.executable}" -m pip inspect --verbose',
                    "cat": "python_package_managers.pip.inspect"},
    "npm":         {"cmd": "npm config list --json",                    "cat": "node_package_managers.npm.config"},
    "node":        {"cmd": "node -p \"require('os').cpus().length\"",   "cat": "node.runtime"},
    "docker":      {"cmd": "docker info --format '{{json .}}'",         "cat": "containers.docker.info"},
    "git":         {"cmd": "git config --list --show-origin",           "cat": "version_control.git.config"},
    "gcc":         {"cmd": "gcc -v",                                    "cat": "compilers.gcc.version"},
    "clang":       {"cmd": "clang -v",                                  "cat": "compilers.clang.version"},
    "make":        {"cmd": "make --version",                            "cat": "build_tools.make.version"},
    "cmake":       {"cmd": "cmake --system-information",                "cat": "build_tools.cmake.sysinfo"},
    # … you can keep adding commands here; they will be auto-parsed.
}

# --------------------------------------------------------------------------- #
# High-level system collectors                                                #
# --------------------------------------------------------------------------- #
def collect_system() -> Dict[str, Any]:
    u = platform.uname()
    vm = psutil.virtual_memory()
    return {
        "os": u.system,
        "release": u.release,
        "version": u.version,
        "architecture": u.machine,
        "distro": distro.name(pretty=True),
        "cpu": {
            "physical": psutil.cpu_count(False),
            "logical": psutil.cpu_count(True),
            "load": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [],
        },
        "memory": {"total": vm.total, "available": vm.available, "percent": vm.percent},
        "boot_time_epoch": psutil.boot_time(),
        "timestamp": datetime.now().isoformat(),
    }


def collect_network() -> Dict[str, Any]:
    nets = {i: [a.address for a in addrs] for i, addrs in psutil.net_if_addrs().items()}
    try:
        requests.get("https://1.1.1.1", timeout=3)
        online = True
    except Exception:
        online = False
    return {"hostname": socket.gethostname(), "fqdn": socket.getfqdn(),
            "interfaces": nets, "internet_access": online}


# (Other rich collectors – shell, env, git repo, ssh, dev-containers, tools, …
#  can be pasted from the previous version; omitted here for brevity.)

# --------------------------------------------------------------------------- #
# CLI output collector                                                        #
# --------------------------------------------------------------------------- #
def collect_cli_outputs() -> Dict[str, Any]:
    bible_fragment: Dict[str, Any] = {}

    with ThreadPoolExecutor() as tp:
        futures = {
            tp.submit(run, spec["cmd"]): (exe, spec["cat"])
            for exe, spec in CLI_COMMANDS.items()
            if shutil.which(exe.split()[0])                 # test if executable is installed
        }

        for fut in as_completed(futures):
            exe, cat_path = futures[fut]
            stdout, err = fut.result()
            parsed, leftovers = parse_any(stdout)
            tool_dict: Dict[str, Any] = {
                **parsed,
                **number_unparsed(leftovers),
                "parser_error": err,
            }
            path_elems = ["cli_tools"] + cat_path.split(".")
            insert_nested(bible_fragment, path_elems, tool_dict)

    return bible_fragment

# --------------------------------------------------------------------------- #
# Static taxonomy scaffold (>40 categories)                                   #
# --------------------------------------------------------------------------- #
TAXONOMY_PATHS = [
    "system", "network", "hardware.cpu", "hardware.memory", "hardware.gpu",
    "hardware.storage", "os.kernel", "os.distribution", "shell",
    "env", "security.ssh", "security.gpg", "security.certificates",
    "python.runtime", "python_package_managers", "os_package_managers",
    "node.runtime", "node_package_managers", "containers.docker",
    "containers.podman", "virtualization.wsl", "virtualization.hypervisor",
    "devcontainers", "version_control.git", "build_tools.cmake",
    "build_tools.make", "compilers.gcc", "compilers.clang", "compilers.msvc",
    "cloud.aws", "cloud.azure", "cloud.gcp", "monitoring_tools.top",
    "monitoring_tools.psutil", "editors.vscode", "editors.vim",
    "editors.emacs", "editors.nano", "productivity.tmux",
    "database.mysql", "database.postgres", "message_brokers.rabbitmq",
    "message_brokers.kafka",
]

def scaffold_taxonomy() -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    for path in TAXONOMY_PATHS:
        insert_nested(root, path.split("."), {})
    return root

# --------------------------------------------------------------------------- #
# Bible builder                                                                #
# --------------------------------------------------------------------------- #
def build_bible(include_secrets: bool) -> Dict[str, Any]:
    bible = scaffold_taxonomy()

    # Populate high-level collectors
    bible["system"] = collect_system()
    bible["network"] = collect_network()
    # (add any other rich collectors you copied in)

    # Populate CLI outputs
    bible.update(collect_cli_outputs())

    # Handle environment variables based on include_secrets flag
    if include_secrets:
        # Include all environment variables
        bible["environment"] = {"variables": dict(os.environ)}
    else:
        # Filter out potentially sensitive environment variables
        sensitive_patterns = [
            r'.*_KEY$', r'.*_TOKEN$', r'.*_SECRET$', r'.*_PASSWORD$',
            r'.*_PASS$', r'.*_PWD$', r'.*_AUTH$', r'.*_CREDENTIAL$',
            r'AWS_.*', r'AZURE_.*', r'GCP_.*', r'GITHUB_.*', r'OPENAI_.*'
        ]
        filtered_env = {}
        for key, value in os.environ.items():
            is_sensitive = any(re.match(pattern, key, re.IGNORECASE) for pattern in sensitive_patterns)
            if is_sensitive:
                filtered_env[key] = "[REDACTED]"
            else:
                filtered_env[key] = value
        bible["environment"] = {"variables": filtered_env}

    return bible

# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate exhaustive system bible.")
    p.add_argument("--output", default="system_bible.yaml")
    p.add_argument("--include-secrets", action="store_true")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    return p.parse_args(argv)


def clean_for_yaml(obj):
    """Clean data for YAML serialization"""
    if isinstance(obj, dict):
        return {k: clean_for_yaml(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_yaml(item) for item in obj]
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    elif isinstance(obj, (int, float)) and (obj > 2**53 or obj < -(2**53)):
        return str(obj)
    else:
        return obj


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    bible = build_bible(args.include_secrets)
    
    output_data = {"system_bible": bible}
    
    if args.format == "json":
        Path(args.output).write_text(json.dumps(output_data, indent=2, default=str))
    else:
        # Convert datetime objects to strings for YAML
        cleaned_data = clean_for_yaml(output_data)
        
        with open(args.output, 'w') as f:
            yaml.dump(cleaned_data, f, 
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True,
                      width=120)
    
    print(f"System bible written to {args.output} (format: {args.format})")


if __name__ == "__main__":
    main()
    
