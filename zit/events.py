from datetime import datetime
from pydantic import BaseModel
from .calculate import *
class Project(BaseModel):
    timestamp: datetime
    name: str

class Subtask(Project):
    note: str

def check_type(event, t):
    return type(event) is t

def sort_events(events, sub_events):

    all_events = events + sub_events
    # Sort by timestamp first, then by event type (main before sub)
    all_events.sort(key=lambda x: (x.timestamp, 0 if check_type(x, Project) else 1))
    return all_events

def create_subtask_dict(events):
    subtask_dict = {}
    name = events[0].name
    subtasks = []
    for event in events:
        if check_type(event, Project) and not check_type(event, Subtask) and event.name != name: 
            subtask_dict[name] = subtasks
            name = event.name
            subtasks = subtask_dict.get(name, [])
        if check_type(event, Subtask):
            subtasks.append(event)
    return subtask_dict


def create_full_list(events):
    projects = []
    
    if check_type(events[0], Subtask):
        raise ValueError("First event cannot be a subtask")
    
    project = events[0]
    subtasks = []
    i = 1
    while i < len(events):
        event = events[i]
        if check_type(event, Project):
            projects.append([project, subtasks])
            subtasks = []
            project = event
        if check_type(event, Subtask):
            subtasks.append(event)
            
