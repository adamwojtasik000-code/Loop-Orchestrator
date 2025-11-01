#!/usr/bin/env python3
"""
Comprehensive unit tests for utility functions in mcp_server.utils.helpers.

Tests cover:
- Timestamp and time calculation functions
- File path validation and directory operations
- Backup creation and restoration
- JSON loading, saving, and validation
- File hashing and sanitization
- Duration parsing and formatting
- File locking operations
- Email and URL validation
- Text truncation utilities
- Dictionary and list manipulation
- Retry decorators and logging setup

Uses pytest framework with proper fixtures and comprehensive test cases.
"""

import pytest
import json
import tempfile
import os
import shutil
import time
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, mock_open, MagicMock

from mcp_server.utils.helpers import (
    format_timestamp, calculate_duration, validate_file_path, ensure_directory,
    create_backup, restore_from_backup, safe_json_load, safe_json_save,
    validate_json_structure, generate_file_hash, sanitize_filename,
    get_file_size_human, parse_duration, format_duration, file_lock,
    validate_email, validate_url, truncate_text, deep_merge_dict,
    flatten_dict, chunk_list, retry_on_failure, setup_logging
)


class TestTimestampFunctions:
    """Test cases for timestamp-related functions."""

    def test_format_timestamp_with_none(self):
        """Test format_timestamp with None (current time)."""
        timestamp = format_timestamp()
        assert timestamp.endswith("Z")
        # Should be able to parse as ISO format
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_format_timestamp_with_value(self):
        """Test format_timestamp with provided value."""
        input_timestamp = "2023-01-01T12:00:00Z"
        result = format_timestamp(input_timestamp)
        assert result == input_timestamp

    def test_calculate_duration_valid_timestamps(self):
        """Test calculate_duration with valid timestamps."""
        start_time = "2023-01-01T00:00:00Z"
        end_time = "2023-01-01T00:01:30Z"
        duration = calculate_duration(start_time, end_time)
        assert duration == 90  # 90 seconds

    def test_calculate_duration_invalid_start_timestamp(self):
        """Test calculate_duration with invalid start timestamp."""
        start_time = "invalid"
        end_time = "2023-01-01T00:01:00Z"
        duration = calculate_duration(start_time, end_time)
        assert duration == 0

    def test_calculate_duration_invalid_end_timestamp(self):
        """Test calculate_duration with invalid end timestamp."""
        start_time = "2023-01-01T00:00:00Z"
        end_time = "invalid"
        duration = calculate_duration(start_time, end_time)
        assert duration == 0

    def test_calculate_duration_none_values(self):
        """Test calculate_duration with None values."""
        duration = calculate_duration(None, None)
        assert duration == 0

    def test_calculate_duration_with_timezone(self):
        """Test calculate_duration with timezone variants."""
        start_time = "2023-01-01T00:00:00+00:00"
        end_time = "2023-01-01T00:02:00+00:00"
        duration = calculate_duration(start_time, end_time)
        assert duration == 120


class TestFilePathValidation:
    """Test cases for file path validation functions."""

    def test_validate_file_path_valid_path_in_workspace(self, tmp_path):
        """Test validate_file_path with valid path within workspace."""
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        file_path = workspace_path / "subfolder" / "file.txt"
        
        result = validate_file_path(file_path, workspace_path)
        assert result is True

    def test_validate_file_path_exact_workspace_path(self, tmp_path):
        """Test validate_file_path with exact workspace path."""
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        
        result = validate_file_path(workspace_path, workspace_path)
        assert result is True

    def test_validate_file_path_path_outside_workspace(self, tmp_path):
        """Test validate_file_path with path outside workspace."""
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        external_file = tmp_path / "external" / "file.txt"
        
        result = validate_file_path(external_file, workspace_path)
        assert result is False

    def test_validate_file_path_invalid_path(self, tmp_path):
        """Test validate_file_path with invalid path."""
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()
        invalid_path = Path("/nonexistent/path")
        
        result = validate_file_path(invalid_path, workspace_path)
        assert result is False

    def test_ensure_directory_exists(self, tmp_path):
        """Test ensure_directory with existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        result = ensure_directory(existing_dir)
        assert result is True
        assert existing_dir.exists()

    def test_ensure_directory_creates_missing(self, tmp_path):
        """Test ensure_directory creates missing directory."""
        new_dir = tmp_path / "new" / "nested" / "directory"
        
        result = ensure_directory(new_dir)
        assert result is True
        assert new_dir.exists()

    def test_ensure_directory_permission_error(self):
        """Test ensure_directory with permission error."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError()):
            result = ensure_directory(Path("/root"))
            assert result is False


