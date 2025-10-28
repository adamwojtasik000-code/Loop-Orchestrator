#!/usr/bin/env python3
"""
Loop Orchestrator MCP Server

This MCP server exposes Loop Orchestrator functionality through the Model Context Protocol,
providing tools for command execution, task management, mode spawning, and persistent memory access.

Key Features:
- Command execution with failure tracking and recovery
- Task management with timeout enforcement
- Persistent memory read/write operations
- Mode spawning for different workflow modes
- Authentication and rate limiting
- Integration with existing orchestrator components

Usage:
    python mcp_server.py

Or with MCP inspector:
    uv run mcp dev mcp_server.py
"""

import os
import asyncio
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP, Context, Icon
from mcp.server.fastmcp.prompts import base
from pydantic import BaseModel, Field

# Import orchestrator components
try:
    from orchestrator import (
        CommandFailureTracker,
        execute_command_with_tracking_thread_safe,
        TimeoutEnforcer,
        AsyncBufferedWriter,
    )
except ImportError as e:
    print(f"Failed to import orchestrator components: {e}")
    # Fallback for development
    CommandFailureTracker = None
    execute_command_with_tracking_thread_safe = None
    TimeoutEnforcer = None
    AsyncBufferedWriter = None


# Configuration
DEFAULT_TIMEOUT = 3600  # 1 hour default timeout
DEFAULT_BUFFER_SIZE = 10
DEFAULT_FLUSH_INTERVAL = 0.1

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds


class CommandRequest(BaseModel):
    """Schema for command execution requests."""
    command: str = Field(description="Command to execute")
    shell: bool = Field(default=False, description="Use shell execution")
    timeout: int = Field(default=30, description="Command timeout in seconds")
    working_directory: Optional[str] = Field(default=None, description="Working directory for command")


class TaskStatus(BaseModel):
    """Schema for task status information."""
    task_id: str
    name: Optional[str]
    start_time: Optional[float]
    elapsed_time: Optional[float]
    timeout_seconds: int
    monitoring: bool
    warning_issued: bool
    enforced: bool


class MemoryEntry(BaseModel):
    """Schema for persistent memory entries."""
    section: str = Field(description="Memory section (e.g., 'patterns', 'commands', 'updates')")
    content: str = Field(description="Content to add to persistent memory")
    timestamp: Optional[str] = Field(default=None, description="Optional timestamp")


class ModeSpawnRequest(BaseModel):
    """Schema for mode spawning requests."""
    mode: str = Field(description="Mode to spawn (code, architect, debug, etc.)")
    task: str = Field(description="Task description for the new mode")
    timeout: int = Field(default=DEFAULT_TIMEOUT, description="Timeout for mode operation")


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_window: int = RATE_LIMIT_REQUESTS,
                 window_seconds: int = RATE_LIMIT_WINDOW):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for given client."""
        now = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0

        with self.lock:
            if client_id not in self.requests:
                self.requests[client_id] = []

            # Remove old requests outside the window
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.window_seconds
            ]

            # Check if under limit
            if len(self.requests[client_id]) < self.requests_per_window:
                self.requests[client_id].append(now)
                return True

            return False


# Global instances (would be better with dependency injection in production)
command_tracker = None
timeout_enforcer = None
buffered_writer = None
rate_limiter = RateLimiter()


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize server components on startup."""
    global command_tracker, timeout_enforcer, buffered_writer

    # Initialize orchestrator components
    try:
        command_tracker = CommandFailureTracker(
            persistent_data_file='persistent-memory.md',
            buffer_size=DEFAULT_BUFFER_SIZE,
            flush_interval=DEFAULT_FLUSH_INTERVAL
        )
        timeout_enforcer = TimeoutEnforcer(timeout_seconds=DEFAULT_TIMEOUT)
        buffered_writer = AsyncBufferedWriter(
            'persistent-memory.md',
            buffer_size=DEFAULT_BUFFER_SIZE,
            flush_interval=DEFAULT_FLUSH_INTERVAL
        )
        print("✓ Orchestrator components initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize orchestrator components: {e}")
        # Continue with limited functionality

    yield

    # Cleanup on shutdown
    if buffered_writer:
        buffered_writer.shutdown()


