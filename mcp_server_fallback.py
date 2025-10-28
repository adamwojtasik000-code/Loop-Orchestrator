#!/usr/bin/env python3
"""
MCP Server Fallback Implementation for Python 3.8

This is a minimal MCP server implementation compatible with Python 3.8
that provides basic orchestrator functionality without requiring the
official MCP SDK (which needs Python 3.10+).

Key Features:
- Command execution with failure tracking
- Task management with timeout enforcement
- Basic MCP protocol compatibility
- JSON-RPC 2.0 over stdio transport

Usage:
    python mcp_server_fallback.py
"""

import os
import asyncio
import json
import sys
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import subprocess
import time

# Import orchestrator components
try:
    from orchestrator import (
        CommandFailureTracker,
        TimeoutEnforcer,
        AsyncBufferedWriter,
    )
except ImportError as e:
    print(f"Failed to import orchestrator components: {e}")
    CommandFailureTracker = None
    TimeoutEnforcer = None
    AsyncBufferedWriter = None


class MCPRequest:
    """MCP JSON-RPC request structure."""

    def __init__(self, data: dict):
        self.jsonrpc = data.get("jsonrpc", "2.0")
        self.id = data.get("id")
        self.method = data.get("method")
        self.params = data.get("params", {})

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": self.params
        }


class MCPResponse:
    """MCP JSON-RPC response structure."""

    def __init__(self, result=None, error=None, id=None):
        self.jsonrpc = "2.0"
        self.id = id
        self.result = result
        self.error = error

    def to_dict(self):
        response = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response


class MCPNotification:
    """MCP notification structure."""

    def __init__(self, method: str, params: dict = None):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params or {}

    def to_dict(self):
        return {"jsonrpc": self.jsonrpc, "method": self.method, "params": self.params}


