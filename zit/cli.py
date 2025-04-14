#!/usr/bin/env python3

import click
from .storage import Storage
from datetime import datetime
from .storage import Event
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
def status():
    """Show current tracking status"""
    storage = Storage()
    events = storage._read_events()
    
    if not events:
        click.echo("No events found for today.")
        return
    project_times = {}
    click.echo("--------------------------------")
    click.echo("Current status...")
    click.echo("--------------------------------")
    for i in range(1, len(events)):
        start_event = events[i-1]
        end_event = events[i]
        start_time = datetime.fromisoformat(start_event[0])
        end_time = datetime.fromisoformat(end_event[0])
        interval = end_time - start_time
        project = start_event[1]  # Get the project name from the event
        hours, remainder = divmod(interval.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        click.echo(f"{project} - {int(hours)}:{int(minutes)}:{int(seconds)}")
        project_times[project] = project_times.get(project, 0) + interval.total_seconds()

    for event in events:
        if event[1] == "STOP":
            break
        click.echo(f"Ongoing project: {event[1]}")
    # time per project
    click.echo("Time per project:")
    click.echo("--------------------------------")
    sum = 0
    for project, total_time in project_times.items():
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        click.echo(f"{project} - {int(hours)}:{int(minutes)}:{int(seconds)}")
        if project != "STOP":
            sum += total_time
    click.echo("--------------------------------")
    click.echo(f"Total time: {int(sum / 3600)}:{int((sum % 3600) / 60)}:{int(sum % 60)}")
    
if __name__ == '__main__':
    cli() 