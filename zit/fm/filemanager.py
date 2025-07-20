from pathlib import Path
from datetime import datetime, timedelta
import csv
from zit.storage import *

class ZitFileManager:
    def __init__(self):
        self.data_dir = Path.home() / '.zit'
        self.trash_dir = Path.home() / '.zit/trash'
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.trash_dir.mkdir(exist_ok=True)

    def get_all_dates(self):
        """Get all files in the data directory, excluding subtask files"""
        return [f for f in self.data_dir.glob('*.csv') if not f.name.endswith('_subtasks.csv')]





   

    
