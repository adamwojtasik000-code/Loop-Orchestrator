"""
File System Access Tools

Tools for reading, writing, and managing files in the Loop-Orchestrator project.
"""

import os
import shutil
import glob
import re
import time
import asyncio
import threading
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

from ..models import FileOperationResult
from ..config.settings import get_server_config
from ..utils.helpers import (
    ensure_directory, create_backup, restore_from_backup, validate_file_path,
    format_timestamp, safe_json_load, safe_json_save
)

# Import performance optimizations
try:
    from performance_optimizations import intelligent_cache, algorithm_optimizer
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False
    intelligent_cache = None
    algorithm_optimizer = None


logger = logging.getLogger(__name__)


async def read_project_file(
    file_path: str,
    encoding: str = "utf-8",
    max_size_mb: Optional[float] = None,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Read any file in the Loop-Orchestrator project.
    
    Args:
        file_path: Path to the file (relative to workspace)
        encoding: File encoding (default: utf-8)
        max_size_mb: Maximum file size to read (optional)
        include_metadata: Whether to include file metadata in response
        
    Returns:
        Dictionary containing file content and metadata
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    target_path = workspace_path / file_path
    
    try:
        # Validate file path
        if not validate_file_path(target_path, workspace_path):
            return {
                "success": False,
                "error": f"Invalid file path: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Check if file exists
        if not target_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Check file size
        file_size = target_path.stat().st_size
        if max_size_mb and file_size > max_size_mb * 1024 * 1024:
            return {
                "success": False,
                "error": f"File too large: {file_size} bytes (max: {max_size_mb} MB)",
                "file_path": file_path,
                "file_size": file_size,
                "timestamp": format_timestamp()
            }
        
        # Read file content
        try:
            with open(target_path, 'r', encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(target_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Could not decode file with encoding {encoding}: {str(e)}",
                    "file_path": file_path,
                    "timestamp": format_timestamp()
                }
        
        # Get file metadata
        file_stat = target_path.stat()
        metadata = {}
        if include_metadata:
            metadata = {
                "size": file_size,
                "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "encoding": encoding,
                "is_file": target_path.is_file(),
                "is_directory": target_path.is_dir()
            }
        
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size": file_size,
            "timestamp": format_timestamp(),
            "metadata": metadata if include_metadata else None
        }
        
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": format_timestamp()
        }


async def write_project_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    create_backup: bool = True,
    append: bool = False,
    ensure_directory: bool = True
) -> Dict[str, Any]:
    """
    Write/update project files.
    
    Args:
        file_path: Path to the file (relative to workspace)
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_backup: Whether to create backup before writing
        append: Whether to append to existing file instead of overwriting
        ensure_directory: Whether to create parent directories if they don't exist
        
    Returns:
        Dictionary containing operation result
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    target_path = workspace_path / file_path
    
    try:
        # Validate file path
        if not validate_file_path(target_path, workspace_path):
            return {
                "success": False,
                "error": f"Invalid file path: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Create backup if file exists and backup is requested
        backup_path = None
        if create_backup and target_path.exists():
            backup_path = create_backup(target_path)
        
        # Ensure parent directory exists
        if ensure_directory:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        if append:
            # Append mode
            mode = 'a'
            if not target_path.exists():
                mode = 'w'  # If file doesn't exist, create it
        else:
            mode = 'w'
        
        with open(target_path, mode, encoding=encoding) as f:
            f.write(content)
        
        # Get file size
        file_size = target_path.stat().st_size
        
        return {
            "success": True,
            "file_path": file_path,
            "operation": "append" if append else "write",
            "size": file_size,
            "backup_created": backup_path,
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "backup_created": backup_path,
            "timestamp": format_timestamp()
        }


async def list_project_structure(
    directory: Optional[str] = None,
    recursive: bool = True,
    include_hidden: bool = False,
    include_directories: bool = True,
    include_files: bool = True,
    file_pattern: Optional[str] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_depth: Optional[int] = None
) -> Dict[str, Any]:
    """
    Recursive directory listing with filtering.
    
    Args:
        directory: Directory to list (relative to workspace, default: workspace root)
        recursive: Whether to list recursively
        include_hidden: Whether to include hidden files/directories
        include_directories: Whether to include directories in results
        include_files: Whether to include files in results
        file_pattern: Glob pattern to filter files
        exclude_patterns: List of patterns to exclude
        max_depth: Maximum depth to recurse
        
    Returns:
        Dictionary containing directory structure
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    
    try:
        if directory:
            target_path = workspace_path / directory
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory}",
                    "directory": directory,
                    "timestamp": format_timestamp()
                }
        else:
            target_path = workspace_path
        
        if not target_path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {directory or 'workspace root'}",
                "directory": directory,
                "timestamp": format_timestamp()
            }
        
        # Build directory structure
        structure = {}
        
        def _build_structure(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if max_depth and current_depth >= max_depth:
                return {}
            
            items = {}
            try:
                for item in path.iterdir():
                    # Skip hidden files if not requested
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    # Check exclude patterns
                    if exclude_patterns and any(re.search(pattern, item.name) for pattern in exclude_patterns):
                        continue
                    
                    # Check file pattern
                    if file_pattern and not re.match(file_pattern.replace('*', '.*'), item.name):
                        if item.is_file():
                            continue
                    
                    if item.is_file() and include_files:
                        try:
                            stat = item.stat()
                            items[item.name] = {
                                "type": "file",
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "path": str(item.relative_to(workspace_path))
                            }
                        except OSError:
                            items[item.name] = {
                                "type": "file",
                                "error": "Could not stat file",
                                "path": str(item.relative_to(workspace_path))
                            }
                    
                    elif item.is_dir() and include_directories:
                        if recursive:
                            items[item.name] = {
                                "type": "directory",
                                "children": _build_structure(item, current_depth + 1),
                                "path": str(item.relative_to(workspace_path))
                            }
                        else:
                            items[item.name] = {
                                "type": "directory",
                                "children": {},
                                "path": str(item.relative_to(workspace_path))
                            }
            
            except PermissionError:
                items["_error"] = "Permission denied"
            except OSError as e:
                items["_error"] = f"OS error: {str(e)}"
            
            return items
        
        structure = _build_structure(target_path)
        
        # Count items
        def count_items(items):
            count = 0
            dirs = 0
            files = 0
            for name, item in items.items():
                if name == "_error":
                    continue
                if item["type"] == "file":
                    files += 1
                    count += 1
                elif item["type"] == "directory":
                    dirs += 1
                    count += 1
                    child_count, child_dirs, child_files = count_items(item.get("children", {}))
                    count += child_count
                    dirs += child_dirs
                    files += child_files
            return count, dirs, files
        
        total_count, dir_count, file_count = count_items(structure)
        
        return {
            "success": True,
            "directory": directory or "workspace_root",
            "recursive": recursive,
            "total_items": total_count,
            "directories": dir_count,
            "files": file_count,
            "structure": structure,
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error listing directory structure: {e}")
        return {
            "success": False,
            "error": str(e),
            "directory": directory,
            "timestamp": format_timestamp()
        }


async def search_in_files(
    pattern: str,
    directory: Optional[str] = None,
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_matches: Optional[int] = None,
    include_line_numbers: bool = True,
    context_lines: int = 0
) -> Dict[str, Any]:
    """
    Optimized regex search across project files with intelligent caching and parallel processing.
    
    Args:
        pattern: Regex pattern to search for
        directory: Directory to search in (relative to workspace)
        file_pattern: Glob pattern to filter files (e.g., "*.py", "*.md")
        case_sensitive: Whether search is case sensitive
        whole_word: Whether to match whole words only
        max_matches: Maximum number of matches to return
        include_line_numbers: Whether to include line numbers in results
        context_lines: Number of context lines to include around matches
        
    Returns:
        Dictionary containing search results
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    
    # Performance optimization: Check cache first
    if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and intelligent_cache:
        cache_key = f"search_{hashlib.md5(f'{pattern}{directory}{file_pattern}{case_sensitive}{whole_word}{max_matches}'.encode()).hexdigest()}"
        cached_result = intelligent_cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for search pattern: {pattern}")
            return cached_result
    
    try:
        if directory:
            search_path = workspace_path / directory
            if not search_path.exists():
                return {
                    "success": False,
                    "error": f"Search directory not found: {directory}",
                    "directory": directory,
                    "timestamp": format_timestamp()
                }
        else:
            search_path = workspace_path
        
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        if whole_word:
            pattern = r'\b' + pattern + r'\b'
        
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {
                "success": False,
                "error": f"Invalid regex pattern: {str(e)}",
                "pattern": pattern,
                "timestamp": format_timestamp()
            }
        
        # Performance optimization: Use optimized algorithm if available
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and algorithm_optimizer:
            # Use optimized file search with early termination
            results = algorithm_optimizer.optimize_file_search(
                f"*{file_pattern or '*.py'}",
                str(search_path),
                max_matches or 100
            )
            
            # Extract just the file paths for processing
            files_to_search = [Path(r['file']) for r in results if 'file' in r]
        else:
            # Find files to search
            files_to_search = []
            if file_pattern:
                files_to_search = list(search_path.rglob(file_pattern))
            else:
                # Search all text files
                text_extensions = {'.txt', '.md', '.py', '.json', '.yaml', '.yml', '.tsv', '.csv', '.html', '.css', '.js', '.ts', '.sh', '.bat'}
                for ext in text_extensions:
                    files_to_search.extend(search_path.rglob(f"*{ext}"))
            
            # Filter files by workspace boundary
            files_to_search = [f for f in files_to_search if f.is_file() and validate_file_path(f, workspace_path)]
        
        # Performance optimization: Use thread pool for parallel file processing
        matches = []
        total_matches = 0
        files_searched = 0
        max_workers = min(8, len(files_to_search))  # Limit concurrent workers
        
        def search_file_worker(file_path: Path) -> Tuple[int, List[Dict]]:
            """Worker function for parallel file search."""
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    line_matches = list(regex.finditer(line))
                    if line_matches:
                        for match in line_matches:
                            match_info = {
                                "file": str(file_path.relative_to(workspace_path)),
                                "line_number": line_num if include_line_numbers else None,
                                "match_text": match.group(),
                                "match_start": match.start(),
                                "match_end": match.end(),
                                "line_content": line.rstrip()
                            }
                            
                            # Add context lines
                            if context_lines > 0:
                                start_line = max(0, line_num - 1 - context_lines)
                                end_line = min(len(lines), line_num + context_lines)
                                context = {
                                    "context_start": start_line + 1,
                                    "context_end": end_line,
                                    "context_lines": [lines[i].rstrip() for i in range(start_line, end_line)]
                                }
                                match_info["context"] = context
                            
                            file_matches.append(match_info)
                
                return len(file_matches), file_matches
                
            except Exception as e:
                logger.warning(f"Error searching in file {file_path}: {e}")
                return 0, []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file search tasks
            future_to_file = {executor.submit(search_file_worker, file_path): file_path
                             for file_path in files_to_search}
            
            # Collect results
            for future in future_to_file:
                try:
                    matches_count, file_matches = future.result(timeout=30)  # 30s timeout per file
                    files_searched += 1
                    if file_matches:
                        matches.extend(file_matches)
                        total_matches += matches_count
                        
                        if max_matches and total_matches >= max_matches:
                            break
                            
                except Exception as e:
                    logger.warning(f"Error processing file {future_to_file[future]}: {e}")
                    files_searched += 1
                    continue
        
        result = {
            "success": True,
            "pattern": pattern,
            "directory": directory or "workspace_root",
            "files_searched": files_searched,
            "total_matches": total_matches,
            "matches": matches[:max_matches] if max_matches else matches,
            "search_options": {
                "case_sensitive": case_sensitive,
                "whole_word": whole_word,
                "context_lines": context_lines,
                "file_pattern": file_pattern,
                "optimizations_applied": PERFORMANCE_OPTIMIZATIONS_AVAILABLE
            },
            "timestamp": format_timestamp()
        }
        
        # Performance optimization: Cache the result
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and intelligent_cache and total_matches < 1000:
            intelligent_cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching in files: {e}")
        return {
            "success": False,
            "error": str(e),
            "pattern": pattern,
            "timestamp": format_timestamp()
        }


async def backup_file(
    file_path: str,
    backup_name: Optional[str] = None,
    include_timestamp: bool = True,
    backup_directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create backups before modifications.
    
    Args:
        file_path: Path to file to backup (relative to workspace)
        backup_name: Custom backup name (optional)
        include_timestamp: Whether to include timestamp in backup name
        backup_directory: Custom backup directory (relative to workspace)
        
    Returns:
        Dictionary containing backup result
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    source_path = workspace_path / file_path
    
    try:
        # Validate file path
        if not validate_file_path(source_path, workspace_path):
            return {
                "success": False,
                "error": f"Invalid file path: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Check if source file exists
        if not source_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Create backup
        backup_path = create_backup(
            source_path, 
            backup_name=backup_name,
            include_timestamp=include_timestamp,
            backup_dir=config.get_backups_dir() if backup_directory is None else workspace_path / backup_directory
        )
        
        return {
            "success": True,
            "source_file": file_path,
            "backup_file": str(backup_path.relative_to(workspace_path)),
            "backup_path": str(backup_path),
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error backing up file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": format_timestamp()
        }


async def restore_file(
    file_path: str,
    backup_path: Optional[str] = None,
    create_backup_before_restore: bool = True
) -> Dict[str, Any]:
    """
    Restore from backups.
    
    Args:
        file_path: Path to file to restore (relative to workspace)
        backup_path: Specific backup to restore from (relative to workspace)
        create_backup_before_restore: Whether to backup current file before restore
        
    Returns:
        Dictionary containing restore result
    """
    config = get_server_config()
    workspace_path = config.workspace_path
    target_path = workspace_path / file_path
    
    try:
        # Validate file path
        if not validate_file_path(target_path, workspace_path):
            return {
                "success": False,
                "error": f"Invalid file path: {file_path}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Find backup to restore from
        if backup_path:
            backup_source = workspace_path / backup_path
        else:
            # Find the most recent backup
            backup_source = restore_from_backup(target_path)
        
        if not backup_source or not backup_source.exists():
            return {
                "success": False,
                "error": f"Backup not found: {backup_path or 'auto-detect'}",
                "file_path": file_path,
                "timestamp": format_timestamp()
            }
        
        # Create backup of current file if it exists and requested
        current_backup = None
        if create_backup_before_restore and target_path.exists():
            current_backup = create_backup(target_path)
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Restore file
        shutil.copy2(backup_source, target_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "restored_from": str(backup_source.relative_to(workspace_path)),
            "current_backup_created": str(current_backup.relative_to(workspace_path)) if current_backup else None,
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error restoring file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": format_timestamp()
        }