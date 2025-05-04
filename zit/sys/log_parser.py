#!/usr/bin/env python3

import subprocess
import re
import os
from datetime import datetime, timedelta
import getpass
import platform
from pathlib import Path
import json

from .sys_storage import SystemStorage
from .sys_events import SystemEvent, SystemEventType
from ..terminal import print_string

def get_boot_events():
    cmd_boots = ["journalctl", "--list-boots", "--no-pager", "-o", "json"]
    output_boots = subprocess.check_output(cmd_boots, text=True)
    return output_boots

def get_other_events(start_date="today"):
    cmd_json = [
        "journalctl", f"--since={start_date}",
        "-o", "json", "--no-pager"
    ]
    output_json = subprocess.check_output(cmd_json, text=True)
    return output_json

def parse_boot_events(output_boots):
    events = []
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})")

    for line in output_boots.strip().split('\n'):
        match = pattern.search(line)
        if match:
            timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            events.append(SystemEvent(
                timestamp=timestamp,
                event_type=SystemEventType.STARTUP,
                details="System boot detected",
                user=getpass.getuser()
            ))
    return events

def parse_other_events(output_json):
    events = []
    for line in output_json.strip().split('\n'):
        entry = json.loads(line)
        event = create_event(entry)
        if event:
            events.append(event)
    return events

def create_event(entry):
    event_type = None
    user = getpass.getuser()
    message = entry.get("MESSAGE", "")
    timestamp_usec = entry.get("__REALTIME_TIMESTAMP")
    unit = entry.get("SYSLOG_IDENTIFIER", entry.get("_SYSTEMD_UNIT", ""))
    comm = entry.get("_COMM", "")

    timestamp = datetime.fromtimestamp(int(timestamp_usec) / 1_000_000)
    # Shutdown
    if message == "Finished System Power Off.": 
        event_type = SystemEventType.SHUTDOWN
        details = "System shutdown (Exact Match)"
    elif "systemd" in unit and "Finished System Power Off" in message: 
        event_type = SystemEventType.SHUTDOWN
        details = "System shutdown (Substring Match)"
    
    # Sleep/Wake 
    elif "systemd-sleep" in unit:
        if "Suspending" in message:
            event_type = SystemEventType.SLEEP
            details = "System sleep"
        elif "Woke up" in message:
            event_type = SystemEventType.WAKE
            details = "System wake"
    
    # Login
    elif comm == "login" and "New session" in message:
        match = re.search(r'for user (\w+)', message)
        if match:
            user = match.group(1)
        event_type = SystemEventType.LOGIN
        details = f"User login"

    # --- Append event if found --- 
    if event_type:
        return SystemEvent(
            timestamp=timestamp,
            event_type=event_type,
            details=details,
            user=user
        )
    return None

def get_auth_log():
    auth_log_file = '/var/log/auth.log'
    if not os.path.exists(auth_log_file) or not os.access(auth_log_file, os.R_OK):
        return []
    return auth_log_file

def create_login_event(line):
    timestamp_pattern = re.compile(r'(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})')
    user_pattern = re.compile(r'for user (\w+)|for (\w+) from')
    current_year = datetime.now().year

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
        

            
        return SystemEvent(
            timestamp=timestamp,
            event_type=SystemEventType.LOGIN,
            details="User login from auth.log",
            user=username
        )
    return None

def get_login_events(auth_log_file):
    cmd = ["grep", "-E", "session opened for user|Accepted password for", auth_log_file]
    output = subprocess.check_output(cmd, text=True)

    events = []
    for line in output.split('\n'):
        if not line:
            continue
        event = create_login_event(line)
        if event:
            events.append(event)
    return events

def parse_auth_log(start_date=None, end_date=None):
    """Parse auth.log for login/logout events"""
    events = []
    
    auth_log_file = get_auth_log()
    if not auth_log_file:
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

def create_sleep_wake_event(entry):
    """Create a SLEEP or WAKE event from a journalctl JSON entry"""
    message = entry.get("MESSAGE", "")
    timestamp_usec = entry.get("__REALTIME_TIMESTAMP")

    if not timestamp_usec:
        return None
        
    timestamp = datetime.fromtimestamp(int(timestamp_usec) / 1_000_000)
    event_type = None
    details = ""
    user = getpass.getuser()

    if "Reached" in message:
        event_type = SystemEventType.SLEEP
        details = "System sleep"
    elif "Stopped" in message:
        event_type = SystemEventType.WAKE
        details = "System wake"

    if event_type:
        return SystemEvent(
            timestamp=timestamp,
            event_type=event_type,
            details=details,
            user=user
        )
    return None

def get_sleep_wake_events(start_date=None):
    """Get SLEEP and WAKE events from journalctl"""
    events = []
    try:
        cmd = [
            "journalctl", f"--since=today", "-o", "json", "-u", "sleep.target"
        ]
        output = subprocess.check_output(cmd, text=True)
        
        for line in output.strip().split('\n'):
            try:
                entry = json.loads(line)
                event = create_sleep_wake_event(entry)
                if event:
                    events.append(event)
            except json.JSONDecodeError:
                continue # Ignore invalid JSON
            except Exception as e:
                print_string(f"Error parsing sleep/wake entry: {e}")
                continue
                
    except subprocess.SubprocessError as e:
        print_string(f"Error executing journalctl for sleep/wake events: {e}")
    except FileNotFoundError:
        print_string("Error: journalctl command not found.")
        
    return events

def extract_events_from_logs(start_date=None, end_date=None):
    """Extract system events from log files"""
    print_string(f"Extracting system events from logs...")
    if not start_date:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    all_events = []
    system = platform.system()
    
    if system == "Linux":
        
        boot_events = parse_boot_events(get_boot_events())
        filtered_boot_events = [event for event in boot_events if start_date <= event.timestamp <= end_date]
        all_events.extend(filtered_boot_events)
        print_string(f"Found {len(filtered_boot_events)} boot events in systemd journal")
        
        other_events = parse_other_events(get_other_events(start_date))
        all_events.extend(other_events)
        print_string(f"Found {len(other_events)} events in syslog")

        #login_events = parse_auth_log(start_date, end_date)
        #all_events.extend(login_events)
        #print_string(f"Found {len(login_events)} login events in auth.log")

        sleep_wake_events = get_sleep_wake_events(start_date)
        all_events.extend(sleep_wake_events)
        print_string(f"Found {len(sleep_wake_events)} sleep/wake events in systemd journal")

        

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