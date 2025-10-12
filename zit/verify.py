from zit.events import Project


def verify_contains(events: list[Project], project_name: str) -> bool:
    """Verify that there is a LUNCH event in the events list"""
    for event in events:
        if event.name == project_name:
            return True
    return False


def verify_lunch(events: list[Project]) -> bool:
    """Verify that there is a LUNCH event in the events list"""
    if not events:
        return False
    return verify_contains(events, "LUNCH")


def verify_stop(events: list[Project]) -> bool:
    """Verify that last event is a STOP event in the events list"""
    if not events:
        return False
    return events[-1].name == "STOP"


def verify_no_default_project(events: list[Project]) -> bool:
    """Verify that no default project is used"""
    for event in events:
        if event.name == "DEFAULT":
            return False
    return True


def verify_max_time(events: list[Project]) -> bool:
    """Verify that the total time is less than 24 hours"""
    total_time = 0
    for event in events:
        total_time += event.timestamp  # type: ignore[assignment]
    return total_time < 24 * 60 * 60


def verify_all(events: list[Project]) -> bool:
    """Verify that the events list is valid"""
    verified = True
    verified &= verify_no_default_project(events)
    verified &= verify_lunch(events)
    verified &= verify_stop(events)
    return verified
