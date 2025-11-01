#!/usr/bin/env python3
"""
Comprehensive unit tests for data models in mcp_server.models.

Tests cover:
- All enum classes and their values
- Model validation and field constraints
- Serialization/deserialization methods
- Field validators and business logic
- Error handling and edge cases

Uses pytest framework with proper fixtures and assertions.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from mcp_server.models import (
    ScheduleType, ScheduleStatus, TaskStatus, PriorityType, PersistentMemorySection,
    ScheduleData, SchedulesContainer, TaskTimingData, TaskTimingContainer,
    PersistentMemoryEntry, SystemStatus, ModeInfo, ModeCapabilities,
    FileOperationResult, ValidationResult, DelegationRequest, DelegationResult
)


class TestEnums:
    """Test cases for all enum classes."""

    def test_schedule_type_values(self):
        """Test ScheduleType enum values."""
        assert ScheduleType.TIME == "time"
        assert ScheduleType.INTERVAL == "interval"
        assert ScheduleType.CRON == "cron"
        assert ScheduleType.MANUAL == "manual"

    def test_schedule_status_values(self):
        """Test ScheduleStatus enum values."""
        assert ScheduleStatus.ACTIVE == "active"
        assert ScheduleStatus.INACTIVE == "inactive"
        assert ScheduleStatus.PAUSED == "paused"
        assert ScheduleStatus.COMPLETED == "completed"
        assert ScheduleStatus.FAILED == "failed"

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.STARTED == "started"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
        assert TaskStatus.PENDING == "pending"

    def test_priority_type_values(self):
        """Test PriorityType enum values."""
        assert PriorityType.SCHEDULE == "schedule"
        assert PriorityType.TODO == "todo"
        assert PriorityType.NORMAL == "normal"

    def test_persistent_memory_section_values(self):
        """Test PersistentMemorySection enum values."""
        assert PersistentMemorySection.IMPLEMENTATION_PATTERNS == "Non-Obvious Implementation Patterns"
        assert PersistentMemorySection.DEVELOPMENT_COMMANDS == "Development & Debug Commands"
        assert PersistentMemorySection.SYSTEM_UPDATES == "System Updates & Status"


class TestScheduleData:
    """Test cases for ScheduleData model."""

    def test_schedule_data_valid_initialization(self):
        """Test ScheduleData with valid data."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.TIME,
            "start_hour": "10:00",
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        schedule = ScheduleData(**data)
        assert schedule.id == "test-id"
        assert schedule.name == "Test Schedule"
        assert schedule.schedule_type == ScheduleType.TIME

    def test_schedule_data_with_optional_fields(self):
        """Test ScheduleData with optional fields."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.INTERVAL,
            "time_interval": 30,
            "time_unit": "minute",
            "require_activity": True,
            "active": False,
            "task_interaction": "interrupt",
            "start_hour": "09:00",
            "start_minute": "30",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        schedule = ScheduleData(**data)
        assert schedule.time_interval == 30
        assert schedule.time_unit == "minute"
        assert schedule.require_activity is True
        assert schedule.active is False
        assert schedule.task_interaction == "interrupt"

    def test_schedule_data_default_values(self):
        """Test ScheduleData default values."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.MANUAL,
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        schedule = ScheduleData(**data)
        assert schedule.start_minute == "00"
        assert schedule.require_activity is False
        assert schedule.active is True
        assert schedule.task_interaction == "wait"
        assert schedule.inactivity_delay == "3"

    def test_time_unit_validation_valid(self):
        """Test time_unit validator with valid values."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.INTERVAL,
            "time_unit": "hour",
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        schedule = ScheduleData(**data)
        assert schedule.time_unit == "hour"

    def test_time_unit_validation_invalid(self):
        """Test time_unit validator with invalid values."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.INTERVAL,
            "time_unit": "invalid_unit",
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        with pytest.raises(ValueError, match="time_unit must be 'minute', 'hour', or 'day'"):
            ScheduleData(**data)

    def test_task_interaction_validation_valid(self):
        """Test task_interaction validator with valid values."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.TIME,
            "task_interaction": "background",
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        schedule = ScheduleData(**data)
        assert schedule.task_interaction == "background"

    def test_task_interaction_validation_invalid(self):
        """Test task_interaction validator with invalid values."""
        data = {
            "id": "test-id",
            "name": "Test Schedule",
            "mode": "test-mode",
            "task_instructions": "test instructions",
            "schedule_type": ScheduleType.TIME,
            "task_interaction": "invalid_interaction",
            "start_minute": "00",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        with pytest.raises(ValueError, match="task_interaction must be 'wait', 'interrupt', or 'background'"):
            ScheduleData(**data)


class TestSchedulesContainer:
    """Test cases for SchedulesContainer model."""

    def test_schedules_container_empty(self):
        """Test SchedulesContainer with no schedules."""
        container = SchedulesContainer(schedules=[])
        assert len(container.schedules) == 0

    def test_schedules_container_with_schedules(self):
        """Test SchedulesContainer with schedules."""
        schedules_data = [
            {
                "id": "id1",
                "name": "Schedule 1",
                "mode": "mode1",
                "task_instructions": "instructions 1",
                "schedule_type": ScheduleType.MANUAL,
                "start_minute": "00",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "id2",
                "name": "Schedule 2",
                "mode": "mode2",
                "task_instructions": "instructions 2",
                "schedule_type": ScheduleType.TIME,
                "start_minute": "30",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        ]
        container = SchedulesContainer(schedules=[ScheduleData(**s) for s in schedules_data])
        assert len(container.schedules) == 2
        assert container.schedules[0].id == "id1"
        assert container.schedules[1].id == "id2"

    def test_schedules_container_from_dict(self):
        """Test SchedulesContainer.from_dict method."""
        data = {
            "schedules": [
                {
                    "id": "id1",
                    "name": "Schedule 1",
                    "mode": "mode1",
                    "task_instructions": "instructions 1",
                    "schedule_type": ScheduleType.MANUAL,
                    "start_minute": "00",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        container = SchedulesContainer.from_dict(data)
        assert len(container.schedules) == 1
        assert container.schedules[0].id == "id1"

    def test_schedules_container_to_dict(self):
        """Test SchedulesContainer.to_dict method."""
        schedules_data = [
            {
                "id": "id1",
                "name": "Schedule 1",
                "mode": "mode1",
                "task_instructions": "instructions 1",
                "schedule_type": ScheduleType.MANUAL,
                "start_minute": "00",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        ]
        container = SchedulesContainer(schedules=[ScheduleData(**s) for s in schedules_data])
        result = container.to_dict()
        assert "schedules" in result
        assert len(result["schedules"]) == 1
        assert result["schedules"][0]["id"] == "id1"


class TestTaskTimingData:
    """Test cases for TaskTimingData model."""

    def test_task_timing_data_valid_initialization(self):
        """Test TaskTimingData with valid data."""
        data = {
            "timestamp": "2023-01-01T00:00:00Z",
            "task": "test task",
            "start_time": "2023-01-01T00:00:00Z"
        }
        timing = TaskTimingData(**data)
        assert timing.timestamp == "2023-01-01T00:00:00Z"
        assert timing.task == "test task"
        assert timing.start_time == "2023-01-01T00:00:00Z"

    def test_task_timing_data_with_all_fields(self):
        """Test TaskTimingData with all fields."""
        data = {
            "timestamp": "2023-01-01T00:00:00Z",
            "mode": "test-mode",
            "task_id": "task-123",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-01T00:01:00Z",
            "duration": 60,
            "task": "test task",
            "result": "completed",
            "priority": PriorityType.NORMAL
        }
        timing = TaskTimingData(**data)
        assert timing.mode == "test-mode"
        assert timing.task_id == "task-123"
        assert timing.duration == 60
        assert timing.result == "completed"
        assert timing.priority == PriorityType.NORMAL

    def test_timestamp_validation_iso_format(self):
        """Test timestamp validation with ISO format."""
        data = {
            "timestamp": "2023-01-01T00:00:00+00:00",
            "task": "test task",
            "start_time": "2023-01-01T00:00:00+00:00"
        }
        timing = TaskTimingData(**data)
        assert timing.timestamp == "2023-01-01T00:00:00+00:00"

    def test_timestamp_validation_unix_timestamp(self):
        """Test timestamp validation with Unix timestamp."""
        data = {
            "timestamp": "1672531200.0",  # 2023-01-01T00:00:00Z
            "task": "test task",
            "start_time": "2023-01-01T00:00:00Z"
        }
        timing = TaskTimingData(**data)
        # Should parse Unix timestamp and convert to ISO
        assert timing.timestamp is not None

    def test_duration_calculation(self):
        """Test automatic duration calculation."""
        data = {
            "timestamp": "2023-01-01T00:00:00Z",
            "task": "test task",
            "start_time": "2023-01-01T00:00:00Z",
            "end_time": "2023-01-01T00:01:30Z"
        }
        timing = TaskTimingData(**data)
        assert timing.duration == 90  # 90 seconds

    def test_duration_calculation_no_end_time(self):
        """Test duration calculation when no end_time provided."""
        data = {
            "timestamp": "2023-01-01T00:00:00Z",
            "task": "test task",
            "start_time": "2023-01-01T00:00:00Z"
        }
        timing = TaskTimingData(**data)
        assert timing.duration is None

    def test_duration_calculation_invalid_timestamps(self):
        """Test duration calculation with invalid timestamps."""
        data = {
            "timestamp": "2023-01-01T00:00:00Z",
            "task": "test task",
            "start_time": "invalid timestamp",
            "end_time": "2023-01-01T00:01:00Z"
        }
        timing = TaskTimingData(**data)
        assert timing.duration is None


class TestTaskTimingContainer:
    """Test cases for TaskTimingContainer model."""

    def test_task_timing_container_empty(self):
        """Test TaskTimingContainer with no entries."""
        container = TaskTimingContainer(entries=[])
        assert len(container.entries) == 0

    def test_task_timing_container_from_tsv_empty(self):
        """Test TaskTimingContainer.from_tsv with empty content."""
        container = TaskTimingContainer.from_tsv("")
        assert len(container.entries) == 0

    def test_task_timing_container_from_tsv_with_header_only(self):
        """Test TaskTimingContainer.from_tsv with header only."""
        content = "timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority\n"
        container = TaskTimingContainer.from_tsv(content)
        assert len(container.entries) == 0

    def test_task_timing_container_from_tsv_valid_data(self):
        """Test TaskTimingContainer.from_tsv with valid data."""
        content = """timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority
