#!/usr/bin/env python3

import subprocess
import re
import os
from datetime import datetime, timedelta
import getpass
import platform
from pathlib import Path

from ..sys_storage import SystemStorage
from ..sys_events import SystemEvent, SystemEventType
from ..terminal import print_string

def parse_systemd_journal(start_date=None, end_date=None):
    """Parse systemd journal for system events"""
    events = []
    
    # Calculate date range
    if not start_date:
        # Default to looking back 7 days
        start_date = datetime.now() - timedelta(days=7)
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date_str = start_date
    
    if not end_date:
        end_date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        end_date_str = end_date
    
    # Look for boot/shutdown events
    try:
        cmd = [
            "journalctl", f"--since={start_date_str}", f"--until={end_date_str}",
            "-o", "short-iso", "--no-pager"
        ]
        output = subprocess.check_output(cmd, text=True)
        
        # Process boot events
        boot_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*kernel.*Startup finished')
        for line in output.split('\n'):
            boot_match = boot_pattern.search(line)
            if boot_match:
                timestamp_str = boot_match.group(1)
                timestamp = datetime.fromisoformat(timestamp_str)
                events.append(SystemEvent(
                    timestamp=timestamp,
                    event_type=SystemEventType.STARTUP,
                    details="System startup from logs",
                    user=getpass.getuser()
                ))
    except subprocess.SubprocessError:
        print_string("Error accessing systemd journal for boot events")
    
    # Look for sleep/wake events
    try:
        cmd = [
            "journalctl", f"--since={start_date_str}", f"--until={end_date_str}",
            "-u", "systemd-sleep", "-o", "short-iso", "--no-pager"
        ]
        output = subprocess.check_output(cmd, text=True)
        
        suspend_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*Suspending')
        wake_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*Woke up')
        
        for line in output.split('\n'):
            suspend_match = suspend_pattern.search(line)
            if suspend_match:
                timestamp_str = suspend_match.group(1)
                timestamp = datetime.fromisoformat(timestamp_str)
                events.append(SystemEvent(
                    timestamp=timestamp,
                    event_type=SystemEventType.SLEEP,
                    details="System sleep from logs",
                    user=getpass.getuser()
                ))
                continue
                
            wake_match = wake_pattern.search(line)
            if wake_match:
                timestamp_str = wake_match.group(1)
                timestamp = datetime.fromisoformat(timestamp_str)
                events.append(SystemEvent(
                    timestamp=timestamp,
                    event_type=SystemEventType.WAKE,
                    details="System wake from logs",
                    user=getpass.getuser()
                ))
    except subprocess.SubprocessError:
        print_string("Error accessing systemd journal for sleep events")
    
    # Look for login/logout events
    try:
        cmd = [
            "journalctl", f"--since={start_date_str}", f"--until={end_date_str}",
            "_COMM=login", "-o", "short-iso", "--no-pager"
        ]
        output = subprocess.check_output(cmd, text=True)
        
        login_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*New session.*for user (\w+)')
        
        for line in output.split('\n'):
            login_match = login_pattern.search(line)
            if login_match:
                timestamp_str = login_match.group(1)
                username = login_match.group(2)
                timestamp = datetime.fromisoformat(timestamp_str)
                events.append(SystemEvent(
                    timestamp=timestamp,
                    event_type=SystemEventType.LOGIN,
                    details=f"User login",
                    user=username
                ))
    except subprocess.SubprocessError:
        print_string("Error accessing systemd journal for login events")
    
    return events