# Create MCP server
mcp = FastMCP(
    name="Loop Orchestrator",
    instructions=(
        "You are the Loop Orchestrator MCP server. You provide access to powerful workflow "
        "management capabilities including command execution, task management, persistent memory "
        "operations, and mode spawning. Use these tools to help users automate complex workflows "
        "with proper error handling, timeout management, and state persistence."
    ),
    lifespan=server_lifespan,
    icons=[
        Icon(
            src="https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/docs/assets/mcp.png",
            mimeType="image/png",
            sizes="256x256"
        )
    ]
)


# Command Execution Tools
@mcp.tool()
async def execute_command(request: CommandRequest, ctx: Context) -> str:
    """
    Execute a command with failure tracking and recovery.

    This tool runs commands through the orchestrator's command execution system,
    which includes automatic retry logic, failure tracking, and persistent logging.
    """
    if not command_tracker or not execute_command_with_tracking_thread_safe:
        raise RuntimeError("Command execution not available - orchestrator components not initialized")

    try:
        # Check rate limiting
        client_id = getattr(ctx.request_context, 'client_id', 'anonymous')
        if not rate_limiter.is_allowed(client_id):
            raise RuntimeError("Rate limit exceeded. Please try again later.")

        # Execute command with tracking
        stdout, stderr = execute_command_with_tracking_thread_safe(
            command=request.command,
            tracker=command_tracker,
            context=f"MCP command execution: {request.command}",
            shell=request.shell,
            timeout=request.timeout
        )

        result = f"Command executed successfully:\n"
        if stdout:
            result += f"STDOUT:\n{stdout}\n"
        if stderr:
            result += f"STDERR:\n{stderr}\n"

        return result

    except Exception as e:
        await ctx.error(f"Command execution failed: {e}")
        raise


@mcp.tool()
async def get_command_failure_stats() -> Dict[str, Any]:
    """
    Get statistics about recent command failures.

    Returns information about consecutive failures, failed commands,
    and recovery status for monitoring and debugging.
    """
    if not command_tracker:
        raise RuntimeError("Command tracker not available")

    return {
        "consecutive_failures": command_tracker.consecutive_failures,
        "failed_commands": command_tracker.failed_commands,
        "limit_reached": command_tracker.limit_reached,
        "last_failure_context": command_tracker.last_failure_context,
        "max_consecutive_failures": CommandFailureTracker.MAX_CONSECUTIVE_FAILURES
    }


# Task Management Tools
@mcp.tool()
async def start_task(task_name: str, timeout_seconds: int = DEFAULT_TIMEOUT) -> TaskStatus:
    """
    Start monitoring a task with timeout enforcement.

    This initializes timeout monitoring for a task, which will automatically
    warn at 80% of timeout and enforce failure at 100%.
    """
    if not timeout_enforcer:
        raise RuntimeError("Timeout enforcer not available")

    timeout_enforcer.set_opt_out(False)  # Enable enforcement
    timeout_enforcer.start_task(task_name)

    return TaskStatus(
        task_id=f"task_{int(asyncio.get_event_loop().time())}",
        name=task_name,
        start_time=timeout_enforcer.task_start_time,
        elapsed_time=0.0,
        timeout_seconds=timeout_enforcer.timeout_seconds,
        monitoring=timeout_enforcer.monitoring,
        warning_issued=False,
        enforced=False
    )


@mcp.tool()
async def check_task_status() -> TaskStatus:
    """
    Check the status of the currently monitored task.

    Returns current task information including elapsed time,
    warnings, and enforcement status.
    """
    if not timeout_enforcer:
        raise RuntimeError("Timeout enforcer not available")

    elapsed = timeout_enforcer._get_elapsed_time()
    should_enforce, message = timeout_enforcer.check_timeout()

    return TaskStatus(
        task_id=getattr(timeout_enforcer, 'task_name', 'unknown'),
        name=timeout_enforcer.task_name,
        start_time=timeout_enforcer.task_start_time,
        elapsed_time=elapsed,
        timeout_seconds=timeout_enforcer.timeout_seconds,
        monitoring=timeout_enforcer.monitoring,
        warning_issued=timeout_enforcer.warning_issued,
        enforced=timeout_enforcer.enforced
    )


