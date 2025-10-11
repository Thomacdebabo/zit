#!/usr/bin/env python3

import click
import subprocess
from datetime import datetime, timedelta
import os
import platform
import shutil
import getpass
from pathlib import Path
import re

from ..terminal import print_string
from .sys_storage import SystemStorage, SYS_DATA_DIR
from .sys_events import SystemEvent, SystemEventType
from .log_parser import extract_events_from_logs, save_events_to_storage


@click.group()
def sys_cli():
    """System events tracking for Zit time tracking"""
    pass


def get_current_user():
    """Get the current user name"""
    return getpass.getuser()


# @sys_cli.command("track")
# @click.argument('event_type', type=click.Choice([e.value for e in SystemEventType]))
# @click.option('--details', '-d', default="", help='Additional details about the event')
# @click.option('--user', '-u', default=get_current_user(), help='User who triggered the event')
# def track_event(event_type, details, user):
#     """Manually track a system event"""
#     event = SystemEvent(
#         timestamp=datetime.now(),
#         event_type=event_type,
#         details=details,
#         user=user
#     )

#     storage = SystemStorage()
#     storage.add_event(event)

#     print_string(f"Tracked {event_type} event: {details}")


@sys_cli.command("list")
@click.option(
    "--date",
    "-d",
    default=datetime.now().strftime("%Y-%m-%d"),
    help="List events for a specific date (format: YYYY-MM-DD)",
)
@click.option("--all", "-a", is_flag=True, help="List events for all dates")
@click.option("--n", "-n", type=int, help="List events for the last n days")
def list_events(date, all, n):
    """List system events"""
    if all:
        dates = SystemStorage.get_all_dates()
    elif n:
        dates = SystemStorage.get_all_dates()[-n:]
    elif date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print_string(f"Invalid date format. Please use YYYY-MM-DD")
            return
        dates = [date]
    else:
        dates = [datetime.now().strftime("%Y-%m-%d")]

    if not dates:
        print_string("No system events found.")
        return

    for date_str in dates:
        storage = SystemStorage(date_str)
        events = storage.get_events()

        if events:
            print_string(f"\n--- System Events for {date_str} ---")
            print_events(events)


def print_events(events, event_type=None):
    """Print events with optional type filtering"""
    filtered_events = events
    if event_type:
        filtered_events = [e for e in events if e.event_type == event_type]

    if not filtered_events:
        print_string("No matching events found.")
        return

    for event in filtered_events:
        details = f" ({event.details})" if event.details else ""
        print_string(
            f"{event.timestamp.strftime('%H:%M:%S')} - {event.event_type}{details}"
        )


# @sys_cli.command("startup")
# def track_startup():
#     """Track system startup"""
#     track_event.callback(event_type=SystemEventType.STARTUP.value, details="System started", user=get_current_user())

# @sys_cli.command("app")
# @click.argument('app_name')
# @click.option('--action', '-a', type=click.Choice(['launch', 'close']), default='launch',
#               help='App action (launch or close)')
# def track_app(app_name, action):
#     """Track application launch or close"""
#     event_type = SystemEventType.APP_LAUNCH if action == 'launch' else SystemEventType.APP_CLOSE
#     track_event.callback(event_type=event_type.value, details=app_name, user=get_current_user())

# @sys_cli.command("monitor")
# @click.option('--apps', '-a', multiple=True, help='Applications to monitor (e.g. firefox, vscode)')
# @click.option('--interval', '-i', type=int, default=30, help='Check interval in seconds')
# def monitor_system(apps, interval):
#     """Monitor system for events (startup, sleep, application launches)"""
#     print_string("Starting system event monitoring...")

#     system = platform.system()

#     if system == "Linux":
#         try:
#             # First check if we have psutil installed
#             import psutil
#             from .linux_monitor import monitor

