#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
from pathlib import Path
from .filemanager import ZitFileManager
# We might need printing functions later, similar to cli.py
from .print import print_events_with_index, print_project_times, total_seconds_2_hms # Import the necessary print function
import sys # Import sys for exit
from collections import defaultdict # Import defaultdict for aggregating times
from .storage import Storage, SubtaskStorage, Project, Subtask
from .calculate import calculate_project_times
def build_project_dict(events: list[Project | Subtask]):
    project_dict = {}
    for event in events:
        if event.name not in project_dict:
            project_dict[event.name] = []
        project_dict[event.name].append(event)
    return project_dict

def parse_date(date_str: str) -> datetime | None:
    """Helper function to parse YYYY-MM-DD date strings."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
def print_files(files):
    total_sum = 0
    for i, file in enumerate(files) :
        click.echo(f"[{i}] {file.stem}")
        # Get the events for this file
        storage = Storage()
        storage.data_file = storage.data_dir / file
        events = storage.get_events()

        if events:
            # Group events by project
            project_times, sum, excluded = calculate_project_times(events)
            
            # Print project times for this day
            if project_times:
                for project, duration in sorted(project_times.items()):
                    hms = total_seconds_2_hms(duration)
                    is_last = project == sorted(project_times.keys())[-1]
                    prefix = "    └── " if is_last else "    ├── "
                    click.echo(f"{prefix}{project}: {hms}")

        click.echo(f"   Total: {total_seconds_2_hms(sum)}")
        total_sum += sum
    click.echo("------")
    click.echo(f"Total: {total_seconds_2_hms(total_sum)}")
@click.group()
def fm():
    """Zit FileManager - Manage historical Zit data"""
    pass

@fm.command(name='list') # New command list-all
@click.option('--all', '-a', is_flag=True, help='Show all files')   
def list_all_files(all):
    """List all available data files."""
    manager = ZitFileManager()
    if all:
        files = sorted(manager.get_all_dates())
    else:
        files = sorted(manager.get_all_dates())[-10:]
    if not files:
        click.echo("No data files found.")
        return
    
    click.echo("Available data files:")
    print_files(files)

@fm.command(name='remove')
def remove_file():
    """Remove a data file by its index number."""
    manager = ZitFileManager()
    files = sorted(manager.get_all_dates())
    
    if not files:
        click.echo("No data files found.")
        return
    print_files(files)
    file_index = click.prompt("Enter the index of the file to remove", type=int)

    if file_index < 0 or file_index >= len(files):
        click.echo(f"Error: Invalid file index. Please choose between 0 and {len(files)-1}.", err=True)
        sys.exit(1)
    
    file_to_remove = files[file_index]
    if click.confirm(f"Are you sure you want to remove {file_to_remove.stem}?"):
        try:
            storage = Storage()
            storage.data_file = storage.data_dir / file_to_remove
            storage.remove_data_file()
            subtask_storage = SubtaskStorage()
            subtask_storage.data_file = subtask_storage.data_dir / file_to_remove
            subtask_storage.remove_data_file()
            click.echo(f"Successfully removed {file_to_remove.stem}")
        except Exception as e:
            click.echo(f"Error removing file: {str(e)}", err=True)
            sys.exit(1)

def status(start_date, end_date):
    """Show total time spent on each project within a date range."""
    manager = ZitFileManager()

    # Default date range: last 7 days
    end_dt = parse_date(end_date) if end_date else datetime.now().replace(hour=23, minute=59, second=59) # End of day today
    start_dt = parse_date(start_date) if start_date else end_dt - timedelta(days=7)
    start_dt = start_dt.replace(hour=0, minute=0, second=0) # Start of day

    if start_date and not start_dt:
        click.echo("Error: Invalid start date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)
    if end_date and not end_dt:
        click.echo("Error: Invalid end date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)
        
    if start_dt > end_dt:
        click.echo("Error: Start date cannot be after end date.", err=True)
        sys.exit(1)

    click.echo(f"Calculating project times from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")

    events = manager.get_all_events(start_dt, end_dt)

    if not events or len(events) < 2:
        click.echo("Not enough event data found to calculate times.")
        return

    # Calculate project times from the sorted events
    project_times = defaultdict(float) # Use float for total seconds
    total_duration_seconds = 0.0
    # TODO: Handle exclude_projects similar to cli.py status?
    # TODO: Handle STOP events correctly if they exist in historical data?
    
    for i in range(len(events) - 1):
        start_event = events[i]
        end_event = events[i+1]
        # Basic duration calculation
        duration = (end_event.timestamp - start_event.timestamp).total_seconds()
        
        # Check if the interval spans across midnight, maybe needs adjustment? Currently simple diff.
        
        # Assign duration to the project of the start_event
        # Consider excluding specific projects like 'STOP' or 'LUNCH' if needed
        project_name = start_event.name
        if project_name.upper() != "STOP": # Simple exclusion of STOP
            project_times[project_name] += duration
            total_duration_seconds += duration
        # Else: potentially track excluded time if needed

    if not project_times:
        click.echo("No project time data calculated.")
        return

    # Print using the imported functions
    print_project_times(project_times)
    click.echo("------") # Separator
    click.echo(f"Total Tracked Time: {total_seconds_2_hms(total_duration_seconds)}")

if __name__ == '__main__':
    fm()
