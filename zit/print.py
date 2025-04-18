import click
from .calculate import calculate_interval, calculate_ongoing_interval

def date_2_str(date):
    return date.strftime('%Y-%m-%d')

def time_2_str(time):
    return time.strftime('%H:%M:%S')

def interval_2_hms(interval):
    return total_seconds_2_hms(interval.total_seconds())


def total_seconds_2_hms(total_seconds):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{int(hours)}:{int(minutes)}:{int(seconds)}'

def pretty_print_title(title):
    width = max(len(title) + 10, 50)
    click.echo("┌" + "─" * (width-2) + "┐")
    click.echo(f"│ {title}".ljust(width-1, " ") + "│")
    click.echo("└" + "─" * (width-2) + "┘")
def print_interval(event1, event2):
    interval = calculate_interval(event1, event2)
    click.echo(f"{event1.project} - {interval_2_hms(interval)} ( {time_2_str(event1.timestamp)} -> {time_2_str(event2.timestamp)})")

def print_intervals(events):
    for i in range(1, len(events)):
        start_event = events[i-1]
        end_event = events[i]
        print_interval(start_event, end_event)

def print_events_and_subtasks(events, sub_events, project_times):
    pretty_print_title("Events and Subtasks:")
    
    # Combine and sort all events chronologically
    all_events = []
    max_project_length = 0
    for event in events:
        all_events.append((event.timestamp, event, "main"))
        max_project_length = max(max_project_length, len(event.project))
    for sub_event in sub_events:
        all_events.append((sub_event.timestamp, sub_event, "sub"))
    # Sort by timestamp first, then by event type (main before sub)
    all_events.sort(key=lambda x: (x[0], 0 if x[2] == "main" else 1))
    
    pad_length = max(max_project_length + 10, 30)
    # Print events in chronological order
    for i, (timestamp, event, event_type) in enumerate(all_events):
        print_string = ""
        if event_type == "main":
            if event.project in ["STOP"]:
                print_string += "  └─"
            else:
                print_string += event.project + " "
            print_string = print_string.ljust(pad_length, "─")
        else:
            if i + 1 < len(all_events) and (all_events[i+1][2] == "sub" or all_events[i+1][1].project == "STOP"):
                print_string += f"  ├─ "
            else:
                print_string += f"  └─ "
            print_string += event.project
            print_string = print_string.ljust(pad_length, " ")

        print_string += f" {time_2_str(timestamp)}"
        if event_type == "main":
            if event.project in project_times and event.project != "STOP":  
                time_seconds = project_times[event.project]
                print_string += " | " +total_seconds_2_hms(time_seconds)
        else:
            if i + 1 < len(all_events):
                interval = calculate_interval(event, all_events[i+1][1]).total_seconds()
            else:
                interval = calculate_ongoing_interval(event)

            print_string += " | " + total_seconds_2_hms(interval)

        click.echo(print_string)
        
def print_events_with_index(events):
    for i, event in enumerate(events):
        click.echo(f"{i}: {event.project} - {time_2_str(event.timestamp)}")

def print_project_times(project_times):
    pretty_print_title("Time per project:")
    for project, total_time in sorted(project_times.items(), key=lambda item: item[1], reverse=True):
        click.echo(f"{project} - {total_seconds_2_hms(total_time)}")

def print_ongoing_interval(event):
    if event.project != "STOP":
        ongoing_interval = calculate_ongoing_interval(event)
        click.echo("Ongoing project:")
        click.echo(f"{event.project} - {total_seconds_2_hms(ongoing_interval)}")

def print_total_time(sum, excluded):
    pretty_print_title("Total time:")
    click.echo(f"Total: {total_seconds_2_hms(sum)}")
    click.echo(f"Excluded: {total_seconds_2_hms(excluded)}")
