from datetime import datetime

def calculate_interval(event1, event2):
    start_time = event1.timestamp
    end_time = event2.timestamp
    return end_time - start_time


def calculate_ongoing_interval(event):
    return max(0, (datetime.now() - event.timestamp).total_seconds())

def calculate_project_times(events, exclude_projects=[], add_ongoing=True):
    sum = 0
    excluded = 0
    project_times = {}

    for i in range(1, len(events)):
        start_event = events[i-1]
        end_event = events[i]
        interval = calculate_interval(start_event, end_event)

        project = start_event.name
        project_times[project] = project_times.get(project, 0) + interval.total_seconds()
        if project not in exclude_projects:
            sum += interval.total_seconds()
        else:
            excluded += interval.total_seconds()

    if add_ongoing and events[-1].name != "STOP":
        ongoing_interval = calculate_ongoing_interval(events[-1])
        project = events[-1].name
        project_times[project] = project_times.get(project, 0) + ongoing_interval
        if project not in exclude_projects:
            sum += ongoing_interval
    return project_times, sum, excluded