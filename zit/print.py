from .terminal import print_string
from .calculate import calculate_interval, calculate_ongoing_interval
from .events import Project, Subtask, sort_events
from enum import Enum, auto
from zit.time_utils import time_2_str, total_seconds_2_hms, interval_2_hms

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
        split_point = text[:max_length].rfind(" ")
        if split_point == -1:
            split_point = max_length
        lines.append(text[:split_point].rstrip())
        text = text[split_point:].lstrip()
    return lines


def pretty_print_title(title: str) -> None:
    width = max(len(title) + 10, DEFAULT_MAX_WIDTH)
    print_string("┌" + "─" * (width - 2) + "┐")
    print_string(f"│ {title}".ljust(width - 1, " ") + "│")
    print_string("└" + "─" * (width - 2) + "┘")


def print_interval(event1: Project, event2: Project) -> None:
    interval = calculate_interval(event1, event2)
    print_string(
        f"{event1.name} - {interval_2_hms(interval)} ( {time_2_str(event1.timestamp)} -> {time_2_str(event2.timestamp)})"
    )


def print_intervals(events: list[Project]) -> None:
    for i in range(1, len(events)):
        start_event = events[i - 1]
        end_event = events[i]
        print_interval(start_event, end_event)


def print_events_and_subtasks(
    events: list[Project],
    sub_events: list[Subtask],
    project_times: dict[str, float],
    verbosity: VerbosityLevel = VerbosityLevel.FULL_NOTES,
) -> None:
    pretty_print_title("Events and Subtasks:")

    all_events = []
    max_project_length = 0
    all_events = sort_events(events, sub_events)

    pad_length = max(max_project_length + 10, DEFAULT_MAX_WIDTH - 20)

    # Print events in chronological order
    for i, event in enumerate(all_events):
        str_to_print = ""
        print_note = ""
        if isinstance(event, Project):
            if event.name in ["STOP"]:
                str_to_print += "  └─"
            else:
                str_to_print += event.name + " "
            str_to_print = str_to_print.ljust(pad_length, "─")
        elif isinstance(event, Subtask):
            next_event = all_events[i + 1] if i + 1 < len(all_events) else None
            if next_event is not None and (
                isinstance(next_event, Subtask)
                or (isinstance(next_event, Project) and next_event.name == "STOP")
            ):
                str_to_print += "  ├─ "
                print_note += "  │  "
            else:
                str_to_print += "  └─ "
                print_note += "     "
            str_to_print += event.name
            str_to_print = str_to_print.ljust(pad_length, " ")

        str_to_print += f" {time_2_str(event.timestamp)}"
        if isinstance(event, Project):
            if event.name in project_times and event.name != "STOP":
                time_seconds = project_times[event.name]
                str_to_print += " | " + total_seconds_2_hms(time_seconds)
            else:
                str_to_print += " ──────────"
        elif isinstance(event, Subtask):
            if i + 1 < len(all_events):
                interval = calculate_interval(event, all_events[i + 1]).total_seconds()
            else:
                interval = calculate_ongoing_interval(event)

            str_to_print += " | " + total_seconds_2_hms(interval)

        print_string(str_to_print)

        if (
            isinstance(event, Subtask)
            and event.note != ""
            and verbosity != VerbosityLevel.NO_NOTES
        ):
            if verbosity == VerbosityLevel.SINGLE_LINE_NOTES:
                # Only show first line of note
                note_lines = split_line(event.note, pad_length + 11)
                printline = print_note + f" └─ {note_lines[0]}"
                if len(note_lines) > 1:
                    printline += "..."
                print_string(printline)
            else:  # FULL_NOTES
                note_lines = split_line(event.note, pad_length + 14)
                for j, line in enumerate(note_lines):
                    if j == 0:
                        print_string(print_note + f" └─ {line}")
                    else:
                        print_string(print_note + f"    {line}")


def print_events_with_index(events: list[Project | Subtask]) -> None:
    for i, event in enumerate(events):
        print_string(f"{i}: {event.name} - {time_2_str(event.timestamp)}")


def print_project_times(project_times: dict[str, float], verbose: bool = False) -> None:
    # TODO if verbose also print subtask times
    pretty_print_title("Time per project:")
    for project, total_time in sorted(
        project_times.items(), key=lambda item: item[1], reverse=True
    ):
        string = (
            f"{project}".ljust(DEFAULT_MAX_WIDTH - 8)
            + f"{total_seconds_2_hms(total_time)}"
        )
        print_string(string)


def print_ongoing_interval(event: Project) -> None:
    if event.name != "STOP":
        ongoing_interval = calculate_ongoing_interval(event)
        print_string("Ongoing project:")
        print_string(f"{event.name} - {total_seconds_2_hms(ongoing_interval)}")


def print_total_time(sum: float, excluded: float) -> None:
    pretty_print_title("Total time:")
    print_string("Total:".ljust(DEFAULT_MAX_WIDTH - 8) + f"{total_seconds_2_hms(sum)}")
    print_string(
        "Excluded:".ljust(DEFAULT_MAX_WIDTH - 8) + f"{total_seconds_2_hms(excluded)}"
    )
