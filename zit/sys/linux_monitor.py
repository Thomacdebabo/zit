#!/usr/bin/env python3

import subprocess
import time
import re
import os
import signal
import sys
from datetime import datetime
import getpass
import psutil
from pathlib import Path

from ..sys_storage import SystemStorage
from ..sys_events import SystemEvent, SystemEventType
from ..terminal import print_string
from typing import Optional, Any

# Target applications to monitor (can be extended)
TARGET_APPS: dict[str, str] = {
    "firefox": "Firefox",
    "chrome": "Chrome",
    "code": "VSCode",
    "vim": "Vim",
    "nvim": "Neovim",
    "emacs": "Emacs",
    "gnome-terminal": "Terminal",
    "konsole": "Konsole",
    "xterm": "XTerm",
}

# Global state tracking
running_processes: dict[int, tuple[str, str]] = {}
last_boot_time: Optional[datetime] = None


def track_event(event_type: SystemEventType, details: str = "") -> None:
    """Track a system event"""
    event = SystemEvent(
        timestamp=datetime.now(),
        event_type=event_type,
        details=details,
        user=getpass.getuser(),
    )

    storage = SystemStorage()
    storage.add_event(event)

    print_string(f"Tracked {event_type} event: {details}")


def get_boot_time() -> datetime:
    """Get the system boot time"""
    return datetime.fromtimestamp(psutil.boot_time())


def check_startup() -> None:
    """Check if the system has just started up"""
    global last_boot_time

    boot_time = get_boot_time()

    if last_boot_time is None:
        last_boot_time = boot_time
        boot_time_str = boot_time.strftime("%Y-%m-%d %H:%M:%S")
        track_event(SystemEventType.STARTUP, f"System booted at {boot_time_str}")
        return

    if boot_time != last_boot_time:
        last_boot_time = boot_time
        boot_time_str = boot_time.strftime("%Y-%m-%d %H:%M:%S")
        track_event(SystemEventType.STARTUP, f"System booted at {boot_time_str}")


def check_sleep_wake() -> None:
    """Check for sleep/wake events using systemd journal"""
    # Use journalctl to look for sleep/wake events in the last minute
    try:
        cmd = [
            "journalctl",
            "--since=1 minute ago",
            "-u",
            "systemd-sleep",
            "--no-pager",
        ]
        output = subprocess.check_output(cmd, text=True)

        # Process the output to find sleep/wake events
        for line in output.split("\n"):
            if "Suspending" in line:
                track_event(SystemEventType.SLEEP, "System going to sleep")
            elif "Woke up" in line:
                track_event(SystemEventType.WAKE, "System woke from sleep")
    except subprocess.SubprocessError:
        # Fall back to checking /var/log/syslog
        try:
            cmd = [
                "grep",
                "-E",
                "PM: suspend|PM: resume",
                "/var/log/syslog",
                "--silent",
            ]
            output = subprocess.check_output(cmd, text=True)
            for line in output.split("\n"):
                if "PM: suspend" in line:
                    track_event(SystemEventType.SLEEP, "System going to sleep")
                elif "PM: resume" in line:
                    track_event(SystemEventType.WAKE, "System woke from sleep")
        except subprocess.SubprocessError:
            pass


def check_app_launches() -> None:
    """Check for target application launches and closures"""
    global running_processes

    # Check for target applications in currently running processes
    current_processes: dict[int, tuple[str, str]] = {}
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_info = proc.info
            proc_name = proc_info["name"]

            # Check if this is a target application
            for target, display_name in TARGET_APPS.items():
                if target in proc_name.lower():
                    current_processes[proc.pid] = (proc_name, display_name)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Find new processes (app launches)
    for pid, (proc_name, display_name) in current_processes.items():
        if pid not in running_processes:
            track_event(SystemEventType.APP_LAUNCH, display_name)

    # Find terminated processes (app closures)
    for pid, (proc_name, display_name) in list(running_processes.items()):
        if pid not in current_processes:
            track_event(SystemEventType.APP_CLOSE, display_name)

    # Update our tracking state
    running_processes = current_processes


def monitor(interval: int = 60, apps: Optional[list[str]] = None) -> None:
    """Monitor the system for events continuously"""
    global TARGET_APPS

    if apps:
        # Only monitor the specified apps
        filtered_apps: dict[str, str] = {}
        for app in apps:
            for target, display_name in TARGET_APPS.items():
                if app.lower() in target or target in app.lower():
                    filtered_apps[target] = display_name

        if filtered_apps:
            TARGET_APPS = filtered_apps

    print_string(f"Starting Linux system monitor. Checking every {interval} seconds.")
    print_string(f"Monitoring apps: {', '.join(app for app in TARGET_APPS.values())}")
    print_string("Press Ctrl+C to stop monitoring.")

    def signal_handler(sig: int, frame: Any) -> None:
        print_string("\nStopping monitor...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Initial checks
    check_startup()
    check_app_launches()

    # Continuous monitoring
    try:
        while True:
            check_startup()
            check_sleep_wake()
            check_app_launches()
            time.sleep(interval)
    except KeyboardInterrupt:
        print_string("\nStopping monitor...")
        sys.exit(0)


if __name__ == "__main__":
    monitor()
