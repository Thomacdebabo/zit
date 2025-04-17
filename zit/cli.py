#!/usr/bin/env python3

import click
from .storage import Storage
from datetime import datetime
from .storage import Event

from .calculate import calculate_project_times
from .print import pretty_print_title, print_intervals, print_project_times, print_ongoing_interval, print_total_time, print_events_with_index
from .verify import verify_lunch, verify_stop

@click.group()
def cli():
    """Zit - Zimple Interval Tracker: A minimal time tracking CLI tool"""
    pass

@cli.command()
@click.argument('project', default='default')
def start(project):
    """Start tracking time for a project"""
    try:
        storage = Storage()
        storage.add_event(Event(timestamp=datetime.now(), project=project))
        click.echo(f"Started tracking time for project: {project}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
def stop():
    """Stop tracking time"""
    click.echo("Stopping time tracking...")
    storage = Storage()
    storage.add_event(Event(timestamp=datetime.now(), project="STOP"))

@cli.command()
@click.option('--yesterday', is_flag=True, help='Show status for yesterday')
def status(yesterday):
    """Show current tracking status"""
    storage = Storage()
    
    if yesterday:
        storage.set_to_yesterday()
    
    events = storage.get_events()
    
    if not events:
        day = "yesterday" if yesterday else "today"
        click.echo(f"No events found for {day}.")
        return
    
    pretty_print_title("Current status...")
    print_intervals(events)
    print_ongoing_interval(events[-1])

    project_times, sum, excluded = calculate_project_times(events, exclude_projects=storage.exclude_projects)
    
    print_project_times(project_times)
    print_total_time(sum, excluded)


@cli.command()
@click.argument('project')
@click.argument('time', metavar='TIME (format: HHMM)')
def add(project, time):
    """Add a project with a specific time (format: HHMM, e.g. 1200 for noon)"""
    try:
        # Parse the time format (HHMM)
        if len(time) != 4 or not time.isdigit():
            click.echo("Error: Time must be in HHMM format (e.g., 1200 for noon)", err=True)
            return
            
        hour = int(time[:2])
        minute = int(time[2:])
        
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            click.echo("Error: Invalid time values", err=True)
            return
            
        # Create a datetime object for today with the specified time
        now = datetime.now()
        event_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        storage = Storage()
        storage.add_event(Event(timestamp=event_time, project=project))
        click.echo(f"Added project: {project} at {event_time.strftime('%H:%M')}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
def clear():
    """Clear all data"""
    storage = Storage()
    storage.remove_data_file()
    click.echo("All data has been cleared.")

@cli.command()
def clean():
    """Clean the data"""
    storage = Storage()
    storage.clean_storage()
    click.echo("Data has been cleaned.")

@cli.command()
def verify():
    """Verify the data"""
    storage = Storage()
    events = storage.get_events()
    if verify_lunch(events):
        click.echo("✓ LUNCH event found")
    else:
        click.echo("✗ LUNCH event not found")
    if verify_stop(events):
        click.echo("✓ final STOP event found")
    else:
        click.echo("✗ final STOP event not found")
@cli.command()
def remove():
    """Remove the last event"""
    storage = Storage()
    events = storage.get_events()
    if len(events) == 0:
        click.echo("No events found. Operation aborted.")
        return
    print_events_with_index(events)
    index = click.prompt("Enter the index of the event to remove", type=int)
    if index < 0 or index >= len(events):
        click.echo("Invalid index. Operation aborted.")
        return
    events.pop(index)
    storage._write_events(events)
    click.echo("Event has been removed.")

if __name__ == '__main__':
    cli() 