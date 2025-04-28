from datetime import datetime
from pydantic import BaseModel

class Project(BaseModel):
    timestamp: datetime
    name: str

class Subtask(Project):
    note: str


def sort_events(events, sub_events):

    all_events = events + sub_events
    # Sort by timestamp first, then by event type (main before sub)
    all_events.sort(key=lambda x: (x.timestamp, 0 if isinstance(x, Project) else 1))
    return all_events

def create_subtask_dict(events):
    subtask_dict = {}
    name = events[0].name
    subtasks = []
    for event in events:
        
        if isinstance(event, Project) and not isinstance(event, Subtask) and event.name != name: 
            subtask_dict[name] = subtasks
            name = event.name
            subtasks = subtask_dict.get(name, [])
        if isinstance(event, Subtask):
            subtasks.append(event)
    return subtask_dict
