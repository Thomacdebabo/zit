from .terminal import *
from .calculate import calculate_interval, calculate_ongoing_interval
from .events import *
from enum import Enum, auto
from zit.time_utils import interval_2_hms, time_2_str, total_seconds_2_hms
DEFAULT_MAX_WIDTH = 70

class VerbosityLevel(Enum):
    NO_NOTES = auto()
    SINGLE_LINE_NOTES = auto()
    FULL_NOTES = auto()


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
    print_string("┌" + "─" * (width-2) + "┐")
    print_string(f"│ {title}".ljust(width-1, " ") + "│")
    print_string("└" + "─" * (width-2) + "┘")
def print_interval(event1, event2):
    interval = calculate_interval(event1, event2)
    print_string(f"{event1.name} - {interval_2_hms(interval)} ( {time_2_str(event1.timestamp)} -> {time_2_str(event2.timestamp)})")

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
        str_to_print = ""
        print_note = ""
        if check_type(event, Project):
            if event.name in ["STOP"]:
                str_to_print += "  └─"
            else:
                str_to_print += event.name + " "
            str_to_print = str_to_print.ljust(pad_length, "─")
        else:
            if i + 1 < len(all_events) and (check_type(all_events[i+1], Subtask) or all_events[i+1].name == "STOP"):
                str_to_print += f"  ├─ "
                print_note += "  │  "
            else:
                str_to_print += f"  └─ "
                print_note += f"     "
            str_to_print += event.name
            str_to_print = str_to_print.ljust(pad_length, " ")

        str_to_print += f" {time_2_str(event.timestamp)}"
        if check_type(event, Project):
            if event.name in project_times and event.name != "STOP":  
                time_seconds = project_times[event.name]
                str_to_print += " | " + total_seconds_2_hms(time_seconds)
            else:
                str_to_print += " ──────────"
        else:
            if i + 1 < len(all_events):
                interval = calculate_interval(event, all_events[i+1]).total_seconds()
            else:
                interval = calculate_ongoing_interval(event)

            str_to_print += " | " + total_seconds_2_hms(interval)

        print_string(str_to_print)
        
        if check_type(event, Subtask) and event.note != "" and verbosity != VerbosityLevel.NO_NOTES:
            if verbosity == VerbosityLevel.SINGLE_LINE_NOTES:
                # Only show first line of note
                note_lines = split_line(event.note, pad_length+11)
                printline = print_note + f" └─ {note_lines[0]}"
                if len(note_lines) > 1:
                    printline += "..."
                print_string(printline)
            else:  # FULL_NOTES
                note_lines = split_line(event.note, pad_length+14)
                for i, line in enumerate(note_lines):
                    if i == 0:
                        print_string(print_note + f" └─ {line}")
                    else:
                        print_string(print_note + f"    {line}")

def print_events_with_index(events):
    for i, event in enumerate(events):
        print_string(f"{i}: {event.name} - {time_2_str(event.timestamp)}")

def print_project_times(project_times, verbose=False):
    #TODO if verbose also print subtask times
    pretty_print_title("Time per project:")
    for project, total_time in sorted(project_times.items(), key=lambda item: item[1], reverse=True):
        string = f"{project}".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(total_time)}"
        print_string(string)

def print_ongoing_interval(event):
    if event.name != "STOP":
        ongoing_interval = calculate_ongoing_interval(event)
        print_string("Ongoing project:")
        print_string(f"{event.name} - {total_seconds_2_hms(ongoing_interval)}")

def print_total_time(sum, excluded):
    pretty_print_title("Total time:")
    print_string(f"Total:".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(sum)}")
    print_string(f"Excluded:".ljust(DEFAULT_MAX_WIDTH-8) + f"{total_seconds_2_hms(excluded)}")
