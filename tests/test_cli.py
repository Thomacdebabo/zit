import pytest
from click.testing import CliRunner
from zit.cli import cli
from zit.storage import Storage
from pathlib import Path
import os
from datetime import datetime, timedelta
import csv

@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Fixture to set up a temporary data directory for tests."""
    # Create a temporary directory for .zit
    zit_dir = tmp_path / ".zit"
    zit_dir.mkdir()
    trash_dir = zit_dir / "trash"
    trash_dir.mkdir()

    # Monkeypatch Storage to use the temporary directory
    monkeypatch.setattr("zit.storage.Storage.data_dir", zit_dir)
    monkeypatch.setattr("zit.storage.Storage.trash_dir", trash_dir)
    
    # Ensure Storage re-initializes paths based on the patched dir
    # We create an instance here, which CLI commands will also do, picking up the patches
    storage = Storage()

    yield zit_dir # Provide the temp dir path to the test if needed

    # Cleanup happens automatically due to tmp_path fixture

@pytest.fixture
def runner():
    """Fixture to provide a CliRunner instance."""
    return CliRunner()

# --- CLI Command Tests ---

def test_start_stop(runner, test_env):
    """Test zit start and zit stop commands."""
    # Start
    result_start = runner.invoke(cli, ['start', 'Work']) 
    assert result_start.exit_code == 0
    assert "Started tracking time for project: Work" in result_start.output

    # Check data file
    storage = Storage() # Re-init to get correct data_file path for today
    assert storage.data_file.exists()
    events = storage.get_events()
    assert len(events) == 1
    assert events[0].project == 'Work'

    # Stop
    # Simulate some time passing
    # (We don't need exact time for integration, just order)
    result_stop = runner.invoke(cli, ['stop'])
    assert result_stop.exit_code == 0
    assert "Stopping time tracking..." in result_stop.output

    # Check data file again
    events = storage.get_events()
    assert len(events) == 2
    assert events[0].project == 'Work'
    assert events[1].project == 'STOP'
    assert events[1].timestamp > events[0].timestamp

def test_add(runner, test_env):
    """Test zit add command."""
    result = runner.invoke(cli, ['add', 'Meeting', '1430'])
    assert result.exit_code == 0
    assert "Added project: Meeting at 14:30" in result.output

    # Check data file
    storage = Storage() 
    events = storage.get_events()
    assert len(events) == 1
    assert events[0].project == 'Meeting'
    assert events[0].timestamp.hour == 14
    assert events[0].timestamp.minute == 30

    # Test invalid time
    result_invalid = runner.invoke(cli, ['add', 'Invalid', '9999'])
    assert result_invalid.exit_code == 0 # Click commands often exit 0 on user error
    assert "Error: Invalid time values" in result_invalid.output

def test_status(runner, test_env):
    """Test zit status command."""
    # Add some data
    runner.invoke(cli, ['add', 'Setup', '0900']) # 9:00
    runner.invoke(cli, ['add', 'Coding', '0930']) # 9:30 (30 mins Setup)
    runner.invoke(cli, ['add', 'Lunch', '1230']) # 12:30 (3h Coding)
    runner.invoke(cli, ['add', 'Coding', '1330']) # 13:30 (1h Lunch)
    # Leave 'Coding' ongoing

    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert "Current status..." in result.output
    # Check intervals
    assert "Setup - 0:30:0 ( 09:00:00 -> 09:30:00)" in result.output
    assert "Coding - 3:0:0 ( 09:30:00 -> 12:30:00)" in result.output
    assert "Lunch - 1:0:0 ( 12:30:00 -> 13:30:00)" in result.output # Note: LUNCH is excluded by default
    # Check ongoing
    assert "Ongoing project:" in result.output
    assert "Coding - " in result.output # Checks that Coding is the ongoing one
    # Check project times (Lunch excluded)
    assert "Time per project:" in result.output
    assert "Coding - " in result.output # Will include ongoing time
    assert "Setup - 0:30:0" in result.output
    assert "Lunch" not in result.output # Excluded project time shouldn't be listed here
    # Check totals (Lunch excluded)
    assert "Total time:" in result.output
    assert "Total:" in result.output # Actual total depends on current time
    assert "Excluded: 1:0:0" in result.output # 1h Lunch

def test_clear(runner, test_env):
    """Test zit clear command."""
    # Add some data
    runner.invoke(cli, ['start', 'ToDelete'])
    storage = Storage()
    assert storage.data_file.exists()
    assert len(storage.trash_dir.glob('*.csv')) == 0

    result = runner.invoke(cli, ['clear'])
    assert result.exit_code == 0
    assert "All data has been cleared." in result.output

    # Check file is moved to trash
    assert not storage.data_file.exists()
    assert len(list(storage.trash_dir.glob('*.csv'))) == 1

def test_clean(runner, test_env):
    """Test zit clean command."""
    storage = Storage()
    now = datetime.now()
    # Manually create unsorted/duplicate data
    with open(storage.data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([(now + timedelta(minutes=10)).isoformat(), "TaskB"])
        writer.writerow([(now).isoformat(), "TaskA"])
        writer.writerow([(now + timedelta(minutes=5)).isoformat(), "TaskA"])
        writer.writerow([(now + timedelta(minutes=20)).isoformat(), "TaskC"])
        writer.writerow([(now + timedelta(minutes=25)).isoformat(), "TaskC"])

    result = runner.invoke(cli, ['clean'])
    assert result.exit_code == 0
    assert "Data has been cleaned." in result.output

    # Check data is sorted and duplicates removed
    events = storage.get_events() # get_events also sorts, but _combine_events is the key
    assert len(events) == 3
    assert events[0].project == "TaskA"
    assert events[1].project == "TaskB"
    assert events[2].project == "TaskC"
    # Verify timestamps are still correct relative to each other
    assert events[0].timestamp < events[1].timestamp < events[2].timestamp

def test_verify(runner, test_env):
    """Test zit verify command."""
    storage = Storage()
    now = datetime.now()

    # Case 1: No Lunch, No Stop
    with open(storage.data_file, 'w', newline='') as f:
        csv.writer(f).writerow([now.isoformat(), "Work"])
    result = runner.invoke(cli, ['verify'])
    assert result.exit_code == 0
    assert "✗ LUNCH event not found" in result.output
    assert "✗ final STOP event not found" in result.output
    storage.remove_data_file() # Clear for next case

    # Case 2: Lunch, No Stop
    with open(storage.data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([(now).isoformat(), "Work"])
        writer.writerow([(now + timedelta(minutes=60)).isoformat(), "LUNCH"])
        writer.writerow([(now + timedelta(minutes=120)).isoformat(), "Work"])
    result = runner.invoke(cli, ['verify'])
    assert result.exit_code == 0
    assert "✓ LUNCH event found" in result.output
    assert "✗ final STOP event not found" in result.output
    storage.remove_data_file()

    # Case 3: No Lunch, Stop
    with open(storage.data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([(now).isoformat(), "Work"])
        writer.writerow([(now + timedelta(minutes=60)).isoformat(), "STOP"])
    result = runner.invoke(cli, ['verify'])
    assert result.exit_code == 0
    assert "✗ LUNCH event not found" in result.output
    assert "✓ final STOP event found" in result.output
    storage.remove_data_file()

    # Case 4: Lunch, Stop
    with open(storage.data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([(now).isoformat(), "Work"])
        writer.writerow([(now + timedelta(minutes=60)).isoformat(), "LUNCH"])
        writer.writerow([(now + timedelta(minutes=120)).isoformat(), "Work"])
        writer.writerow([(now + timedelta(minutes=180)).isoformat(), "STOP"])
    result = runner.invoke(cli, ['verify'])
    assert result.exit_code == 0
    assert "✓ LUNCH event found" in result.output
    assert "✓ final STOP event found" in result.output

# TODO: Test for status --yesterday (requires creating a file with yesterday's date) 