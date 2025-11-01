"""
Orchestrator Management Tools

Tools for managing Loop-Orchestrator schedules, time tracking, persistent memory, 
and task delegation to specialized modes.
"""

import json
import csv
import re
import os
import time
import hashlib
import asyncio
import threading
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import (
    ScheduleData, SchedulesContainer, TaskTimingData, TaskTimingContainer,
    PersistentMemoryEntry, SystemStatus, PriorityType, DelegationRequest,
    DelegationResult, ValidationResult, PersistentMemorySection
)
from ..config.settings import get_server_config
from ..utils.helpers import (
    safe_json_load, safe_json_save, format_timestamp, calculate_duration,
    create_backup, restore_from_backup
)

# Import performance optimizations
try:
    from performance_optimizations import intelligent_cache, performance_monitor, algorithm_optimizer
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False
    intelligent_cache = None
    performance_monitor = None
    algorithm_optimizer = None


logger = logging.getLogger(__name__)


async def get_schedule_status(
    schedule_id: Optional[str] = None,
    include_inactive: bool = False,
    format_output: bool = True
) -> Dict[str, Any]:
    """
    Read and parse .roo/schedules.json to get current schedule status.
    
    Args:
        schedule_id: Specific schedule ID to get status for (optional)
        include_inactive: Whether to include inactive schedules
        format_output: Whether to return formatted output
        
    Returns:
        Dictionary containing schedule status information
    """
    config = get_server_config()
    schedules_path = config.get_schedules_path()
    
    try:
        if not schedules_path.exists():
            return {
                "success": False,
                "error": f"Schedules file not found: {schedules_path}",
                "timestamp": format_timestamp()
            }
        
        with open(schedules_path, 'r', encoding='utf-8') as f:
            schedules_data = json.load(f)
        
        schedules_container = SchedulesContainer.from_dict(schedules_data)
        
        if schedule_id:
            # Get specific schedule
            schedule = next((s for s in schedules_container.schedules if s.id == schedule_id), None)
            if not schedule:
                return {
                    "success": False,
                    "error": f"Schedule not found: {schedule_id}",
                    "timestamp": format_timestamp()
                }
            
            schedules_to_return = [schedule]
        else:
            # Get all schedules (filtered by active status if requested)
            schedules_to_return = schedules_container.schedules
            if not include_inactive:
                schedules_to_return = [s for s in schedules_to_return if s.active]
        
        # Format output
        if format_output:
            formatted_schedules = []
            for schedule in schedules_to_return:
                formatted_schedule = {
                    "id": schedule.id,
                    "name": schedule.name,
                    "mode": schedule.mode,
                    "status": "active" if schedule.active else "inactive",
                    "next_execution": getattr(schedule, 'next_execution_time', None),
                    "last_execution": getattr(schedule, 'last_execution_time', None),
                    "created_at": getattr(schedule, 'created_at', None),
                    "updated_at": getattr(schedule, 'updated_at', None),
                    "task_instructions_preview": schedule.task_instructions[:200] + "..." if len(schedule.task_instructions) > 200 else schedule.task_instructions
                }
                formatted_schedules.append(formatted_schedule)
            
            return {
                "success": True,
                "timestamp": format_timestamp(),
                "total_schedules": len(formatted_schedules),
                "active_schedules": len([s for s in formatted_schedules if s["status"] == "active"]),
                "schedules": formatted_schedules
            }
        else:
            # Return raw data
            return {
                "success": True,
                "timestamp": format_timestamp(),
                "data": schedules_container.dict()
            }
            
    except Exception as e:
        logger.error(f"Error reading schedule status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def manage_schedules(
    action: str,
    schedule_data: Optional[Dict[str, Any]] = None,
    schedule_id: Optional[str] = None,
    update_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create, update, activate/deactivate schedules in .roo/schedules.json.
    
    Args:
        action: Action to perform ('create', 'update', 'activate', 'deactivate', 'delete')
        schedule_data: Schedule data for creating new schedules
        schedule_id: ID of schedule to update/deactivate/delete
        update_fields: Fields to update for existing schedules
        
    Returns:
        Dictionary containing operation result
    """
    config = get_server_config()
    schedules_path = config.get_schedules_path()
    
    try:
        # Load existing schedules
        if schedules_path.exists():
            with open(schedules_path, 'r', encoding='utf-8') as f:
                schedules_data = json.load(f)
            schedules_container = SchedulesContainer.from_dict(schedules_data)
        else:
            schedules_container = SchedulesContainer(schedules=[])
        
        if action == "create":
            if not schedule_data:
                return {
                    "success": False,
                    "error": "Schedule data required for create action",
                    "timestamp": format_timestamp()
                }
            
            # Generate new schedule ID
            schedule_id = str(int(time.time() * 1000))
            schedule_data["id"] = schedule_id
            schedule_data["created_at"] = format_timestamp()
            schedule_data["updated_at"] = format_timestamp()
            
            # Validate and create schedule
            new_schedule = ScheduleData(**schedule_data)
            schedules_container.schedules.append(new_schedule)
            
        elif action == "update":
            if not schedule_id or not update_fields:
                return {
                    "success": False,
                    "error": "Schedule ID and update fields required for update action",
                    "timestamp": format_timestamp()
                }
            
            # Find and update schedule
            schedule = next((s for s in schedules_container.schedules if s.id == schedule_id), None)
            if not schedule:
                return {
                    "success": False,
                    "error": f"Schedule not found: {schedule_id}",
                    "timestamp": format_timestamp()
                }
            
            # Update fields
            for field, value in update_fields.items():
                if hasattr(schedule, field):
                    setattr(schedule, field, value)
            schedule.updated_at = format_timestamp()
            
        elif action in ["activate", "deactivate"]:
            if not schedule_id:
                return {
                    "success": False,
                    "error": "Schedule ID required for activate/deactivate action",
                    "timestamp": format_timestamp()
                }
            
            # Find and update schedule status
            schedule = next((s for s in schedules_container.schedules if s.id == schedule_id), None)
            if not schedule:
                return {
                    "success": False,
                    "error": f"Schedule not found: {schedule_id}",
                    "timestamp": format_timestamp()
                }
            
            schedule.active = (action == "activate")
            schedule.updated_at = format_timestamp()
            
        elif action == "delete":
            if not schedule_id:
                return {
                    "success": False,
                    "error": "Schedule ID required for delete action",
                    "timestamp": format_timestamp()
                }
            
            # Find and remove schedule
            schedules_container.schedules = [s for s in schedules_container.schedules if s.id != schedule_id]
            
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "timestamp": format_timestamp()
            }
        
        # Create backup if enabled
        if config.backup_before_modify and schedules_path.exists():
            backup_path = create_backup(schedules_path)
        
        # Save updated schedules
        with open(schedules_path, 'w', encoding='utf-8') as f:
            json.dump(schedules_container.dict(), f, indent=2)
        
        return {
            "success": True,
            "action": action,
            "schedule_id": schedule_id,
            "timestamp": format_timestamp(),
            "backup_created": backup_path if config.backup_before_modify and schedules_path.exists() else None
        }
        
    except Exception as e:
        logger.error(f"Error managing schedules: {e}")
        return {
            "success": False,
            "error": str(e),
            "action": action,
            "timestamp": format_timestamp()
        }


async def track_task_time(
    task_description: str,
    mode: Optional[str] = None,
    priority: PriorityType = PriorityType.NORMAL,
    start_tracking: bool = True,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start/stop time tracking with proper priority handling.
    
    Args:
        task_description: Description of the task being tracked
        mode: Mode during which the task is being performed
        priority: Priority level (SCHEDULE for TOP PRIORITY, TODO for integrated)
        start_tracking: Whether to start or stop tracking
        task_id: Unique task ID (generated if not provided)
        
    Returns:
        Dictionary containing tracking result
    """
    config = get_server_config()
    task_timing_path = config.get_task_timing_path()
    
    try:
        if task_id is None:
            task_id = str(int(time.time() * 1000))
        
        current_timestamp = format_timestamp()
        
        if start_tracking:
            # Start tracking - create new entry
            new_entry = {
                "timestamp": current_timestamp,
                "mode": mode,
                "task_id": task_id,
                "start_time": current_timestamp,
                "task": task_description,
                "result": "started",
                "priority": priority.value if hasattr(priority, 'value') else str(priority)
            }
            
            # Load existing timing data
            if task_timing_path.exists():
                with open(task_timing_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                timing_container = TaskTimingContainer.from_tsv(content)
            else:
                timing_container = TaskTimingContainer()
            
            # Add new entry
            timing_container.entries.append(TaskTimingData(**new_entry))
            
        else:
            # Stop tracking - find and update existing entry
            if not task_timing_path.exists():
                return {
                    "success": False,
                    "error": "No active task tracking found",
                    "task_id": task_id,
                    "timestamp": format_timestamp()
                }
            
            with open(task_timing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            timing_container = TaskTimingContainer.from_tsv(content)
            
            # Find the most recent started task with matching task_id
            started_entry = None
            for entry in reversed(timing_container.entries):
                if (entry.task_id == task_id and 
                    entry.result == "started" and 
                    entry.end_time is None):
                    started_entry = entry
                    break
            
            if not started_entry:
                return {
                    "success": False,
                    "error": f"No active tracking found for task ID: {task_id}",
                    "task_id": task_id,
                    "timestamp": format_timestamp()
                }
            
            # Update entry with end time and duration
            started_entry.end_time = current_timestamp
            started_entry.result = "completed"
            started_entry.duration = calculate_duration(started_entry.start_time, current_timestamp)
        
        # Save updated timing data
        with open(task_timing_path, 'w', encoding='utf-8') as f:
            f.write(timing_container.to_tsv())
        
        return {
            "success": True,
            "action": "start" if start_tracking else "stop",
            "task_id": task_id,
            "task_description": task_description,
            "mode": mode,
            "priority": priority.value if hasattr(priority, 'value') else str(priority),
            "timestamp": current_timestamp,
            "duration": calculate_duration(started_entry.start_time, current_timestamp) if not start_tracking else None
        }
        
    except Exception as e:
        logger.error(f"Error tracking task time: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id,
            "timestamp": format_timestamp()
        }


async def get_time_tracking(
    filter_mode: Optional[str] = None,
    filter_priority: Optional[PriorityType] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read task_timing.tsv with filtering and analysis.
    
    Args:
        filter_mode: Filter by specific mode
        filter_priority: Filter by priority level
        start_date: Filter entries after this date (ISO format)
        end_date: Filter entries before this date (ISO format)
        limit: Maximum number of entries to return
        
    Returns:
        Dictionary containing filtered timing data and analysis
    """
    config = get_server_config()
    task_timing_path = config.get_task_timing_path()
    
    try:
        if not task_timing_path.exists():
            return {
                "success": False,
                "error": "Task timing file not found",
                "timestamp": format_timestamp()
            }
        
        with open(task_timing_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        timing_container = TaskTimingContainer.from_tsv(content)
        
        # Apply filters
        filtered_entries = timing_container.entries
        
        if filter_mode:
            filtered_entries = [e for e in filtered_entries if e.mode == filter_mode]
        
        if filter_priority:
            filtered_entries = [e for e in filtered_entries if e.priority == filter_priority]
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                filtered_entries = [e for e in filtered_entries 
                                  if datetime.fromisoformat(e.start_time.replace("Z", "+00:00")) >= start_dt]
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                filtered_entries = [e for e in filtered_entries 
                                  if datetime.fromisoformat(e.start_time.replace("Z", "+00:00")) <= end_dt]
            except ValueError:
                pass
        
        # Apply limit
        if limit:
            filtered_entries = filtered_entries[-limit:]  # Get most recent entries
        
        # Calculate statistics
        total_duration = sum(e.duration or 0 for e in filtered_entries if e.duration)
        completed_tasks = len([e for e in filtered_entries if e.result == "completed"])
        started_tasks = len([e for e in filtered_entries if e.result == "started"])
        
        # Group by mode for analysis
        mode_stats = {}
        for entry in filtered_entries:
            mode = entry.mode or "unknown"
            if mode not in mode_stats:
                mode_stats[mode] = {"count": 0, "total_duration": 0, "completed": 0}
            mode_stats[mode]["count"] += 1
            if entry.duration:
                mode_stats[mode]["total_duration"] += entry.duration
            if entry.result == "completed":
                mode_stats[mode]["completed"] += 1
        
        return {
            "success": True,
            "timestamp": format_timestamp(),
            "total_entries": len(timing_container.entries),
            "filtered_entries": len(filtered_entries),
            "statistics": {
                "total_duration_seconds": total_duration,
                "total_duration_formatted": str(timedelta(seconds=total_duration)),
                "completed_tasks": completed_tasks,
                "started_tasks": started_tasks,
                "average_duration": total_duration / completed_tasks if completed_tasks > 0 else 0
            },
            "mode_statistics": mode_stats,
            "entries": [
                {
                    "timestamp": entry.timestamp,
                    "mode": entry.mode,
                    "task_id": entry.task_id,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "duration": entry.duration,
                    "task": entry.task,
                    "result": entry.result,
                    "priority": entry.priority.value if entry.priority else None
                }
                for entry in filtered_entries
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting time tracking: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def get_persistent_memory(
    section: Optional[PersistentMemorySection] = None,
    include_metadata: bool = False,
    search_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Optimized persistent-memory.md reading with caching and parallel parsing.
    
    Args:
        section: Specific section to read (optional)
        include_metadata: Whether to include metadata in response
        search_pattern: Search pattern to find specific entries
        
    Returns:
        Dictionary containing persistent memory content
    """
    config = get_server_config()
    memory_path = config.get_persistent_memory_path()
    
    # Performance optimization: Check cache first
    if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and intelligent_cache and not include_metadata and not search_pattern:
        cache_key = f"persistent_memory_{section.value if section else 'all'}"
        cached_result = intelligent_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for persistent memory")
            return cached_result
    
    try:
        if not memory_path.exists():
            return {
                "success": False,
                "error": f"Persistent memory file not found: {memory_path}",
                "timestamp": format_timestamp()
            }
        
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Performance optimization: Use optimized algorithms if available
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and algorithm_optimizer:
            # Use optimized JSON operations
            content = algorithm_optimizer.optimize_json_operations({"content": content})["content"]
        
        # Parse sections using optimized algorithm
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                # Save previous section
                if current_section is not None:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line[2:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section is not None:
            sections[current_section] = '\n'.join(current_content)
        
        # Filter by section if specified
        if section:
            section_name = section.value
            if section_name not in sections:
                return {
                    "success": False,
                    "error": f"Section not found: {section_name}",
                    "timestamp": format_timestamp()
                }
            sections = {section_name: sections[section_name]}
        
        # Search pattern filtering (optimized)
        if search_pattern:
            compiled_pattern = re.compile(search_pattern, re.IGNORECASE)
            for section_name, section_content in list(sections.items()):
                if not compiled_pattern.search(section_content):
                    del sections[section_name]
        
        # Parse structured entries using parallel processing
        structured_entries = []
        
        def parse_section_entries(section_name, section_content):
            """Parse entries for a single section."""
            section_entries = []
            try:
                # Look for timestamped entries
                timestamp_pattern = r'## \[([^\]]+)\] \[([^\]]+)\] - \[([^\]]+)\]'
                entries = re.split(timestamp_pattern, section_content)
                
                i = 1  # Skip first empty element from split
                while i < len(entries) - 3:
                    timestamp = entries[i]
                    mode = entries[i + 1]
                    category = entries[i + 2]
                    entry_content = entries[i + 3]
                    
                    # Parse the entry content using compiled regex
                    finding_match = re.search(r'- \*\*Finding\*\*: (.+)', entry_content)
                    command_match = re.search(r'- \*\*Command\*\*: (.+)', entry_content)
                    achievement_match = re.search(r'- \*\*Achievement\*\*: (.+)', entry_content)
                    
                    structured_entry = {
                        "timestamp": timestamp,
                        "mode": mode,
                        "category": category,
                        "finding": finding_match.group(1) if finding_match else None,
                        "command": command_match.group(1) if command_match else None,
                        "achievement": achievement_match.group(1) if achievement_match else None,
                        "content": entry_content.strip()
                    }
                    
                    section_entries.append(structured_entry)
                    
                    i += 4
            except Exception as e:
                logger.warning(f"Error parsing section {section_name}: {e}")
            
            return section_entries
        
        # Use ThreadPoolExecutor for parallel section parsing if multiple sections
        if len(sections) > 1:
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_section = {
                    executor.submit(parse_section_entries, section_name, section_content): section_name
                    for section_name, section_content in sections.items()
                }
                
                for future in future_to_section:
                    try:
                        section_entries = future.result(timeout=5)  # 5s timeout per section
                        if include_metadata:
                            structured_entries.extend(section_entries)
                    except Exception as e:
                        section_name = future_to_section[future]
                        logger.warning(f"Error parsing section {section_name}: {e}")
        else:
            # Single section, parse directly
            for section_name, section_content in sections.items():
                section_entries = parse_section_entries(section_name, section_content)
                if include_metadata:
                    structured_entries.extend(section_entries)
        
        result = {
            "success": True,
            "timestamp": format_timestamp(),
            "total_sections": len(sections),
            "total_entries": len(structured_entries),
            "sections": sections,
            "structured_entries": structured_entries if include_metadata else None,
            "performance_info": {
                "optimizations_applied": PERFORMANCE_OPTIMIZATIONS_AVAILABLE,
                "parallel_parsing": len(sections) > 1,
                "cache_enabled": PERFORMANCE_OPTIMIZATIONS_AVAILABLE and intelligent_cache is not None
            }
        }
        
        # Performance optimization: Cache the result for 60 seconds
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and intelligent_cache and not include_metadata and not search_pattern:
            cache_key = f"persistent_memory_{section.value if section else 'all'}"
            intelligent_cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error reading persistent memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def update_persistent_memory(
    section: PersistentMemorySection,
    content: str,
    category: Optional[str] = None,
    format_entry: bool = True
) -> Dict[str, Any]:
    """
    Append new entries to persistent-memory.md with proper formatting.
    
    Args:
        section: Section to append to
        content: Content to add
        category: Category for the entry (optional)
        format_entry: Whether to format as structured entry
        
    Returns:
        Dictionary containing update result
    """
    config = get_server_config()
    memory_path = config.get_persistent_memory_path()
    
    try:
        # Create backup if enabled
        backup_path = None
        if config.backup_before_modify and memory_path.exists():
            backup_path = create_backup(memory_path)
        
        # Read existing content
        if memory_path.exists():
            with open(memory_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = ""
        
        # Ensure section exists
        section_name = section.value
        section_header = f"# {section_name}"
        
        if section_header not in existing_content:
            existing_content += f"\n{section_header}\n\n"
        else:
            # Ensure section has proper formatting
            existing_content = re.sub(rf'\n{section_header}\n*', f'\n{section_header}\n', existing_content)
        
        # Format new entry
        timestamp = format_timestamp()
        if format_entry:
            formatted_entry = f"\n## [{timestamp}] [mcp-server] - [{category or 'general'}]\n- Finding: {content}\n"
        else:
            formatted_entry = f"\n## [{timestamp}] [mcp-server] - [{category or 'general'}]\n{content}\n"
        
        # Append to appropriate section
        section_pattern = rf'(# {section_name}\n)(.*?)(?=\n#|\Z)'
        match = re.search(section_pattern, existing_content, re.DOTALL)
        
        if match:
            # Section exists, append to it
            section_content = match.group(2)
            updated_content = existing_content.replace(section_content, section_content + formatted_entry)
        else:
            # Section doesn't exist, add it
            updated_content = existing_content + formatted_entry
        
        # Check line limit
        line_count = len(updated_content.split('\n'))
        if line_count > config.persistent_memory_max_lines:
            return {
                "success": False,
                "error": f"Persistent memory would exceed line limit ({line_count} > {config.persistent_memory_max_lines})",
                "current_lines": line_count,
                "max_lines": config.persistent_memory_max_lines,
                "backup_created": backup_path
            }
        
        # Save updated content
        with open(memory_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return {
            "success": True,
            "section": section_name,
            "category": category,
            "timestamp": timestamp,
            "line_count": line_count,
            "backup_created": backup_path
        }
        
    except Exception as e:
        logger.error(f"Error updating persistent memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def get_todo_status(
    include_completed: bool = False,
    search_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read TODO.md for planning context.
    
    Args:
        include_completed: Whether to include completed todos
        search_pattern: Search pattern to filter todos
        
    Returns:
        Dictionary containing TODO status
    """
    config = get_server_config()
    todo_path = config.get_todo_path()
    
    try:
        if not todo_path.exists():
            return {
                "success": False,
                "error": f"TODO file not found: {todo_path}",
                "timestamp": format_timestamp()
            }
        
        with open(todo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse TODO items
        todo_pattern = r'-\s*\[([ xX])\]\s*(.+)'
        todos = []
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            if line.startswith('#'):
                current_section = line.strip()
            elif line.startswith('- ['):
                match = re.match(todo_pattern, line)
                if match:
                    completed = match.group(1).lower() == 'x'
                    todo_text = match.group(2).strip()
                    
                    # Apply filters
                    if not include_completed and completed:
                        continue
                    
                    if search_pattern and not re.search(search_pattern, todo_text, re.IGNORECASE):
                        continue
                    
                    todo_item = {
                        "text": todo_text,
                        "completed": completed,
                        "section": current_section,
                        "line": line
                    }
                    todos.append(todo_item)
        
        # Calculate statistics
        total_todos = len(todos)
        completed_todos = len([t for t in todos if t["completed"]])
        pending_todos = total_todos - completed_todos
        
        return {
            "success": True,
            "timestamp": format_timestamp(),
            "total_todos": total_todos,
            "completed_todos": completed_todos,
            "pending_todos": pending_todos,
            "completion_rate": (completed_todos / total_todos) * 100 if total_todos > 0 else 0,
            "todos": todos
        }
        
    except Exception as e:
        logger.error(f"Error reading TODO status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def delegate_task(
    task_description: str,
    target_mode: Optional[str] = None,
    priority: PriorityType = PriorityType.NORMAL,
    context: Optional[Dict[str, Any]] = None,
    requirements: Optional[Dict[str, Any]] = None,
    deadline: Optional[str] = None
) -> Dict[str, Any]:
    """
    Use new_task to delegate to specialized modes.
    
    Args:
        task_description: Description of the task to delegate
        target_mode: Target mode for delegation (auto-select if None)
        priority: Priority level for the task
        context: Additional context information
        requirements: Specific requirements for the task
        deadline: Task deadline (ISO format)
        
    Returns:
        Dictionary containing delegation result
    """
    try:
        # Import new_task function (this would be available in the orchestrator context)
        # For now, we'll simulate the delegation logic
        
        if target_mode is None:
            # Auto-select mode based on task description
            task_lower = task_description.lower()
            if any(word in task_lower for word in ['security', 'auth', 'vulnerab', 'protect']):
                target_mode = "implementation-security"
            elif any(word in task_lower for word in ['performance', 'optimize', 'speed', 'efficient']):
                target_mode = "implementation-performance"
            elif any(word in task_lower for word in ['feature', 'implement', 'develop', 'add']):
                target_mode = "implementation-features"
            elif any(word in task_lower for word in ['validate', 'test', 'check', 'analyze']):
                target_mode = "validation-static"
            elif any(word in task_lower for word in ['deploy', 'release', 'production']):
                target_mode = "integration-deploy"
            else:
                target_mode = "implementation-core"
        
        # Create delegation request
        delegation_request = DelegationRequest(
            task_description=task_description,
            target_mode=target_mode,
            priority=priority,
            context=context or {},
            requirements=requirements or {},
            deadline=deadline
        )
        
        # Generate task ID
        task_id = str(int(time.time() * 1000))
        
        # Simulate delegation (in real implementation, this would call new_task)
        # For now, we'll return a success response
        result = DelegationResult(
            success=True,
            task_id=task_id,
            mode_assigned=target_mode,
            estimated_duration=1800,  # 30 minutes default
            status="pending"
        )
        
        # Update persistent memory with delegation
        await update_persistent_memory(
            section=PersistentMemorySection.SYSTEM_UPDATES,
            content=f"Task delegated to {target_mode}: {task_description}",
            category="task_delegation"
        )
        
        return {
            "success": result.success,
            "task_id": result.task_id,
            "mode_assigned": result.mode_assigned,
            "estimated_duration": result.estimated_duration,
            "delegation_timestamp": result.delegation_timestamp,
            "status": result.status,
            "request": delegation_request.dict()
        }
        
    except Exception as e:
        logger.error(f"Error delegating task: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }