#!/usr/bin/env python3
"""
Comprehensive unit tests for orchestrator I/O functions in mcp_server.utils.orchestrator_io.

Tests cover:
- OrchestratorIO class initialization and state management
- File state tracking and change detection
- Schedules loading and saving operations
- Task timing data loading and saving
- Persistent memory operations
- TODO status loading
- Schedule management functions
- Time tracking operations
- Error handling for all file operations
- Integration with helper functions

Uses pytest framework with proper fixtures and comprehensive test cases.
"""

import pytest
import json
import tempfile
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, mock_open, MagicMock, Mock

from mcp_server.utils.orchestrator_io import (
    OrchestratorIO, get_orchestrator_io,
    load_schedules, save_schedules,
    load_task_timing, save_task_timing,
    load_persistent_memory, save_persistent_memory,
    load_todo_status,
    schedule_task_execution, get_active_schedules, get_next_execution_schedules,
    update_schedule_execution,
    add_time_tracking_entry, get_time_tracking_summary,
    add_persistent_memory_entry,
    _create_default_persistent_memory, _parse_persistent_memory_sections,
    _get_time_unit_seconds
)

from mcp_server.models import (
    ScheduleData, SchedulesContainer, TaskTimingData, TaskTimingContainer,
    PersistentMemorySection, PriorityType, ScheduleType
)


class TestOrchestratorIO:
    """Test cases for OrchestratorIO class."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create temporary workspace with all orchestrator files."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        # Create .roo directory
        roo_dir = workspace / ".roo"
        roo_dir.mkdir()
        
        # Create orchestrator files
        schedules_file = roo_dir / "schedules.json"
        schedules_file.write_text('{"schedules": []}')
        
        task_timing_file = workspace / "task_timing.tsv"
        task_timing_file.write_text("timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority\n")
        
        persistent_memory_file = workspace / "persistent-memory.md"
        persistent_memory_file.write_text("# Persistent Memory\n")
        
        todo_file = workspace / "TODO.md"
        todo_file.write_text("- [ ] Test TODO item\n")
        
        return workspace

    @pytest.fixture
    def mock_config(self):
        """Mock server configuration."""
        mock_config = Mock()
        mock_config.workspace_path = Path("/mock/workspace")
        mock_config.get_schedules_path.return_value = Path("/mock/workspace/.roo/schedules.json")
        mock_config.get_task_timing_path.return_value = Path("/mock/workspace/task_timing.tsv")
        mock_config.get_persistent_memory_path.return_value = Path("/mock/workspace/persistent-memory.md")
        mock_config.get_todo_path.return_value = Path("/mock/workspace/TODO.md")
        mock_config.get_modes_path.return_value = Path("/mock/workspace/.roo/modes.json")
        mock_config.get_backups_dir.return_value = Path("/mock/workspace/.roo/backups")
        return mock_config

    def test_orchestrator_io_initialization_default_config(self, mock_config):
        """Test OrchestratorIO initialization with default config."""
        with patch('mcp_server.utils.orchestrator_io.get_server_config', return_value=mock_config):
            io = OrchestratorIO()
            assert io.config == mock_config
            assert io.workspace_path == Path("/mock/workspace")

    def test_orchestrator_io_initialization_custom_config(self, mock_config):
        """Test OrchestratorIO initialization with custom config."""
        io = OrchestratorIO(config=mock_config)
        assert io.config == mock_config
        assert io.workspace_path == Path("/mock/workspace")

    def test_get_file_state_nonexistent_file(self, tmp_path):
        """Test get_file_state with nonexistent file."""
        io = OrchestratorIO()
        file_path = tmp_path / "nonexistent.txt"
        state = io.get_file_state(file_path)
        
        assert state["exists"] is False
        assert state["last_modified"] is None
        assert state["size"] == 0
        assert state["checksum"] is None

    def test_get_file_state_existing_file(self, tmp_path):
        """Test get_file_state with existing file."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        test_content = "test content"
        file_path.write_text(test_content)
        
        state = io.get_file_state(file_path)
        
        assert state["exists"] is True
        assert state["last_modified"] is not None
        assert state["size"] == len(test_content)
        assert state["checksum"] is not None

    def test_calculate_file_checksum(self, tmp_path):
        """Test _calculate_file_checksum method."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        test_content = "test content for checksum"
        file_path.write_text(test_content)
        
        checksum = io._calculate_file_checksum(file_path)
        assert checksum is not None
        assert len(checksum) == 32  # MD5 hex digest

    def test_calculate_file_checksum_nonexistent(self):
        """Test _calculate_file_checksum with nonexistent file."""
        io = OrchestratorIO()
        checksum = io._calculate_file_checksum(Path("/nonexistent.txt"))
        assert checksum is None

    def test_is_file_changed_first_time(self, tmp_path):
        """Test is_file_changed for first time seeing a file."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        result = io.is_file_changed(file_path)
        assert result is True  # First time, should return True

    def test_is_file_changed_no_change(self, tmp_path):
        """Test is_file_changed when file hasn't changed."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        content = "test content"
        file_path.write_text(content)
        
        # First call to establish baseline
        io.is_file_changed(file_path)
        io.update_file_state(file_path)
        
        # Second call with same file - should return False
        result = io.is_file_changed(file_path)
        assert result is False

    def test_is_file_changed_content_modified(self, tmp_path):
        """Test is_file_changed when file content is modified."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        
        # Write initial content
        file_path.write_text("original content")
        io.is_file_changed(file_path)
        io.update_file_state(file_path)
        
        # Modify content
        file_path.write_text("modified content")
        result = io.is_file_changed(file_path)
        assert result is True

    def test_update_file_state(self, tmp_path):
        """Test update_file_state method."""
        io = OrchestratorIO()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        io.update_file_state(file_path)
        
        # State should be tracked
        assert str(file_path) in io._file_states