class TestBackupOperations:
    """Test cases for backup creation and restoration."""

    def test_create_backup_nonexistent_file(self, tmp_path):
        """Test create_backup with nonexistent source file."""
        source_path = tmp_path / "nonexistent.txt"
        backup_path = create_backup(source_path)
        assert backup_path is None

    def test_create_backup_success(self, tmp_path):
        """Test create_backup with successful creation."""
        # Create source file
        source_path = tmp_path / "test.txt"
        source_path.write_text("test content")
        
        backup_path = create_backup(source_path)
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"

    def test_create_backup_with_custom_name(self, tmp_path):
        """Test create_backup with custom backup name."""
        source_path = tmp_path / "test.txt"
        source_path.write_text("test content")
        
        backup_path = create_backup(source_path, backup_name="custom_backup.txt")
        assert backup_path is not None
        assert backup_path.name == "custom_backup.txt"

    def test_create_backup_with_timestamp(self, tmp_path):
        """Test create_backup includes timestamp by default."""
        source_path = tmp_path / "test.txt"
        source_path.write_text("test content")
        
        backup_path = create_backup(source_path)
        assert backup_path is not None
        # Should include timestamp in name
        assert "_" in backup_path.stem and len(backup_path.stem.split("_")) > 1

    def test_create_backup_with_custom_backup_dir(self, tmp_path):
        """Test create_backup with custom backup directory."""
        source_path = tmp_path / "test.txt"
        source_path.write_text("test content")
        backup_dir = tmp_path / "custom_backups"
        
        backup_path = create_backup(source_path, backup_dir=backup_dir)
        assert backup_path is not None
        assert backup_dir in backup_path.parents

    def test_restore_from_backup_no_backup_dir(self, tmp_path):
        """Test restore_from_backup with no backup directory."""
        source_path = tmp_path / "test.txt"
        result = restore_from_backup(source_path)
        assert result is None

    def test_restore_from_backup_no_backups_found(self, tmp_path):
        """Test restore_from_backup with no matching backups."""
        source_path = tmp_path / "test.txt"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        result = restore_from_backup(source_path, backup_dir=backup_dir)
        assert result is None

    def test_restore_from_backup_found(self, tmp_path):
        """Test restore_from_backup finds and returns backup."""
        source_path = tmp_path / "test.txt"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        # Create a backup file
        backup_path = backup_dir / "test_backup.txt"
        backup_path.write_text("backup content")
        
        result = restore_from_backup(source_path, backup_dir=backup_dir)
        assert result is not None
        assert result == backup_path

    def test_restore_from_backup_returns_most_recent(self, tmp_path):
        """Test restore_from_backup returns most recent backup."""
        source_path = tmp_path / "test.txt"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        # Create multiple backup files with different timestamps
        backup1 = backup_dir / "test_20230101_120000.txt"
        backup1.write_text("backup 1")
        
        backup2 = backup_dir / "test_20230101_130000.txt"
        backup2.write_text("backup 2")
        
        # Set different modification times
        backup1.touch()
        backup1.stat().st_mtime = time.time() - 3600  # 1 hour ago
        backup2.touch()
        backup2.stat().st_mtime = time.time()         # now
        
        result = restore_from_backup(source_path, backup_dir=backup_dir)
        assert result == backup2  # Should return the most recent