def parse_syslog(start_date=None, end_date=None):
    """Parse syslog for system events on systems without systemd"""
    events = []
    
    # Calculate date range
    if not start_date:
        # Default to looking back 7 days
        start_date = datetime.now() - timedelta(days=7)
    
    syslog_files = ['/var/log/syslog']
    # Add rotated logs if they exist
    for i in range(1, 7):  # Check syslog.1 through syslog.6
        rotated_file = f'/var/log/syslog.{i}'
        if os.path.exists(rotated_file):
            syslog_files.append(rotated_file)
    
    # Parse each syslog file
    for syslog_file in syslog_files:
        if not os.path.exists(syslog_file) or not os.access(syslog_file, os.R_OK):
            continue
            
        try:
            # Use grep to extract relevant lines for better performance
            for event_type, pattern in [
                (SystemEventType.STARTUP, "kernel: Linux version|Booting Linux"),
                (SystemEventType.SLEEP, "PM: suspend entry|Freezing user space"),
                (SystemEventType.WAKE, "PM: resume from suspend|Restarting tasks")
            ]:
                cmd = ["grep", "-E", pattern, syslog_file]
                try:
                    output = subprocess.check_output(cmd, text=True)
                    
                    # Parse timestamps (typical format: Jan 1 00:00:00)
                    timestamp_pattern = re.compile(r'(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})')
                    current_year = datetime.now().year
                    
                    for line in output.split('\n'):
                        if not line:
                            continue
                            
                        timestamp_match = timestamp_pattern.search(line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            # Add the current year since syslog doesn't include it
                            timestamp = datetime.strptime(f"{timestamp_str} {current_year}", "%b %d %H:%M:%S %Y")
                            
                            # Adjust year if timestamp is in the future
                            if timestamp > datetime.now():
                                timestamp = timestamp.replace(year=current_year - 1)
                            
                            # Filter by date range
                            if start_date and timestamp < start_date:
                                continue
                            if end_date and timestamp > end_date:
                                continue
                                
                            events.append(SystemEvent(
                                timestamp=timestamp,
                                event_type=event_type,
                                details=f"From syslog: {line.strip()[:50]}...",
                                user=getpass.getuser()
                            ))
                except subprocess.SubprocessError:
                    pass  # Continue with other patterns if one fails
        except Exception as e:
            print_string(f"Error parsing {syslog_file}: {str(e)}")
    
    return events

def parse_auth_log(start_date=None, end_date=None):
    """Parse auth.log for login/logout events"""
    events = []
    
    auth_log_file = '/var/log/auth.log'
    if not os.path.exists(auth_log_file) or not os.access(auth_log_file, os.R_OK):
        return events
    
    try:
        # Extract login events
        cmd = ["grep", "-E", "session opened for user|Accepted password for", auth_log_file]
        output = subprocess.check_output(cmd, text=True)
        
        # Parse timestamps
        timestamp_pattern = re.compile(r'(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})')
        user_pattern = re.compile(r'for user (\w+)|for (\w+) from')
        current_year = datetime.now().year
        
        for line in output.split('\n'):
            if not line:
                continue
                
            timestamp_match = timestamp_pattern.search(line)
            user_match = user_pattern.search(line)
            
            if timestamp_match and user_match:
                timestamp_str = timestamp_match.group(1)
                username = user_match.group(1) or user_match.group(2)
                
                # Add the current year since auth.log doesn't include it
                timestamp = datetime.strptime(f"{timestamp_str} {current_year}", "%b %d %H:%M:%S %Y")
                
                # Adjust year if timestamp is in the future
                if timestamp > datetime.now():
                    timestamp = timestamp.replace(year=current_year - 1)
                
                # Filter by date range
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                    
                events.append(SystemEvent(
                    timestamp=timestamp,
                    event_type=SystemEventType.LOGIN,
                    details="User login from auth.log",
                    user=username
                ))
    except Exception as e:
        print_string(f"Error parsing auth.log: {str(e)}")
    
    return events

def extract_events_from_logs(start_date=None, end_date=None):
    """Extract system events from log files"""
    print_string(f"Extracting system events from logs...")
    
    all_events = []
    system = platform.system()
    
    if system == "Linux":
        # Try systemd journal first (modern systems)
        try:
            journal_events = parse_systemd_journal(start_date, end_date)
            all_events.extend(journal_events)
            print_string(f"Found {len(journal_events)} events in systemd journal")
        except Exception as e:
            print_string(f"Error parsing systemd journal: {str(e)}")
        
        # Try traditional syslog (older systems or additional events)
        try:
            syslog_events = parse_syslog(start_date, end_date)
            all_events.extend(syslog_events)
            print_string(f"Found {len(syslog_events)} events in syslog")
        except Exception as e:
            print_string(f"Error parsing syslog: {str(e)}")
        
        # Try auth.log for login events
        try:
            auth_events = parse_auth_log(start_date, end_date)
            all_events.extend(auth_events)
            print_string(f"Found {len(auth_events)} events in auth.log")
        except Exception as e:
            print_string(f"Error parsing auth.log: {str(e)}")
    elif system == "Darwin":  # macOS
        print_string("Log parsing for macOS is not yet implemented")
    elif system == "Windows":
        print_string("Log parsing for Windows is not yet implemented")
    else:
        print_string(f"Unsupported system: {system}")
    
    # Sort events by timestamp
    all_events.sort(key=lambda e: e.timestamp)
    
    return all_events

def save_events_to_storage(events):
    """Save extracted events to system storage"""
    if not events:
        print_string("No events to save")
        return 0
    
    # Group events by date
    events_by_date = {}
    for event in events:
        date_str = event.timestamp.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)
    
    # Save events for each date
    total_saved = 0
    for date_str, date_events in events_by_date.items():
        storage = SystemStorage(date_str)
        for event in date_events:
            storage.add_event(event)
            total_saved += 1
    
    return total_saved 