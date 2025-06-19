#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_guardian_2.sh
# - Provides advanced process guardian functionality
# - Manages resource limits and process monitoring
# 

"""
DHT Guardian 2 Module.

Provides advanced process guardian functionality for resource management.
"""

import os
import psutil
import subprocess
import threading
import time
from typing import Optional, List

from .dhtl_error_handling import log_error, log_warning, log_info


class AdvancedProcessGuardian:
    """Advanced process guardian with monitoring capabilities."""
    
    def __init__(self):
        """Initialize the advanced process guardian."""
        self.default_mem_limit = int(os.environ.get("DEFAULT_MEM_LIMIT", "2048"))
        self.monitoring = False
    
    def monitor_process(self, pid: int, mem_limit: int) -> None:
        """Monitor a process for resource usage."""
        try:
            process = psutil.Process(pid)
            while self.monitoring:
                # Check memory usage
                mem_info = process.memory_info()
                mem_mb = mem_info.rss / (1024 * 1024)
                
                if mem_mb > mem_limit:
                    log_warning(f"Process {pid} exceeds memory limit: {mem_mb:.1f}MB > {mem_limit}MB")
                    # TODO: Take action (kill, notify, etc.)
                
                time.sleep(1)  # Check every second
        except psutil.NoSuchProcess:
            log_info(f"Process {pid} has terminated")
        except Exception as e:
            log_error(f"Error monitoring process: {e}")
    
    def run_with_monitoring(self, command: List[str], mem_limit: Optional[int] = None) -> int:
        """Run a command with active monitoring."""
        if mem_limit is None:
            mem_limit = self.default_mem_limit
        
        log_info(f"Running command with monitoring: {mem_limit}MB limit")
        
        try:
            # Start the process
            process = subprocess.Popen(command)
            
            # Start monitoring thread
            self.monitoring = True
            monitor_thread = threading.Thread(
                target=self.monitor_process,
                args=(process.pid, mem_limit)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Wait for completion
            returncode = process.wait()
            
            # Stop monitoring
            self.monitoring = False
            monitor_thread.join(timeout=2)
            
            return returncode
            
        except Exception as e:
            log_error(f"Error running command: {e}")
            return 1


# Export functions
def ensure_process_guardian_running():
    """Ensure process guardian is initialized."""
    # In Python version, guardian is created on demand
    log_info("Process guardian ready")
    return True