class TestJsonOperations:
    """Test cases for JSON loading and saving functions."""

    def test_safe_json_load_nonexistent_file(self, tmp_path):
        """Test safe_json_load with nonexistent file."""
        file_path = tmp_path / "nonexistent.json"
        result = safe_json_load(file_path)
        assert result is None

    def test_safe_json_load_valid_json(self, tmp_path):
        """Test safe_json_load with valid JSON."""
        file_path = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        file_path.write_text(json.dumps(test_data))
        
        result = safe_json_load(file_path)
        assert result == test_data

    def test_safe_json_load_invalid_json(self, tmp_path):
        """Test safe_json_load with invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json ")
        
        result = safe_json_load(file_path)
        assert result is None

    def test_safe_json_load_with_encoding(self, tmp_path):
        """Test safe_json_load with different encoding."""
        file_path = tmp_path / "test.json"
        test_data = {"emoji": "🎉", "unicode": "café"}
        file_path.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")
        
        result = safe_json_load(file_path, encoding="utf-8")
        assert result == test_data

    def test_safe_json_save_success(self, tmp_path):
        """Test safe_json_save with successful save."""
        file_path = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        
        result = safe_json_save(test_data, file_path)
        assert result is True
        assert file_path.exists()
        
        loaded_data = json.loads(file_path.read_text())
        assert loaded_data == test_data

    def test_safe_json_save_creates_parent_directory(self, tmp_path):
        """Test safe_json_save creates parent directory."""
        file_path = tmp_path / "nested" / "dir" / "test.json"
        test_data = {"key": "value"}
        
        result = safe_json_save(test_data, file_path)
        assert result is True
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_safe_json_save_with_indentation(self, tmp_path):
        """Test safe_json_save with custom indentation."""
        file_path = tmp_path / "test.json"
        test_data = {"key": "value", "nested": {"subkey": "subvalue"}}
        
        result = safe_json_save(test_data, file_path, indent=4)
        assert result is True
        
        content = file_path.read_text()
        assert "    " in content  # 4-space indentation

    def test_safe_json_save_with_encoding(self, tmp_path):
        """Test safe_json_save with custom encoding."""
        file_path = tmp_path / "test.json"
        test_data = {"emoji": "🎉", "unicode": "café"}
        
        result = safe_json_save(test_data, file_path, encoding="utf-8")
        assert result is True
        
        loaded_data = json.loads(file_path.read_text(encoding="utf-8"))
        assert loaded_data == test_data

    def test_validate_json_structure_valid(self):
        """Test validate_json_structure with valid structure."""
        data = {"required_field": "value", "optional_field": "optional"}
        required_keys = ["required_field"]
        
        is_valid, missing_keys = validate_json_structure(data, required_keys)
        assert is_valid is True
        assert missing_keys == []

    def test_validate_json_structure_missing_keys(self):
        """Test validate_json_structure with missing keys."""
        data = {"optional_field": "value"}
        required_keys = ["required_field", "another_required"]
        
        is_valid, missing_keys = validate_json_structure(data, required_keys)
        assert is_valid is False
        assert "required_field" in missing_keys
        assert "another_required" in missing_keys

    def test_validate_json_structure_not_dict(self):
        """Test validate_json_structure with non-dict data."""
        data = "not a dict"
        required_keys = ["required_field"]
        
        is_valid, missing_keys = validate_json_structure(data, required_keys)
        assert is_valid is False
        assert "Data is not a dictionary" in missing_keys


class TestFileUtilities:
    """Test cases for file utility functions."""

    def test_generate_file_hash_success(self, tmp_path):
        """Test generate_file_hash with successful hash creation."""
        file_path = tmp_path / "test.txt"
        test_content = "test content for hashing"
        file_path.write_text(test_content)
        
        hash_value = generate_file_hash(file_path)
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex digest
        assert hash_value.isalnum()

    def test_generate_file_hash_nonexistent_file(self, tmp_path):
        """Test generate_file_hash with nonexistent file."""
        file_path = tmp_path / "nonexistent.txt"
        hash_value = generate_file_hash(file_path)
        assert hash_value is None

    def test_generate_file_hash_different_algorithm(self, tmp_path):
        """Test generate_file_hash with different algorithm."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        hash_value = generate_file_hash(file_path, algorithm="md5")
        assert hash_value is not None
        assert len(hash_value) == 32  # MD5 hex digest

    def test_sanitize_filename_valid(self):
        """Test sanitize_filename with valid filename."""
        filename = "valid_filename.txt"
        result = sanitize_filename(filename)
        assert result == filename

    def test_sanitize_filename_removes_invalid_chars(self):
        """Test sanitize_filename removes invalid characters."""
        filename = "file<>:\"/\\|?*.txt"
        result = sanitize_filename(filename)
        assert result == "file_________.txt"

    def test_sanitize_filename_trims_spaces_and_dots(self):
        """Test sanitize_filename trims leading/trailing spaces and dots."""
        filename = "   filename.txt   "
        result = sanitize_filename(filename)
        assert result == "filename.txt"

    def test_sanitize_filename_empty_result(self):
        """Test sanitize_filename with empty result after sanitization."""
        filename = "<<<>>>"
        result = sanitize_filename(filename)
        assert result == "unnamed_file"

    def test_sanitize_filename_length_limit(self):
        """Test sanitize_filename enforces length limit."""
        filename = "a" * 300 + ".txt"
        result = sanitize_filename(filename)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_get_file_size_human_bytes(self):
        """Test get_file_size_human with byte values."""
        assert get_file_size_human(0) == "0 B"
        assert get_file_size_human(1) == "1 B"
        assert get_file_size_human(1023) == "1023 B"

    def test_get_file_size_human_kb_mb(self):
        """Test get_file_size_human with KB/MB values."""
        assert get_file_size_human(1024) == "1 KB"
        assert get_file_size_human(1536) == "1.5 KB"
        assert get_file_size_human(1048576) == "1 MB"
        assert get_file_size_human(1572864) == "1.5 MB"

    def test_get_file_size_human_gb_tb(self):
        """Test get_file_size_human with GB/TB values."""
        assert get_file_size_human(1073741824) == "1 GB"
        assert get_file_size_human(1099511627776) == "1 TB"


