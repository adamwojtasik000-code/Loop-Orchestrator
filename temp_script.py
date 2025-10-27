#!/usr/bin/env python3
import time
import os
try:
    import fcntl
except ImportError:
    import msvcrt

class FileLocker:
    def __init__(self):
        self._has_fcntl = 'fcntl' in globals()

    def lock_file(self, file_handle, exclusive=True):
        if self._has_fcntl:
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        else:
            import msvcrt
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK, 1)

    def unlock_file(self, file_handle):
        if self._has_fcntl:
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        else:
            import msvcrt
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)

# Current timestamp in ISO format
current_timestamp = "2025-10-27T21:45:16.736Z"

# Task details
task_id = "fix_issues_2025_10_27"
mode = "orchestrator"
task_description = "continue fixing current issues or identify new ones for improvement"

# Format: task_id\tstart_timestamp\t\t\t\ttask\tstarted
entry = f"{task_id}\t{current_timestamp}\t\t\t\t\t{task_description}\tstarted\n"

file_path = "task_timing.tsv"
locker = FileLocker()

with open(file_path, 'a') as f:
    locker.lock_file(f)
    f.write(entry)
    locker.unlock_file(f)

print("Start time recorded successfully")