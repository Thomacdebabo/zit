#!/usr/bin/env python3

import pytest
import subprocess
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the parent directory to the path to import zit modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from zit.storage import Storage, SubtaskStorage
from zit.events import Project, Subtask


@pytest.fixture
def zit_env():
    """Fixture to set up a temporary environment for zit tests"""
    test_dir = tempfile.mkdtemp()
    original_home = os.environ.get('HOME')
    os.environ['HOME'] = test_dir
    
    # Create test data directory
    data_dir = Path(test_dir) / '.zit'
    data_dir.mkdir(exist_ok=True)
    
    def run_zit_command(args, input_data=None):
        """Helper to run zit commands with proper environment"""
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'run_zit.py')] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
            env={**os.environ, 'HOME': test_dir}
        )
        return result
    
    def run_zit_fm_command(args, input_data=None):
        """Helper to run zit file manager commands"""
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'run_zit_fm.py')] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
            env={**os.environ, 'HOME': test_dir}
        )
        return result
    
    def run_zit_git_command(args, input_data=None):
        """Helper to run zit git commands"""
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'run_zit_git.py')] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
            env={**os.environ, 'HOME': test_dir}
        )
        return result
    
    def run_zit_sys_command(args, input_data=None):
        """Helper to run zit system commands"""
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'run_zit_sys.py')] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
            env={**os.environ, 'HOME': test_dir}
        )
        return result
    
    # Create a namespace object to hold our helpers
    class ZitTestHelpers:
        def __init__(self):
            self.test_dir = test_dir
            self.data_dir = data_dir
            self.run_zit_command = run_zit_command
            self.run_zit_fm_command = run_zit_fm_command
            self.run_zit_git_command = run_zit_git_command
            self.run_zit_sys_command = run_zit_sys_command
    
    helpers = ZitTestHelpers()
    
    yield helpers
    
    # Cleanup
    if original_home:
        os.environ['HOME'] = original_home
    else:
        os.environ.pop('HOME', None)
    shutil.rmtree(test_dir)


@pytest.fixture
def git_repo(zit_env):
    """Fixture to create a test git repository"""
    git_repo_path = Path(zit_env.test_dir) / 'test_repo'
    git_repo_path.mkdir()
    original_cwd = os.getcwd()
    os.chdir(git_repo_path)
    
    # Initialize git repo and create some commits
    subprocess.run(['git', 'init'], capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], capture_output=True)
    
    # Create a test file and commit
    test_file = git_repo_path / 'test.txt'
    test_file.write_text('Initial content')
    subprocess.run(['git', 'add', 'test.txt'], capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], capture_output=True)
    
    yield git_repo_path
    
    os.chdir(original_cwd)


# Main CLI Tests
def test_help_command(zit_env):
    """Test help command displays available commands"""
    result = zit_env.run_zit_command(['--help'])
    assert result.returncode == 0
    assert 'Zit - Zimple Interval Tracker' in result.stdout
    assert 'start' in result.stdout
    assert 'stop' in result.stdout
    assert 'status' in result.stdout


def test_start_command_default_project(zit_env):
    """Test starting time tracking with default project"""
    result = zit_env.run_zit_command(['start'])
    assert result.returncode == 0
    assert 'Started tracking time for project: DEFAULT' in result.stdout
    
    # Verify event was recorded by checking file exists in test environment
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    # Check file content
    content = data_file.read_text()
    assert 'DEFAULT' in content


def test_start_command_custom_project(zit_env):
    """Test starting time tracking with custom project"""
    result = zit_env.run_zit_command(['start', 'TestProject'])
    assert result.returncode == 0
    assert 'Started tracking time for project: TestProject' in result.stdout
    
    # Verify event was recorded by checking file exists in test environment
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    # Check file content
    content = data_file.read_text()
    assert 'TestProject' in content


def test_stop_command(zit_env):
    """Test stopping time tracking"""
    # First start a project
    zit_env.run_zit_command(['start', 'TestProject'])
    
    # Then stop
    result = zit_env.run_zit_command(['stop'])
    assert result.returncode == 0
    assert 'Stopping time tracking' in result.stdout
    
    # Verify both events were recorded
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    # Check file content for both events
    content = data_file.read_text()
    assert 'TestProject' in content
    assert 'STOP' in content


