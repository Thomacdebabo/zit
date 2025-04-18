#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
from pathlib import Path
from .filemanager import ZitFileManager
# We might need printing functions later, similar to cli.py
from .print import print_events_with_index, print_project_times, total_seconds_2_hms # Import the necessary print function
import sys # Import sys for exit
from collections import defaultdict # Import defaultdict for aggregating times

def parse_date(date_str: str) -> datetime | None:
    """Helper function to parse YYYY-MM-DD date strings."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

@click.group()
def fm():
    """Zit FileManager - Manage historical Zit data"""
    pass

@fm.command(name='list-all') # New command list-all
def list_all_files():
    """List all available data files."""
    manager = ZitFileManager()
    files = manager.get_all_files()
    if not files:
        click.echo("No data files found.")
        return
    
    click.echo("Available data files:")
    for file in sorted(files):
        click.echo(f"- {file.name}")

@fm.command(name='list-range') # Renamed command
@click.option('--start-date', '-s', type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', type=str, help='End date (YYYY-MM-DD)')
def list_files_in_range(start_date, end_date):
    """List available data files within a specific date range."""
    manager = ZitFileManager()
    
    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None

    if start_date and not start_dt:
        click.echo("Error: Invalid start date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)
    if end_date and not end_dt:
        click.echo("Error: Invalid end date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)

    if start_dt and end_dt and start_dt > end_dt:
        click.echo("Error: Start date cannot be after end date.", err=True)
        sys.exit(1)

    # Default to a large range if only one date is provided
    if start_dt and not end_dt:
        end_dt = datetime.now() + timedelta(days=365*10) # Far future default end
    if end_dt and not start_dt:
        start_dt = datetime.now() - timedelta(days=365*10) # Far past default start

    if start_dt and end_dt:
        files = manager.get_files_in_date_range(start_dt, end_dt)
        click.echo(f"Data files between {start_dt.strftime('%Y-%m-%d')} and {end_dt.strftime('%Y-%m-%d')}:")
    else:
        # This case should ideally not be hit if options are mandatory or have defaults,
        # but keeping it for safety. It duplicates list-all behavior.
        files = manager.get_all_files()
        click.echo("All available data files:") 

    if not files:
        click.echo("No data files found.")
        return
    
    # Print sorted file names
    for file in sorted(files):
        click.echo(f"- {file.name}")

@fm.command()
@click.option('--start-date', '-s', type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', type=str, help='End date (YYYY-MM-DD)')
@click.option('--project', '-p', type=str, help='Filter by project name')
def show(start_date, end_date, project):
    """Show events, optionally filtered by date range and/or project."""
    manager = ZitFileManager()

    # Default date range: last 7 days
    end_dt = parse_date(end_date) if end_date else datetime.now()
    start_dt = parse_date(start_date) if start_date else end_dt - timedelta(days=7)

    if start_date and not start_dt:
        click.echo("Error: Invalid start date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)
    if end_date and not end_dt:
        click.echo("Error: Invalid end date format. Use YYYY-MM-DD.", err=True)
        sys.exit(1)
        
    if start_dt > end_dt:
        click.echo("Error: Start date cannot be after end date.", err=True)
        sys.exit(1)

    click.echo(f"Showing events from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
    if project:
        click.echo(f"Filtering for project: {project}")
        events = manager.get_project_events(project, start_dt, end_dt)
    else:
        events = manager.get_all_events(start_dt, end_dt)

    if not events:
        click.echo("No events found for the specified criteria.")
        return

    print_events_with_index(events) # Use the imported print function

@fm.command()
@click.option('--start-date', '-s', type=str, help='Start date (YYYY-MM-DD), defaults to 7 days ago')
@click.option('--end-date', '-e', type=str, help='End date (YYYY-MM-DD), defaults to today')
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
