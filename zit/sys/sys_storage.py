import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import os
import time
import getpass

from .sys_events import SystemEvent, SystemEventType

# Define directory for system-specific data
SYS_DATA_DIR = Path.home() / ".zit" / "system"


def load_date(date: str) -> datetime:
    return datetime.fromisoformat(date)


class SystemStorage:
    def __init__(self, current_date: str = datetime.now().strftime("%Y-%m-%d")) -> None:
        self.data_dir: Path = SYS_DATA_DIR
        self.trash_dir: Path = self.data_dir / "trash"
        self._ensure_data_dir()
        self.current_date: str = current_date
        self.data_file: Path = self.data_dir / f"{self.current_date}.csv"

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.trash_dir.mkdir(exist_ok=True, parents=True)

    def _read_events(self) -> List[SystemEvent]:
        """Read all events from the daily file"""
        if not self.data_file.exists():
            return []

        events = []
        with open(self.data_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                row[0] = load_date(row[0])
                event = SystemEvent.from_row(row)
                events.append(event)

        return self._sort_events(events)

    def _clean_file(self) -> None:
        """Clean the daily file"""
        events = self._read_events()
        events = self._sort_events(events)
        self._write_events(events)

    def _write_events(self, events: List[SystemEvent]) -> None:
        """Write events to the daily file"""
        with open(self.data_file, "w") as f:
            writer = csv.writer(f)
            for event in events:
                writer.writerow(event.to_row())

    def get_events(self) -> List[SystemEvent]:
        events = self._read_events()
        return self._sort_events(events)

    def add_event(self, event: SystemEvent) -> None:
        """Append a single event to the daily file"""
        events = self._read_events()

        # Check if a similar event already exists within a small time window
        time_window = 5  # seconds
        for existing_event in events:
            time_diff = abs(
                (existing_event.timestamp - event.timestamp).total_seconds()
            )
            if (
                time_diff < time_window
                and existing_event.event_type == event.event_type
                and existing_event.details == event.details
            ):
                # Event already exists, don't add duplicate
                return

        # Append the event if it doesn't exist
        with open(self.data_file, "a") as f:
            writer = csv.writer(f)
            writer.writerow(event.to_row())

    def _sort_events(self, events: List[SystemEvent]) -> List[SystemEvent]:
        events.sort(key=lambda event: event.timestamp)
        return events

    def clean_storage(self) -> None:
        self._clean_file()

    def set_to_yesterday(self) -> None:
        self.current_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.data_file = self.data_dir / f"{self.current_date}.csv"

    def remove_data_file(self) -> None:
        self._ensure_data_dir()
        trash_file = (
            self.trash_dir
            / f"{self.data_file.stem}_trash_{datetime.now().strftime('%H_%M_%S')}.csv"
        )
        if self.data_file.exists():
            os.rename(self.data_file, trash_file)

    @staticmethod
    def get_all_dates() -> list[str]:
        """Get all dates for which we have system event data"""
        if not SYS_DATA_DIR.exists():
            return []

        return sorted([f.stem for f in SYS_DATA_DIR.glob("*.csv") if f.is_file()])
