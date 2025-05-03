from datetime import datetime
from pydantic import BaseModel
from .calculate import *

def load_date(date):
    return datetime.fromisoformat(date)

class Project(BaseModel):
    timestamp: datetime
    name: str

    def from_row(row):
        timestamp = load_date(row[0])
        return Project(timestamp=timestamp, name=row[1])
    
    def to_row(self):
        return [self.timestamp, self.name]

class Subtask(Project):
    note: str

    def from_row(row):
        timestamp = load_date(row[0])
        if len(row) == 3:   
            return Subtask(timestamp=timestamp, name=row[1], note=row[2])
        else:
            return Subtask(timestamp=timestamp, name=row[1], note="")
    
    def to_row(self):
        return [self.timestamp, self.name, self.note]

class GitCommit(BaseModel):
    timestamp: datetime
    hash: str
    message: str
    author: str
    email: str

    def from_row(row):
        timestamp = load_date(row[0])
        return GitCommit(timestamp=timestamp, hash=row[1], message=row[2], author=row[3], email=row[4])
    
    def to_row(self):
        return [self.timestamp, self.hash, self.message, self.author, self.email]

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
            