class TestGlobalOrchestratorIO:
    """Test cases for global orchestrator I/O instance."""

    def test_get_orchestrator_io_creates_instance(self):
        """Test get_orchestrator_io creates global instance."""
        global _orchestrator_io
        _orchestrator_io = None  # Reset global instance
        
        io = get_orchestrator_io()
        assert io is not None
        assert isinstance(io, OrchestratorIO)
        assert _orchestrator_io == io

    def test_get_orchestrator_io_returns_existing(self):
        """Test get_orchestrator_io returns existing instance."""
        global _orchestrator_io
        mock_io = Mock(spec=OrchestratorIO)
        _orchestrator_io = mock_io
        
        io = get_orchestrator_io()
        assert io == mock_io


class TestSchedulesIO:
    """Test cases for schedules loading and saving functions."""

    @pytest.fixture
    def schedules_data(self):
        """Sample schedules data."""
        return {
            "schedules": [
                {
                    "id": "schedule1",
                    "name": "Test Schedule 1",
                    "mode": "test-mode",
                    "task_instructions": "Test task instructions",
                    "schedule_type": "time",
                    "start_hour": "09:00",
                    "start_minute": "00",
                    "active": True,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }

    def test_load_schedules_file_not_found(self, tmp_path):
        """Test load_schedules when file doesn't exist."""
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = tmp_path / "nonexistent.json"
            mock_get_io.return_value = mock_io
            
            result = load_schedules()
            assert result is not None
            assert len(result.schedules) == 0

    def test_load_schedules_success(self, tmp_path, schedules_data):
        """Test load_schedules with valid data."""
        schedules_file = tmp_path / "schedules.json"
        schedules_file.write_text(json.dumps(schedules_data))
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            result = load_schedules()
            assert result is not None
            assert len(result.schedules) == 1
            assert result.schedules[0].id == "schedule1"
            assert result.schedules[0].name == "Test Schedule 1"

    def test_load_schedules_invalid_json(self, tmp_path):
        """Test load_schedules with invalid JSON."""
        schedules_file = tmp_path / "schedules.json"
        schedules_file.write_text("{ invalid json ")
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            result = load_schedules()
            assert result is None

    def test_save_schedules_success(self, tmp_path, schedules_data):
        """Test save_schedules with successful save."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_io.schedules_path.exists.return_value = True
            mock_io.config.get_backups_dir.return_value = tmp_path / "backups"
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.helpers.safe_json_save', return_value=True):
                container = SchedulesContainer.from_dict(schedules_data)
                result = save_schedules(container)
                assert result is True

    def test_save_schedules_backward_compatibility(self, tmp_path):
        """Test save_schedules uses dict() method for backward compatibility."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_io.schedules_path.exists.return_value = True
            mock_io.config.get_backups_dir.return_value = tmp_path / "backups"
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.helpers.safe_json_save', return_value=True) as mock_save:
                container = SchedulesContainer(schedules=[])
                result = save_schedules(container)
                assert result is True
                mock_save.assert_called_once()

    def test_save_schedules_failure(self, tmp_path):
        """Test save_schedules with failure."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.helpers.safe_json_save', return_value=False):
                container = SchedulesContainer(schedules=[])
                result = save_schedules(container)
                assert result is False


class TestTaskTimingIO:
    """Test cases for task timing loading and saving functions."""

    @pytest.fixture
    def task_timing_content(self):
        """Sample task timing TSV content."""
        return """timestamp\tmode\ttask_id\tstart_time\tend_time\tduration\ttask\tresult\tpriority
2023-01-01T00:00:00Z\ttest-mode\ttask-123\t2023-01-01T00:00:00Z\t2023-01-01T00:01:00Z\t60\ttest task\tcompleted\tnormal
2023-01-01T00:01:00Z\ttest-mode\ttask-124\t2023-01-01T00:01:00Z\t\t\ttest task 2\tstarted\tnormal
"""

    def test_load_task_timing_file_not_found(self, tmp_path):
        """Test load_task_timing when file doesn't exist."""
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = tmp_path / "nonexistent.tsv"
            mock_get_io.return_value = mock_io
            
            result = load_task_timing()
            assert result is not None
            assert len(result.entries) == 0

    def test_load_task_timing_success(self, tmp_path, task_timing_content):
        """Test load_task_timing with valid data."""
        timing_file = tmp_path / "task_timing.tsv"
        timing_file.write_text(task_timing_content)
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            result = load_task_timing()
            assert result is not None
            assert len(result.entries) == 2
            assert result.entries[0].task_id == "task-123"
            assert result.entries[0].duration == 60
            assert result.entries[1].task_id == "task-124"

    def test_load_task_timing_empty_content(self, tmp_path):
        """Test load_task_timing with empty content."""
        timing_file = tmp_path / "task_timing.tsv"
        timing_file.write_text("")
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            result = load_task_timing()
            assert result is not None
            assert len(result.entries) == 0

    def test_save_task_timing_success(self, tmp_path):
        """Test save_task_timing with successful save."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_io.task_timing_path.exists.return_value = True
            mock_io.config.get_backups_dir.return_value = tmp_path / "backups"
            mock_get_io.return_value = mock_io
            
            # Create test timing data
            entries = [
                TaskTimingData(
                    timestamp="2023-01-01T00:00:00Z",
                    task="test task",
                    start_time="2023-01-01T00:00:00Z"
                )
            ]
            container = TaskTimingContainer(entries=entries)
            
            result = save_task_timing(container)
            assert result is True
            # File should be written
            assert timing_file.exists()

    def test_save_task_timing_failure(self, tmp_path):
        """Test save_task_timing with failure."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            with patch('builtins.open', side_effect=IOError("Write failed")):
                container = TaskTimingContainer(entries=[])
                result = save_task_timing(container)
                assert result is False


class TestPersistentMemoryIO:
    """Test cases for persistent memory operations."""

    @pytest.fixture
    def persistent_memory_content(self):
        """Sample persistent memory content."""
        return """# Persistent Memory

# Non-Obvious Implementation Patterns

## [2023-01-01T00:00:00Z] [mcp-server] - [general]
- Finding: Test pattern for implementation

# Development & Debug Commands

## [2023-01-01T00:01:00Z] [mcp-server] - [testing]
- Finding: Test command for debugging

# System Updates & Status

## [2023-01-01T00:02:00Z] [mcp-server] - [status]
- Finding: Test system update
"""

    def test_load_persistent_memory_file_not_found(self, tmp_path):
        """Test load_persistent_memory when file doesn't exist."""
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = tmp_path / "nonexistent.md"
            mock_get_io.return_value = mock_io
            
            result = load_persistent_memory()
            assert isinstance(result, dict)
            assert len(result) == 3  # Should create default sections

    def test_load_persistent_memory_success(self, tmp_path, persistent_memory_content):
        """Test load_persistent_memory with valid content."""
        pm_file = tmp_path / "persistent-memory.md"
        pm_file.write_text(persistent_memory_content)
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            result = load_persistent_memory()
            assert isinstance(result, dict)
            assert len(result) >= 3  # Should have at least the 3 required sections

    def test_save_persistent_memory_success(self, tmp_path):
        """Test save_persistent_memory with successful save."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_io.persistent_memory_path.exists.return_value = True
            mock_io.config.get_backups_dir.return_value = tmp_path / "backups"
            mock_get_io.return_value = mock_io
            
            sections = {
                "Non-Obvious Implementation Patterns": "test content 1",
                "Development & Debug Commands": "test content 2",
                "System Updates & Status": "test content 3"
            }
            
            result = save_persistent_memory(sections)
            assert result is True
            assert pm_file.exists()

    def test_save_persistent_memory_with_custom_sections(self, tmp_path):
        """Test save_persistent_memory with additional sections."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_io.persistent_memory_path.exists.return_value = False
            mock_io.config.get_backups_dir.return_value = tmp_path / "backups"
            mock_get_io.return_value = mock_io
            
            sections = {
                "Non-Obvious Implementation Patterns": "test content 1",
                "Development & Debug Commands": "test content 2",
                "System Updates & Status": "test content 3",
                "Custom Section": "custom content"
            }
            
            result = save_persistent_memory(sections)
            assert result is True
            
            content = pm_file.read_text()
            assert "# Custom Section" in content
            assert "custom content" in content

    def test_create_default_persistent_memory(self):
        """Test _create_default_persistent_memory function."""
        result = _create_default_persistent_memory()
        assert isinstance(result, dict)
        assert len(result) == 3
        assert "Non-Obvious Implementation Patterns" in result
        assert "Development & Debug Commands" in result
        assert "System Updates & Status" in result

    def test_parse_persistent_memory_sections(self, persistent_memory_content):
        """Test _parse_persistent_memory_sections function."""
        result = _parse_persistent_memory_sections(persistent_memory_content)
        assert isinstance(result, dict)
        assert len(result) >= 3
        assert "Non-Obvious Implementation Patterns" in result
        assert "Development & Debug Commands" in result
        assert "System Updates & Status" in result


class TestTodoStatus:
    """Test cases for TODO status loading."""

    @pytest.fixture
    def todo_content(self):
        """Sample TODO content."""
        return """# TODO

- [x] Completed TODO item
- [ ] Pending TODO item
- [X] Another completed item (uppercase X)
- [ ] Second pending item
"""

    def test_load_todo_status_success(self, tmp_path, todo_content):
        """Test load_todo_status with valid content."""
        todo_file = tmp_path / "TODO.md"
        todo_file.write_text(todo_content)
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.todo_path = todo_file
            mock_get_io.return_value = mock_io
            
            result = load_todo_status()
            assert result["total"] == 4
            assert result["completed"] == 2
            assert result["pending"] == 2
            assert len(result["todos"]) == 4

    def test_load_todo_status_file_not_found(self, tmp_path):
        """Test load_todo_status when file doesn't exist."""
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.todo_path = tmp_path / "nonexistent.md"
            mock_get_io.return_value = mock_io
            
            result = load_todo_status()
            assert result["total"] == 0
            assert result["completed"] == 0
            assert result["pending"] == 0
            assert result["todos"] == []

    def test_load_todo_status_invalid_format(self, tmp_path):
        """Test load_todo_status with invalid format."""
        todo_file = tmp_path / "TODO.md"
        todo_file.write_text("This is not a valid TODO format")
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.todo_path = todo_file
            mock_get_io.return_value = mock_io
            
            result = load_todo_status()
            assert result["total"] == 0
            assert result["completed"] == 0
            assert result["pending"] == 0


class TestScheduleManagement:
    """Test cases for schedule management functions."""

    @pytest.fixture
    def schedules_data(self):
        """Sample schedules data."""
        return {
            "schedules": [
                {
                    "id": "active1",
                    "name": "Active Schedule 1",
                    "mode": "test-mode",
                    "task_instructions": "Test task 1",
                    "schedule_type": "manual",
                    "active": True,
                    "start_minute": "00",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                },
                {
                    "id": "inactive1",
                    "name": "Inactive Schedule",
                    "mode": "test-mode",
                    "task_instructions": "Test task 2",
                    "schedule_type": "manual",
                    "active": False,
                    "start_minute": "00",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }

    def test_schedule_task_execution_success(self, tmp_path):
        """Test schedule_task_execution with successful creation."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_io.schedules_path.exists.return_value = False
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=SchedulesContainer(schedules=[])):
                with patch('mcp_server.utils.orchestrator_io.save_schedules', return_value=True):
                    schedule_id = schedule_task_execution("Test task", "test-mode")
                    assert schedule_id is not None

    def test_schedule_task_execution_with_config(self, tmp_path):
        """Test schedule_task_execution with additional configuration."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_io.schedules_path.exists.return_value = False
            mock_get_io.return_value = mock_io
            
            schedule_config = {
                "start_hour": "09:00",
                "require_activity": True
            }
            
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=SchedulesContainer(schedules=[])):
                with patch('mcp_server.utils.orchestrator_io.save_schedules', return_value=True) as mock_save:
                    schedule_id = schedule_task_execution("Test task", "test-mode", schedule_config)
                    assert schedule_id is not None
                    # Verify that save was called (indicating schedule was created)
                    mock_save.assert_called_once()

    def test_schedule_task_execution_failure(self, tmp_path):
        """Test schedule_task_execution with failure."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=None):
                schedule_id = schedule_task_execution("Test task", "test-mode")
                assert schedule_id is None

    def test_get_active_schedules_with_schedules(self, tmp_path, schedules_data):
        """Test get_active_schedules with active schedules."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            container = SchedulesContainer.from_dict(schedules_data)
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=container):
                active_schedules = get_active_schedules()
                assert len(active_schedules) == 1
                assert active_schedules[0].id == "active1"

    def test_get_active_schedules_no_schedules(self, tmp_path):
        """Test get_active_schedules with no schedules."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=SchedulesContainer(schedules=[])):
                active_schedules = get_active_schedules()
                assert len(active_schedules) == 0

    def test_get_next_execution_schedules_manual_schedule(self, tmp_path):
        """Test get_next_execution_schedules excludes manual schedules."""
        schedules_data = {
            "schedules": [
                {
                    "id": "manual1",
                    "name": "Manual Schedule",
                    "mode": "test-mode",
                    "task_instructions": "Test task",
                    "schedule_type": "manual",
                    "active": True,
                    "start_minute": "00",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            container = SchedulesContainer.from_dict(schedules_data)
            with patch('mcp_server.utils.orchestrator_io.get_active_schedules', return_value=container.schedules):
                next_schedules = get_next_execution_schedules()
                assert len(next_schedules) == 0  # Manual schedules should be excluded

    def test_update_schedule_execution_success(self, tmp_path):
        """Test update_schedule_execution with successful update."""
        schedules_data = {
            "schedules": [
                {
                    "id": "schedule1",
                    "name": "Test Schedule",
                    "mode": "test-mode",
                    "task_instructions": "Test task",
                    "schedule_type": "time",
                    "active": True,
                    "time_interval": 60,
                    "time_unit": "minute",
                    "start_minute": "00",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            container = SchedulesContainer.from_dict(schedules_data)
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=container):
                with patch('mcp_server.utils.orchestrator_io.save_schedules', return_value=True):
                    result = update_schedule_execution("schedule1", "completed")
                    assert result is True

    def test_update_schedule_execution_not_found(self, tmp_path):
        """Test update_schedule_execution when schedule not found."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_schedules', return_value=SchedulesContainer(schedules=[])):
                result = update_schedule_execution("nonexistent", "completed")
                assert result is False


class TestTimeTracking:
    """Test cases for time tracking operations."""

    def test_add_time_tracking_entry_success(self, tmp_path):
        """Test add_time_tracking_entry with successful addition."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=TaskTimingContainer()):
                with patch('mcp_server.utils.orchestrator_io.save_task_timing', return_value=True):
                    result = add_time_tracking_entry("Test task", "test-mode")
                    assert result is True

    def test_add_time_tracking_entry_with_all_params(self, tmp_path):
        """Test add_time_tracking_entry with all parameters."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            container = TaskTimingContainer()
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=container):
                with patch('mcp_server.utils.orchestrator_io.save_task_timing', return_value=True) as mock_save:
                    start_time = "2023-01-01T00:00:00Z"
                    end_time = "2023-01-01T00:01:30Z"
                    
                    result = add_time_tracking_entry(
                        task_description="Test task",
                        mode="test-mode",
                        task_id="task-123",
                        priority=PriorityType.NORMAL,
                        start_time=start_time,
                        end_time=end_time,
                        result="completed"
                    )
                    assert result is True
                    # Should have been called with updated container
                    mock_save.assert_called_once()

    def test_add_time_tracking_entry_failure(self, tmp_path):
        """Test add_time_tracking_entry with failure."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=TaskTimingContainer()):
                with patch('mcp_server.utils.orchestrator_io.save_task_timing', return_value=False):
                    result = add_time_tracking_entry("Test task", "test-mode")
                    assert result is False

    def test_get_time_tracking_summary_with_data(self, tmp_path):
        """Test get_time_tracking_summary with timing data."""
        timing_file = tmp_path / "task_timing.tsv"
        
        # Create test data
        entries = [
            TaskTimingData(
                timestamp="2023-01-01T00:00:00Z",
                task="task 1",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T00:01:00Z",
                duration=60,
                result="completed",
                priority=PriorityType.NORMAL
            ),
            TaskTimingData(
                timestamp="2023-01-01T00:01:00Z",
                task="task 2",
                start_time="2023-01-01T00:01:00Z",
                end_time="2023-01-01T00:02:30Z",
                duration=90,
                result="completed",
                priority=PriorityType.NORMAL
            )
        ]
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            container = TaskTimingContainer(entries=entries)
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=container):
                summary = get_time_tracking_summary()
                assert summary["total_entries"] == 2
                assert summary["total_duration_seconds"] == 150
                assert summary["total_tasks"] == 2
                assert summary["average_duration_seconds"] == 75

    def test_get_time_tracking_summary_with_filters(self, tmp_path):
        """Test get_time_tracking_summary with mode and priority filters."""
        timing_file = tmp_path / "task_timing.tsv"
        
        entries = [
            TaskTimingData(
                timestamp="2023-01-01T00:00:00Z",
                mode="mode1",
                task="task 1",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T00:01:00Z",
                duration=60,
                result="completed",
                priority=PriorityType.NORMAL
            ),
            TaskTimingData(
                timestamp="2023-01-01T00:01:00Z",
                mode="mode2",
                task="task 2",
                start_time="2023-01-01T00:01:00Z",
                duration=30,
                result="completed",
                priority=PriorityType.SCHEDULE
            )
        ]
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            container = TaskTimingContainer(entries=entries)
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=container):
                # Filter by mode
                summary = get_time_tracking_summary(mode="mode1")
                assert summary["total_entries"] == 1
                
                # Filter by priority
                summary = get_time_tracking_summary(priority=PriorityType.SCHEDULE)
                assert summary["total_entries"] == 1

    def test_get_time_tracking_summary_empty_data(self, tmp_path):
        """Test get_time_tracking_summary with no data."""
        timing_file = tmp_path / "task_timing.tsv"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.task_timing_path = timing_file
            mock_get_io.return_value = mock_io
            
            container = TaskTimingContainer(entries=[])
            with patch('mcp_server.utils.orchestrator_io.load_task_timing', return_value=container):
                summary = get_time_tracking_summary()
                assert summary["total_entries"] == 0
                assert summary["total_duration_seconds"] == 0
                assert summary["total_tasks"] == 0
                assert summary["average_duration_seconds"] == 0


class TestPersistentMemoryEntry:
    """Test cases for persistent memory entry operations."""

    def test_add_persistent_memory_entry_success(self, tmp_path):
        """Test add_persistent_memory_entry with successful addition."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_persistent_memory', return_value={}):
                with patch('mcp_server.utils.orchestrator_io.save_persistent_memory', return_value=True):
                    result = add_persistent_memory_entry(
                        section=PersistentMemorySection.IMPLEMENTATION_PATTERNS,
                        content="Test entry"
                    )
                    assert result is True

    def test_add_persistent_memory_entry_with_category(self, tmp_path):
        """Test add_persistent_memory_entry with category."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            initial_sections = {
                "Non-Obvious Implementation Patterns": "existing content\n"
            }
            
            with patch('mcp_server.utils.orchestrator_io.load_persistent_memory', return_value=initial_sections):
                with patch('mcp_server.utils.orchestrator_io.save_persistent_memory', return_value=True) as mock_save:
                    result = add_persistent_memory_entry(
                        section=PersistentMemorySection.IMPLEMENTATION_PATTERNS,
                        content="Test entry",
                        category="testing"
                    )
                    assert result is True
                    # Should be called with updated sections
                    mock_save.assert_called_once()

    def test_add_persistent_memory_entry_without_formatting(self, tmp_path):
        """Test add_persistent_memory_entry without entry formatting."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_persistent_memory', return_value={}):
                with patch('mcp_server.utils.orchestrator_io.save_persistent_memory', return_value=True):
                    result = add_persistent_memory_entry(
                        section=PersistentMemorySection.DEVELOPMENT_COMMANDS,
                        content="Test entry",
                        format_entry=False
                    )
                    assert result is True

    def test_add_persistent_memory_entry_failure(self, tmp_path):
        """Test add_persistent_memory_entry with failure."""
        pm_file = tmp_path / "persistent-memory.md"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.orchestrator_io.load_persistent_memory', return_value={}):
                with patch('mcp_server.utils.orchestrator_io.save_persistent_memory', return_value=False):
                    result = add_persistent_memory_entry(
                        section=PersistentMemorySection.SYSTEM_UPDATES,
                        content="Test entry"
                    )
                    assert result is False


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_get_time_unit_seconds_valid_units(self):
        """Test _get_time_unit_seconds with valid units."""
        assert _get_time_unit_seconds("minute") == 60
        assert _get_time_unit_seconds("hour") == 3600
        assert _get_time_unit_seconds("day") == 86400

    def test_get_time_unit_seconds_invalid_unit(self):
        """Test _get_time_unit_seconds with invalid unit."""
        assert _get_time_unit_seconds("invalid") == 60  # Default to minutes
        assert _get_time_unit_seconds("") == 60  # Default to minutes
        assert _get_time_unit_seconds(None) == 60  # Default to minutes


class TestErrorHandling:
    """Test cases for comprehensive error handling."""

    def test_load_schedules_io_error(self, tmp_path):
        """Test load_schedules with I/O error."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('builtins.open', side_effect=IOError("Read failed")):
                result = load_schedules()
                assert result is None

    def test_save_schedules_io_error(self, tmp_path):
        """Test save_schedules with I/O error."""
        schedules_file = tmp_path / "schedules.json"
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.schedules_path = schedules_file
            mock_get_io.return_value = mock_io
            
            with patch('mcp_server.utils.helpers.safe_json_save', side_effect=IOError("Write failed")):
                container = SchedulesContainer(schedules=[])
                result = save_schedules(container)
                assert result is False

    def test_load_persistent_memory_malformed_content(self, tmp_path):
        """Test load_persistent_memory with malformed content."""
        pm_file = tmp_path / "persistent-memory.md"
        pm_file.write_text("malformed content without proper sections")
        
        with patch('mcp_server.utils.orchestrator_io.get_orchestrator_io') as mock_get_io:
            mock_io = Mock()
            mock_io.persistent_memory_path = pm_file
            mock_get_io.return_value = mock_io
            
            result = load_persistent_memory()
            assert isinstance(result, dict)
            # Should create default sections
            assert len(result) == 3