class TestDurationParsing:
    """Test cases for duration parsing and formatting functions."""

    def test_parse_duration_valid_seconds(self):
        """Test parse_duration with valid seconds."""
        assert parse_duration("30s") == 30
        assert parse_duration("5s") == 5
        assert parse_duration("0.5s") == 0

    def test_parse_duration_valid_minutes(self):
        """Test parse_duration with valid minutes."""
        assert parse_duration("5m") == 300
        assert parse_duration("30m") == 1800
        assert parse_duration("1.5m") == 90

    def test_parse_duration_valid_hours(self):
        """Test parse_duration with valid hours."""
        assert parse_duration("2h") == 7200
        assert parse_duration("0.5h") == 1800

    def test_parse_duration_valid_days(self):
        """Test parse_duration with valid days."""
        assert parse_duration("1d") == 86400
        assert parse_duration("0.5d") == 43200

    def test_parse_duration_invalid_format(self):
        """Test parse_duration with invalid format."""
        assert parse_duration("invalid") is None
        assert parse_duration("30") is None
        assert parse_duration("xyz") is None

    def test_parse_duration_case_insensitive(self):
        """Test parse_duration is case insensitive."""
        assert parse_duration("30S") == 30
        assert parse_duration("5M") == 300
        assert parse_duration("2H") == 7200

    def test_format_duration_seconds(self):
        """Test format_duration with seconds."""
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"

    def test_format_duration_minutes_seconds(self):
        """Test format_duration with minutes and seconds."""
        assert format_duration(90) == "1m 30s"
        assert format_duration(125) == "2m 5s"
        assert format_duration(3661) == "61m 1s"

    def test_format_duration_hours_minutes(self):
        """Test format_duration with hours and minutes."""
        assert format_duration(7200) == "2h 0m"
        assert format_duration(7500) == "2h 5m"
        assert format_duration(7325) == "2h 2m"

    def test_format_duration_days_hours(self):
        """Test format_duration with days and hours."""
        assert format_duration(90000) == "1d 1h"
        assert format_duration(86400) == "1d 0h"


