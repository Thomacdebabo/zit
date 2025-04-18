import csv
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os
import time

class Event(BaseModel):
    timestamp: datetime
    project: str
    subtask: Optional[str] = None

def event_2_row(event):
    return [event.timestamp, event.project]

def row_2_event(row):
    return Event(timestamp=row[0], project=row[1])

def load_date(date):
    return datetime.fromisoformat(date)

class Storage:
    def __init__(self):
        self.data_dir = Path.home() / '.zit'
        self.trash_dir = Path.home() / '.zit/trash'
        self._ensure_data_dir()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.data_file = self.data_dir / f'{self.current_date}.csv'
        self.exclude_projects = ['STOP', 'LUNCH']

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.trash_dir.mkdir(exist_ok=True)

    def _read_events(self):
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []

        events = []
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                row[0] = load_date(row[0])
                event = row_2_event(row)
                events.append(event)


        return self._sort_events(events)

    def _clean_file(self):
        """Clean the daily file"""
        events = self._read_events()
        events = self._sort_events(events)
        events = self._combine_events(events)
        self._write_events(events)

    def _combine_events(self, events):
        """Combine events with the same project name following the same logic as the CLI"""
        combined_events = []
        for event in events:
            if combined_events:
                if combined_events[-1].project == event.project:
                    continue
            combined_events.append(event)
        return combined_events

    def _write_events(self, events):
        """Write events to the daily file"""
        with open(self.data_file, 'w') as f:
            writer = csv.writer(f)
            for event in events:
                writer.writerow(event_2_row(event))

    def get_events(self):
        events = self._read_events()
        return self._sort_events(events)

    def add_event(self, event: Event):
        """Append a single event to the daily file"""
        events = self._read_events()
        for existing_event in events:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        with open(self.data_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(event_2_row(event))

    def _sort_events(self, events):
        events.sort(key=lambda event: event.timestamp)
        return events

    def clean_storage(self):
        self._clean_file()

    def set_to_yesterday(self):
        self.current_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.data_file = self.data_dir / f'{self.current_date}.csv'

    def remove_data_file(self):
        self._ensure_data_dir()
        trash_file = self.trash_dir / f"{self.data_file.stem}_trash_{datetime.now().strftime('%H_%M_%S')}.csv"
        if self.data_file.exists():
            os.rename(self.data_file, trash_file)

    def get_current_task(self):
        events = self.get_events()
        if len(events) == 0:
            return None
        if events[-1].project in self.exclude_projects:
            return None
        return events[-1].project
    def get_project_at_time(self, timestamp):
        events = self.get_events()
        project = None
        for event in events:
            if event.timestamp <= timestamp:
                project = event
            else:
                break
        return project

class SubtaskStorage(Storage):
    def __init__(self):
        super().__init__()
        self.data_dir = Path.home() / '.zit'
        self.trash_dir = Path.home() / '.zit/trash'
        self._ensure_data_dir()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.data_file = self.data_dir / f'{self.current_date}_subtasks.csv'
        