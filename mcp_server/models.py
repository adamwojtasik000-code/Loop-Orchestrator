"""
Data Models for Loop-Orchestrator MCP Server

Pydantic models for structured data handling and validation.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import json


class ScheduleType(str, Enum):
    """Schedule type enumeration."""
    TIME = "time"
    INTERVAL = "interval"
    CRON = "cron"
    MANUAL = "manual"


class ScheduleStatus(str, Enum):
    """Schedule status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING = "pending"


class PriorityType(str, Enum):
    """Priority type for tasks."""
    SCHEDULE = "schedule"  # TOP PRIORITY for schedule-driven tasks
    TODO = "todo"         # Integrated priority for TODO tasks
    NORMAL = "normal"     # Normal priority for other tasks


class PersistentMemorySection(str, Enum):
    """Persistent memory sections."""
    IMPLEMENTATION_PATTERNS = "Non-Obvious Implementation Patterns"
    DEVELOPMENT_COMMANDS = "Development & Debug Commands"
    SYSTEM_UPDATES = "System Updates & Status"


class ScheduleData(BaseModel):
    """Structured model for schedule information."""
    id: str
    name: str
    mode: str
    task_instructions: str
    schedule_type: ScheduleType
    time_interval: Optional[int] = None
    time_unit: Optional[str] = None
    selected_days: Dict[str, bool] = Field(default_factory=dict)
    start_date: Optional[str] = None
    start_hour: Optional[str] = None
    start_minute: str = "00"
    expiration_date: Optional[str] = None
    expiration_hour: Optional[str] = None
    expiration_minute: Optional[str] = None
    require_activity: bool = False
    active: bool = True
    task_interaction: str = "wait"
    inactivity_delay: str = "3"
    last_execution_time: Optional[str] = None
    last_skipped_time: Optional[str] = None
    last_task_id: Optional[str] = None
    next_execution_time: Optional[str] = None
    mode_display_name: Optional[str] = None
    created_at: str
    updated_at: str

    @field_validator("time_unit")
    @classmethod
    def validate_time_unit(cls, v):
        """Validate time unit values."""
        if v and v not in ["minute", "hour", "day"]:
            raise ValueError("time_unit must be 'minute', 'hour', or 'day'")
        return v

    @field_validator("task_interaction")
    @classmethod
    def validate_task_interaction(cls, v):
        """Validate task interaction values."""
        if v and v not in ["wait", "interrupt", "background"]:
            raise ValueError("task_interaction must be 'wait', 'interrupt', or 'background'")
        return v


class SchedulesContainer(BaseModel):
    """Container for multiple schedules."""
    schedules: List[ScheduleData]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulesContainer":
        """Create container from dictionary."""
        return cls(schedules=[ScheduleData(**item) for item in data.get("schedules", [])])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"schedules": [schedule.model_dump() for schedule in self.schedules]}


