# Zit - Zimple Interval Tracker
- simple time tracking tool
- similar to grindstone without the annoying gui and the constant pop ups
- cli?


Datastructure:
- basically just timestamp -> everything is calculated on top
- projects
	- subtasks
		- notes
- unadressed

Commands:
- ***add**     Add a project with a specific time (format: HHMM, e.g.
- **clean**   Clean the data
- **clear**   Clear all data
- **remove**  Remove the last event
- **start**   Start tracking time for a project
- **status**  Show current tracking status
- **stop**    Stop tracking time
- **verify**  Verify the data

# Implementation
- CLI interface which just lets me write to a file directly

# Build
Use pyinstaller to get the zit executable
``` bash
pyinstaller --onefile --name zit run_zit.py
mv ./dist/zit ~/.local/bin
```

# Timetracking
---
- (estimate) until v0.2.1: ~5h

## 18.04.25
```
┌────────────────────────────────────────────────┐
│ Events and Subtasks:                           │
└────────────────────────────────────────────────┘
zit ────────────────────────── 16:01:00 | 0:56:21
  ├─ zit-fm                    16:01:00 | 0:19:51
  ├─ attach                    16:20:52 | 0:14:53
  ├─ subtaskintegration        16:35:45 | 0:21:36
  └─────────────────────────── 16:57:21
┌────────────────────────────────────────────────┐
│ Total time:                                    │
└────────────────────────────────────────────────┘
Total: 0:56:21
Excluded: 0:0:0
  
```