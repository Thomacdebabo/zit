from datetime import datetime
from tkinter import E
from pydantic import BaseModel
from .calculate import *
import csv
from pathlib import Path


def load_date(date):
    return datetime.fromisoformat(date)


from abc import ABC, abstractmethod


class Event(BaseModel, ABC):
    timestamp: datetime

    @abstractmethod
    def from_row(row):
        pass

    @abstractmethod
    def to_row(self):
        pass


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

    def to_csv(self, csv_file):
        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            for event in self.events:
                writer.writerow(event.to_row())

    def sort(self):
        self.events.sort(key=lambda x: x.timestamp)

    def combine_events(self):
        combined_events = []
        for event in self.events:
            if combined_events:
                if combined_events[-1].name == event.name:
                    continue
            combined_events.append(event)
        self.events = combined_events

    def __iter__(self):
        return iter(self.events)

    def __len__(self):
        return len(self.events)

    def __getitem__(self, index):
        return self.events[index]

    def __setitem__(self, index, value):
        self.events[index] = value

    def add_item(self, event):
        self.events.append(event)
        self.sort()


class Project(Event):
    timestamp: datetime
    name: str

    def from_row(row):
        row = [item.strip() for item in row]
        timestamp = load_date(row[0])
        return Project(timestamp=timestamp, name=row[1])

    def to_row(self):
        return [self.timestamp, self.name]


class Subtask(Event):
    timestamp: datetime
    name: str
    note: str

    def from_row(row):
        row = [item.strip() for item in row]
        timestamp = load_date(row[0])
        if len(row) == 3:
            return Subtask(timestamp=timestamp, name=row[1], note=row[2])
        else:
            return Subtask(timestamp=timestamp, name=row[1], note="")

    def to_row(self):
        return [self.timestamp, self.name, self.note]


class GitCommit(BaseModel):
    hash: str
    message: str
    author: str
    email: str

    def from_row(row):
        timestamp = load_date(row[0])
        return GitCommit(
            timestamp=timestamp,
            hash=row[1],
            message=row[2],
            author=row[3],
            email=row[4],
        )

    def to_row(self):
        return [self.timestamp, self.hash, self.message, self.author, self.email]


def check_type(event, t):
    return type(event) is t


def sort_events(events, sub_events):
    all_events = events + sub_events
    # Sort by timestamp first, then by event type (main before sub)
    all_events.sort(key=lambda x: (x.timestamp, 0 if check_type(x, Project) else 1))
    return all_events


def create_subtask_dict(events):
    subtask_dict = {}
    name = events[0].name
    subtasks = []
    for event in events:
        if (
            check_type(event, Project)
            and not check_type(event, Subtask)
            and event.name != name
        ):
            subtask_dict[name] = subtasks
            name = event.name
            subtasks = subtask_dict.get(name, [])
        if check_type(event, Subtask):
            subtasks.append(event)
    return subtask_dict


def create_full_list(events):
    projects = []

    if check_type(events[0], Subtask):
        raise ValueError("First event cannot be a subtask")

    project = events[0]
    subtasks = []
    i = 1
    while i < len(events):
        event = events[i]
        if check_type(event, Project):
            projects.append([project, subtasks])
            subtasks = []
            project = event
        if check_type(event, Subtask):
            subtasks.append(event)
