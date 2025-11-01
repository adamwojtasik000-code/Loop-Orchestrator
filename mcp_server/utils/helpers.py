"""
Utility Functions and Helpers

Common utility functions for file operations, validation, formatting, and system helpers.
"""

import os
import json
import shutil
import time
import re
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import logging


logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    Format timestamp in ISO 8601 format.
    
    Args:
        timestamp: Optional timestamp to format (defaults to current time)
        
    Returns:
        ISO 8601 formatted timestamp string
    """
    if timestamp is None:
        return datetime.utcnow().isoformat() + "Z"
    return timestamp


def calculate_duration(start_time: Optional[str], end_time: Optional[str]) -> int:
    """
    Calculate duration in seconds between two timestamps.
    
    Args:
        start_time: Start timestamp (ISO format)
        end_time: End timestamp (ISO format)
        
    Returns:
        Duration in seconds
    """
    try:
        if start_time is None or end_time is None:
            return 0
        
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        return int((end_dt - start_dt).total_seconds())
    except (ValueError, TypeError):
        return 0


def validate_file_path(file_path: Path, workspace_path: Path) -> bool:
    """
    Validate that file path is within workspace boundaries.
    
    Args:
        file_path: File path to validate
        workspace_path: Workspace root path
        
    Returns:
        True if path is valid and within workspace, False otherwise
    """
    try:
        # Resolve paths to get absolute paths
        resolved_file = file_path.resolve()
        resolved_workspace = workspace_path.resolve()
        
        # Check if file path is within workspace
        return resolved_workspace in resolved_file.parents or resolved_file == resolved_workspace
    except Exception:
        return False


def ensure_directory(directory: Path) -> bool:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory: Directory path to ensure exists
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def create_backup(
    source_path: Path,
    backup_name: Optional[str] = None,
    include_timestamp: bool = True,
    backup_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Create backup of a file.
    
    Args:
        source_path: Path to source file
        backup_name: Custom backup name (optional)
        include_timestamp: Whether to include timestamp in backup name
        backup_dir: Directory for backups (defaults to source directory)
        
    Returns:
        Path to backup file or None if backup failed
    """
    try:
        if not source_path.exists():
            return None
        
        if backup_dir is None:
            backup_dir = source_path.parent / "backups"
        
        # Ensure backup directory exists
        ensure_directory(backup_dir)
        
        # Generate backup name
        if backup_name:
            backup_filename = backup_name
        else:
            backup_filename = source_path.name
        
        # Only add timestamp if backup_name is not provided
        if include_timestamp and not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = source_path.stem
            suffix = source_path.suffix
            backup_filename = f"{stem}_{timestamp}{suffix}"
        
        backup_path = backup_dir / backup_filename
        
        # Create backup
        shutil.copy2(source_path, backup_path)
        
        logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to create backup for {source_path}: {e}")
        return None


def restore_from_backup(source_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find and return the most recent backup for a source file.
    
    Args:
        source_path: Original file path
        backup_dir: Directory containing backups
        
    Returns:
        Path to most recent backup or None if no backup found
    """
    try:
        if backup_dir is None:
            backup_dir = source_path.parent / "backups"
        
        if not backup_dir.exists():
            return None
        
        # Find backup files matching the source filename pattern
        stem = source_path.stem
        suffix = source_path.suffix
        pattern = f"{stem}_*{suffix}"
        
        backup_files = list(backup_dir.glob(pattern))
        
        if not backup_files:
            return None
        
        # Sort by modification time and return most recent
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return backup_files[0]
        
    except Exception as e:
        logger.error(f"Failed to find backup for {source_path}: {e}")
        return None


def safe_json_load(file_path: Path, encoding: str = "utf-8") -> Optional[Dict[str, Any]]:
    """
    Safely load JSON from file with error handling.
    
    Args:
        file_path: Path to JSON file
        encoding: File encoding
        
    Returns:
        Parsed JSON data or None if failed
    """
    try:
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None


def safe_json_save(data: Dict[str, Any], file_path: Path, encoding: str = "utf-8", indent: int = 2) -> bool:
    """
    Safely save JSON to file with error handling.
    
    Args:
        data: Data to save as JSON
        file_path: Path to save JSON file
        encoding: File encoding
        indent: JSON indentation level
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file first
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        
        with open(temp_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        # Atomic move to final location
        shutil.move(str(temp_path), str(file_path))
        
        logger.info(f"Saved JSON to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        # Clean up temp file if it exists
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        if temp_path.exists():
            temp_path.unlink()
        return False


def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate JSON structure has required keys.
    
    Args:
        data: JSON data to validate
        required_keys: List of required keys
        
    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    if not isinstance(data, dict):
        return False, [f"Data is not a dictionary"]
    
    missing_keys = []
    for key in required_keys:
        if key not in data:
            missing_keys.append(key)
    
    return len(missing_keys) == 0, missing_keys


def generate_file_hash(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Generate hash of file content.
    
    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of file hash or None if failed
    """
    try:
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        return None


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250-len(ext)] + ext
    
    return sanitized


def get_file_size_human(size_bytes: int) -> str:
    """
    Convert file size in bytes to human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string into seconds.
    
    Args:
        duration_str: Duration string (e.g., "30s", "5m", "2h", "1d")
        
    Returns:
        Duration in seconds or None if invalid
    """
    try:
        duration_str = duration_str.lower().strip()
        
        # Extract number and unit
        match = re.match(r'^(\d+(?:\.\d+)?)([smhd])$', duration_str)
        if not match:
            return None
        
        value, unit = match.groups()
        value = float(value)
        
        multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        return int(value * multipliers[unit])
    except Exception:
        return None


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human readable duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        return f"{days}d {remaining_hours}h"


@contextmanager
def file_lock(file_path: Path, timeout: int = 30):
    """
    Context manager for file locking.
    
    Args:
        file_path: Path to file to lock
        timeout: Lock timeout in seconds
    """
    import fcntl
    
    lock_file = file_path.with_suffix(file_path.suffix + ".lock")
    lock_handle = None
    
    try:
        lock_handle = open(lock_file, 'w')
        # Try to acquire lock
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except (IOError, OSError):
        # Lock acquisition failed
        if lock_handle:
            lock_handle.close()
        time.sleep(1)
        timeout -= 1
        if timeout <= 0:
            raise TimeoutError(f"Could not acquire lock for {file_path} within timeout")
        # Retry
        with file_lock(file_path, timeout):
            yield
    finally:
        # Release lock
        try:
            if lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
                lock_handle.close()
                lock_file.unlink(missing_ok=True)
        except (IOError, OSError):
            pass


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL format is valid
    """
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary with updates
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = ".", prefix: str = "") -> Dict[str, str]:
    """
    Flatten nested dictionary.
    
    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        prefix: Prefix for keys
        
    Returns:
        Flattened dictionary
    """
    result = {}
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = str(value)
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying functions on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise e
                    
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
    """
    import logging.config
    
    # Create logs directory if needed
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        },
        "loggers": {
            "mcp_server": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": str(log_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        config["root"]["handlers"].append("file")
        config["loggers"]["mcp_server"]["handlers"].append("file")
    
    logging.config.dictConfig(config)