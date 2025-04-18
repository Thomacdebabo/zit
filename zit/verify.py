
def verify_contains(events, project_name):
    """Verify that there is a LUNCH event in the events list"""
    for event in events:
        if event.name == project_name:
            return True
    return False

def verify_lunch(events):
    """Verify that there is a LUNCH event in the events list"""
    if not events:
        return False
    return verify_contains(events, "LUNCH")

def verify_stop(events):
    """Verify that last event is a STOP event in the events list"""
    if not events:
        return False
    return events[-1].name == "STOP"

def verify_no_default_project(events):
    """Verify that no default project is used"""
    for event in events:
        if event.name == "DEFAULT":
            return False
    return True