class SimpleRateLimiter:
    """Simple in-memory rate limiter for Python 3.8 compatibility."""

    def __init__(self, requests_per_window: int = 100, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for given client."""
        now = time.time()
        client_id = client_id or "anonymous"

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


class FallbackMCPTools:
    """Fallback MCP tools implementation for Python 3.8."""

    def __init__(self):
        self.command_tracker = None
        self.timeout_enforcer = None
        self.buffered_writer = None
        self.rate_limiter = SimpleRateLimiter()

    def initialize_components(self):
        """Initialize orchestrator components."""
        try:
            self.command_tracker = CommandFailureTracker(
                persistent_data_file='persistent-memory.md',
                buffer_size=10,
                flush_interval=0.1
            )
            self.timeout_enforcer = TimeoutEnforcer(timeout_seconds=3600)
            self.buffered_writer = AsyncBufferedWriter(
                'persistent-memory.md',
                buffer_size=10,
                flush_interval=0.1
            )
            return True
        except Exception as e:
            print(f"Failed to initialize orchestrator components: {e}")
            return False

    def execute_command(self, command: str, shell: bool = False, timeout: int = 30, working_directory: str = None) -> Dict[str, Any]:
        """Execute a command with failure tracking."""
        if not self.command_tracker:
            raise RuntimeError("Command execution not available - orchestrator components not initialized")

        try:
            # Check rate limiting
            if not self.rate_limiter.is_allowed("mcp_client"):
                raise RuntimeError("Rate limit exceeded. Please try again later.")

            # Execute command (simplified for fallback)
            result = subprocess.run(
                command if shell else command.split(),
                shell=shell,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def start_task(self, task_name: str, timeout_seconds: int = 3600) -> Dict[str, Any]:
        """Start monitoring a task."""
        if not self.timeout_enforcer:
            raise RuntimeError("Timeout enforcer not available")

        self.timeout_enforcer.set_opt_out(False)
        self.timeout_enforcer.start_task(task_name)

        return {
            "task_id": f"task_{int(time.time())}",
            "name": task_name,
            "start_time": self.timeout_enforcer.task_start_time,
            "timeout_seconds": timeout_seconds,
            "monitoring": True
        }

    def check_task_status(self) -> Dict[str, Any]:
        """Check current task status."""
        if not self.timeout_enforcer:
            raise RuntimeError("Timeout enforcer not available")

        elapsed = self.timeout_enforcer._get_elapsed_time()
        should_enforce, message = self.timeout_enforcer.check_timeout()

        return {
            "task_name": self.timeout_enforcer.task_name,
            "elapsed_time": elapsed,
            "timeout_seconds": self.timeout_enforcer.timeout_seconds,
            "warning_issued": self.timeout_enforcer.warning_issued,
            "enforced": self.timeout_enforcer.enforced,
            "monitoring": self.timeout_enforcer.monitoring
        }

    def stop_task(self) -> str:
        """Stop monitoring current task."""
        if not self.timeout_enforcer:
            raise RuntimeError("Timeout enforcer not available")

        self.timeout_enforcer.stop_task()
        return "Task monitoring stopped"

    def add_memory_entry(self, section: str, content: str, timestamp: str = None) -> str:
        """Add entry to persistent memory."""
        if not self.buffered_writer:
            raise RuntimeError("Buffered writer not available")

        if not timestamp:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        formatted_entry = f"- [{timestamp}] [Fallback MCP] - {content}\n"

        # Simplified synchronous write for fallback
        try:
            with open('persistent-memory.md', 'a') as f:
                f.write(formatted_entry)
            return f"Entry added to {section} section"
        except Exception as e:
            raise RuntimeError(f"Failed to write to persistent memory: {e}")

    def search_memory(self, query: str, section: str = None) -> Dict[str, Any]:
        """Search persistent memory."""
        try:
            with open('persistent-memory.md', 'r') as f:
                content = f.read()

            if section:
                lines = content.split('\n')
                section_content = []
                in_section = False

                for line in lines:
                    if line.startswith(f'# {section}'):
                        in_section = True
                    elif line.startswith('# ') and in_section:
                        break
                    elif in_section:
                        section_content.append(line)

                search_content = '\n'.join(section_content)
            else:
                search_content = content

            # Case-insensitive search
            lines = search_content.split('\n')
            matches = [line for line in lines if query.lower() in line.lower()]

            return {
                "query": query,
                "matches": matches[:20],  # Limit results
                "total_matches": len(matches)
            }

        except FileNotFoundError:
            return {"error": "Persistent memory file not found"}
        except Exception as e:
            return {"error": str(e)}


class FallbackMCPServer:
    """Fallback MCP server implementation for Python 3.8."""

    def __init__(self):
        self.tools = FallbackMCPTools()
        self.running = False

    def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialize request."""
        return MCPResponse(result={
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "Loop Orchestrator Fallback MCP Server",
                "version": "1.0.0"
            }
        }, id=request.id)

    def handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request."""
        tools = [
            {
                "name": "execute_command",
                "description": "Execute a command with failure tracking and recovery",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "shell": {"type": "boolean", "description": "Use shell execution", "default": False},
                        "timeout": {"type": "integer", "description": "Command timeout in seconds", "default": 30},
                        "working_directory": {"type": "string", "description": "Working directory"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "start_task",
                "description": "Start monitoring a task with timeout enforcement",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_name": {"type": "string", "description": "Name of the task"},
                        "timeout_seconds": {"type": "integer", "description": "Timeout in seconds", "default": 3600}
                    },
                    "required": ["task_name"]
                }
            },
            {
                "name": "check_task_status",
                "description": "Check the status of the currently monitored task",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "stop_task",
                "description": "Stop monitoring the current task",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "add_memory_entry",
                "description": "Add an entry to persistent memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "section": {"type": "string", "description": "Memory section"},
                        "content": {"type": "string", "description": "Content to add"},
                        "timestamp": {"type": "string", "description": "Optional timestamp"}
                    },
                    "required": ["section", "content"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search persistent memory for content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "section": {"type": "string", "description": "Optional section filter"}
                    },
                    "required": ["query"]
                }
            }
        ]

        return MCPResponse(result={"tools": tools}, id=request.id)

    def handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request."""
        try:
            tool_name = request.params.get("name")
            tool_args = request.params.get("arguments", {})

            if tool_name == "execute_command":
                result = self.tools.execute_command(**tool_args)
                return MCPResponse(result=result, id=request.id)

            elif tool_name == "start_task":
                result = self.tools.start_task(**tool_args)
                return MCPResponse(result=result, id=request.id)

            elif tool_name == "check_task_status":
                result = self.tools.check_task_status()
                return MCPResponse(result=result, id=request.id)

            elif tool_name == "stop_task":
                result = self.tools.stop_task()
                return MCPResponse(result=result, id=request.id)

            elif tool_name == "add_memory_entry":
                result = self.tools.add_memory_entry(**tool_args)
                return MCPResponse(result=result, id=request.id)

            elif tool_name == "search_memory":
                result = self.tools.search_memory(**tool_args)
                return MCPResponse(result=result, id=request.id)

            else:
                return MCPResponse(error={
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found"
                }, id=request.id)

        except Exception as e:
            return MCPResponse(error={
                "code": -32000,
                "message": str(e)
            }, id=request.id)

    def handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/list request."""
        resources = [
            {
                "uri": "memory://patterns",
                "name": "Implementation Patterns",
                "description": "Non-obvious implementation patterns from persistent memory",
                "mimeType": "text/markdown"
            },
            {
                "uri": "memory://commands",
                "name": "Debug Commands",
                "description": "Development and debug commands from persistent memory",
                "mimeType": "text/markdown"
            },
            {
                "uri": "memory://status",
                "name": "System Status",
                "description": "System updates and status from persistent memory",
                "mimeType": "text/markdown"
            }
        ]

        return MCPResponse(result={"resources": resources}, id=request.id)

    def handle_resources_read(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/read request."""
        try:
            uri = request.params.get("uri")

            if uri == "memory://patterns":
                with open('persistent-memory.md', 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    patterns_section = []
                    in_patterns = False

                    for line in lines:
                        if line.startswith('# Non-Obvious Implementation Patterns'):
                            in_patterns = True
                            patterns_section.append(line)
                        elif line.startswith('# ') and in_patterns:
                            break
                        elif in_patterns:
                            patterns_section.append(line)

                    content = '\n'.join(patterns_section)

            elif uri == "memory://commands":
                with open('persistent-memory.md', 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    commands_section = []
                    in_commands = False

                    for line in lines:
                        if line.startswith('# Development & Debug Commands'):
                            in_commands = True
                            commands_section.append(line)
                        elif line.startswith('# ') and in_commands:
                            break
                        elif in_commands:
                            commands_section.append(line)

                    content = '\n'.join(commands_section)

            elif uri == "memory://status":
                with open('persistent-memory.md', 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    status_section = []
                    in_status = False

                    for line in lines:
                        if line.startswith('# System Updates & Status'):
                            in_status = True
                            status_section.append(line)
                        elif in_status:
                            status_section.append(line)

                    content = '\n'.join(status_section)

            else:
                return MCPResponse(error={
                    "code": -32000,
                    "message": f"Resource '{uri}' not found"
                }, id=request.id)

            return MCPResponse(result={
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": content
                }]
            }, id=request.id)

        except FileNotFoundError:
            return MCPResponse(error={
                "code": -32000,
                "message": "Persistent memory file not found"
            }, id=request.id)
        except Exception as e:
            return MCPResponse(error={
                "code": -32000,
                "message": str(e)
            }, id=request.id)

    def handle_request(self, request_data) -> Optional[dict]:
        """Handle an MCP request."""
        request = None
        try:
            if not isinstance(request_data, dict):
                raise ValueError("Request must be a JSON object")
            request = MCPRequest(request_data)

            if request.method == "initialize":
                return self.handle_initialize(request).to_dict()

            elif request.method == "tools/list":
                return self.handle_tools_list(request).to_dict()

            elif request.method == "tools/call":
                return self.handle_tools_call(request).to_dict()

            elif request.method == "resources/list":
                return self.handle_resources_list(request).to_dict()

            elif request.method == "resources/read":
                return self.handle_resources_read(request).to_dict()

            else:
                return MCPResponse(error={
                    "code": -32601,
                    "message": f"Method '{request.method}' not found"
                }, id=request.id).to_dict()

        except Exception as e:
            request_id = getattr(request, 'id', None) if request else None
            return MCPResponse(error={
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }, id=request_id).to_dict()

    def run_stdio(self):
        """Run the MCP server using stdio transport."""
        print("Fallback MCP Server starting (Python 3.8 compatible)...", file=sys.stderr)
        print("Ready to handle MCP requests", file=sys.stderr)

        # Initialize components
        if not self.tools.initialize_components():
            print("Warning: Failed to initialize orchestrator components", file=sys.stderr)

        self.running = True

        try:
            while self.running:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request_data = json.loads(line.strip())
                    response = self.handle_request(request_data)

                    if response:
                        # Send response to stdout
                        print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    # Send error response for invalid JSON
                    error_response = MCPResponse(error={
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }).to_dict()
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            print("MCP Server shutting down...", file=sys.stderr)
        except Exception as e:
            print(f"MCP Server error: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    server = FallbackMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()