#             # Use our Linux-specific monitor
#             monitor(interval=interval, apps=apps)
#             return
#         except ImportError:
#             print_string("The 'psutil' package is required for Linux monitoring.")
#             print_string("Install it with: pip install psutil")
#             return
#     elif system == "Darwin":  # macOS
#         print_string("macOS system monitoring is not yet implemented.")
#         print_string("You can manually track events using the 'track' command.")
#     elif system == "Windows":
#         print_string("Windows system monitoring is not yet implemented.")
#         print_string("You can manually track events using the 'track' command.")
#     else:
#         print_string(f"Unsupported system: {system}")
#         return


@sys_cli.command("import")
# @click.option('--start-date', help='Start date for log parsing (format: YYYY-MM-DD)')
# @click.option('--end-date', help='End date for log parsing (format: YYYY-MM-DD)')
@click.option("--n", "-n", type=int, help="Import events from the last n days")
def parse_logs(n):
    """Parse system logs to extract events like startup and sleep/wake"""

    # Validate date formats if provided
    if not n:
        n = 1
    start_date = datetime.now() - timedelta(days=n)
    end_date = datetime.now() + timedelta(days=1)
    events = extract_events_from_logs(start_date, end_date)

    if not events:
        print_string("No relevant system events found in logs.")
        return

    print_string("\nExtracted Events:")
    print_events(events)

    print_string("\nSaving events to storage...")
    num_saved = save_events_to_storage(events)
    print_string(f"Saved {num_saved} events.")


@sys_cli.command("remove")
@click.option(
    "--date", "-d", help="Remove events for a specific date (format: YYYY-MM-DD)"
)
@click.option("--all", "-a", is_flag=True, help="Remove all system event data")
@click.confirmation_option(prompt="Are you sure you want to remove system event data?")
def remove_data(date, all):
    """Remove system event data"""
    if all:
        if not SYS_DATA_DIR.exists():
            print_string("No system event data found.")
            return

        shutil.rmtree(SYS_DATA_DIR)
        print_string("All system event data has been removed.")
        return

    if date:
        storage = SystemStorage(date)
        storage.remove_data_file()
        print_string(f"System event data for {date} has been removed.")
    else:
        storage = SystemStorage()
        storage.remove_data_file()
        print_string("Today's system event data has been removed.")


@sys_cli.command("awake")
@click.option(
    "--date",
    "-d",
    default=datetime.now().strftime("%Y-%m-%d"),
    help="Show awake intervals for a specific date (format: YYYY-MM-DD)",
)
@click.option("--all", "-a", is_flag=True, help="Show awake intervals for all dates")
def show_awake_intervals(date, all):
    """Show intervals when the device was awake and calculate total awake time"""

    def process_events(events):
        awake_intervals = []
        current_start = None

        for event in events:
            if event.event_type == SystemEventType.WAKE and current_start is None:
                current_start = event.timestamp
            elif (
                event.event_type in [SystemEventType.SLEEP, SystemEventType.SHUTDOWN]
                and current_start is not None
            ):
                awake_intervals.append((current_start, event.timestamp))
                current_start = None
        # Handle case where system is still awake
        if current_start is not None:
            awake_intervals.append((current_start, datetime.now()))

        return awake_intervals

    def print_intervals(intervals, date_str):
        if not intervals:
            print_string(f"No awake intervals found for {date_str}")
            return

        total_awake = timedelta()
        print_string(f"\nAwake intervals for {date_str}:")

        for start, end in intervals:
            duration = end - start
            total_awake += duration
            print_string(
                f"  {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')} "
                f"({duration.total_seconds() / 3600:.2f} hours)"
            )

        print_string(
            f"\nTotal awake time: {total_awake.total_seconds() / 3600:.2f} hours"
        )

    if all:
        dates = SystemStorage.get_all_dates()
        if not dates:
            print_string("No system events found.")
            return

        for date_str in dates:
            storage = SystemStorage(date_str)
            events = storage.get_events()
            intervals = process_events(events)
            print_intervals(intervals, date_str)
    else:
        storage = SystemStorage(date)
        events = storage.get_events()
        intervals = process_events(events)
        print_intervals(intervals, date)


if __name__ == "__main__":
    sys_cli()
