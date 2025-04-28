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
from .calculate import calculate_project_times, add_project_times
from .events import sort_events, create_subtask_dict
from .filemanager import ZitFileManager
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
        storage = Storage(file.stem)
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
            storage = Storage(file_to_remove.stem)
            storage.remove_data_file()
            subtask_storage = SubtaskStorage(file_to_remove.stem)
            subtask_storage.remove_data_file()
            click.echo(f"Successfully removed {file_to_remove.stem}")
        except Exception as e:
            click.echo(f"Error removing file: {str(e)}", err=True)
            sys.exit(1)

@fm.command(name='status')
@click.option('--all', '-a', is_flag=True, help='Show all projects')

def status(all):
    """Show total time spent on each project within a date range."""
    manager = ZitFileManager()
    if all:
        dates = manager.get_all_dates()
    else:
        dates = manager.get_all_dates()[-10:]

    project_times = {}
    for date in dates:
        storage = Storage(date.stem)
        events = storage.get_events()
        if events:
            pt,_,_ = calculate_project_times(events)
            project_times = add_project_times(project_times, pt)
    print_project_times(project_times)

@fm.command(name='lprojects')
def lprojects():
    """List all projects in all files."""
    manager = ZitFileManager()
    files = sorted(manager.get_all_dates())
    all_projects = set()
    
    for file in files:
        click.echo(f"[{file.stem}]")
        storage = Storage(file.stem)
        sub_storage = SubtaskStorage(file.stem)
        events = storage.get_events()
        
        sub_events = sub_storage.get_events()
        all_events = sort_events(events, sub_events)
        subtask_dict = create_subtask_dict(all_events)

        for project, subtasks in subtask_dict.items():
            if project in storage.exclude_projects:
                continue
            click.echo(f"{project}:")
            for subtask in subtasks:
                click.echo(f"  {subtask.name}")

    for project in sorted(all_projects):
        if project not in storage.exclude_projects:
            click.echo(project)



if __name__ == '__main__':
    fm()
