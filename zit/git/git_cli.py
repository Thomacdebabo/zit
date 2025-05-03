#!/usr/bin/env python3
from ..terminal import *
import click
import subprocess
from datetime import datetime
import os
import shutil
from pathlib import Path
from .git_storage import GitStorage, GIT_DATA_DIR
from ..events import Project, Subtask, GitCommit
from ..print import print_events_with_index
@click.group()
def git_cli():
    """Git integration for Zit time tracking"""
    pass

def get_git_commits(directory=None, since=None, author=None, limit=None, email=None):
    """Get git commits from repository"""
    cmd = ['git']
    
    if directory:
        cmd.extend(['-C', directory])
    
    cmd.extend(['log', '--pretty=format:%H|%an|%at|%s|%ae'])
    
    if since:
        cmd.extend(['--since', since])
    
    if author:
        cmd.extend(['--author', author])
        
    if limit:
        cmd.extend(['-n', str(limit)])
    
    if email:
        cmd.extend(['--author-email', email])
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        commits = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('|', 4)  # Split into 5 parts max
            if len(parts) < 5:
                # Handle case where email might be missing
                if len(parts) == 4:
                    # Add empty email
                    parts.append("")
                else:
                    continue
                
            commit_hash, author, timestamp, message, email = parts
            # Convert Unix timestamp to datetime
            commit_time = datetime.fromtimestamp(int(timestamp))
            
            commits.append({
                'hash': commit_hash,
                'author': author,
                'email': email,
                'timestamp': commit_time,
                'message': message
            })
            
        return commits
    except subprocess.CalledProcessError as e:
        print_string(f"Error fetching git commits: {e}", err=True)
        return []

@git_cli.command("import")
@click.option('--directory', '-d', help='Git repository directory')
@click.option('--since', '-s', help='Get commits since date (e.g. "1 week ago", "2023-01-01")')
@click.option('--author', '-a', help='Filter by author')
@click.option('--limit', '-l', type=int, help='Limit number of commits')
@click.option('--as-subtasks', is_flag=True, help='Import commits as subtasks')
@click.option('--project-name', '-p', default='default', help='Project name for the commits')
def import_commits(directory, since, author, limit, as_subtasks, project_name):
    """Import git commits as Zit tasks"""
    if not directory:
        directory = os.getcwd()
    
    # Use the project name (or repo name if not specified)
    if project_name == 'default':
        # Try to get repo name from directory
        repo_name = os.path.basename(os.path.abspath(directory))
        if repo_name:
            project_name = repo_name
    
    print_string(f"Importing git commits from {directory} into project '{project_name}'...")
    
    commits = get_git_commits(directory, since, author, limit)
    
    if not commits:
        print_string("No commits found.")
        return
    
    # Group commits by date
    commits_by_date = {}
    for commit in commits:
        date_str = commit['timestamp'].strftime('%Y-%m-%d')
        if date_str not in commits_by_date:
            commits_by_date[date_str] = []
        commits_by_date[date_str].append(commit)
    
    total_imported = 0
    
    # Process commits for each date separately
    for date_str, date_commits in commits_by_date.items():
        storage = GitStorage(project_name=project_name, current_date=date_str)
        
        print_string(f"\nProcessing {len(date_commits)} commits for date {date_str}...")
        
        for commit in date_commits:
            timestamp = commit['timestamp']
            message = commit['message']
            commit_hash = commit['hash'][:7]  # Short hash
            author = commit['author']
            email = commit['email']
            if as_subtasks:
                # Find the project that was active at this time or use the specified project

                storage.add_event(GitCommit(
                    timestamp=timestamp,
                    hash=commit_hash,
                    message=message,
                    author=author,
                    email=email  
                ))
                print_string(f"Added subtask: {message} at {timestamp.strftime('%H:%M')}")
            else:
                storage.add_event(GitCommit(
                    timestamp=timestamp,
                    hash=commit_hash,
                    message=message,
                    author=author,
                    email=email
                ))

                print_string(f"Added project: {message} at {timestamp.strftime('%H:%M')}")
            
            total_imported += 1
    
    print_string(f"\nImported {total_imported} commits across {len(commits_by_date)} different dates.")

