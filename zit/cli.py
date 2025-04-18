#!/usr/bin/env python3

import click
from .storage import Storage, SubtaskStorage
from datetime import datetime
from .storage import Project, Subtask

from .calculate import *
from .print import *
from .verify import *

@click.group()
def cli():
    """Zit - Zimple Interval Tracker: A minimal time tracking CLI tool"""
    pass

@cli.command()
@click.argument('project', default='DEFAULT')
def start(project):
    """Start tracking time for a project"""
    try:
        storage = Storage()
        storage.add_event(Project(timestamp=datetime.now(), name=project))
        click.echo(f"Started tracking time for project: {project}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
def stop():
    """Stop tracking time"""
    click.echo("Stopping time tracking...")
    storage = Storage()
    storage.add_event(Project(timestamp=datetime.now(), name="STOP"))

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
@click.option('--subtask', '--sub', '-s', is_flag=True, help='Add a subtask')
@click.option('--note', '-n', default="", help='Add a note to the project')
def add(project, time, subtask, note):
    """Add a project with a specific time (format: HHMM, e.g. 1200 for noon)
    Use --subtask (or --sub, -s) flag to add a subtask instead of a main project"""
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
        if subtask:
            if storage.get_project_at_time(event_time) is None:
                click.echo("No current task. No subtask added.")
                return
            sub_storage = SubtaskStorage()
            sub_storage.add_event(Subtask(timestamp=event_time, name=project, note=note))
            click.echo(f"Added subtask: {project} at {event_time.strftime('%H:%M')}")
        else:
            
            storage.add_event(Project(timestamp=event_time, name=project))
            click.echo(f"Added project: {project} at {event_time.strftime('%H:%M')}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
def clear():
    """Clear all data"""
    storage = Storage()
    storage.remove_data_file()

    sub_storage = SubtaskStorage()
    sub_storage.remove_data_file()
    click.echo("All data has been cleared.")

@cli.command()
def clean():
    """Clean the data"""
    storage = Storage()
    storage.clean_storage()
    sub_storage = SubtaskStorage()
    sub_storage.clean_storage()
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
    if verify_no_default_project(events):
        click.echo("✓ no DEFAULT times found")
    else:
        click.echo("✗ DEFAULT times found, please assign them to a project")

    sub_storage = SubtaskStorage()
    sub_events = sub_storage.get_events()  
    if verify_no_default_project(sub_events):
        click.echo("✓ no DEFAULT subtasks found")
    else:
        click.echo("✗ DEFAULT subtasks found, please assign them to a project")

@cli.command()
@click.option('--subtask', '--sub', '-s', is_flag=True, help='Remove a subtask instead of a main project')
def remove(subtask):
    """Remove the last event"""
    if subtask:
        storage = SubtaskStorage()
    else:
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

@cli.command()
@click.option('--subtask', '--sub', '-s', is_flag=True, help='Change a subtask instead of a main project')
def change(subtask):
    """Change an event"""
    if subtask:
        storage = SubtaskStorage()
    else:
        storage = Storage()

    events = storage.get_events()
    if len(events) == 0:
        click.echo("No events found. Operation aborted.")
        return

    print_events_with_index(events)
    index = click.prompt("Enter the index of the event to change", type=int)

    if index < 0 or index >= len(events):
        click.echo("Invalid index. Operation aborted.")
        return

    event = events[index]
    name = click.prompt("Enter the new name", type=str)
    event.name = name
    storage._write_events(events)
    click.echo("Event has been changed.")

@cli.command()
@click.argument('subtask', default="DEFAULT")
@click.option('--note', '-n', default="", help='Add a note to the subtask')
def sub(subtask, note):
    """Add a subtask"""
    sub_storage = SubtaskStorage()
    storage = Storage()
    current_task = storage.get_current_task()
    if current_task is None:
        click.echo("No current task. Operation aborted.")
        return
    
    sub_storage.add_event(Subtask(timestamp=datetime.now(), name=subtask, note=note))
    click.echo(f"Added subtask: {subtask}")

@cli.command()
@click.argument('subtask')
def attach(subtask):
    """Attach a subtask to a main project"""
    storage = Storage()
    sub_storage = SubtaskStorage()
    events = storage.get_events()
    if len(events) == 0:
        click.echo("No events found. Operation aborted.")
        return
    print_events_with_index(events)
    index = click.prompt("Enter the index of the event to attach", type=int)
    if index < 0 or index >= len(events):
        click.echo("Invalid index. Operation aborted.")
        return
    event = events[index]
    sub_storage.add_event(Subtask(timestamp=event.timestamp, name=subtask))
    click.echo(f"Subtask {subtask} attached to {event.project}")
    
@cli.command()
def current():
    """Show the current task"""
    storage = Storage()
    current_task = storage.get_current_task()
    if current_task is None:
        click.echo("No current task.")
        return
    click.echo(f"Current task: {current_task}")

@cli.command()
@click.option('-v', '--verbosity', count=True, default=2, help='Increase verbosity level (-v: none, -vv: single line, -vvv: full notes)')
def list(verbosity):
    """List all subtasks"""
    sub_storage = SubtaskStorage()
    storage = Storage()

    events = storage.get_events()
    sub_events = sub_storage.get_events()
    project_times, sum, excluded = calculate_project_times(events, exclude_projects=storage.exclude_projects)
    print_events_and_subtasks(events, sub_events, project_times, VerbosityLevel(verbosity))
    print_total_time(sum, excluded)

@cli.command()
@click.argument('note')
@click.option('--pick', '-p', is_flag=True, help='Pick a subtask to add a note to')
def note(note, pick):
    """Add a note to the current task"""
    sub_storage = SubtaskStorage()
    events = sub_storage.get_events()
    if len(events) == 0:
        click.echo("No current task. Operation aborted.")
        return
    if pick:
        print_events_with_index(events)
        index = click.prompt("Enter the index of the event to add a note to", type=int)
        if index < 0 or index >= len(events):
            click.echo("Invalid index. Operation aborted.")
            return
        event = events[index]
    else:
        event = events[-1]

    if event.note:
        click.echo(f"Subtask: {event.name}")
        click.echo(f"Current note: {event.note}")
        if click.confirm("Do you want to overwrite the note?"):
            event.note = note   
            sub_storage._write_events(events)
            click.echo(f"Added note to {event.name}: {note}")
        else:
            click.echo("Note not overwritten.")
    else:
        event.note = note
        sub_storage._write_events(events)
        click.echo(f"Added note to {event.name}: {note}")
if __name__ == '__main__':
    cli() 