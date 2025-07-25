#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
from pathlib import Path
from .filemanager import ZitFileManager
from ..terminal import *
# We might need printing functions later, similar to cli.py
from ..print import print_events_with_index, print_project_times, total_seconds_2_hms # Import the necessary print function
import sys # Import sys for exit
from collections import defaultdict # Import defaultdict for aggregating times
from ..storage import Storage, SubtaskStorage, Project, Subtask
from ..calculate import calculate_project_times, add_project_times
from ..events import sort_events, create_subtask_dict
from .filemanager import ZitFileManager
from ..verify import verify_all
def parse_date(date_str: str) -> datetime | None:
    """Helper function to parse YYYY-MM-DD date strings."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def print_files(files, verbose=False):
    total_sum = 0
    for i, file in enumerate(files) :
        
        # Get the events for this file
        storage = Storage(file.stem)
        events = storage.get_events()
        if events:
            project_times, sum, excluded = calculate_project_times(events, exclude_projects=storage.exclude_projects, add_ongoing=False)
            verified = verify_all(events)
            mark = "✔" if verified else "✗"
            print_string(f"[{i}] {file.stem}            Total: {total_seconds_2_hms(sum)} | {mark}")

            for exclude_project in storage.exclude_projects:
                project_times.pop(exclude_project, None)

            if project_times and verbose:
                for project, duration in sorted(project_times.items()):
                    hms = total_seconds_2_hms(duration)
                    is_last = project == sorted(project_times.keys())[-1]
                    prefix = "    └── " if is_last else "    ├── "
                    print_string(f"{prefix}{project}: {hms}")

        total_sum += sum
    print_string("------")
    print_string(f"Total: {total_seconds_2_hms(total_sum)}")
@click.group()
def fm():
    """Zit FileManager - Manage historical Zit data"""
    pass

@fm.command(name='list') # New command list-all
@click.option('--n', '-n', type=int, help='Show last n files')   
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def list_all_files(n, verbose):
    """List all available data files."""
    manager = ZitFileManager()
    if n:
        files = sorted(manager.get_all_dates())[-n:]
    else:
        files = sorted(manager.get_all_dates())
    if not files:
        print_string("No data files found.")
        return
    
    print_string("Available data files:")
    print_files(files, verbose)

@fm.command(name='remove')
def remove_file():
    """Remove a data file by its index number."""
    manager = ZitFileManager()
    files = sorted(manager.get_all_dates())
    
    if not files:
        print_string("No data files found.")
        return
    print_files(files)
    file_index = prompt_for_index()

    if file_index < 0 or file_index >= len(files):
        print_string(f"Error: Invalid file index. Please choose between 0 and {len(files)-1}.", err=True)
        sys.exit(1)
    
    file_to_remove = files[file_index]
    if click.confirm(f"Are you sure you want to remove {file_to_remove.stem}?"):
        try:
            storage = Storage(file_to_remove.stem)
            storage.remove_data_file()
            subtask_storage = SubtaskStorage(file_to_remove.stem)
            subtask_storage.remove_data_file()
            print_string(f"Successfully removed {file_to_remove.stem}")
        except Exception as e:
            print_string(f"Error removing file: {str(e)}", err=True)
            sys.exit(1)

@fm.command(name='status')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
@click.option('--n', '-n', type=int, help='Show last n dates')
def status(verbose, n):
    """Show total time spent on each project within a date range."""
    manager = ZitFileManager()
    if n:
        dates = manager.get_all_dates()[-n:]
    else:
        dates = manager.get_all_dates()

    project_times = {}
    for date in dates:
        storage = Storage(date.stem)
        events = storage.get_events()
        if events:
            pt,_,_ = calculate_project_times(events, exclude_projects=storage.exclude_projects, add_ongoing=False)

            project_times = add_project_times(project_times, pt)
        for exclude_project in storage.exclude_projects:
            project_times.pop(exclude_project, None)
    print_project_times(project_times)


# @fm.command(name='lprojects')
# def lprojects():
#     """List all projects in all files."""
#     manager = ZitFileManager()
#     files = sorted(manager.get_all_dates())
#     all_projects = set()
    
#     for file in files:
#         print_string(f"[{file.stem}]")
#         storage = Storage(file.stem)
#         sub_storage = SubtaskStorage(file.stem)
#         events = storage.get_events()
        
#         sub_events = sub_storage.get_events()
#         all_events = sort_events(events, sub_events)
#         subtask_dict = create_subtask_dict(all_events)

#         for project, subtasks in subtask_dict.items():
#             if project in storage.exclude_projects:
#                 continue
#             print_string(f"{project}:")
#             for subtask in subtasks:
#                 print_string(f"  {subtask.name}")

#     for project in sorted(all_projects):
#         if project not in storage.exclude_projects:
#             print_string(project)



if __name__ == '__main__':
    fm()
