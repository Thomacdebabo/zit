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
    click.echo("--------------------------------")
    click.echo(title)
    click.echo("--------------------------------")

def print_interval(event1, event2):
    interval = calculate_interval(event1, event2)
    click.echo(f"{event1.project} - {interval_2_hms(interval)} ( {time_2_str(event1.timestamp)} -> {time_2_str(event2.timestamp)})")

def print_intervals(events):
    for i in range(1, len(events)):
        start_event = events[i-1]
        end_event = events[i]
        print_interval(start_event, end_event)

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
