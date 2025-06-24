#!/usr/bin/env python3
"""
diagnostic_system_info.py - System information collection utilities.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from diagnostic_reporter_v2.py to reduce file size
# - Contains system information collection functions
# - Supports psutil for enhanced system info when available
# - Follows CLAUDE.md modularity guidelines
#

import platform
import socket
from typing import Any

# Try to import optional dependencies
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import distro

    HAS_DISTRO = True
except ImportError:
    HAS_DISTRO = False


def collect_basic_system_info() -> dict[str, Any]:
    """
    Collect basic system information using standard library.

    Returns:
        dict: Basic system information
    """
    info = {
        "platform": platform.system().lower(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    # Add Linux distribution info if available
    if info["platform"] == "linux" and HAS_DISTRO:
        dist_info = distro.info()
        info["distribution"] = dist_info.get("id", "unknown")
        info["distribution_version"] = dist_info.get("version", "unknown")
        info["distribution_like"] = dist_info.get("like", "")

    return info


def collect_psutil_info() -> dict[str, Any]:
    """
    Collect enhanced system information using psutil.

    Returns:
        dict: Enhanced system information or empty dict if psutil unavailable
    """
    if not HAS_PSUTIL:
        return {}

    info: dict[str, Any] = {}

    # CPU information
    try:
        info["cpu"] = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_freq_mhz": getattr(psutil.cpu_freq(), "current", None) if psutil.cpu_freq() else None,
            "max_freq_mhz": getattr(psutil.cpu_freq(), "max", None) if psutil.cpu_freq() else None,
        }
    except Exception:
        pass

    # Memory information
    try:
        vm = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": round(vm.total / 1024 / 1024),
            "available_mb": round(vm.available / 1024 / 1024),
            "used_mb": round(vm.used / 1024 / 1024),
            "percent": vm.percent,
        }
    except Exception:
        pass

    # Disk information
    try:
        disk = psutil.disk_usage("/")
        info["disk"] = {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
            "percent": disk.percent,
        }
    except Exception:
        pass

    # Network interfaces
    try:
        interfaces: list[dict[str, Any]] = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append({"name": name, "ipv4": addr.address})
                elif addr.family == socket.AF_INET6:
                    interfaces.append({"name": name, "ipv6": addr.address})
        if interfaces:
            info["network_interfaces"] = interfaces
    except Exception:
        pass

    return info
