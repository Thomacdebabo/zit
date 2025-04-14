from datetime import datetime
from pydantic import BaseModel

class SubTask(BaseModel):
    name: str
    description: str | None = None
    completed: bool = False

class ProjectEvent(BaseModel):
    project_name: str
    timestamp: datetime
    subtask: SubTask 