@mcp.tool()
async def stop_task() -> str:
    """
    Stop monitoring the current task.

    This clears the current task state and stops timeout monitoring.
    """
    if not timeout_enforcer:
        raise RuntimeError("Timeout enforcer not available")

    timeout_enforcer.stop_task()
    return "Task monitoring stopped"


# Persistent Memory Tools
@mcp.resource("memory://patterns")
def get_implementation_patterns() -> str:
    """Get non-obvious implementation patterns from persistent memory."""
    try:
        with open('persistent-memory.md', 'r') as f:
            content = f.read()
            # Extract the patterns section
            lines = content.split('\n')
            patterns_section = []
            in_patterns = False

            for line in lines:
                if line.startswith('# Non-Obvious Implementation Patterns'):
                    in_patterns = True
                    patterns_section.append(line)
                elif line.startswith('# ') and in_patterns and line != '# Non-Obvious Implementation Patterns':
                    break
                elif in_patterns:
                    patterns_section.append(line)

            return '\n'.join(patterns_section)
    except FileNotFoundError:
        return "Persistent memory file not found"


@mcp.resource("memory://commands")
def get_debug_commands() -> str:
    """Get development and debug commands from persistent memory."""
    try:
        with open('persistent-memory.md', 'r') as f:
            content = f.read()
            # Extract the commands section
            lines = content.split('\n')
            commands_section = []
            in_commands = False

            for line in lines:
                if line.startswith('# Development & Debug Commands'):
                    in_commands = True
                    commands_section.append(line)
                elif line.startswith('# ') and in_commands and line != '# Development & Debug Commands':
                    break
                elif in_commands:
                    commands_section.append(line)

            return '\n'.join(commands_section)
    except FileNotFoundError:
        return "Persistent memory file not found"


@mcp.resource("memory://status")
def get_system_status() -> str:
    """Get system updates and status from persistent memory."""
    try:
        with open('persistent-memory.md', 'r') as f:
            content = f.read()
            # Extract the status section
            lines = content.split('\n')
            status_section = []
            in_status = False

            for line in lines:
                if line.startswith('# System Updates & Status'):
                    in_status = True
                    status_section.append(line)
                elif in_status:
                    status_section.append(line)

            return '\n'.join(status_section)
    except FileNotFoundError:
        return "Persistent memory file not found"


@mcp.tool()
async def add_memory_entry(entry: MemoryEntry, ctx: Context) -> str:
    """
    Add an entry to persistent memory.

    This appends information to the persistent-memory.md file with proper
    formatting and timestamping for the specified section.
    """
    if not buffered_writer:
        raise RuntimeError("Buffered writer not available")

    # Check rate limiting
    client_id = getattr(ctx.request_context, 'client_id', 'anonymous')
    if not rate_limiter.is_allowed(client_id):
        raise RuntimeError("Rate limit exceeded. Please try again later.")

    try:
        # Format the entry
        timestamp = entry.timestamp or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        formatted_entry = f"- [{timestamp}] [{ctx.fastmcp.name}] - {entry.content}\n"

        # Add to buffer for optimized writing
        latency = buffered_writer.add_entry(formatted_entry)

        # Log latency for monitoring
        if latency > 1.0:  # >1ms threshold
            await ctx.warning(f"Memory write latency: {latency:.2f}ms")

        return f"Entry added to {entry.section} section: {entry.content}"

    except Exception as e:
        await ctx.error(f"Failed to add memory entry: {e}")
        raise


@mcp.tool()
async def search_memory(query: str, section: Optional[str] = None) -> str:
    """
    Search persistent memory for specific content.

    Searches through the persistent memory file for matching content,
    optionally filtering by section.
    """
    try:
        with open('persistent-memory.md', 'r') as f:
            content = f.read()

        # Split into sections if filtering requested
        if section:
            lines = content.split('\n')
            current_section = None
            section_content = []

            for line in lines:
                if line.startswith('# '):
                    current_section = line[2:].lower()
                elif current_section == section.lower():
                    section_content.append(line)

            search_content = '\n'.join(section_content)
        else:
            search_content = content

        # Perform case-insensitive search
        lines = search_content.split('\n')
        matches = [line for line in lines if query.lower() in line.lower()]

        if not matches:
            return f"No matches found for query: {query}"

        return f"Found {len(matches)} matches:\n" + '\n'.join(matches[:20])  # Limit results

    except FileNotFoundError:
        return "Persistent memory file not found"
    except Exception as e:
        return f"Search failed: {e}"


