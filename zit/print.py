import click
from .calculate import calculate_interval, calculate_ongoing_interval
from .events import *
from enum import Enum, auto

DEFAULT_MAX_WIDTH = 70

class VerbosityLevel(Enum):
    NO_NOTES = auto()
    SINGLE_LINE_NOTES = auto()
    FULL_NOTES = auto()

def date_2_str(date):
    return date.strftime('%Y-%m-%d')

def time_2_str(time):
    return f"{time.hour:02d}:{time.minute:02d}:{time.second:02d}"

def interval_2_hms(interval):
    return total_seconds_2_hms(interval.total_seconds())


def total_seconds_2_hms(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'

def split_line(text: str, max_length: int) -> list[str]:
    lines = []
    while text:
        if len(text) <= max_length:
            lines.append(text.rstrip())
            break
        split_point = text[:max_length].rfind(' ')
        if split_point == -1:
            split_point = max_length
        lines.append(text[:split_point].rstrip())
        text = text[split_point:].lstrip()
    return lines

def pretty_print_title(title):
    width = max(len(title) + 10, DEFAULT_MAX_WIDTH)
    click.echo("┌" + "─" * (width-2) + "┐")
    click.echo(f"│ {title}".ljust(width-1, " ") + "│")
    click.echo("└" + "─" * (width-2) + "┘")
def print_interval(event1, event2):
    interval = calculate_interval(event1, event2)
    click.echo(f"{event1.name} - {interval_2_hms(interval)} ( {time_2_str(event1.timestamp)} -> {time_2_str(event2.timestamp)})")

def print_intervals(events):
    for i in range(1, len(events)):
        start_event = events[i-1]
        end_event = events[i]
        print_interval(start_event, end_event)

def print_events_and_subtasks(events, sub_events, project_times, verbosity: VerbosityLevel = VerbosityLevel.FULL_NOTES):
    pretty_print_title("Events and Subtasks:")
    

    all_events = []
    max_project_length = 0
    all_events = sort_events(events, sub_events)
    
    pad_length = max(max_project_length + 10, DEFAULT_MAX_WIDTH-20)

    # Print events in chronological order
    for i, event in enumerate(all_events):
        print_string = ""
        print_note = ""
        if check_type(event, Project):
            if event.name in ["STOP"]:
                print_string += "  └─"
            else:
                print_string += event.name + " "
            print_string = print_string.ljust(pad_length, "─")
        else:
            if i + 1 < len(all_events) and (check_type(all_events[i+1], Subtask) or all_events[i+1].name == "STOP"):
                print_string += f"  ├─ "
                print_note += "  │  "
            else:
                print_string += f"  └─ "
                print_note += f"     "
            print_string += event.name
            print_string = print_string.ljust(pad_length, " ")

        print_string += f" {time_2_str(event.timestamp)}"
        if check_type(event, Project):
            if event.name in project_times and event.name != "STOP":  
                time_seconds = project_times[event.name]
                print_string += " | " + total_seconds_2_hms(time_seconds)
            else:
                print_string += " ──────────"
        else:
            if i + 1 < len(all_events):
                interval = calculate_interval(event, all_events[i+1]).total_seconds()
            else:
                interval = calculate_ongoing_interval(event)

            print_string += " | " + total_seconds_2_hms(interval)

        click.echo(print_string)
        
        if check_type(event, Subtask) and event.note != "" and verbosity != VerbosityLevel.NO_NOTES:
            if verbosity == VerbosityLevel.SINGLE_LINE_NOTES:
                # Only show first line of note
                note_lines = split_line(event.note, pad_length+11)
                printline = print_note + f" └─ {note_lines[0]}"
                if len(note_lines) > 1:
                    printline += "..."
                click.echo(printline)
            else:  # FULL_NOTES
                note_lines = split_line(event.note, pad_length+14)
                for i, line in enumerate(note_lines):
                    if i == 0:
                        click.echo(print_note + f" └─ {line}")
                    else:
                        click.echo(print_note + f"    {line}")

def print_events_with_index(events):
    for i, event in enumerate(events):
        click.echo(f"{i}: {event.name} - {time_2_str(event.timestamp)}")

def print_project_times(project_times):
    pretty_print_title("Time per project:")
    for project, total_time in sorted(project_times.items(), key=lambda item: item[1], reverse=True):
        string = f"{project}".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(total_time)}"
        click.echo(string)

def print_ongoing_interval(event):
    if event.name != "STOP":
        ongoing_interval = calculate_ongoing_interval(event)
        click.echo("Ongoing project:")
        click.echo(f"{event.name} - {total_seconds_2_hms(ongoing_interval)}")

def print_total_time(sum, excluded):
    pretty_print_title("Total time:")
    click.echo(f"Total:".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(sum)}")
    click.echo(f"Excluded:".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(excluded)}")
