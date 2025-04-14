import json
import csv
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

class Event(BaseModel):
    timestamp: datetime
    project: str
    subtask: Optional[str] = None

class Storage:
    def __init__(self):
        self.data_dir = Path.home() / '.zit'
        self._ensure_data_dir()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.data_file = self.data_dir / f'{self.current_date}.csv'

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)

    def add_event(self, event: Event):
        """Append a single event to the daily file"""
        with open(self.data_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([event.timestamp, event.project])
    def _read_events(self):
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []
        
        events = []
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                events.append(row)
        return events