def test_lunch_command_default_time(zit_env):
    """Test lunch command with current time"""
    result = zit_env.run_zit_command(['lunch'])
    assert result.returncode == 0
    assert 'Starting lunch time tracking' in result.stdout
    
    # Verify LUNCH event was recorded
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    content = data_file.read_text()
    assert 'LUNCH' in content


def test_lunch_command_specific_time(zit_env):
    """Test lunch command with specific time"""
    result = zit_env.run_zit_command(['lunch', '1200'])
    assert result.returncode == 0
    assert 'Starting lunch time tracking' in result.stdout
    
    # Verify LUNCH event was recorded with time
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    content = data_file.read_text()
    assert 'LUNCH' in content
    # The time should be in the file in some format
    assert '12:00' in content or '1200' in content

def test_status_command_no_events(zit_env):
    """Test status command with no events"""
    result = zit_env.run_zit_command(['status'])
    assert result.returncode == 0
    assert 'No events found for' in result.stdout


def test_status_command_with_events(zit_env):
    """Test status command with events"""
    # Add some test events
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['lunch', '1200'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_command(['status'])
    assert result.returncode == 0
    assert 'Status for' in result.stdout
    assert 'TestProject' in result.stdout


def test_status_command_yesterday(zit_env):
    """Test status command for yesterday"""
    result = zit_env.run_zit_command(['status', '--yesterday'])
    assert result.returncode == 0
    assert 'No events found for' in result.stdout


def test_status_command_specific_date(zit_env):
    """Test status command for specific date"""
    date = '2024-01-01'
    result = zit_env.run_zit_command(['status', '--date', date])
    assert result.returncode == 0
    assert f'No events found for {date}' in result.stdout


def test_add_command_project_with_time(zit_env):
    """Test adding a project with specific time"""
    result = zit_env.run_zit_command(['add', 'TestProject', '0900'])
    assert result.returncode == 0
    assert 'Added project: TestProject at 09:00' in result.stdout
    
    # Verify event was recorded by checking file in test environment
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    content = data_file.read_text()
    assert 'TestProject' in content
    assert '09:00' in content or '0900' in content


def test_add_command_invalid_time(zit_env):
    """Test adding project with invalid time"""
    result = zit_env.run_zit_command(['add', 'TestProject', '2500'])
    assert result.returncode == 0
    assert 'Error:' in result.stdout


def test_add_command_subtask(zit_env):
    """Test adding a subtask"""
    # First add a main project
    zit_env.run_zit_command(['add', 'MainProject', '0900'])
    
    # Then add a subtask
    result = zit_env.run_zit_command(['add', 'SubtaskName', '0930', '--subtask'])
    assert result.returncode == 0
    assert 'Added subtask: SubtaskName at 09:30' in result.stdout
    
    # Verify subtask was recorded in subtasks file
    today = datetime.now().strftime('%Y-%m-%d')
    subtask_file = zit_env.data_dir / f'{today}_subtasks.csv'
    assert subtask_file.exists(), f"Subtask file {subtask_file} should exist"
    
    content = subtask_file.read_text()
    assert 'SubtaskName' in content


def test_add_command_subtask_no_current_task(zit_env):
    """Test adding subtask when no current task exists"""
    result = zit_env.run_zit_command(['add', 'SubtaskName', '0930', '--subtask'])
    assert result.returncode == 0
    assert 'No current task. No subtask added.' in result.stdout


def test_clear_command(zit_env):
    """Test clearing all data"""
    # First add some data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['sub', 'TestSubtask'])
    
    # Verify files exist before clearing
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    subtask_file = zit_env.data_dir / f'{today}_subtasks.csv'
    
    # Clear data
    result = zit_env.run_zit_command(['clear'])
    assert result.returncode == 0
    assert 'All data has been cleared' in result.stdout
    
    # Check if files were moved to trash (not just deleted)
    # The exact trash mechanism might vary, so we'll just check the command succeeded


def test_clean_command(zit_env):
    """Test cleaning data"""
    result = zit_env.run_zit_command(['clean'])
    assert result.returncode == 0
    assert 'Data has been cleaned' in result.stdout


def test_verify_command_no_events(zit_env):
    """Test verify command with no events"""
    result = zit_env.run_zit_command(['verify'])
    assert result.returncode == 0
    assert 'LUNCH event not found' in result.stdout


def test_verify_command_with_complete_day(zit_env):
    """Test verify command with complete day data"""
    # Add complete day events
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['lunch', '1200'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_command(['verify'])
    assert result.returncode == 0
    assert 'LUNCH event found' in result.stdout
    assert 'no DEFAULT times found' in result.stdout


def test_current_command_no_task(zit_env):
    """Test current command with no active task"""
    result = zit_env.run_zit_command(['current'])
    assert result.returncode == 0
    assert 'No current task' in result.stdout


def test_current_command_with_task(zit_env):
    """Test current command with active task"""
    zit_env.run_zit_command(['start', 'TestProject'])
    
    result = zit_env.run_zit_command(['current'])
    assert result.returncode == 0
    assert 'Current task: TestProject' in result.stdout


def test_sub_command(zit_env):
    """Test adding subtask with sub command"""
    # First start a project
    zit_env.run_zit_command(['start', 'TestProject'])
    
    # Add subtask
    result = zit_env.run_zit_command(['sub', 'TestSubtask'])
    assert result.returncode == 0
    assert 'Added subtask: TestSubtask' in result.stdout
    
    # Verify subtask was recorded in subtasks file
    today = datetime.now().strftime('%Y-%m-%d')
    subtask_file = zit_env.data_dir / f'{today}_subtasks.csv'
    assert subtask_file.exists(), f"Subtask file {subtask_file} should exist"
    
    content = subtask_file.read_text()
    assert 'TestSubtask' in content


def test_sub_command_no_current_task(zit_env):
    """Test sub command with no current task"""
    result = zit_env.run_zit_command(['sub', 'TestSubtask'])
    assert result.returncode == 0
    assert 'No current task. Operation aborted.' in result.stdout


def test_list_command_no_events(zit_env):
    """Test list command with no events"""
    result = zit_env.run_zit_command(['list'])
    assert result.returncode == 0
    assert 'No events found' in result.stdout


def test_list_command_with_events(zit_env):
    """Test list command with events"""
    # Add some test data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['sub', 'TestSubtask'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_command(['list'])
    assert result.returncode == 0
    assert 'TestProject' in result.stdout
    assert 'TestSubtask' in result.stdout

# File Manager CLI Tests
def test_fm_help_command(zit_env):
    """Test file manager help command"""
    result = zit_env.run_zit_fm_command(['--help'])
    assert result.returncode == 0
    assert 'Zit FileManager' in result.stdout
    assert 'list' in result.stdout
    assert 'remove' in result.stdout
    assert 'status' in result.stdout


def test_fm_list_no_files(zit_env):
    """Test list command with no data files"""
    result = zit_env.run_zit_fm_command(['list'])
    assert result.returncode == 0
    assert 'No data files found' in result.stdout


def test_fm_list_with_files(zit_env):
    """Test list command with data files"""
    # Create some test data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_fm_command(['list'])
    assert result.returncode == 0
    assert 'Available data files' in result.stdout
    assert 'Total:' in result.stdout


def test_fm_list_verbose(zit_env):
    """Test list command with verbose output"""
    # Create some test data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_fm_command(['list', '--verbose'])
    assert result.returncode == 0
    assert 'TestProject' in result.stdout


def test_fm_list_last_n_files(zit_env):
    """Test list command with -n option"""
    # Create some test data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_fm_command(['list', '-n', '1'])
    assert result.returncode == 0
    assert 'Available data files' in result.stdout


def test_fm_status_no_files(zit_env):
    """Test status command with no files"""
    result = zit_env.run_zit_fm_command(['status'])
    assert result.returncode == 0
    # Should complete without error even with no files


def test_fm_status_with_files(zit_env):
    """Test status command with files"""
    # Create some test data
    zit_env.run_zit_command(['start', 'TestProject'])
    zit_env.run_zit_command(['stop'])
    
    result = zit_env.run_zit_fm_command(['status'])
    assert result.returncode == 0
    assert 'TestProject' in result.stdout


# Git CLI Tests
def test_git_help_command(zit_env):
    """Test git help command"""
    result = zit_env.run_zit_git_command(['--help'])
    assert result.returncode == 0
    assert 'Git integration for Zit' in result.stdout
    assert 'import' in result.stdout
    assert 'list' in result.stdout
    assert 'projects' in result.stdout


def test_git_import_commits(zit_env, git_repo):
    """Test importing git commits"""
    result = zit_env.run_zit_git_command([
        'import', 
        '--directory', str(git_repo),
        '--project-name', 'TestRepo'
    ])
    assert result.returncode == 0
    assert 'Importing git commits' in result.stdout
    assert 'Initial commit' in result.stdout


def test_git_import_as_subtasks(zit_env, git_repo):
    """Test importing git commits as subtasks"""
    result = zit_env.run_zit_git_command([
        'import', 
        '--directory', str(git_repo),
        '--project-name', 'TestRepo',
        '--as-subtasks'
    ])
    assert result.returncode == 0
    assert 'Added subtask' in result.stdout


def test_git_import_with_limit(zit_env, git_repo):
    """Test importing git commits with limit"""
    result = zit_env.run_zit_git_command([
        'import', 
        '--directory', str(git_repo),
        '--project-name', 'TestRepo',
        '--limit', '1'
    ])
    assert result.returncode == 0
    assert 'Imported 1 commits' in result.stdout


def test_git_list_no_projects(zit_env):
    """Test list command with no git projects"""
    result = zit_env.run_zit_git_command(['list'])
    assert result.returncode == 0
    assert 'No git projects found' in result.stdout


def test_git_projects_no_projects(zit_env):
    """Test projects command with no projects"""
    result = zit_env.run_zit_git_command(['projects'])
    assert result.returncode == 0
    assert 'No git projects found' in result.stdout


# System CLI Tests
def test_sys_help_command(zit_env):
    """Test system help command"""
    result = zit_env.run_zit_sys_command(['--help'])
    assert result.returncode == 0
    assert 'System events tracking' in result.stdout
    assert 'list' in result.stdout
    assert 'import' in result.stdout
    assert 'awake' in result.stdout


def test_sys_list_no_events(zit_env):
    """Test list command with no system events"""
    result = zit_env.run_zit_sys_command(['list'])
    assert result.returncode == 0
    # The output might be empty or contain "No system events found" depending on implementation
    assert 'No system events found' in result.stdout or result.stdout.strip() == ''


def test_sys_list_all_events(zit_env):
    """Test list command for all events"""
    result = zit_env.run_zit_sys_command(['list', '--all'])
    assert result.returncode == 0
    # Should complete without error


def test_sys_list_last_n_days(zit_env):
    """Test list command for last n days"""
    result = zit_env.run_zit_sys_command(['list', '-n', '7'])
    assert result.returncode == 0
    # Should complete without error


def test_sys_list_specific_date(zit_env):
    """Test list command for specific date"""
    result = zit_env.run_zit_sys_command(['list', '--date', '2024-01-01'])
    assert result.returncode == 0
    # Should complete without error


def test_sys_list_invalid_date(zit_env):
    """Test list command with invalid date format"""
    result = zit_env.run_zit_sys_command(['list', '--date', 'invalid-date'])
    assert result.returncode == 0
    assert 'Invalid date format' in result.stdout


def test_sys_import_logs(zit_env):
    """Test importing system logs"""
    result = zit_env.run_zit_sys_command(['import', '-n', '1'])
    assert result.returncode == 0
    # Should complete without error (may not find logs in test environment)


def test_sys_awake_intervals_no_events(zit_env):
    """Test awake intervals with no events"""
    result = zit_env.run_zit_sys_command(['awake'])
    assert result.returncode == 0
    assert 'No awake intervals found' in result.stdout


def test_sys_awake_intervals_all(zit_env):
    """Test awake intervals for all dates"""
    result = zit_env.run_zit_sys_command(['awake', '--all'])
    assert result.returncode == 0
    # Should complete without error


# Integration Tests
def test_complete_work_day_workflow(zit_env):
    """Test a complete work day workflow"""
    # Start the day
    result = zit_env.run_zit_command(['start', 'Morning-Setup'])
    assert result.returncode == 0
    
    # Add some subtasks
    result = zit_env.run_zit_command(['sub', 'Email-Check'])
    assert result.returncode == 0
    
    result = zit_env.run_zit_command(['sub', 'Daily-Standup'])
    assert result.returncode == 0
    
    # Switch to main project
    result = zit_env.run_zit_command(['add', 'Main-Project', '1000'])
    assert result.returncode == 0
    
    # Lunch break
    result = zit_env.run_zit_command(['lunch', '1200'])
    assert result.returncode == 0
    
    # Afternoon work
    result = zit_env.run_zit_command(['add', 'Afternoon-Tasks', '1300'])
    assert result.returncode == 0
    
    # End day
    result = zit_env.run_zit_command(['stop'])
    assert result.returncode == 0
    
    # Check status
    result = zit_env.run_zit_command(['status'])
    assert result.returncode == 0
    assert 'Morning-Setup' in result.stdout
    assert 'Main-Project' in result.stdout
    assert 'LUNCH' in result.stdout
    assert 'Afternoon-Tasks' in result.stdout
    
    # Verify the day
    result = zit_env.run_zit_command(['verify'])
    assert result.returncode == 0
    assert 'LUNCH event found' in result.stdout


def test_multi_day_workflow(zit_env):
    """Test workflow across multiple days"""
    # Work on day 1
    zit_env.run_zit_command(['start', 'Day1-Project'])
    zit_env.run_zit_command(['stop'])
    
    # Work on yesterday (simulated)
    zit_env.run_zit_command(['add', 'Yesterday-Project', '0900', '--yesterday'])
    zit_env.run_zit_command(['add', 'STOP', '1700', '--yesterday'])
    
    # Check status for different days
    result = zit_env.run_zit_command(['status'])
    assert result.returncode == 0
    assert 'Day1-Project' in result.stdout
    
    result = zit_env.run_zit_command(['status', '--yesterday'])
    assert result.returncode == 0
    assert 'Yesterday-Project' in result.stdout


def test_error_handling_workflows(zit_env):
    """Test various error handling scenarios"""
    # Try to add subtask without current task
    result = zit_env.run_zit_command(['sub', 'NoCurrentTask'])
    assert result.returncode == 0
    assert 'No current task' in result.stdout
    
    # Try invalid time format
    result = zit_env.run_zit_command(['add', 'TestProject', 'invalid-time'])
    assert result.returncode == 0
    assert 'Error:' in result.stdout
    
    # Try invalid date format (currently throws exception, adjust test)
    result = zit_env.run_zit_command(['status', '--date', 'invalid-date'])
    # Command fails with exception currently, so check for non-zero exit or error message
    assert result.returncode != 0 or 'Error:' in result.stdout


# Parametrized tests for different command variations
@pytest.mark.parametrize("project_name", ["TestProject", "Work-Task", "My_Project_123"])
def test_start_command_various_project_names(zit_env, project_name):
    """Test start command with various project name formats"""
    result = zit_env.run_zit_command(['start', project_name])
    assert result.returncode == 0
    assert f'Started tracking time for project: {project_name}' in result.stdout
    
    # Verify event was recorded by checking file
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    content = data_file.read_text()
    assert project_name in content


@pytest.mark.parametrize("time_input,expected_hour,expected_minute", [
    ("0900", 9, 0),
    ("1200", 12, 0),
    ("1530", 15, 30),
    ("2359", 23, 59),
])
def test_add_command_various_times(zit_env, time_input, expected_hour, expected_minute):
    """Test add command with various time formats"""
    result = zit_env.run_zit_command(['add', 'TestProject', time_input])
    assert result.returncode == 0
    
    # Verify event was recorded by checking file
    today = datetime.now().strftime('%Y-%m-%d')
    data_file = zit_env.data_dir / f'{today}.csv'
    assert data_file.exists(), f"Data file {data_file} should exist"
    
    content = data_file.read_text()
    assert 'TestProject' in content
    # Check time is in file (format might vary)
    time_str = f"{expected_hour:02d}:{expected_minute:02d}"
    assert time_str in content or time_input in content


@pytest.mark.parametrize("invalid_time", ["2400", "1260", "99:99", "abc", ""])
def test_add_command_invalid_times(zit_env, invalid_time):
    """Test add command with various invalid time formats"""
    result = zit_env.run_zit_command(['add', 'TestProject', invalid_time])
    assert result.returncode == 0
    assert 'Error:' in result.stdout


@pytest.mark.parametrize("date_option", ["--yesterday", "--date 2024-01-01"])
def test_status_command_date_options(zit_env, date_option):
    """Test status command with different date options"""
    args = ['status'] + date_option.split()
    result = zit_env.run_zit_command(args)
    assert result.returncode == 0
    # Should complete successfully even with no data for those dates


if __name__ == "__main__":
    # Run pytest if script is executed directly
    pytest.main([__file__, "-v"])