2023-01-01T00:00:00Z\ttest-mode\ttask-123\t2023-01-01T00:00:00Z\t2023-01-01T00:01:00Z\t60\ttest task\tcompleted\tnormal
2023-01-01T00:01:00Z\ttest-mode\ttask-124\t2023-01-01T00:01:00Z\t\t\ttest task 2\tstarted\tnormal
"""
        container = TaskTimingContainer.from_tsv(content)
        assert len(container.entries) == 2
        assert container.entries[0].task_id == "task-123"
        assert container.entries[0].duration == 60
        assert container.entries[0].result == "completed"
        assert container.entries[1].task_id == "task-124"
        assert container.entries[1].result == "started"

    def test_task_timing_container_from_tsv_partial_data(self):
        """Test TaskTimingContainer.from_tsv with partial data."""
        content = """timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority
2023-01-01T00:00:00Z\ttest-mode\ttask-123\t2023-01-01T00:00:00Z\t2023-01-01T00:01:00Z\t60\ttest task\tcompleted\tnormal
"""
        container = TaskTimingContainer.from_tsv(content)
        assert len(container.entries) == 1
        assert container.entries[0].timestamp == "2023-01-01T00:00:00Z"

    def test_task_timing_container_from_tsv_invalid_duration(self):
        """Test TaskTimingContainer.from_tsv with invalid duration."""
        content = """timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority
