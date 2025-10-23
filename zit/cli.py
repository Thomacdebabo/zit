#!/usr/bin/env python3

import click
from .terminal import (
    print_string,
    prompt_for_index,
    date_options,
    time_argument,
)
from .storage import Storage, SubtaskStorage
from datetime import datetime, timedelta
from .events import Project, Subtask
from .calculate import calculate_project_times
from .print import (
    print_intervals,
    print_ongoing_interval,
    print_project_times,
    print_total_time,
    pretty_print_title,
    print_events_with_index,
    print_events_and_subtasks,
    VerbosityLevel,
)
from .verify import verify_lunch, verify_stop, verify_no_default_project
from .fm.filemanager import ZitFileManager
from .time_utils import parse_time, verify_date, determine_date

from importlib.metadata import version, PackageNotFoundError


def pick_event(events):
    print_events_with_index(events)
    index = prompt_for_index()
    if index < 0 or index >= len(events):
        print_string("Invalid index. Operation aborted.")
        return None
    return events[index]


def get_version():
    try:
        return version("zit")
    except PackageNotFoundError:
        return "unknown"


@click.group()
@click.version_option(
    get_version(), "-v", "--version", message="Zit version: %(version)s"
)
def cli():
    """Zit - Zimple Interval Tracker: A minimal time tracking CLI tool"""
    pass


@cli.command()
@click.argument("project", default="DEFAULT")
def start(project: str):
    """Start tracking time for a project.

    Begin tracking time for the specified project. If no project name is provided,
    uses "DEFAULT" as the project name.

    Examples:
      zit start meeting
    """
    try:
        storage = Storage()
        storage.add_event(Project(timestamp=datetime.now(), name=project))
        print_string(f"Started tracking time for project: {project}")
    except ValueError as e:
        print_string(f"Error: {str(e)}", err=True)


@cli.command()
def stop():
    """Stop tracking time.

    End the current time tracking session by adding a STOP event.

    Examples:
      zit stop
    """
    print_string("Stopping time tracking...")
    storage = Storage()
    storage.add_event(Project(timestamp=datetime.now(), name="STOP"))


@cli.command()
@time_argument
def lunch(time: str):
    """Start tracking time for lunch.

    Add a LUNCH event at the current time or at a specific time if provided.
    Time format: HHMM (e.g., 1200 for noon, 1330 for 1:30 PM)

    Examples:
      zit lunch
      zit lunch 1200
      zit lunch 1330
    """
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
@date_options
def status(yesterday: bool, date: str):
    """Show current tracking status.

    Display the status of time tracking for today or a specified date, including
    all intervals, ongoing tasks, project time summaries, and total time.

    Flags:
      -y, --yesterday    Show status for yesterday
      -d, --date DATE    Show status for a specific date (format: YYYY-MM-DD)

    Examples:
      zit status
      zit status --yesterday
      zit status -y
      zit status --date 2025-10-15
      zit status -d 2025-10-15
    """
    day = determine_date(yesterday, date)
    storage = Storage(day)

    events = storage.get_events()
    if not events:
        print_string(f"No events found for {day}.")
        return

    pretty_print_title(f"Status for {day}...")
    print_intervals(events)
    print_ongoing_interval(events[-1])

    project_times, time_sum, excluded = calculate_project_times(
        events, exclude_projects=storage.exclude_projects
    )

    print_project_times(project_times)
    print_total_time(time_sum, excluded)


