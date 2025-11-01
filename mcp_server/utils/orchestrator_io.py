"""
Orchestrator I/O Integration

Direct integration with Loop-Orchestrator system files including schedules.json, 
task_timing.tsv, persistent-memory.md, and other orchestrator components.
"""

import json
import csv
import re
import os
import time
from typing import Dict, List, Any, Optional, Union, IO
from datetime import datetime
from pathlib import Path
import logging

from ..models import (
    ScheduleData, SchedulesContainer, TaskTimingData, TaskTimingContainer,
    PersistentMemoryEntry, PersistentMemorySection, PriorityType
)
from ..config.settings import get_server_config
from ..utils.helpers import safe_json_load, safe_json_save, format_timestamp


logger = logging.getLogger(__name__)


class OrchestratorIO:
    """
    Orchestrator I/O manager for handling system file operations.
    
    Provides centralized access to all Loop-Orchestrator system files with
    proper validation, error handling, and data consistency management.
    """
    
    def __init__(self, config=None):
        """
        Initialize OrchestratorIO with configuration.
        
        Args:
            config: ServerConfig instance (uses global config if None)
        """
        self.config = config or get_server_config()
        self.workspace_path = self.config.workspace_path
        
        # File paths
        self.schedules_path = self.config.get_schedules_path()
        self.task_timing_path = self.config.get_task_timing_path()
        self.persistent_memory_path = self.config.get_persistent_memory_path()
        self.todo_path = self.config.get_todo_path()
        self.modes_path = self.config.get_modes_path()
        
        # File state tracking
        self._file_states = {}
        self._last_sync_times = {}
    
    def get_file_state(self, file_path: Path) -> Dict[str, Any]:
        """
        Get current state of a file including timestamps and checksums.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary containing file state information
        """
        if not file_path.exists():
            return {"exists": False, "last_modified": None, "size": 0, "checksum": None}
        
        stat = file_path.stat()
        return {
            "exists": True,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size": stat.st_size,
            "checksum": self._calculate_file_checksum(file_path)
        }
    
    def _calculate_file_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate checksum for file content."""
        try:
            import hashlib
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def is_file_changed(self, file_path: Path) -> bool:
        """
        Check if file has changed since last sync.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file has changed, False otherwise
        """
        current_state = self.get_file_state(file_path)
        file_key = str(file_path)
        
        if file_key not in self._file_states:
            return True  # First time seeing this file
        
        previous_state = self._file_states[file_key]
        
        return (
            current_state["last_modified"] != previous_state["last_modified"] or
            current_state["size"] != previous_state["size"] or
            current_state["checksum"] != previous_state["checksum"]
        )
    
    def update_file_state(self, file_path: Path) -> None:
        """Update tracked state for a file."""
        self._file_states[str(file_path)] = self.get_file_state(file_path)


# Global orchestrator I/O instance
_orchestrator_io: Optional[OrchestratorIO] = None


def get_orchestrator_io() -> OrchestratorIO:
    """Get global orchestrator I/O instance."""
    global _orchestrator_io
    if _orchestrator_io is None:
        _orchestrator_io = OrchestratorIO()
    return _orchestrator_io


# Direct functions for common operations

def load_schedules() -> Optional[SchedulesContainer]:
    """
    Load schedules from .roo/schedules.json.
    
    Returns:
        SchedulesContainer instance or None if failed
    """
    io = get_orchestrator_io()
    
    try:
        if not io.schedules_path.exists():
            logger.warning(f"Schedules file not found: {io.schedules_path}")
            return SchedulesContainer(schedules=[])
        
        with open(io.schedules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schedules_container = SchedulesContainer.from_dict(data)
        io.update_file_state(io.schedules_path)
        
        logger.info(f"Loaded {len(schedules_container.schedules)} schedules")
        return schedules_container
        
    except Exception as e:
        logger.error(f"Failed to load schedules: {e}")
        return None


def save_schedules(schedules_container: SchedulesContainer) -> bool:
    """
    Save schedules to .roo/schedules.json.
    
    Args:
        schedules_container: SchedulesContainer to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    io = get_orchestrator_io()
    
    try:
        # Create backup
        if io.schedules_path.exists():
            backup_path = io.config.get_backups_dir() / f"schedules_backup_{int(time.time())}.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(io.schedules_path, backup_path)
        
        # Save schedules
        success = safe_json_save(
            schedules_container.dict(),
            io.schedules_path,
            indent=2
        )
        
        if success:
            io.update_file_state(io.schedules_path)
            logger.info(f"Saved {len(schedules_container.schedules)} schedules")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to save schedules: {e}")
        return False