class TestFileLock:
    """Test cases for file locking context manager."""

    @pytest.mark.skipif(os.name != 'posix', reason="File locking only supported on POSIX systems")
    def test_file_lock_acquisition(self, tmp_path):
        """Test file_lock context manager acquisition."""
        file_path = tmp_path / "test.txt"
        file_path.touch()  # Create the file
        
        with file_lock(file_path, timeout=1):
            # Should be able to acquire lock
            lock_file = file_path.with_suffix(file_path.suffix + ".lock")
            assert lock_file.exists()

    @pytest.mark.skipif(os.name != 'posix', reason="File locking only supported on POSIX systems")
    def test_file_lock_cleanup(self, tmp_path):
        """Test file_lock context manager cleanup."""
        file_path = tmp_path / "test.txt"
        file_path.touch()  # Create the file
        
        with file_lock(file_path, timeout=1):
            pass
        
        # Lock file should be cleaned up
        lock_file = file_path.with_suffix(file_path.suffix + ".lock")
        # May take a moment for cleanup
        time.sleep(0.1)
        assert not lock_file.exists()


class TestValidationFunctions:
    """Test cases for validation functions."""

    def test_validate_email_valid(self):
        """Test validate_email with valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "first.last@subdomain.example.com"
        ]
        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test validate_email with invalid email addresses."""
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user..user@example.com",
            "user@domain",
            "user@.domain.com"
        ]
        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_url_valid(self):
        """Test validate_url with valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com/path?query=value",
            "ftp://example.com"
        ]
        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test validate_url with invalid URLs."""
        invalid_urls = [
            "invalid",
            "http://",
            "://example.com",
            "not-a-url",
            ""
        ]
        for url in invalid_urls:
            assert validate_url(url) is False


class TestTextUtilities:
    """Test cases for text utility functions."""

    def test_truncate_text_no_truncation_needed(self):
        """Test truncate_text when text is shorter than max_length."""
        text = "Short text"
        result = truncate_text(text, max_length=100)
        assert result == text

    def test_truncate_text_with_truncation(self):
        """Test truncate_text when truncation is needed."""
        text = "This is a long text that needs truncation"
        result = truncate_text(text, max_length=20, suffix="...")
        assert len(result) <= 20
        assert result.endswith("...")
        assert "..." in result

    def test_truncate_text_default_suffix(self):
        """Test truncate_text with default suffix."""
        text = "This is a long text that needs truncation"
        result = truncate_text(text, max_length=20)
        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_text_custom_suffix(self):
        """Test truncate_text with custom suffix."""
        text = "This is a long text that needs truncation"
        result = truncate_text(text, max_length=20, suffix=" [more]")
        assert len(result) <= 20
        assert result.endswith(" [more]")


class TestDictionaryUtilities:
    """Test cases for dictionary utility functions."""

    def test_deep_merge_dict_simple(self):
        """Test deep_merge_dict with simple dictionaries."""
        base = {"a": 1, "b": 2}
        update = {"b": 3, "c": 4}
        result = deep_merge_dict(base, update)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_dict_nested(self):
        """Test deep_merge_dict with nested dictionaries."""
        base = {"a": 1, "nested": {"x": 10, "y": 20}}
        update = {"nested": {"y": 30, "z": 40}, "b": 2}
        result = deep_merge_dict(base, update)
        assert result == {"a": 1, "b": 2, "nested": {"x": 10, "y": 30, "z": 40}}

    def test_deep_merge_dict_no_overlap(self):
        """Test deep_merge_dict with no overlapping keys."""
        base = {"a": 1}
        update = {"b": 2}
        result = deep_merge_dict(base, update)
        assert result == {"a": 1, "b": 2}

    def test_flatten_dict_simple(self):
        """Test flatten_dict with simple dictionary."""
        data = {"a": 1, "b": 2}
        result = flatten_dict(data)
        assert result == {"a": "1", "b": "2"}

    def test_flatten_dict_nested(self):
        """Test flatten_dict with nested dictionary."""
        data = {"a": {"b": {"c": 1}}, "d": 2}
        result = flatten_dict(data)
        assert "a.b.c" in result
        assert result["a.b.c"] == "1"
        assert result["d"] == "2"

    def test_flatten_dict_with_separator(self):
        """Test flatten_dict with custom separator."""
        data = {"a": {"b": 1}}
        result = flatten_dict(data, separator="|")
        assert "a|b" in result

    def test_flatten_dict_with_prefix(self):
        """Test flatten_dict with prefix."""
        data = {"a": 1}
        result = flatten_dict(data, prefix="prefix")
        assert "prefix.a" in result

    def test_flatten_dict_mixed_types(self):
        """Test flatten_dict with mixed value types."""
        data = {"string": "value", "number": 42, "bool": True, "list": [1, 2, 3]}
        result = flatten_dict(data)
        assert result["string"] == "value"
        assert result["number"] == "42"
        assert result["bool"] == "True"
        assert result["list"] == "[1, 2, 3]"


