from pathlib import Path
from datetime import datetime, timedelta
import csv
from zit.storage import Event, load_date, row_2_event

class ZitFileManager:
    def __init__(self):
        self.data_dir = Path.home() / '.zit'
        self.trash_dir = Path.home() / '.zit/trash'
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.trash_dir.mkdir(exist_ok=True)

    def get_all_files(self):
        """Get all CSV files in the data directory"""
        return list(self.data_dir.glob('*.csv'))

    def get_files_in_date_range(self, start_date: datetime, end_date: datetime):
        """Get all CSV files within a date range"""
        files = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            main_file = self.data_dir / f'{date_str}.csv'
            subtask_file = self.data_dir / f'{date_str}_subtasks.csv'
            if main_file.exists():
                files.append(main_file)
            if subtask_file.exists():
                files.append(subtask_file)
            current_date += timedelta(days=1)
        return files

    def read_file(self, file_path: Path) -> list[Event]:
        """Read events from a specific file"""
        events = []
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                row[0] = load_date(row[0])
                event = row_2_event(row)
                events.append(event)
        return events

    def get_all_events(self, start_date: datetime, end_date: datetime) -> list[Event]:
        """Get all events from all files within a date range"""
        files = self.get_files_in_date_range(start_date, end_date)
        all_events = []
        for file in files:
            events = self.read_file(file)
            all_events.extend(events)
        return sorted(all_events, key=lambda event: event.timestamp)

    def get_project_events(self, project_name: str, start_date: datetime, end_date: datetime) -> list[Event]:
        """Get all events for a specific project within a date range"""
        all_events = self.get_all_events(start_date, end_date)
        return [event for event in all_events if event.project == project_name]

    def get_total_time_for_project(self, project_name: str, start_date: datetime, end_date: datetime) -> timedelta:
        """Calculate total time spent on a project within a date range"""
        events = self.get_project_events(project_name, start_date, end_date)
        if not events:
            return timedelta()
        
        total_time = timedelta()
        for i in range(len(events) - 1):
            time_diff = events[i + 1].timestamp - events[i].timestamp
            total_time += time_diff
        return total_time

    def get_total_time_for_all_projects(self, start_date: datetime, end_date: datetime) -> timedelta:
        """Calculate total time spent on all projects within a date range"""
        all_events = self.get_all_events(start_date, end_date)
        total_time = timedelta()
        for event in all_events:
            total_time += event.timestamp - event.timestamp
        return total_time

    def get_total_time_for_all_projects_in_date(self, date: datetime) -> timedelta:
        """Calculate total time spent on all projects for a specific date"""
        return self.get_total_time_for_all_projects(date, date)
