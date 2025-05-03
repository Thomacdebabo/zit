import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import os
import time

from ..events import Project, Subtask, GitCommit

# Define directory for git-specific data
GIT_DATA_DIR = Path.home() / '.zit' / 'git'



class GitStorage:
    def __init__(self, project_name='default', current_date=datetime.now().strftime('%Y-%m-%d')):
        self.project_name = project_name
        self.data_dir = GIT_DATA_DIR / self.project_name
        self.trash_dir = self.data_dir / 'trash'
        self._ensure_data_dir()
        self.current_date = current_date
        self.data_file = self.data_dir / f'{self.current_date}.csv'


    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.trash_dir.mkdir(exist_ok=True, parents=True)

    def _read_events(self) -> list[GitCommit]:
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []

        commits = []
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                commit = GitCommit.from_row(row)
                commits.append(commit)

        return self._sort_events(commits)

    def _clean_file(self):
        """Clean the daily file"""
        events = self._read_events()
        events = self._sort_events(events)
        events = self._combine_events(events)
        self._write_events(events)

    def _combine_events(self, events: list[GitCommit]) -> list[GitCommit]:
        """Combine events with the same project name following the same logic as the CLI"""
        combined_events = []
        for event in events:
            if combined_events:
                if combined_events[-1].hash == event.hash:
                    continue
            combined_events.append(event)
        return combined_events

    def _write_events(self, events: list[GitCommit]):
        """Write events to the daily file"""
        with open(self.data_file, 'w') as f:
            writer = csv.writer(f)
            for event in events:
                writer.writerow(event.to_row())

    def get_events(self) -> list[GitCommit]:
        events = self._read_events()
        return self._sort_events(events)

    def add_event(self, event: GitCommit):
        """Append a single event to the daily file"""
        events = self._read_events()
        for existing_event in events:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        with open(self.data_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(event.to_row())

    def _sort_events(self, events: list[GitCommit]) -> list[GitCommit]:
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

    def get_current_task(self) -> Optional[str]:
        events = self.get_events()
        if len(events) == 0:
            return None
        return events[-1].hash
        
    def get_project_at_time(self, timestamp: datetime) -> Optional[GitCommit]:
        events = self.get_events()
        commit = None
        for event in events:
            if event.timestamp <= timestamp:
                commit = event
            else:
                break
        return commit

    @staticmethod
    def list_projects():
        """List all git projects in the data directory"""
        projects = []
        if GIT_DATA_DIR.exists():
            projects = [p.name for p in GIT_DATA_DIR.iterdir() if p.is_dir() and p.name != 'trash']
        return projects