def load_task_timing() -> TaskTimingContainer:
    """
    Load task timing data from task_timing.tsv.
    
    Returns:
        TaskTimingContainer instance
    """
    io = get_orchestrator_io()
    
    try:
        if not io.task_timing_path.exists():
            logger.info("Task timing file not found, creating new container")
            return TaskTimingContainer()
        
        with open(io.task_timing_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        timing_container = TaskTimingContainer.from_tsv(content)
        io.update_file_state(io.task_timing_path)
        
        logger.info(f"Loaded {len(timing_container.entries)} task timing entries")
        return timing_container
        
    except Exception as e:
        logger.error(f"Failed to load task timing: {e}")
        return TaskTimingContainer()


def save_task_timing(timing_container: TaskTimingContainer) -> bool:
    """
    Save task timing data to task_timing.tsv.
    
    Args:
        timing_container: TaskTimingContainer to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    io = get_orchestrator_io()
    
    try:
        # Create backup
        if io.task_timing_path.exists():
            backup_path = io.config.get_backups_dir() / f"task_timing_backup_{int(time.time())}.tsv"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(io.task_timing_path, backup_path)
        
        # Save timing data
        tsv_content = timing_container.to_tsv()
        io.task_timing_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(io.task_timing_path, 'w', encoding='utf-8') as f:
            f.write(tsv_content)
        
        io.update_file_state(io.task_timing_path)
        logger.info(f"Saved {len(timing_container.entries)} task timing entries")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save task timing: {e}")
        return False


def load_persistent_memory() -> Dict[str, str]:
    """
    Load persistent memory content from persistent-memory.md.
    
    Returns:
        Dictionary mapping section names to content
    """
    io = get_orchestrator_io()
    
    try:
        if not io.persistent_memory_path.exists():
            logger.info("Persistent memory file not found, creating new structure")
            return _create_default_persistent_memory()
        
        with open(io.persistent_memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse sections
        sections = _parse_persistent_memory_sections(content)
        io.update_file_state(io.persistent_memory_path)
        
        logger.info(f"Loaded persistent memory with {len(sections)} sections")
        return sections
        
    except Exception as e:
        logger.error(f"Failed to load persistent memory: {e}")
        return _create_default_persistent_memory()


def save_persistent_memory(sections: Dict[str, str]) -> bool:
    """
    Save persistent memory content to persistent-memory.md.
    
    Args:
        sections: Dictionary mapping section names to content
        
    Returns:
        True if saved successfully, False otherwise
    """
    io = get_orchestrator_io()
    
    try:
        # Create backup
        if io.persistent_memory_path.exists():
            backup_path = io.config.get_backups_dir() / f"persistent_memory_backup_{int(time.time())}.md"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(io.persistent_memory_path, backup_path)
        
        # Build content
        content_parts = ["# Persistent Memory\\n"]
        
        # Ensure required sections exist in order
        required_sections = [
            PersistentMemorySection.IMPLEMENTATION_PATTERNS.value,
            PersistentMemorySection.DEVELOPMENT_COMMANDS.value,
            PersistentMemorySection.SYSTEM_UPDATES.value
        ]
        
        for section_name in required_sections:
            if section_name in sections:
                content_parts.append(f"# {section_name}\\n")
                content_parts.append(sections[section_name])
                content_parts.append("\\n")
        
        # Add any additional sections
        for section_name, section_content in sections.items():
            if section_name not in required_sections:
                content_parts.append(f"# {section_name}\\n")
                content_parts.append(section_content)
                content_parts.append("\\n")
        
        # Save content
        content = "".join(content_parts)
        io.persistent_memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(io.persistent_memory_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        io.update_file_state(io.persistent_memory_path)
        logger.info(f"Saved persistent memory with {len(sections)} sections")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save persistent memory: {e}")
        return False


def load_todo_status() -> Dict[str, Any]:
    """
    Load TODO status from TODO.md.
    
    Returns:
        Dictionary containing TODO information
    """
    io = get_orchestrator_io()
    
    try:
        if not io.todo_path.exists():
            logger.info("TODO file not found")
            return {"todos": [], "total": 0, "completed": 0, "pending": 0}
        
        with open(io.todo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse TODO items
        todo_pattern = r'-\s*\[([ xX])\]\s*(.+)'
        todos = []
        
        lines = content.split('\\n')
        for line in lines:
            if line.startswith('- ['):
                match = re.match(todo_pattern, line)
                if match:
                    completed = match.group(1).lower() == 'x'
                    todo_text = match.group(2).strip()
                    todos.append({"text": todo_text, "completed": completed})
        
        completed_count = sum(1 for todo in todos if todo["completed"])
        pending_count = len(todos) - completed_count
        
        io.update_file_state(io.todo_path)
        
        logger.info(f"Loaded TODO with {len(todos)} items ({completed_count} completed)")
        
        return {
            "todos": todos,
            "total": len(todos),
            "completed": completed_count,
            "pending": pending_count
        }
        
    except Exception as e:
        logger.error(f"Failed to load TODO status: {e}")
        return {"todos": [], "total": 0, "completed": 0, "pending": 0}


def schedule_task_execution(
    task_instructions: str,
    mode: str,
    schedule_config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Schedule a task for execution via schedules.json.
    
    Args:
        task_instructions: Instructions for the task
        mode: Mode to execute the task
        schedule_config: Additional schedule configuration
        
    Returns:
        Schedule ID if created successfully, None otherwise
    """
    schedules_container = load_schedules()
    if schedules_container is None:
        return None
    
    try:
        # Generate schedule ID
        schedule_id = str(int(time.time() * 1000))
        
        # Create schedule data
        schedule_data = {
            "id": schedule_id,
            "name": f"Scheduled Task {schedule_id}",
            "mode": mode,
            "task_instructions": task_instructions,
            "schedule_type": "manual",
            "active": True,
            "created_at": format_timestamp(),
            "updated_at": format_timestamp()
        }
        
        # Add schedule configuration if provided
        if schedule_config:
            schedule_data.update(schedule_config)
        
        # Create and add schedule
        new_schedule = ScheduleData(**schedule_data)
        schedules_container.schedules.append(new_schedule)
        
        # Save schedules
        if save_schedules(schedules_container):
            logger.info(f"Scheduled task with ID: {schedule_id}")
            return schedule_id
        else:
            return None
        
    except Exception as e:
        logger.error(f"Failed to schedule task: {e}")
        return None


def get_active_schedules() -> List[ScheduleData]:
    """
    Get all active schedules.
    
    Returns:
        List of active ScheduleData instances
    """
    schedules_container = load_schedules()
    if schedules_container is None:
        return []
    
    return [schedule for schedule in schedules_container.schedules if schedule.active]


def get_next_execution_schedules() -> List[ScheduleData]:
    """
    Get schedules that should be executed next (based on timing).
    
    Returns:
        List of schedules ready for execution
    """
    active_schedules = get_active_schedules()
    current_time = datetime.utcnow()
    
    ready_schedules = []
    
    for schedule in active_schedules:
        if schedule.schedule_type == "manual":
            continue
        
        # Check if schedule has next execution time
        if schedule.next_execution_time:
            try:
                next_exec_time = datetime.fromisoformat(schedule.next_execution_time.replace("Z", "+00:00"))
                if next_exec_time <= current_time:
                    ready_schedules.append(schedule)
            except (ValueError, TypeError):
                continue
        
        # For time-based schedules without next_execution_time
        elif schedule.schedule_type == "time" and schedule.time_interval:
            # Calculate next execution time
            if not schedule.last_execution_time:
                ready_schedules.append(schedule)  # Never executed, ready to run
            else:
                try:
                    last_exec = datetime.fromisoformat(schedule.last_execution_time.replace("Z", "+00:00"))
                    interval_seconds = schedule.time_interval * _get_time_unit_seconds(schedule.time_unit)
                    next_exec = last_exec + timedelta(seconds=interval_seconds)
                    
                    if next_exec <= current_time:
                        ready_schedules.append(schedule)
                except (ValueError, TypeError):
                    continue
    
    return ready_schedules


def update_schedule_execution(schedule_id: str, execution_status: str = "completed") -> bool:
    """
    Update schedule after execution.
    
    Args:
        schedule_id: ID of executed schedule
        execution_status: Status of execution ("completed", "failed", "skipped")
        
    Returns:
        True if updated successfully, False otherwise
    """
    schedules_container = load_schedules()
    if schedules_container is None:
        return False
    
    try:
        # Find and update schedule
        for schedule in schedules_container.schedules:
            if schedule.id == schedule_id:
                schedule.last_execution_time = format_timestamp()
                schedule.updated_at = format_timestamp()
                
                # Calculate next execution time for time-based schedules
                if schedule.schedule_type == "time" and schedule.time_interval:
                    current_time = datetime.utcnow()
                    interval_seconds = schedule.time_interval * _get_time_unit_seconds(schedule.time_unit)
                    next_exec = current_time + timedelta(seconds=interval_seconds)
                    schedule.next_execution_time = next_exec.isoformat() + "Z"
                
                break
        
        return save_schedules(schedules_container)
        
    except Exception as e:
        logger.error(f"Failed to update schedule execution: {e}")
        return False


def add_time_tracking_entry(
    task_description: str,
    mode: str,
    task_id: Optional[str] = None,
    priority: PriorityType = PriorityType.NORMAL,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    result: str = "started"
) -> bool:
    """
    Add a time tracking entry.
    
    Args:
        task_description: Description of the task
        mode: Mode during which task is performed
        task_id: Unique task ID (generated if None)
        priority: Priority level
        start_time: Start timestamp
        end_time: End timestamp
        result: Result status
        
    Returns:
        True if added successfully, False otherwise
    """
    if task_id is None:
        task_id = str(int(time.time() * 1000))
    
    if start_time is None:
        start_time = format_timestamp()
    
    # Create timing entry
    timing_data = {
        "timestamp": start_time,
        "mode": mode,
        "task_id": task_id,
        "start_time": start_time,
        "end_time": end_time,
        "task": task_description,
        "result": result,
        "priority": priority.value
    }
    
    # Calculate duration if end_time provided
    if end_time:
        from ..utils.helpers import calculate_duration
        timing_data["duration"] = calculate_duration(start_time, end_time)
    
    try:
        # Load existing timing data
        timing_container = load_task_timing()
        
        # Add new entry
        new_entry = TaskTimingData(**timing_data)
        timing_container.entries.append(new_entry)
        
        # Save updated timing data
        return save_task_timing(timing_container)
        
    except Exception as e:
        logger.error(f"Failed to add time tracking entry: {e}")
        return False


def get_time_tracking_summary(
    mode: Optional[str] = None,
    priority: Optional[PriorityType] = None,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Get time tracking summary for recent period.
    
    Args:
        mode: Filter by mode (optional)
        priority: Filter by priority (optional)
        hours: Number of hours to look back
        
    Returns:
        Dictionary containing timing summary
    """
    timing_container = load_task_timing()
    
    try:
        # Filter entries
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=hours)
        
        filtered_entries = []
        for entry in timing_container.entries:
            try:
                entry_time = datetime.fromisoformat(entry.start_time.replace("Z", "+00:00"))
                if entry_time >= cutoff_time:
                    
                    # Apply filters
                    if mode and entry.mode != mode:
                        continue
                    if priority and entry.priority != priority:
                        continue
                    
                    filtered_entries.append(entry)
            except (ValueError, TypeError):
                continue
        
        # Calculate summary
        total_duration = sum(e.duration or 0 for e in filtered_entries)
        completed_entries = [e for e in filtered_entries if e.result == "completed"]
        total_tasks = len(completed_entries)
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        # Group by mode
        mode_summary = {}
        for entry in filtered_entries:
            mode_name = entry.mode or "unknown"
            if mode_name not in mode_summary:
                mode_summary[mode_name] = {"count": 0, "total_duration": 0}
            mode_summary[mode_name]["count"] += 1
            if entry.duration:
                mode_summary[mode_name]["total_duration"] += entry.duration
        
        return {
            "period_hours": hours,
            "total_entries": len(filtered_entries),
            "total_duration_seconds": total_duration,
            "total_tasks": total_tasks,
            "average_duration_seconds": avg_duration,
            "mode_summary": mode_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get time tracking summary: {e}")
        return {}


# Helper functions

def _create_default_persistent_memory() -> Dict[str, str]:
    """Create default persistent memory structure."""
    return {
        PersistentMemorySection.IMPLEMENTATION_PATTERNS.value: "",
        PersistentMemorySection.DEVELOPMENT_COMMANDS.value: "",
        PersistentMemorySection.SYSTEM_UPDATES.value: ""
    }


def _parse_persistent_memory_sections(content: str) -> Dict[str, str]:
    """Parse persistent memory content into sections."""
    sections = {}
    current_section = None
    current_content = []
    
    lines = content.split('\\n')
    for line in lines:
        if line.startswith('# '):
            # Save previous section
            if current_section is not None:
                sections[current_section] = '\\n'.join(current_content)
            
            # Start new section
            current_section = line[2:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_section is not None:
        sections[current_section] = '\\n'.join(current_content)
    
    return sections


def _get_time_unit_seconds(time_unit: str) -> int:
    """Convert time unit to seconds."""
    multipliers = {
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }
    return multipliers.get(time_unit, 60)  # Default to minutes


def add_persistent_memory_entry(
    section: PersistentMemorySection,
    content: str,
    category: Optional[str] = None,
    format_entry: bool = True
) -> bool:
    """
    Add entry to persistent memory with proper formatting.
    
    Args:
        section: Section to add entry to
        content: Content of the entry
        category: Category for the entry
        format_entry: Whether to format as structured entry
        
    Returns:
        True if added successfully, False otherwise
    """
    try:
        # Load current content
        sections = load_persistent_memory()
        
        # Format new entry
        timestamp = format_timestamp()
        if format_entry:
            formatted_entry = f"\\n## [{timestamp}] [mcp-server] - [{category or 'general'}]\\n"
            formatted_entry += f"- Finding: {content}\\n"
        else:
            formatted_entry = f"\\n## [{timestamp}] [mcp-server] - [{category or 'general'}]\\n{content}\\n"
        
        # Append to section
        section_name = section.value
        if section_name in sections:
            sections[section_name] += formatted_entry
        else:
            sections[section_name] = formatted_entry
        
        # Check line limit
        total_content = "\\n".join([f"# {name}\\n{content}" for name, content in sections.items()])
        line_count = len(total_content.split('\\n'))
        
        if line_count > get_server_config().persistent_memory_max_lines:
            logger.warning(f"Persistent memory would exceed line limit ({line_count} > {get_server_config().persistent_memory_max_lines})")
            # Could implement cleanup logic here
        
        return save_persistent_memory(sections)
        
    except Exception as e:
        logger.error(f"Failed to add persistent memory entry: {e}")
        return False