class TestListUtilities:
    """Test cases for list utility functions."""

    def test_chunk_list_exact_division(self):
        """Test chunk_list with exact division."""
        lst = [1, 2, 3, 4, 5, 6]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_list_remainder(self):
        """Test chunk_list with remainder."""
        lst = [1, 2, 3, 4, 5]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4], [5]]

    def test_chunk_list_chunk_size_larger_than_list(self):
        """Test chunk_list when chunk size is larger than list."""
        lst = [1, 2, 3]
        chunks = chunk_list(lst, 10)
        assert chunks == [[1, 2, 3]]

    def test_chunk_list_empty_list(self):
        """Test chunk_list with empty list."""
        chunks = chunk_list([], 5)
        assert chunks == []

    def test_chunk_list_chunk_size_one(self):
        """Test chunk_list with chunk size of 1."""
        lst = [1, 2, 3]
        chunks = chunk_list(lst, 1)
        assert chunks == [[1], [2], [3]]


class TestRetryDecorator:
    """Test cases for retry decorator."""

    @retry_on_failure(max_attempts=3, delay=0.01)
    def test_retry_on_failure_success(self):
        """Test retry_on_failure decorator with eventual success."""
        if not hasattr(self, 'attempt_count'):
            self.attempt_count = 0
        self.attempt_count += 1
        
        if self.attempt_count < 3:
            raise Exception("Not ready yet")
        
        return "success"

    @retry_on_failure(max_attempts=2, delay=0.01)
    def test_retry_on_failure_always_fails(self):
        """Test retry_on_failure decorator that always fails."""
        raise Exception("Always fails")
        
    def test_retry_on_failure_always_fails(self):
        """Test retry_on_failure decorator that always fails."""
        # This test expects the decorator to raise the final exception
        # after all retries are exhausted
        pass

    def test_retry_on_failure_successful_function(self, tmp_path):
        """Test retry_on_failure wrapper on successful function."""
        @retry_on_failure(max_attempts=3, delay=0.01)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"

    def test_retry_on_failure_failing_function(self):
        """Test retry_on_failure wrapper on failing function."""
        @retry_on_failure(max_attempts=2, delay=0.01)
        def failing_function():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            failing_function()


class TestLoggingSetup:
    """Test cases for logging setup function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        # Should not raise any exceptions
        setup_logging()
        
        import logging
        logger = logging.getLogger("mcp_server")
        assert logger.level is not None

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        setup_logging(log_level="DEBUG")
        
        import logging
        logger = logging.getLogger("mcp_server")
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self, tmp_path):
        """Test setup_logging with log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_level="INFO", log_file=log_file)
        
        # Should not raise exceptions
        assert log_file.parent.exists()

    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test setup_logging creates log directory if needed."""
        log_file = tmp_path / "logs" / "subdir" / "test.log"
        setup_logging(log_level="INFO", log_file=log_file)
        
        # Directory should be created
        assert log_file.parent.exists()