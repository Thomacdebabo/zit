# Zit Bash Implementation

A hybrid bash/Python implementation of Zit (Zimple Interval Tracker) - a minimal time tracking CLI tool.

## Architecture

This implementation uses a **hybrid approach**:

- **Bash-implemented commands**: Simple, fast commands for the most common operations (start, stop, lunch, add, sub, current)
- **Python-forwarded commands**: Complex commands that require calculations and formatting (status, clean, verify, remove, change, list, note)

This approach provides the best of both worlds: the speed and simplicity of bash for routine tasks, and the full power of the Python implementation for advanced features.

## Features

### Bash-Implemented Commands

These run directly in bash for maximum speed:

- **start** - Start tracking a project or subtask
- **stop** - Stop tracking time
- **lunch** - Track lunch breaks
- **add** - Add entries at specific times
- **sub** - Add subtasks to the current project
- **current** - Show the current task

### Python-Forwarded Commands

These forward to the full Python implementation:

- **status** - Show detailed status with time calculations
- **clean** - Clean and organize entries
- **verify** - Verify data integrity
- **remove** - Interactively remove events
- **change** - Interactively change event names
- **list** - List all subtasks with details
- **note** - Add notes to subtasks
- **attach** - Attach subtasks to projects

## Installation

**Prerequisites**: A file named `zit-python` must exist in the same directory as the bash `zit` script. This should be:
- A symlink to your Python zit installation, or
- A copy/wrapper that calls the Python version

Example setup:
```bash
cd zit-bash
chmod +x zit

# Option 1: Symlink to installed Python zit
ln -s ~/.local/bin/zit zit-python

# Option 2: Symlink to compiled binary
ln -s ../build/zit/zit zit-python

# Option 3: Create a wrapper script
cat > zit-python << 'EOF'
#!/usr/bin/env python3
import sys
import subprocess
sys.exit(subprocess.call([sys.executable, '-m', 'zit'] + sys.argv[1:]))
EOF
chmod +x zit-python
```

Then optionally add to your PATH:
```bash
# Add to PATH (e.g., in ~/.bashrc)
export PATH="/path/to/zit-bash:$PATH"
```

## Usage

All commands work identically to the Python version. The bash script automatically routes commands to the appropriate implementation.

### Start tracking a project

```bash
./zit start PROJECT_NAME
./zit start "My Project"
./zit start                 # Uses DEFAULT
```

### Start with a subtask

**Note:** `--sub` now takes a string argument (changed from flag):

```bash
./zit start PROJECT --sub SUBTASK_NAME
./zit start "Coding" --sub "implement-login" --note "User auth feature"
```

### Stop tracking

```bash
./zit stop
```

### Track lunch

```bash
./zit lunch          # Current time
./zit lunch 1200     # At noon
./zit lunch 1330     # At 1:30 PM
```

### Add entries at specific times

Add a project:
```bash
./zit add MEETING 1400
./zit add "Code Review" 0930
```

Add a subtask at specific time:
```bash
./zit add PROJECT 1400 --sub "my-subtask" --note "Some notes"
```

### Add subtask to current project

```bash
./zit sub "implement feature"
./zit sub "bug fix" --note "Issue #123"
```

### Show current task

```bash
./zit current
```

### Show status

```bash
./zit status
```

## Data Storage

Data is stored in `~/.zit/` directory:
- Projects: `YYYY-MM-DD.csv`
- Subtasks: `YYYY-MM-DD_subtasks.csv`

### CSV Format

**Projects:**
```csv
TIMESTAMP,PROJECT_NAME
```

**Subtasks:**
```csv
TIMESTAMP,SUBTASK_NAME,NOTE
```

Timestamp format: `YYYY-MM-DD HH:MM:SS.microseconds`

## Compatibility

The bash implementation is fully compatible with the Python version:
- Uses the same CSV format
- Stores data in the same directory structure
- Can read and write files created by either version
- All Python commands are accessible via forwarding

## Key Changes from Pure Python Version

1. **Hybrid architecture** - Common commands run in bash, complex commands forward to Python

2. **`--sub` is now a string argument** instead of a flag for bash commands:
   - Old (Python flag): `zit start --sub` (uses project name as subtask)
   - New (Bash): `zit start PROJECT --sub SUBTASK_NAME` (explicit subtask name)

3. **Faster for routine operations** - No Python startup overhead for simple commands

4. **Full compatibility** - All Python features still available through forwarding

## How Forwarding Works

When you run a forwarded command (status, clean, verify, remove, change, list, note, attach), the bash script:

1. Locates the Python zit installation (checks `~/.local/bin/zit`, `/usr/local/bin/zit`, `/usr/bin/zit`)
2. Passes all arguments directly to the Python implementation
3. Returns the same output and exit code

This means you get the full power of the Python implementation when needed, with zero compromise on functionality.

## Examples

```bash
# Start work day (bash command - fast)
./zit start "Morning standup"

# Add a subtask (bash command)
./zit sub "discuss sprint goals"

# Switch to coding (bash command)
./zit start "Development" --sub "implement-api" --note "REST endpoints"

# Lunch break (bash command)
./zit lunch 1200

# Back to work (bash command)
./zit start "Development"

# End of day (bash command)
./zit stop

# Check detailed status (forwarded to Python)
./zit status

# Verify today's data (forwarded to Python)
./zit verify

# Remove an event interactively (forwarded to Python)
./zit remove

# Check yesterday's status with all features (forwarded to Python)
./zit status --yesterday

# List all subtasks with details (forwarded to Python)
./zit list
```

## Performance

Bash-implemented commands execute instantly (< 10ms on typical systems) since they avoid Python startup overhead. Python-forwarded commands have standard Python startup time but provide full functionality.

For typical daily usage patterns (many start/stop/add operations, occasional status checks), this hybrid approach provides the best overall experience.