def get_date_files_for_project(project_name):
    """Get all date files for a project"""
    project_dir = GIT_DATA_DIR / project_name
    if not project_dir.exists():
        return []
    
    # Get all CSV files in the project directory that don't end with _subtasks.csv
    date_files = [f for f in project_dir.glob("*.csv") if not f.name.endswith("_subtasks.csv")]
    return sorted(date_files)

@git_cli.command("list")
@click.option('--date', '-d', default=datetime.now().strftime('%Y-%m-%d'), help='List events for a specific date (format: YYYY-MM-DD)')
@click.option('--all', '-a', is_flag=True, help='List events for all dates')
@click.option('--project', '-p', help='Project name to list events for')
def list_git_events(date, all, project):
    """List all git events"""
    if not project:
        # Try to get project name from current directory
        current_dir = os.path.basename(os.path.abspath(os.getcwd()))
        projects = GitStorage.list_projects()
        
        if current_dir in projects:
            project = current_dir
        else:
            if not projects:
                print_string("No git projects found.")
                return
            
            print_string("\nAvailable git projects:")
            for i, proj in enumerate(projects, 0):
                print_string(f"[{i}] {proj}")
            index = click.prompt("Enter project number to view events", type=int, default=0)
            project = projects[index]
    if all:
        # Show events for all dates
        date_files = get_date_files_for_project(project)
        
        if not date_files:
            print_string(f"No git events found for project '{project}'.")
            return
    if date:
        # Show events for a specific date
        storage = GitStorage(project_name=project, current_date=date)
        
        commits = storage.get_events()
        
        if not commits:
            print_string(f"No git events found for project '{project}' on {date}.")
            return
        
        print_string(f"\nGit Projects for '{project}' on {date}:")
        for commit in commits:
            print_string(f"{commit.timestamp.strftime('%H:%M')} - {commit.message}")
    else:
        # Show events for all dates
        date_files = get_date_files_for_project(project)
        
        if not date_files:
            print_string(f"No git events found for project '{project}'.")
            return
        
        for date_file in date_files:
            date_str = date_file.stem
            storage = GitStorage(project_name=project, current_date=date_str)

            commits = storage.get_events()
            
            if commits:
                print_string(f"\n--- Events for {date_str} ---")
                
                if commits:
                    print_string(f"\nCommits:")
                    current_author = None
                    for commit in commits:
                        if current_author != commit.author:
                            print_string(f"    by {commit.author} ({commit.email})")
                            current_author = commit.author
                        print_string(f"    {commit.timestamp.strftime('%H:%M')} - {commit.message}")

@git_cli.command("projects")
def list_git_projects():
    """List all git projects"""
    projects = GitStorage.list_projects()
    
    if not projects:
        print_string("No git projects found.")
        return
    
    print_string("\nGit Projects:")
    for project in projects:
        print_string(f"- {project}")

@git_cli.command("remove")
@click.argument('project_name')
@click.option('--all', '-a', is_flag=True, help='Remove all git projects')
@click.confirmation_option(prompt='Are you sure you want to remove git project data?')
def remove_git_project(project_name, all):
    """Remove a specific git project or all git projects"""
    from .git_storage import GIT_DATA_DIR
    
    if all:
        # Remove all projects
        if not GIT_DATA_DIR.exists():
            print_string("No git projects found.")
            return
            
        for project_dir in GIT_DATA_DIR.iterdir():
            if project_dir.is_dir():
                shutil.rmtree(project_dir)
        
        print_string("All git projects have been removed.")
        return
    
    if not project_name:
        # List projects for selection
        projects = GitStorage.list_projects()
        if not projects:
            print_string("No git projects found.")
            return
        
        print_string("\nAvailable git projects:")
        for i, proj in enumerate(projects, 1):
            print_string(f"{i}. {proj}")
        
        selection = click.prompt("Enter project number to remove", type=int, default=1)
        if selection < 1 or selection > len(projects):
            print_string("Invalid selection.")
            return
            
        project_name = projects[selection-1]
    
    # Remove the project directory
    project_dir = GIT_DATA_DIR / project_name
    if not project_dir.exists():
        print_string(f"Project '{project_name}' not found.")
        return
    
    shutil.rmtree(project_dir)
    print_string(f"Project '{project_name}' has been removed.")

if __name__ == '__main__':
    git_cli()
