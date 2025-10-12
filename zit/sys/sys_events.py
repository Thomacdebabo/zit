from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from typing import Any
from collections.abc import Sequence


class SystemEventType(str, Enum):
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    SLEEP = "sleep"
    WAKE = "wake"
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"
    LOGIN = "login"
    LOGOUT = "logout"


class SystemEvent(BaseModel):
    timestamp: datetime
    event_type: SystemEventType
    details: str = ""
    user: str = ""

    def to_row(self) -> list[Any]:
        return [self.timestamp, self.event_type, self.details, self.user]

    @classmethod
    def from_row(cls, row: Sequence[Any]) -> 'SystemEvent':
        if len(row) >= 4:
            return cls(timestamp=row[0], event_type=row[1], details=row[2], user=row[3])
        elif len(row) == 3:
            return cls(timestamp=row[0], event_type=row[1], details=row[2])
        else:
            return cls(timestamp=row[0], event_type=row[1])
