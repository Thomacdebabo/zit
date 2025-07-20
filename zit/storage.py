import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import os
import time
DATA_DIR = Path.home() / '.zit'
TRASH_DIR = Path.home() / '.zit/trash'

from zit.events import Project, Subtask

class Storage:
    def __init__(self, current_date=datetime.now().strftime('%Y-%m-%d')):
        self.data_dir = DATA_DIR
        self.trash_dir = TRASH_DIR
        self._ensure_data_dir()
        self.current_date = current_date
        self.data_file = self.data_dir / f'{self.current_date}.csv'
        self.exclude_projects = ['STOP', 'LUNCH']

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.trash_dir.mkdir(exist_ok=True)

    def _read_events(self) -> list[Project]:
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []

        projects = []
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # Only process non-empty rows
                    project = Project.from_row(row)
                    projects.append(project)

        return self._sort_events(projects)

    def _clean_file(self):
        """Clean the daily file"""
        events = self._read_events()
        events = self._sort_events(events)
        events = self._combine_events(events)
        self._write_events(events)

    def _combine_events(self, events: list[Project | Subtask]) -> list[Project | Subtask]:
        """Combine events with the same project name following the same logic as the CLI"""
        combined_events = []
        for event in events:
            if combined_events:
                if combined_events[-1].name == event.name:
                    continue
            combined_events.append(event)
        return combined_events

    def _write_events(self, events: list[Project]):
        """Write events to the daily file"""
        with open(self.data_file, 'w') as f:
            writer = csv.writer(f)
            for event in events:
                writer.writerow(event.to_row())

    def get_events(self) -> list[Project | Subtask]:
        events = self._read_events()
        return self._sort_events(events)

    def add_event(self, event: Project):
        """Append a single event to the daily file"""
        events = self._read_events()
        for existing_event in events:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        with open(self.data_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(event.to_row())

    def _sort_events(self, events: list[Project | Subtask]) -> list[Project | Subtask]:
        events.sort(key=lambda event: event.timestamp)
        return events

    def clean_storage(self):
        self._clean_file()

    def set_to_date(self, date: str):
        self.current_date = date
        self.data_file = self.data_dir / f'{self.current_date}.csv'

    def set_to_yesterday(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.set_to_date(yesterday)

    def remove_data_file(self):
        self._ensure_data_dir()
        trash_file = self.trash_dir / f"{self.data_file.stem}_trash_{datetime.now().strftime('%H_%M_%S')}.csv"
        if self.data_file.exists():
            os.rename(self.data_file, trash_file)

    def get_current_task(self) -> Optional[str]:
        events = self.get_events()
        if len(events) == 0:
            return None
        if events[-1].name in self.exclude_projects:
            return None
        return events[-1].name
        
    def get_project_at_time(self, timestamp: datetime) -> Optional[Project]:
        events = self.get_events()
        project = None
        for event in events:
            if event.timestamp <= timestamp:
                project = event
            else:
                break
        return project

class SubtaskStorage(Storage):
    def __init__(self, current_date=datetime.now().strftime('%Y-%m-%d')):
        super().__init__(current_date)
        self.data_file = self.data_dir / f'{self.current_date}_subtasks.csv'

    def _read_events(self) -> list[Subtask]:
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []

        subtasks = []
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                subtask = Subtask.from_row(row)
                subtasks.append(subtask)
        return subtasks

    def _write_events(self, events: list[Subtask]):
        """Write events to the daily file"""
        with open(self.data_file, 'w') as f:
            writer = csv.writer(f)
            for event in events:
                writer.writerow(event.to_row())
        
    def add_event(self, event: Subtask):
        """Append a single event to the daily file"""
        events = self._read_events()
        for existing_event in events:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        with open(self.data_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(event.to_row())
   