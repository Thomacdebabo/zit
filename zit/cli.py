#!/usr/bin/env python3

import click
from .terminal import *
from .storage import Storage, SubtaskStorage
from datetime import datetime
from .storage import Project, Subtask

from .calculate import *
from .print import *
from .verify import *
from .filemanager import ZitFileManager

def parse_time(time):
            # Parse the time format (HHMM)
    if len(time) != 4 or not time.isdigit():
        raise ValueError("Time must be in HHMM format (e.g., 1200 for noon)")
        
    hour = int(time[:2])
    minute = int(time[2:])
        
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Invalid time values")
    now = datetime.now()
    event_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return event_time

def pick_event(events):
    print_events_with_index(events)
    index = prompt_for_index()
    if index < 0 or index >= len(events):
        print_string("Invalid index. Operation aborted.")
        return None
    return events[index]
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
        print_string(f"Started tracking time for project: {project}")
    except ValueError as e:
        print_string(f"Error: {str(e)}", err=True)

@cli.command()
def stop():
    """Stop tracking time"""
    print_string("Stopping time tracking...")
    storage = Storage()
    storage.add_event(Project(timestamp=datetime.now(), name="STOP"))

@cli.command()
@click.argument('time', required=False, default=None, metavar='TIME (format: HHMM)')
def lunch(time):
    """Start tracking time for lunch"""

    print_string("Starting lunch time tracking...")
    if time:
        try:
            event_time = parse_time(time)
        except ValueError as e:
            print_string(f"Error: {str(e)}", err=True)
            return
    else:
        event_time = datetime.now()
    storage = Storage()
    storage.add_event(Project(timestamp=event_time, name="LUNCH"))

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
        print_string(f"No events found for {day}.")
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
        event_time = parse_time(time) 
    except ValueError as e:
        print_string(f"Error: {str(e)}", err=True)
        return
    # Create a datetime object for today with the specified time

    storage = Storage()
    if subtask:
        if storage.get_project_at_time(event_time) is None:
            print_string("No current task. No subtask added.")
            return
        sub_storage = SubtaskStorage()
        sub_storage.add_event(Subtask(timestamp=event_time, name=project, note=note))
        print_string(f"Added subtask: {project} at {event_time.strftime('%H:%M')}")
    else:
        
        storage.add_event(Project(timestamp=event_time, name=project))
        print_string(f"Added project: {project} at {event_time.strftime('%H:%M')}")


@cli.command()
def clear():
    """Clear all data"""
    storage = Storage()
    storage.remove_data_file()

    sub_storage = SubtaskStorage()
    sub_storage.remove_data_file()
    print_string("All data has been cleared.")

@cli.command()
def clean():
    """Clean the data"""
    storage = Storage()
    storage.clean_storage()
    sub_storage = SubtaskStorage()
    sub_storage.clean_storage()
    print_string("Data has been cleaned.")

@cli.command()
def verify():
    """Verify the data"""
    storage = Storage()
    events = storage.get_events()
    if verify_lunch(events):
        print_string("✓ LUNCH event found")
    else:
        print_string("✗ LUNCH event not found")
    if verify_stop(events):
        print_string("✓ final STOP event found")
    else:
        print_string("✗ final STOP event not found")
    if verify_no_default_project(events):
        print_string("✓ no DEFAULT times found")
    else:
        print_string("✗ DEFAULT times found, please assign them to a project")

    sub_storage = SubtaskStorage()
    sub_events = sub_storage.get_events()  
    if verify_no_default_project(sub_events):
        print_string("✓ no DEFAULT subtasks found")
    else:
        print_string("✗ DEFAULT subtasks found, please assign them to a project")

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
        print_string("No events found. Operation aborted.")
        return
    print_events_with_index(events)
    index = prompt_for_index()
    if index < 0 or index >= len(events):
        print_string("Invalid index. Operation aborted.")
        return
    events.pop(index)
    storage._write_events(events)
    print_string("Event has been removed.")

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
        print_string("No events found. Operation aborted.")
        return

    print_events_with_index(events)
    index = prompt_for_index()

    if index < 0 or index >= len(events):
        print_string("Invalid index. Operation aborted.")
        return

    event = events[index]
    name = click.prompt("Enter the new name", type=str)
    event.name = name
    storage._write_events(events)
    print_string("Event has been changed.")

@cli.command()
@click.argument('subtask', default="DEFAULT")
@click.option('--note', '-n', default="", help='Add a note to the subtask')
def sub(subtask, note):
    """Add a subtask"""
    sub_storage = SubtaskStorage()
    storage = Storage()
    current_task = storage.get_current_task()
    if current_task is None:
        print_string("No current task. Operation aborted.")
        return
    
    sub_storage.add_event(Subtask(timestamp=datetime.now(), name=subtask, note=note))
    print_string(f"Added subtask: {subtask}")

@cli.command()
@click.argument('subtask')
@click.option('--note', '-n', default="", help='Add a note to the subtask')
def attach(subtask, note):
    """Attach a subtask to a main project"""
    storage = Storage()
    sub_storage = SubtaskStorage()
    events = storage.get_events()

    if len(events) == 0:
        print_string("No events found. Operation aborted.")
        return
    
    event = pick_event(events)

    if event is not None:
        sub_storage.add_event(Subtask(timestamp=event.timestamp, name=subtask, note=note))
        print_string(f"Subtask {subtask} attached to {event.name}")
    else:
        print_string("Operation aborted.")
    
@cli.command()
def current():
    """Show the current task"""
    storage = Storage()
    current_task = storage.get_current_task()
    if current_task is None:
        print_string("No current task.")
        return
    print_string(f"Current task: {current_task}")

@cli.command()
@click.option('-v', '--verbosity', count=True, default=2, help='Increase verbosity level (-v: none, -vv: single line, -vvv: full notes)')
@click.option('-p', '--pick', is_flag=True, help='Pick a date')

def list(verbosity, pick):
    """List all subtasks"""
    if pick:
        zfm = ZitFileManager()
        files = sorted(zfm.get_all_dates())

        for i, f in enumerate(files):
            print_string(f"[{i}] {f.stem}")  

        index = prompt_for_index()

        if index < 0 or index >= len(files):
            print_string("Invalid index. Operation aborted.")
            return
        
        storage = Storage(files[index].stem)
        sub_storage = SubtaskStorage(files[index].stem)
    else:
        sub_storage = SubtaskStorage()
        storage = Storage()

    events = storage.get_events()
    sub_events = sub_storage.get_events()

    if len(events) == 0:
        print_string("No events found.")
        return
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
        print_string("No current task. Operation aborted.")
        return
    if pick:
        event = pick_event(events)
        if event is None:
            print_string("Operation aborted.")
            return
    else:
        event = events[-1]

    if event.note:
        print_string(f"Subtask: {event.name}")
        print_string(f"Current note: {event.note}")
        if click.confirm("Do you want to overwrite the note?"):
            event.note = note   
            sub_storage._write_events(events)
            print_string(f"Added note to {event.name}: {note}")
        else:
            print_string("Note not overwritten.")
    else:
        event.note = note
        sub_storage._write_events(events)
        print_string(f"Added note to {event.name}: {note}")
if __name__ == '__main__':
    cli() 