from datetime import datetime

def calculate_interval(event1, event2):
    start_time = event1.timestamp
    end_time = event2.timestamp
    return end_time - start_time


def calculate_ongoing_interval(event):
    now = datetime.now()
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    return max(0, (end_of_day - event.timestamp).total_seconds())
def add_project_times(project_time1, project_time2):
    sum = {}
    all_keys = set(project_time1.keys()) | set(project_time2.keys())
    for key in all_keys:
        sum[key] = project_time1.get(key, 0) + project_time2.get(key, 0)
    return sum

def calculate_project_times(events, exclude_projects=[], add_ongoing=True):
    if len(events) == 0:
        return {}, 0, 0
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