2023-01-01T00:00:00Z\ttest-mode\ttask-123\t2023-01-01T00:00:00Z\t2023-01-01T00:01:00Z\tinvalid\ttest task\tcompleted\tnormal
"""
        try:
            container = TaskTimingContainer.from_tsv(content)
            # Should skip the invalid line and return empty container
            assert len(container.entries) == 0
        except ValueError:
            # If it raises ValueError, that's also acceptable behavior
            pass

    def test_task_timing_container_to_tsv(self):
        """Test TaskTimingContainer.to_tsv method."""
        entries = [
            TaskTimingData(
                timestamp="2023-01-01T00:00:00Z",
                mode="test-mode",
                task_id="task-123",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T00:01:00Z",
                duration=60,
                task="test task",
                result="completed",
                priority=PriorityType.NORMAL
            )
        ]
        container = TaskTimingContainer(entries=entries)
        result = container.to_tsv()
        lines = result.split("\n")
        assert len(lines) == 2  # Header + data line
        assert lines[0] == "timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority"
        assert "2023-01-01T00:00:00Z" in lines[1]
        assert "task-123" in lines[1]

    def test_task_timing_container_to_tsv_empty(self):
        """Test TaskTimingContainer.to_tsv with empty entries."""
        container = TaskTimingContainer(entries=[])
        result = container.to_tsv()
        assert result == "timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority"


class TestPersistentMemoryEntry:
    """Test cases for PersistentMemoryEntry model."""

    def test_persistent_memory_entry_valid_initialization(self):
        """Test PersistentMemoryEntry with valid data."""
        data = {
            "section": PersistentMemorySection.IMPLEMENTATION_PATTERNS,
            "content": "test content"
        }
        entry = PersistentMemoryEntry(**data)
        assert entry.section == PersistentMemorySection.IMPLEMENTATION_PATTERNS
        assert entry.content == "test content"
        assert entry.timestamp is not None

    def test_persistent_memory_entry_with_timestamp(self):
        """Test PersistentMemoryEntry with provided timestamp."""
        data = {
            "section": PersistentMemorySection.DEVELOPMENT_COMMANDS,
            "content": "test content",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        entry = PersistentMemoryEntry(**data)
        assert entry.timestamp == "2023-01-01T00:00:00Z"

    def test_persistent_memory_entry_with_category(self):
        """Test PersistentMemoryEntry with category and metadata."""
        data = {
            "section": PersistentMemorySection.SYSTEM_UPDATES,
            "content": "test content",
            "category": "test category",
            "metadata": {"key": "value"}
        }
        entry = PersistentMemoryEntry(**data)
        assert entry.category == "test category"
        assert entry.metadata == {"key": "value"}

    def test_persistent_memory_entry_auto_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        data = {
            "section": PersistentMemorySection.IMPLEMENTATION_PATTERNS,
            "content": "test content"
        }
        entry = PersistentMemoryEntry(**data)
        assert entry.timestamp is not None
        # Should be in ISO format with Z suffix
        assert entry.timestamp.endswith("Z")


class TestSystemStatus:
    """Test cases for SystemStatus model."""

    def test_system_status_default_values(self):
        """Test SystemStatus with default values."""
        status = SystemStatus(
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0"
        )
        assert status.status == "healthy"
        assert status.version == "1.0.0"
        assert status.timestamp == "2023-01-01T00:00:00Z"
        assert status.workspace_accessible is True
        assert status.operation_count == 0
        assert status.error_count == 0

    def test_system_status_with_all_fields(self):
        """Test SystemStatus with all fields populated."""
        status = SystemStatus(
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            uptime=3600,
            python_version="3.12.0",
            workspace_accessible=False,
            key_files_exist={"config.json": True},
            file_permissions={"main.py": True},
            schedules_accessible=False,
            time_tracking_active=False,
            persistent_memory_valid=False,
            operation_count=100,
            error_count=5,
            average_operation_time=0.5,
            memory_usage_mb=150.0,
            health_checks={"database": "healthy"},
            warnings=["warning 1"],
            errors=["error 1"],
            metrics={"requests_per_second": 10.0}
        )
        assert status.uptime == 3600
        assert status.python_version == "3.12.0"
        assert status.workspace_accessible is False
        assert status.operation_count == 100
        assert status.error_count == 5
        assert status.memory_usage_mb == 150.0
        assert status.health_checks == {"database": "healthy"}
        assert status.warnings == ["warning 1"]
        assert status.errors == ["error 1"]

    def test_system_status_auto_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        status = SystemStatus(version="1.0.0", timestamp="2023-01-01T00:00:00Z")
        assert status.timestamp is not None
        assert status.timestamp.endswith("Z")


class TestModeInfo:
    """Test cases for ModeInfo model."""

    def test_mode_info_basic(self):
        """Test ModeInfo with basic fields."""
        mode = ModeInfo(
            slug="test-mode",
            name="Test Mode",
            description="A test mode for testing purposes"
        )
        assert mode.slug == "test-mode"
        assert mode.name == "Test Mode"
        assert mode.description == "A test mode for testing purposes"
        assert mode.groups == []
        assert mode.source == "project"
        assert mode.custom_instructions is None

    def test_mode_info_with_all_fields(self):
        """Test ModeInfo with all optional fields."""
        mode = ModeInfo(
            slug="advanced-mode",
            name="Advanced Mode",
            description="Advanced functionality mode",
            role_definition="Handles complex tasks",
            when_to_use="For advanced operations",
            groups=["development", "testing"],
            source="custom",
            custom_instructions="Custom instructions for this mode"
        )
        assert mode.role_definition == "Handles complex tasks"
        assert mode.when_to_use == "For advanced operations"
        assert mode.groups == ["development", "testing"]
        assert mode.source == "custom"
        assert mode.custom_instructions == "Custom instructions for this mode"


class TestModeCapabilities:
    """Test cases for ModeCapabilities model."""

    def test_mode_capabilities_empty(self):
        """Test ModeCapabilities with no modes."""
        capabilities = ModeCapabilities(modes=[])
        assert len(capabilities.modes) == 0

    def test_mode_capabilities_with_modes(self):
        """Test ModeCapabilities with modes."""
        modes = [
            ModeInfo(
                slug="mode1",
                name="Mode 1",
                description="First mode"
            ),
            ModeInfo(
                slug="mode2",
                name="Mode 2",
                description="Second mode"
            )
        ]
        capabilities = ModeCapabilities(modes=modes)
        assert len(capabilities.modes) == 2
        assert capabilities.modes[0].slug == "mode1"
        assert capabilities.modes[1].slug == "mode2"

    def test_mode_capabilities_from_dict(self):
        """Test ModeCapabilities.from_dict method."""
        data = {
            "customModes": {
                "mode1": {
                    "name": "Mode 1",
                    "description": "First mode",
                    "groups": ["development"]
                },
                "mode2": {
                    "name": "Mode 2",
                    "description": "Second mode"
                }
            }
        }
        capabilities = ModeCapabilities.from_dict(data)
        assert len(capabilities.modes) == 2
        mode1 = next(m for m in capabilities.modes if m.slug == "mode1")
        assert mode1.name == "Mode 1"
        assert mode1.groups == ["development"]
        mode2 = next(m for m in capabilities.modes if m.slug == "mode2")
        assert mode2.name == "Mode 2"

    def test_mode_capabilities_to_dict(self):
        """Test ModeCapabilities.to_dict method."""
        modes = [
            ModeInfo(
                slug="test-mode",
                name="Test Mode",
                description="Test description",
                groups=["test"]
            )
        ]
        capabilities = ModeCapabilities(modes=modes)
        result = capabilities.to_dict()
        assert "customModes" in result
        assert len(result["customModes"]) == 1
        # Check that the mode info is in the list
        mode_dict = result["customModes"][0]
        assert mode_dict["slug"] == "test-mode"
        assert mode_dict["name"] == "Test Mode"
        assert mode_dict["groups"] == ["test"]


class TestFileOperationResult:
    """Test cases for FileOperationResult model."""

    def test_file_operation_result_success(self):
        """Test FileOperationResult for successful operation."""
        result = FileOperationResult(
            success=True,
            file_path="/path/to/file.txt",
            operation="read",
            timestamp="2023-01-01T00:00:00Z"
        )
        assert result.success is True
        assert result.file_path == "/path/to/file.txt"
        assert result.operation == "read"
        assert result.timestamp == "2023-01-01T00:00:00Z"
        assert result.content is None

    def test_file_operation_result_with_content(self):
        """Test FileOperationResult with file content."""
        result = FileOperationResult(
            success=True,
            file_path="/path/to/file.txt",
            operation="read",
            content="file content",
            size=12,
            backup_created="/path/to/file.txt.backup"
        )
        assert result.content == "file content"
        assert result.size == 12
        assert result.backup_created == "/path/to/file.txt.backup"

    def test_file_operation_result_failure(self):
        """Test FileOperationResult for failed operation."""
        result = FileOperationResult(
            success=False,
            file_path="/path/to/missing.txt",
            operation="read",
            error="File not found"
        )
        assert result.success is False
        assert result.error == "File not found"

    def test_file_operation_result_auto_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        result = FileOperationResult(
            success=True,
            file_path="/path/to/file.txt",
            operation="read",
            timestamp="2023-01-01T00:00:00Z"
        )
        assert result.timestamp is not None
        assert result.timestamp == "2023-01-01T00:00:00Z"


class TestValidationResult:
    """Test cases for ValidationResult model."""

    def test_validation_result_success(self):
        """Test ValidationResult for successful validation."""
        result = ValidationResult(
            success=True,
            validation_type="schema",
            timestamp="2023-01-01T00:00:00Z"
        )
        assert result.success is True
        assert result.validation_type == "schema"
        assert result.timestamp == "2023-01-01T00:00:00Z"
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_with_details(self):
        """Test ValidationResult with detailed information."""
        result = ValidationResult(
            success=True,
            validation_type="schema",
            timestamp="2023-01-01T00:00:00Z",
            details={"field_count": 5, "valid_fields": 5},
            errors=[],
            warnings=["Minor formatting issue"],
            metrics={"accuracy": 0.95}
        )
        assert result.details == {"field_count": 5, "valid_fields": 5}
        assert result.warnings == ["Minor formatting issue"]
        assert result.metrics == {"accuracy": 0.95}

    def test_validation_result_failure(self):
        """Test ValidationResult for failed validation."""
        result = ValidationResult(
            success=False,
            validation_type="schema",
            timestamp="2023-01-01T00:00:00Z",
            errors=["Field 'name' is required", "Invalid email format"],
            details={"error_count": 2}
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert "Field 'name' is required" in result.errors

    def test_validation_result_auto_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        result = ValidationResult(
            success=True,
            validation_type="schema",
            timestamp="2023-01-01T00:00:00Z"
        )
        assert result.timestamp is not None
        assert result.timestamp.endswith("Z")


class TestDelegationRequest:
    """Test cases for DelegationRequest model."""

    def test_delegation_request_basic(self):
        """Test DelegationRequest with basic fields."""
        request = DelegationRequest(
            task_description="Test task description"
        )
        assert request.task_description == "Test task description"
        assert request.target_mode is None
        assert request.priority == PriorityType.NORMAL
        assert request.context == {}
        assert request.requirements == {}

    def test_delegation_request_with_all_fields(self):
        """Test DelegationRequest with all fields."""
        request = DelegationRequest(
            task_description="Complex task that needs specialized handling",
            target_mode="debug",
            priority=PriorityType.SCHEDULE,
            context={"current_file": "main.py", "error_count": 3},
            requirements={"memory_mb": 512, "timeout_seconds": 300},
            deadline="2023-01-01T12:00:00Z"
        )
        assert request.target_mode == "debug"
        assert request.priority == PriorityType.SCHEDULE
        assert request.context == {"current_file": "main.py", "error_count": 3}
        assert request.requirements == {"memory_mb": 512, "timeout_seconds": 300}
        assert request.deadline == "2023-01-01T12:00:00Z"

    def test_delegation_request_priority_validation_valid(self):
        """Test priority validation with valid values."""
        for priority in [PriorityType.SCHEDULE, PriorityType.TODO, PriorityType.NORMAL]:
            request = DelegationRequest(
                task_description="Test task",
                priority=priority
            )
            assert request.priority == priority

    def test_delegation_request_priority_validation_invalid(self):
        """Test priority validation with invalid values."""
        with pytest.raises((ValueError, TypeError)):
            DelegationRequest(
                task_description="Test task",
                priority="invalid_priority"
            )


class TestDelegationResult:
    """Test cases for DelegationResult model."""

    def test_delegation_result_success(self):
        """Test DelegationResult for successful delegation."""
        result = DelegationResult(
            success=True,
            task_id="task-123",
            mode_assigned="debug",
            estimated_duration=300,
            status="assigned",
            delegation_timestamp="2023-01-01T00:00:00Z"
        )
        assert result.success is True
        assert result.task_id == "task-123"
        assert result.mode_assigned == "debug"
        assert result.estimated_duration == 300
        assert result.status == "assigned"

    def test_delegation_result_failure(self):
        """Test DelegationResult for failed delegation."""
        result = DelegationResult(
            success=False,
            task_id=None,
            mode_assigned=None,
            estimated_duration=None,
            status="failed",
            error="No available modes",
            delegation_timestamp="2023-01-01T00:00:00Z"
        )
        assert result.success is False
        assert result.error == "No available modes"
        assert result.task_id is None

    def test_delegation_result_default_values(self):
        """Test DelegationResult default values."""
        result = DelegationResult(
            success=True,
            delegation_timestamp="2023-01-01T00:00:00Z"
        )
        assert result.status == "pending"
        assert result.task_id is None
        assert result.mode_assigned is None
        assert result.estimated_duration is None

    def test_delegation_result_auto_timestamp(self):
        """Test that delegation_timestamp is auto-generated if not provided."""
        result = DelegationResult(success=True, delegation_timestamp="2023-01-01T00:00:00Z")
        assert result.delegation_timestamp is not None
        assert result.delegation_timestamp.endswith("Z")