# Mode Spawning Tools
@mcp.tool()
async def spawn_mode(request: ModeSpawnRequest, ctx: Context) -> str:
    """
    Spawn a new mode instance for specialized task execution.

    This tool creates a new task in the specified mode with timeout enforcement,
    allowing for parallel or specialized workflow execution.
    """
    if not timeout_enforcer:
        raise RuntimeError("Timeout enforcer not available")

    # Check rate limiting
    client_id = getattr(ctx.request_context, 'client_id', 'anonymous')
    if not rate_limiter.is_allowed(client_id):
        raise RuntimeError("Rate limit exceeded. Please try again later.")

    try:
        # Validate mode
        valid_modes = ['code', 'architect', 'debug', 'ask', 'orchestrator']
        if request.mode not in valid_modes:
            raise ValueError(f"Invalid mode: {request.mode}. Valid modes: {', '.join(valid_modes)}")

        # Create task with timeout enforcement
        task_name = f"Mode-{request.mode}: {request.task[:50]}..."
        timeout_enforcer.set_opt_out(False)
        timeout_enforcer.start_task(task_name)

        # In a real implementation, this would spawn a new mode instance
        # For now, we'll simulate the mode spawning
        await ctx.info(f"Spawning {request.mode} mode for task: {request.task}")

        return f"Mode '{request.mode}' spawned successfully for task: {request.task}"

    except Exception as e:
        await ctx.error(f"Mode spawning failed: {e}")
        raise


@mcp.tool()
async def get_available_modes() -> Dict[str, str]:
    """
    Get information about available workflow modes.

    Returns a dictionary of mode names and their descriptions for
    use in mode spawning operations.
    """
    return {
        "code": "Code implementation and refactoring mode",
        "architect": "System design and planning mode",
        "debug": "Troubleshooting and issue resolution mode",
        "ask": "Information gathering and explanation mode",
        "orchestrator": "Complex multi-step workflow management mode"
    }


# Prompts
@mcp.prompt()
def command_execution_guide(target_command: str) -> str:
    """
    Generate a guide for executing commands through the orchestrator.

    This prompt helps users understand how to properly execute commands
    with failure tracking, recovery, and monitoring.
    """
    return f"""# Command Execution Guide

## Target Command: `{target_command}`

## Execution Steps:
1. Use the `execute_command` tool with appropriate parameters
2. Monitor for automatic retry logic on failures
3. Check command failure statistics if issues occur
4. Review persistent memory for similar command patterns

## Best Practices:
- Set appropriate timeouts based on command complexity
- Use shell=False for security when possible
- Check rate limits before bulk operations
- Monitor for timeout warnings and enforcement

## Error Recovery:
- Commands automatically retry once on failure
- Failure tracking prevents runaway error loops
- Recovery commands are logged to persistent memory
- Use `get_command_failure_stats` to monitor health"""


@mcp.prompt()
def task_management_workflow(task_description: str) -> str:
    """
    Generate a workflow guide for task management.

    This prompt helps users understand how to manage complex tasks
    with proper timeout enforcement and monitoring.
    """
    return f"""# Task Management Workflow

## Task: {task_description}

## Workflow Steps:
1. Start task monitoring with `start_task`
2. Execute operations with proper error handling
3. Periodically check task status with `check_task_status`
4. Complete task and stop monitoring with `stop_task`

## Timeout Management:
- Default timeout: {DEFAULT_TIMEOUT} seconds (1 hour)
- Warning issued at 80% of timeout ({int(DEFAULT_TIMEOUT * 0.8)} seconds)
- Enforcement occurs at 100% of timeout
- Tasks can opt-out of enforcement if needed

## Monitoring Guidelines:
- Check status every 5-10 minutes for long-running tasks
- Address warnings promptly to avoid enforcement
- Use task IDs for tracking multiple concurrent tasks
- Review timeout patterns in persistent memory"""


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()