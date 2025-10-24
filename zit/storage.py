from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, cast
import os

from zit.events import Project, Subtask, DataStorage

DATA_DIR = Path.home() / ".zit"
TRASH_DIR = Path.home() / ".zit/trash"


class Storage:
    def __init__(self, current_date: str = datetime.now().strftime("%Y-%m-%d")) -> None:
        self.data_dir: Path = DATA_DIR
        self.trash_dir: Path = TRASH_DIR
        self._ensure_data_dir()
        self.current_date: str = current_date
        self.data_file: Path = self.data_dir / f"{self.current_date}.csv"
        self.exclude_projects: list[str] = ["STOP", "LUNCH"]

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.trash_dir.mkdir(exist_ok=True)

    def _read_events(self) -> DataStorage:
        """Read all events from the daily file"""
        return DataStorage.from_csv(self.data_file, Project)

    def _clean_file(self) -> None:
        """Clean the daily file"""
        data_storage = self._read_events()
        data_storage.sort()
        data_storage.combine_events()
        data_storage.to_csv(self.data_file)

    def _write_events(self, data_storage: DataStorage) -> None:
        """Write events to the daily file"""
        data_storage.to_csv(self.data_file)

    def get_events(self) -> list[Project]:
        data_storage = self._read_events()
        return data_storage.events  # type: ignore[return-value]

    def add_event(self, event: Project) -> None:
        """Append a single event to the daily file"""
        data_storage = self._read_events()
        for existing_event in data_storage:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        data_storage.add_item(event)
        self._write_events(data_storage)

    def clean_storage(self) -> None:
        self._clean_file()

    def set_to_date(self, date: str) -> None:
        self.current_date = date
        self.data_file = self.data_dir / f"{self.current_date}.csv"

    def set_to_yesterday(self) -> None:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.set_to_date(yesterday)

    def remove_data_file(self) -> None:
        self._ensure_data_dir()
        trash_file = (
            self.trash_dir
            / f"{self.data_file.stem}_trash_{datetime.now().strftime('%H_%M_%S')}.csv"
        )
        if self.data_file.exists():
            os.rename(self.data_file, trash_file)

    def get_current_task(self) -> Optional[str]:
        data_storage = self._read_events()
        if len(data_storage) == 0:
            return None
        last_event = data_storage[-1]
        if not isinstance(last_event, Project):
            return None
        if last_event.name in self.exclude_projects:
            return None
        return last_event.name

    def get_project_at_time(self, timestamp: datetime) -> Project | None:
        data_storage = self._read_events()
        project: Project | None = None
        for event in data_storage:
            if event.timestamp <= timestamp:
                project = event  # type: ignore[assignment]
            else:
                break
        return project


class SubtaskStorage(Storage):
    def __init__(self, current_date: str = datetime.now().strftime("%Y-%m-%d")) -> None:
        super().__init__(current_date)
        self.data_file = self.data_dir / f"{self.current_date}_subtasks.csv"

    def _read_events(self) -> DataStorage:
        """Read all events from the daily file"""
        return DataStorage.from_csv(self.data_file, Subtask)

    def get_events(self) -> list[Subtask]:
        data_storage = self._read_events()
        return cast(list[Subtask], data_storage.events)

    def add_event(self, event: Subtask) -> None:
        """Append a single subtask event to the daily file"""
        data_storage = self._read_events()
        for existing_event in data_storage:
            if existing_event.timestamp == event.timestamp:
                print(f"Event already exists at {event.timestamp}")
                return
        data_storage.add_item(cast(Project, event))
        self._write_events(data_storage)