@cli.command()
@click.argument("project")
@time_argument
@click.option("--subtask", "--sub", "-s", is_flag=True, help="Add a subtask")
@click.option("--note", "-n", default="", help="Add a note to the project")
@date_options
def add(project: str, time: str, subtask: str, note: str, yesterday: bool, date: str):
    """Add a project or subtask with a specific time.

    Add a project event at the specified time. Time format is HHMM (e.g., 1200 for
    noon, 0930 for 9:30 AM). Can also add subtasks with the --subtask flag.

    Flags:
      -s, --subtask, --sub    Add a subtask instead of a main project
      -n, --note TEXT         Add a note to the project or subtask
      -y, --yesterday         Add the event for yesterday
      -d, --date DATE         Add the event for a specific date (format: YYYY-MM-DD)

    Examples:
      zit add MEETING 1400
      zit add CODING 0900 --note "Working on feature X"
      zit add "code review" 1530 --subtask
      zit add MEETING 1400 --yesterday
      zit add MEETING 1400 -d 2025-10-15
    """
    try:
        event_time = parse_time(time)
    except ValueError as e:
        print_string(f"Error: {str(e)}")
        return

    day = determine_date(yesterday, date)
    storage = Storage(day)

    if subtask:
        if storage.get_project_at_time(event_time) is None:
            print_string("No current task. No subtask added.")
            return
        sub_storage = SubtaskStorage(day)
        sub_storage.add_event(Subtask(timestamp=event_time, name=project, note=note))
        print_string(f"Added subtask: {project} at {event_time.strftime('%H:%M')}")
    else:
        storage.add_event(Project(timestamp=event_time, name=project))
        print_string(f"Added project: {project} at {event_time.strftime('%H:%M')}")


# @cli.command()
def clear():
    """Clear all data.

    Delete all time tracking data including projects and subtasks.
    This operation cannot be undone.

    Examples:
      zit clear
    """
    storage = Storage()
    storage.remove_data_file()

    sub_storage = SubtaskStorage()
    sub_storage.remove_data_file()
    print_string("All data has been cleared.")


@cli.command()
def clean():
    """Clean the data.

    Clean up the storage by removing any invalid or corrupted entries.

    Examples:
      zit clean
    """
    storage = Storage()
    storage.clean_storage()
    sub_storage = SubtaskStorage()
    sub_storage.clean_storage()
    print_string("Data has been cleaned.")


@cli.command()
@date_options
def verify(yesterday: bool, date: str):
    """Verify the data.

    Check the data for today or a specified date to ensure it contains required
    events (LUNCH, STOP) and has no DEFAULT projects or subtasks.

    Flags:
      -y, --yesterday    Verify the data for yesterday
      -d, --date DATE    Verify the data for a specific date (format: YYYY-MM-DD)

    Examples:
      zit verify
      zit verify --yesterday
      zit verify -d 2025-10-15
    """
    day = determine_date(yesterday, date)
    storage = Storage(day)

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

    if yesterday:
        sub_storage.set_to_yesterday()
    elif date:
        verify_date(date)
        sub_storage.set_to_date(date)

    if verify_no_default_project(sub_events):
        print_string("✓ no DEFAULT subtasks found")
    else:
        print_string("✗ DEFAULT subtasks found, please assign them to a project")


@cli.command()
@click.option(
    "--subtask",
    "--sub",
    "-s",
    is_flag=True,
    help="Remove a subtask instead of a main project",
)
@date_options
def remove(subtask: str, yesterday: bool, date: str):
    """Remove an event.

    Remove a project or subtask event by selecting it from a list.
    You will be prompted to choose which event to remove.

    Flags:
      -s, --subtask, --sub    Remove a subtask instead of a main project
      -y, --yesterday         Remove an event from yesterday
      -d, --date DATE         Remove an event from a specific date (format: YYYY-MM-DD)

    Examples:
      zit remove
      zit remove --subtask
      zit remove -s -y
      zit remove -d 2025-10-15
    """
    day = determine_date(yesterday, date)
    if subtask:
        storage = SubtaskStorage(day)
    else:
        storage = Storage(day)

    data_storage = storage._read_events()
    if len(data_storage) == 0:
        print_string("No events found. Operation aborted.")
        return
    print_events_with_index(data_storage.events)
    index = prompt_for_index()
    if index < 0 or index >= len(data_storage):
        print_string("Invalid index. Operation aborted.")
        return
    data_storage.remove_item(index)
    storage._write_events(data_storage)
    print_string("Event has been removed.")


