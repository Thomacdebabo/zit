from datetime import datetime, timedelta
from zit.events import Event, Project, Subtask, ProjectInterval, ProjectIntervalStorage


def calculate_interval(event1: Event, event2: Event) -> timedelta:
    start_time = event1.timestamp
    end_time = event2.timestamp
    return end_time - start_time


def calculate_ongoing_interval(event: Event) -> float:
    now = datetime.now()
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    return min(
        (now - event.timestamp).total_seconds(),
        (end_of_day - event.timestamp).total_seconds(),
    )


def add_project_times(project_time1: dict[str, float], project_time2: dict[str, float]) -> dict[str, float]:
    time_sum: dict[str, float] = {}
    all_keys = set(project_time1.keys()) | set(project_time2.keys())
    for key in all_keys:
        time_sum[key] = project_time1.get(key, 0) + project_time2.get(key, 0)
    return time_sum


def calculate_project_times(events: list[Project], exclude_projects: list[str] = [], add_ongoing: bool = True) -> tuple[dict[str, float], float, float]:
    if len(events) == 0:
        return {}, 0, 0

    project_interval_storage = ProjectIntervalStorage.from_events(events)
    project_times = project_interval_storage.calculate_project_times()

    if add_ongoing and events[-1].name != "STOP":
        ongoing_interval = calculate_ongoing_interval(events[-1])
        project = events[-1].name
        project_times.add_time(project, ongoing_interval)
    time_sum, excluded = project_times.total_time(exclude_projects=exclude_projects)
    return project_times.project_times, time_sum, excluded
