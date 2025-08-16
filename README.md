# Zit - Zimple Interval Tracker
- simple time tracking tool
- similar to grindstone without the annoying gui and the constant pop ups
- cli?

# Quickstart
Install:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install.sh | bash
```
Simple use case:
```
# start timetracking in the morning maybe you do not know yet what you will be working on so we just do this:
zit start # will start DEFAULT project, you can also give it a project name if you know already...


Started tracking time for project: DEFAULT

# If later on you figure out what you did you can change an existing entry:
zit change
0: DEFAULT - 14:04:47
Enter index: 0  # you will be asked to enter the index of the item you want to change
Enter the new name: project_name # enter new name
Event has been changed.

# At some point you will be changing your work item so in that case you can just do
zit start new_work_item_name # now you are tracking time for this new item.

# Note: whenever you change work just use zit start again

# At some point you might want to go to lunch. There is a special lunch command for this because it is a common thing in my workday
# Note: lunch is a special work item which is not counted in the end towards your working hours
zit lunch
Starting lunch time tracking...

# Then when you are back you can do zit start again...
# At some point you might have an appointment so to stop time_tracking you can just do
zit stop
Stopping time tracking...

# when you are back resume again with zit start...
# you can also remove entries with:
zit remove # again it will ask you for an index

# Maybe you have forgotten to add an entry or have not been at your computer to do so in time.
# Adding an entry afterwards is done simply by: 
zit add work_item 1400 # time here is written as HHMM (military style I suppose in 24h format)

# At the end of the day you might want to see what you did, maybe change some things.
zit list # will list all entries that you have entered during the day.
# Note: your manual entries should be lower case, special entries are uppercase
# STOP and LUNCH are special and will not be counted towards your total work hours
# DEFAULT will be counted but it is a placeholder which you should change

zit status # summarizes your work day and sums up your hours by working item

zit verify # is a tool to quickly check if your entries seem reasonable
# It checks that:
# - there are no DEFAULT entries
# - there is a final stop entry (you did not forget without stopping)
# - there is a lunch entry (I assume you ate)
# - no default subtasks (will not go into that topic here)
# if everything is good it should look like this:

✓ LUNCH event found
✓ final STOP event found
✓ no DEFAULT times found
✓ no DEFAULT subtasks found

# This check is only to help you, it will not impact the tracking in any way.

```



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
# Install
All:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install.sh | bash
```
zit:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install_zit.sh | bash
```

zit-fm:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install_zit_fm.sh | bash
```

zit-git:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install_zit_git.sh | bash
```

zit-sys:
```
curl -sSL https://raw.githubusercontent.com/Thomacdebabo/zit/main/scripts/install_zit_sys.sh | bash
```
# Implementation
- CLI interface which just lets me write to a file directly

# Build
Use pyinstaller to get the zit executable
``` bash
pyinstaller --onefile --name zit run_zit.py
mv ./dist/zit ~/.local/bin
```
Also to get zit-fm
``` bash
pyinstaller --onefile --name zit-fm run_zit_fm.py
mv ./dist/zit-fm ~/.local/bin

```
And zit-git
``` bash
pyinstaller --onefile --name zit-git run_zit_git.py
mv ./dist/zit-git ~/.local/bin

```

# TODO
## General
- [ ] implement server version
- [ ] testing
- [x] import timestamps from git
- [x] import timestamps from system

## zit-fm
- [ ] add options to change and fix old entries
- [ ] improve printing and verbosity
## zit-git
- [x] installer
- [ ] better printing
- [ ] figure out which features are needed
- [ ] integrate with subtasks
- [ ] handling multiple days

## zit-sys
- [x] installer
- [ ] check if we get all sys events
- [ ] add more events
- [ ] improve cli
- [ ] handling multiple days





# Timetracking
---
- (estimate) until v0.2.1: ~5h

## 18.04.25
```
┌────────────────────────────────────────────────────────────────────┐
│ Events and Subtasks:                                               │
└────────────────────────────────────────────────────────────────────┘
zit ────────────────────────────────────────────── 16:01:00 | 02:39:10
  ├─ zit-fm                                        16:01:00 | 00:19:51
  ├─ attach                                        16:20:52 | 00:14:53
  ├─ subtaskintegration                            16:35:45 | 00:21:36
  └─────────────────────────────────────────────── 16:57:21 ──────────
zit ────────────────────────────────────────────── 19:21:22 | 02:39:10
  ├─ verify_no_default                             19:21:22 | 00:07:53
  ├─ subdefault                                    19:29:16 | 00:04:53
  ├─ update_pydantic                               19:34:10 | 00:40:49
  │   └─ refactored the pydantic model to seperate projects and...
  ├─ notes                                         20:15:00 | 00:37:36
  │   └─ improved printing and fixed bugs...
  └─ pretty_print                                  20:52:36 | 00:11:35
┌────────────────────────────────────────────────────────────────────┐
│ Total time:                                                        │
└────────────────────────────────────────────────────────────────────┘
Total:                                                        02:39:10
Excluded:                                                     02:24:01
```

## 19.04.25
```
┌────────────────────────────────────────────────────────────────────┐
│ Events and Subtasks:                                               │
└────────────────────────────────────────────────────────────────────┘
zit ────────────────────────────────────────────── 13:50:00 | 00:48:30
  ├─ install_script                                13:50:00 | 00:13:37
  ├─ fixing_attach                                 14:03:37 | 00:34:52
  └─────────────────────────────────────────────── 14:38:30 ──────────
┌────────────────────────────────────────────────────────────────────┐
│ Total time:                                                        │
└────────────────────────────────────────────────────────────────────┘
Total:                                                        00:48:30
Excluded:                                                     00:00:00
```