class TaskTimingData(BaseModel):
    """Structured model for task timing information."""
    timestamp: str
    mode: Optional[str] = None
    task_id: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds
    task: str
    result: Optional[str] = None
    priority: Optional[PriorityType] = None

    @field_validator("start_time")
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamps are in ISO format."""
        if isinstance(v, str):
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
                return v
            except ValueError:
                # Try to parse as Unix timestamp
                try:
                    dt = datetime.fromtimestamp(float(v))
                    return dt.isoformat()
                except ValueError:
                    pass
        return v

    @field_validator("duration")
    @classmethod
    def calculate_duration(cls, v, values):
        """Calculate duration if not provided."""
        if v is None and values.get("start_time") and values.get("end_time"):
            try:
                start = datetime.fromisoformat(values["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(values["end_time"].replace("Z", "+00:00"))
                return int((end - start).total_seconds())
            except (ValueError, TypeError):
                pass
        return v


class TaskTimingContainer(BaseModel):
    """Container for task timing data."""
    entries: List[TaskTimingData] = Field(default_factory=list)

    @classmethod
    def from_tsv(cls, content: str) -> "TaskTimingContainer":
        """Parse TSV content into task timing entries."""
        entries = []
        lines = content.strip().split("\n")
        
        if not lines:
            return cls(entries=[])
        
        # Skip header
        for line in lines[1:]:
            if not line.strip():
                continue
                
            parts = line.split("\t")
            if len(parts) >= 7:
                entry_data = {
                    "timestamp": parts[0],
                    "mode": parts[1] if len(parts) > 1 else None,
                    "task_id": parts[2] if len(parts) > 2 else None,
                    "start_time": parts[3] if len(parts) > 3 else "",
                    "end_time": parts[4] if len(parts) > 4 else None,
                    "duration": int(parts[5]) if len(parts) > 5 and parts[5] else None,
                    "task": parts[6] if len(parts) > 6 else "",
                    "result": parts[7] if len(parts) > 7 else None,
                    "priority": parts[8] if len(parts) > 8 else None,
                }
                entries.append(TaskTimingData(**entry_data))
        
        return cls(entries=entries)

    def to_tsv(self) -> str:
        """Convert to TSV format."""
        lines = ["timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority"]
        
        for entry in self.entries:
            line = "\t".join([
                entry.timestamp or "",
                entry.mode or "",
                entry.task_id or "",
                entry.start_time or "",
                entry.end_time or "",
                str(entry.duration) if entry.duration else "",
                entry.task or "",
                entry.result or "",
                entry.priority.value if entry.priority else "",
            ])
            lines.append(line)
        
        return "\n".join(lines)


class PersistentMemoryEntry(BaseModel):
    """Structured entry for persistent memory."""
    section: PersistentMemorySection
    content: str
    timestamp: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        if v is None:
            return datetime.utcnow().isoformat() + "Z"
        return v


class SystemStatus(BaseModel):
    """Comprehensive system health status."""
    status: str = "healthy"
    timestamp: str
    version: str
    uptime: Optional[int] = None  # Uptime in seconds
    python_version: Optional[str] = None
    
    # File system status
    workspace_accessible: bool = True
    key_files_exist: Dict[str, bool] = Field(default_factory=dict)
    file_permissions: Dict[str, bool] = Field(default_factory=dict)
    
    # Orchestrator integration
    schedules_accessible: bool = True
    time_tracking_active: bool = True
    persistent_memory_valid: bool = True
    
    # Performance metrics
    operation_count: int = 0
    error_count: int = 0
    average_operation_time: float = 0.0
    memory_usage_mb: Optional[float] = None
    
    # Health checks
    health_checks: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @field_validator("timestamp")
    @classmethod
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        if v is None:
            return datetime.utcnow().isoformat() + "Z"
        return v


class ModeInfo(BaseModel):
    """Information about available modes."""
    slug: str
    name: str
    description: str
    role_definition: Optional[str] = None
    when_to_use: Optional[str] = None
    groups: List[str] = Field(default_factory=list)
    source: str = "project"
    custom_instructions: Optional[str] = None


class ModeCapabilities(BaseModel):
    """Container for mode capabilities."""
    modes: List[ModeInfo]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModeCapabilities":
        """Create from modes dictionary."""
        modes = []
        for slug, mode_data in data.get("customModes", {}).items():
            mode_data["slug"] = slug
            modes.append(ModeInfo(**mode_data))
        return cls(modes=modes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"customModes": [mode.model_dump() for mode in self.modes]}


class FileOperationResult(BaseModel):
    """Result of file operations."""
    success: bool
    file_path: str
    operation: str
    content: Optional[str] = None
    size: Optional[int] = None
    timestamp: Optional[str] = None
    backup_created: Optional[str] = None
    error: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        if v is None:
            return datetime.utcnow().isoformat() + "Z"
        return v


class ValidationResult(BaseModel):
    """Result of validation operations."""
    success: bool
    validation_type: str
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        if v is None:
            return datetime.utcnow().isoformat() + "Z"
        return v


class DelegationRequest(BaseModel):
    """Request for task delegation to specialized modes."""
    task_description: str
    target_mode: Optional[str] = None
    priority: PriorityType = PriorityType.NORMAL
    context: Dict[str, Any] = Field(default_factory=dict)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority setting."""
        if v not in [PriorityType.SCHEDULE, PriorityType.TODO, PriorityType.NORMAL]:
            raise ValueError("priority must be one of: schedule, todo, normal")
        return v


class DelegationResult(BaseModel):
    """Result of task delegation."""
    success: bool
    task_id: Optional[str] = None
    mode_assigned: Optional[str] = None
    estimated_duration: Optional[int] = None  # Duration in seconds
    delegation_timestamp: str
    status: str = "pending"
    error: Optional[str] = None

    @field_validator("delegation_timestamp")
    @classmethod
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        if v is None:
            return datetime.utcnow().isoformat() + "Z"
        return v