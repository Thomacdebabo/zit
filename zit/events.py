from datetime import datetime
from pydantic import BaseModel
import csv
from pathlib import Path
from zit.time_utils import interval_2_hms, time_2_str
from typing import Iterator, Any
from collections.abc import Sequence


def load_date(date: str) -> datetime:
    return datetime.fromisoformat(date)


from abc import ABC, abstractmethod


class Event(BaseModel, ABC):
    timestamp: datetime

    @staticmethod
    @abstractmethod
    def from_row(row: Sequence[str]) -> 'Event':
        pass

    @abstractmethod
    def to_row(self) -> list[Any]:
        pass


class Interval(BaseModel, ABC):
    start: datetime
    end: datetime


class DataStorage(BaseModel):
    events: list[Event]

    def __init__(self, events: list[Event]):
        super().__init__(events=events)

    @classmethod
    def from_csv(cls, csv_file: Path, event_type: type[Event]):
        events = []
        if csv_file.exists():
            with open(csv_file, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    events.append(event_type.from_row(row))
            events.sort(key=lambda x: x.timestamp)
        return cls(events)

    def to_csv(self, csv_file: Path) -> None:
        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            for event in self.events:
                writer.writerow(event.to_row())

    def sort(self) -> None:
        self.events.sort(key=lambda x: x.timestamp)

    def combine_events(self) -> None:
        combined_events: list[Event] = []
        for event in self.events:
            if combined_events:
                if combined_events[-1].name == event.name:  # type: ignore[attr-defined]
                    continue
            combined_events.append(event)
        self.events = combined_events

    def __iter__(self) -> Iterator[Event]:
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, index: int) -> Event:
        return self.events[index]

    def remove_item(self, index: int) -> None:
        self.events.pop(index)

    def __setitem__(self, index: int, value: Event) -> None:
        self.events[index] = value

    def add_item(self, event: Event) -> None:
        self.events.append(event)
        self.sort()


class Project(Event):
    timestamp: datetime
    name: str

    @staticmethod
    def from_row(row: Sequence[str]) -> 'Project':
        row = [item.strip() for item in row]
        timestamp = load_date(row[0])
        return Project(timestamp=timestamp, name=row[1])

    def to_row(self) -> list[Any]:
        return [self.timestamp, self.name]


class ProjectInterval(Interval):
    name: str

    @staticmethod
    def from_events(start_event: Project, end_event: Project) -> 'ProjectInterval':
        return ProjectInterval(
            start=start_event.timestamp, end=end_event.timestamp, name=start_event.name
        )

    @property
    def duration(self) -> float:
        return (self.end - self.start).total_seconds()

    def __str__(self) -> str:
        return f"{self.name} - {interval_2_hms(self.duration)} ( {time_2_str(self.start)} -> {time_2_str(self.end)})"


class ProjectIntervalStorage(BaseModel):
    intervals: dict[str, list[ProjectInterval]]

    def __init__(self, intervals: list[ProjectInterval] = []) -> None:
        interval_dict: dict[str, list[ProjectInterval]] = {}
        for interval in intervals:
            if interval.name not in interval_dict:
                interval_dict[interval.name] = []
            interval_dict[interval.name].append(interval)
        super().__init__(intervals=interval_dict)

    @staticmethod
    def from_events(events: list[Project]) -> 'ProjectIntervalStorage':
        intervals = ProjectIntervalStorage()
        for i in range(1, len(events)):
            interval = ProjectInterval.from_events(events[i - 1], events[i])
            intervals.add_interval(interval)
        return intervals

    def add_interval(self, interval: ProjectInterval) -> None:
        if interval.name not in self.intervals:
            self.intervals[interval.name] = []
        self.intervals[interval.name].append(interval)

    def calculate_project_times(self) -> 'ProjectTimes':
        return ProjectTimes.from_intervals(self)


class ProjectTimes(BaseModel):
    project_times: dict[str, float]

    @staticmethod
    def from_intervals(intervals: ProjectIntervalStorage) -> 'ProjectTimes':
        project_times: dict[str, float] = {}
        for project, interval_list in intervals.intervals.items():
            project_times[project] = sum(
                interval.duration for interval in interval_list
            )
        return ProjectTimes(project_times=project_times)

    def add(self, other: 'ProjectTimes') -> 'ProjectTimes':
        combined_times: dict[str, float] = {}
        all_keys = set(self.project_times.keys()) | set(other.project_times.keys())
        for key in all_keys:
            combined_times[key] = self.project_times.get(
                key, 0
            ) + other.project_times.get(key, 0)
        return ProjectTimes(project_times=combined_times)

    def add_time(self, project: str, time: float) -> None:
        if project in self.project_times:
            self.project_times[project] += time
        else:
            self.project_times[project] = time

    def total_time(self, exclude_projects: list[str] = []) -> tuple[float, float]:
        total_time = 0.0
        excluded = 0.0
        for project, time in self.project_times.items():
            if project not in exclude_projects:
                total_time += time
            else:
                excluded += time
        return total_time, excluded


class Subtask(Event):
    timestamp: datetime
    name: str
    note: str

    @staticmethod
    def from_row(row: Sequence[str]) -> 'Subtask':
        row = [item.strip() for item in row]
        timestamp = load_date(row[0])
        if len(row) == 3:
            return Subtask(timestamp=timestamp, name=row[1], note=row[2])
        else:
            return Subtask(timestamp=timestamp, name=row[1], note="")

    def to_row(self) -> list[Any]:
        return [self.timestamp, self.name, self.note]


class GitCommit(Event):
    timestamp: datetime
    hash: str
    message: str
    author: str
    email: str

    @staticmethod
    def from_row(row: Sequence[str]) -> 'GitCommit':
        timestamp = load_date(row[0])
        return GitCommit(
            timestamp=timestamp,
            hash=row[1],
            message=row[2],
            author=row[3],
            email=row[4],
        )

    def to_row(self) -> list[Any]:
        return [self.timestamp, self.hash, self.message, self.author, self.email]


def check_type(event: Event, t: type) -> bool:
    return type(event) is t


def sort_events(events: list[Event], sub_events: list[Event]) -> list[Event]:
    all_events = events + sub_events
    # Sort by timestamp first, then by event type (main before sub)
    all_events.sort(key=lambda x: (x.timestamp, 0 if check_type(x, Project) else 1))
    return all_events


def create_subtask_dict(events: list[Event]) -> dict[str, list[Subtask]]:
    subtask_dict: dict[str, list[Subtask]] = {}
    name = events[0].name  # type: ignore[attr-defined]
    subtasks: list[Subtask] = []
    for event in events:
        if (
            check_type(event, Project)
            and not check_type(event, Subtask)
            and event.name != name  # type: ignore[attr-defined]
        ):
            subtask_dict[name] = subtasks
            name = event.name  # type: ignore[attr-defined]
            subtasks = subtask_dict.get(name, [])
        if check_type(event, Subtask):
            subtasks.append(event)  # type: ignore[arg-type]
    return subtask_dict


def create_full_list(events: list[Event]) -> list[list[Event | list[Subtask]]]:
    projects: list[list[Event | list[Subtask]]] = []

    if check_type(events[0], Subtask):
        raise ValueError("First event cannot be a subtask")

    project = events[0]
    subtasks: list[Subtask] = []
    i = 1
    while i < len(events):
        event = events[i]
        if check_type(event, Project):
            projects.append([project, subtasks])
            subtasks = []
            project = event
        if check_type(event, Subtask):
            subtasks.append(event)  # type: ignore[arg-type]
        i += 1
    projects.append([project, subtasks])
    return projects
