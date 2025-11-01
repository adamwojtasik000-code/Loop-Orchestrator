"""
Loop-Orchestrator MCP Server

Main FastMCP server implementation providing orchestrator management, 
file system access, and development tools for the Loop-Orchestrator project.
"""

import logging
import asyncio
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .config.settings import get_server_config, validate_environment
from .config.settings import setup_logging
from .models import SystemStatus, ValidationResult
from .tools.orchestrator import (
    get_schedule_status, manage_schedules, track_task_time, get_time_tracking,
    get_persistent_memory, update_persistent_memory, get_todo_status, delegate_task
)
from .tools.filesystem import (
    read_project_file, write_project_file, list_project_structure,
    search_in_files, backup_file, restore_file
)
from .tools.development import (
    get_system_status as get_comprehensive_system_status,
    switch_mode, run_validation, get_mode_capabilities,
    error_recovery, sync_environment
)
from .utils.helpers import format_timestamp


# Global server instance
_server_instance: Optional[FastMCP] = None
_failure_counter = {}


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server instance.
    
    Returns:
        Configured FastMCP server instance
    """
    config = get_server_config()
    
    # Setup logging
    logger = setup_logging(config)
    
    # Create FastMCP server
    server = FastMCP(
        name=config.name,
        instructions=config.instructions
    )
    
    logger.info(f"Creating Loop-Orchestrator MCP Server v{config.version}")
    
    # Register all tools with proper error handling and logging
    
    # Orchestrator Management Tools
    @server.tool()
    async def get_schedule_status_tool(
        schedule_id: Optional[str] = None,
        include_inactive: bool = False,
        format_output: bool = True
    ) -> Dict[str, Any]:
        """Read and parse .roo/schedules.json to get current schedule status."""
        return await get_schedule_status(schedule_id, include_inactive, format_output)
    
    @server.tool()
    async def manage_schedules_tool(
        action: str,
        schedule_data: Optional[Dict[str, Any]] = None,
        schedule_id: Optional[str] = None,
        update_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create, update, activate/deactivate schedules in .roo/schedules.json."""
        return await manage_schedules(action, schedule_data, schedule_id, update_fields)
    
    @server.tool()
    async def track_task_time_tool(
        task_description: str,
        mode: Optional[str] = None,
        priority: str = "normal",
        start_tracking: bool = True,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start/stop time tracking with proper priority handling."""
        from .models import PriorityType
        priority_enum = PriorityType(priority)
        return await track_task_time(task_description, mode, priority_enum, start_tracking, task_id)
    
    @server.tool()
    async def get_time_tracking_tool(
        filter_mode: Optional[str] = None,
        filter_priority: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read task_timing.tsv with filtering and analysis."""
        from .models import PriorityType
        priority_enum = PriorityType(filter_priority) if filter_priority else None
        return await get_time_tracking(filter_mode, priority_enum, start_date, end_date, limit)
    
    @server.tool()
    async def get_persistent_memory_tool(
        section: Optional[str] = None,
        include_metadata: bool = False,
        search_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read persistent-memory.md with section parsing."""
        from .models import PersistentMemorySection
        section_enum = PersistentMemorySection(section) if section else None
        return await get_persistent_memory(section_enum, include_metadata, search_pattern)
    
    @server.tool()
    async def update_persistent_memory_tool(
        section: str,
        content: str,
        category: Optional[str] = None,
        format_entry: bool = True
    ) -> Dict[str, Any]:
        """Append new entries to persistent-memory.md with proper formatting."""
        from .models import PersistentMemorySection
        section_enum = PersistentMemorySection(section)
        return await update_persistent_memory(section_enum, content, category, format_entry)
    
    @server.tool()
    async def get_todo_status_tool(
        include_completed: bool = False,
        search_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read TODO.md for planning context."""
        return await get_todo_status(include_completed, search_pattern)
    
    @server.tool()
    async def delegate_task_tool(
        task_description: str,
        target_mode: Optional[str] = None,
        priority: str = "normal",
        context: Optional[Dict[str, Any]] = None,
        requirements: Optional[Dict[str, Any]] = None,
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use new_task to delegate to specialized modes."""
        from .models import PriorityType
        priority_enum = PriorityType(priority)
        return await delegate_task(task_description, target_mode, priority_enum, context, requirements, deadline)
    
    # File System Tools
    @server.tool()
    async def read_project_file_tool(
        file_path: str,
        encoding: str = "utf-8",
        max_size_mb: Optional[float] = None,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """Read any file in the Loop-Orchestrator project."""
        return await read_project_file(file_path, encoding, max_size_mb, include_metadata)
    
    @server.tool()
    async def write_project_file_tool(
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_backup: bool = True,
        append: bool = False,
        ensure_directory: bool = True
    ) -> Dict[str, Any]:
        """Write/update project files."""
        return await write_project_file(file_path, content, encoding, create_backup, append, ensure_directory)
    
    @server.tool()
    async def list_project_structure_tool(
        directory: Optional[str] = None,
        recursive: bool = True,
        include_hidden: bool = False,
        include_directories: bool = True,
        include_files: bool = True,
        file_pattern: Optional[str] = None,
        exclude_patterns: Optional[list] = None,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """Recursive directory listing with filtering."""
        return await list_project_structure(
            directory, recursive, include_hidden, include_directories, include_files,
            file_pattern, exclude_patterns, max_depth
        )
    
    @server.tool()
    async def search_in_files_tool(
        pattern: str,
        directory: Optional[str] = None,
        file_pattern: Optional[str] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        max_matches: Optional[int] = None,
        include_line_numbers: bool = True,
        context_lines: int = 0
    ) -> Dict[str, Any]:
        """Regex search across project files."""
        return await search_in_files(
            pattern, directory, file_pattern, case_sensitive, whole_word,
            max_matches, include_line_numbers, context_lines
        )
    
    @server.tool()
    async def backup_file_tool(
        file_path: str,
        backup_name: Optional[str] = None,
        include_timestamp: bool = True,
        backup_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create backups before modifications."""
        return await backup_file(file_path, backup_name, include_timestamp, backup_directory)
    
    @server.tool()
    async def restore_file_tool(
        file_path: str,
        backup_path: Optional[str] = None,
        create_backup_before_restore: bool = True
    ) -> Dict[str, Any]:
        """Restore from backups."""
        return await restore_file(file_path, backup_path, create_backup_before_restore)
    
    # Development Tools
    @server.tool()
    async def get_system_status_tool(
        include_performance: bool = True,
        include_file_health: bool = True,
        include_orchestrator_status: bool = True,
        check_external_dependencies: bool = False
    ) -> Dict[str, Any]:
        """Comprehensive system health check."""
        return await get_comprehensive_system_status(
            include_performance, include_file_health, include_orchestrator_status, check_external_dependencies
        )
    
    @server.tool()
    async def switch_mode_tool(
        target_mode: str,
        task_context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        track_time: bool = True
    ) -> Dict[str, Any]:
        """Coordinate mode transitions with time tracking."""
        from .models import PriorityType
        priority_enum = PriorityType(priority)
        return await switch_mode(target_mode, task_context, priority_enum, track_time)
    
    @server.tool()
    async def run_validation_tool(
        validation_type: str,
        target_path: Optional[str] = None,
        validation_options: Optional[Dict[str, Any]] = None,
        fail_fast: bool = False
    ) -> Dict[str, Any]:
        """Execute validation workflows."""
        return await run_validation(validation_type, target_path, validation_options, fail_fast)
    
    @server.tool()
    async def get_mode_capabilities_tool(
        filter_by_group: Optional[str] = None,
        include_instructions: bool = True
    ) -> Dict[str, Any]:
        """List available modes from .roomodes."""
        return await get_mode_capabilities(filter_by_group, include_instructions)
    
    @server.tool()
    async def error_recovery_tool(
        operation: str,
        error_context: Dict[str, Any],
        recovery_strategy: Optional[str] = None,
        create_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """Handle error scenarios and recovery procedures."""
        return await error_recovery(operation, error_context, recovery_strategy, create_checkpoint)
    
    @server.tool()
    async def sync_environment_tool(
        sync_type: str = "full",
        target_components: Optional[list] = None,
        verify_sync: bool = True
    ) -> Dict[str, Any]:
        """Coordinate environment synchronization."""
        return await sync_environment(sync_type, target_components, verify_sync)
    
    logger.info("Loop-Orchestrator MCP Server created successfully")
    return server


def get_server() -> FastMCP:
    """
    Get the global server instance.
    
    Returns:
        FastMCP server instance
    """
    global _server_instance
    if _server_instance is None:
        _server_instance = create_server()
    return _server_instance


def handle_tool_failure(operation: str, error: Exception) -> Dict[str, Any]:
    """
    Handle tool failures with 3-failure escalation and rollback procedures.
    
    Args:
        operation: Operation that failed
        error: Exception that occurred
        
    Returns:
        Error response with recovery information
    """
    config = get_server_config()
    
    # Track failures
    global _failure_counter
    operation_key = f"{operation}:{type(error).__name__}"
    _failure_counter[operation_key] = _failure_counter.get(operation_key, 0) + 1
    
    failure_count = _failure_counter[operation_key]
    
    # Log to persistent memory
    try:
        from .utils.orchestrator_io import add_persistent_memory_entry
        from .models import PersistentMemorySection
        
        error_entry = f"Tool failure in {operation}: {str(error)} (attempt {failure_count}/{config.command_failure_limit})"
        add_persistent_memory_entry(
            PersistentMemorySection.SYSTEM_UPDATES,
            error_entry,
            "tool_failure"
        )
    except Exception:
        pass  # Don't let logging failures cascade
    
    # Determine if escalation is needed
    should_escalate = failure_count >= config.command_failure_limit
    
    if should_escalate:
        # Reset counter after escalation
        _failure_counter[operation_key] = 0
        
        # Trigger recovery procedure
        try:
            recovery_result = asyncio.run(error_recovery(operation, {"error": str(error)}))
            recovery_info = recovery_result.get("recovery_result", {})
        except Exception:
            recovery_info = {"action": "manual_intervention_required"}
    else:
        recovery_info = {"action": "retry_recommended", "attempts_remaining": config.command_failure_limit - failure_count}
    
    return {
        "success": False,
        "error": str(error),
        "operation": operation,
        "failure_count": failure_count,
        "should_escalate": should_escalate,
        "recovery_info": recovery_info,
        "timestamp": format_timestamp()
    }


def validate_server_environment() -> Dict[str, Any]:
    """
    Validate server environment and configuration.
    
    Returns:
        Validation results
    """
    try:
        config = get_server_config()
        env_validation = validate_environment()
        
        # Run system health check
        server = get_server()
        
        validation_result = {
            "server_config": config.to_dict(),
            "environment_validation": env_validation,
            "validation_timestamp": format_timestamp(),
            "status": "valid" if all(env_validation.values()) else "partial"
        }
        
        return validation_result
        
    except Exception as e:
        return {
            "error": str(e),
            "validation_timestamp": format_timestamp(),
            "status": "invalid"
        }


async def main():
    """
    Main server entry point.
    """
    config = get_server_config()
    
    try:
        # Validate environment
        validation = validate_server_environment()
        if validation.get("status") == "invalid":
            logging.error(f"Server environment validation failed: {validation}")
            sys.exit(1)
        
        # Create server
        server = get_server()
        
        logging.info(f"Starting Loop-Orchestrator MCP Server v{config.version}")
        logging.info(f"Transport: {config.transport}, Port: {config.base_port}")
        
        # Run server based on transport
        if config.transport == "stdio":
            await server.run_stdio_async()
        elif config.transport == "sse":
            await server.run_sse_async()
        elif config.transport == "streamable-http":
            await server.run_streamable_http_async()
        else:
            logging.error(f"Unsupported transport: {config.transport}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Server shutdown requested")
    except Exception as e:
        logging.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())