@cli.command()
@click.option(
    "--subtask",
    "--sub",
    "-s",
    is_flag=True,
    help="Change a subtask instead of a main project",
)
@date_options
def change(subtask: str, yesterday: bool, date: str):
    """Change an event.

    Change the name of a project or subtask event by selecting it from a list.
    You will be prompted to choose which event to change and enter a new name.

    Flags:
      -s, --subtask, --sub    Change a subtask instead of a main project
      -y, --yesterday         Change an event from yesterday
      -d, --date DATE         Change an event from a specific date (format: YYYY-MM-DD)

    Examples:
      zit change
      zit change --subtask
      zit change -s -y
      zit change -d 2025-10-15
    """
    day = determine_date(yesterday, date)

    if subtask:
        storage = SubtaskStorage(day)
    else:
        storage = Storage(day)

    data_storage = storage._read_events()
    if len(data_storage) == 0:
        print_string("No events found. Operation aborted.")
        return

    print_events_with_index(data_storage.events)
    index = prompt_for_index()

    if index < 0 or index >= len(data_storage):
        print_string("Invalid index. Operation aborted.")
        return

    event = data_storage[index]
    name = click.prompt("Enter the new name", type=str)
    event.name = name
    data_storage[index] = event
    storage._write_events(data_storage)
    print_string("Event has been changed.")


@cli.command()
@click.argument("subtask", default="DEFAULT")
@click.option("--note", "-n", default="", help="Add a note to the subtask")
def sub(subtask: str, note: str):
    """Add a subtask.

    Add a subtask to the current project at the current time. If no subtask name
    is provided, uses "DEFAULT" as the subtask name.

    Flags:
      -n, --note TEXT    Add a note to the subtask

    Examples:
      zit sub "implement login"
      zit sub "fix bug" --note "Issue #123"
    """
    sub_storage = SubtaskStorage()
    storage = Storage()
    current_task = storage.get_current_task()
    if current_task is None:
        print_string("No current task. Operation aborted.")
        return

    sub_storage.add_event(Subtask(timestamp=datetime.now(), name=subtask, note=note))
    print_string(f"Added subtask: {subtask}")


@cli.command()
@click.argument("subtask")
@click.option("--note", "-n", default="", help="Add a note to the subtask")
def attach(subtask: str, note: str):
    """Attach a subtask to a main project"""
    storage = Storage()
    sub_storage = SubtaskStorage()
    events = storage.get_events()

    if len(events) == 0:
        print_string("No events found. Operation aborted.")
        return

    event = pick_event(events)

    if event is not None:
        sub_storage.add_event(
            Subtask(timestamp=event.timestamp, name=subtask, note=note)
        )
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
@click.option(
    "-v",
    "--verbosity",
    count=True,
    default=2,
    help="Increase verbosity level (-v: none, -vv: single line, -vvv: full notes)",
)
@date_options
@click.option("-p", "--pick", is_flag=True, help="Pick a date")
def list(verbosity: bool, pick: bool, yesterday: bool, date: str):
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
        day = files[index].stem
    else:
        day = determine_date(yesterday, date)

    sub_storage = SubtaskStorage(day)
    storage = Storage(day)

    events = storage.get_events()
    sub_events = sub_storage.get_events()

    if len(events) == 0:
        print_string("No events found.")
        return
    project_times, sum_prj, excluded = calculate_project_times(
        events, exclude_projects=storage.exclude_projects
    )
    print_events_and_subtasks(
        events, sub_events, project_times, VerbosityLevel(verbosity)
    )
    print_total_time(sum_prj, excluded)


@cli.command()
@click.argument("note")
@click.option("--pick", "-p", is_flag=True, help="Pick a subtask to add a note to")
def note(note: str, pick: bool):
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


if __name__ == "__main__":
    cli()
