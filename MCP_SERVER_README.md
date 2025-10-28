# MCP Server Integration for Loop Orchestrator

This document describes the Model Context Protocol (MCP) server integration for the Loop Orchestrator, enabling external tools and applications to interact with orchestrator functionality.

## Overview

The MCP server provides a standardized interface for external systems to:
- Execute commands with failure tracking and recovery
- Manage tasks with timeout enforcement
- Access persistent memory and system state
- Spawn new workflow modes
- Query system capabilities and status

## Architecture

### Server Implementations

The system supports two MCP server implementations based on Python version compatibility:

1. **Full MCP Server** (`mcp_server.py`): Requires Python 3.10+ and official MCP SDK
2. **Fallback MCP Server** (`mcp_server_fallback.py`): Compatible with Python 3.8+ using custom JSON-RPC implementation

### Automatic Detection

The integration automatically detects the appropriate server implementation:

```bash
# Check server compatibility and status
python mcp_startup.py --info
```

Output:
```json
{
  "python_version": "3.8.0",
  "python_compatible": false,
  "server_running": false,
  "server_pid": null,
  "server_mode": "fallback"
}
```

## Installation and Setup

### Prerequisites

- Python 3.8.0 or higher
- Loop Orchestrator components (orchestrator.py, persistent-memory.md)

### Dependencies

For full MCP server (Python 3.10+):
```bash
pip install mcp
```

For fallback server (Python 3.8+):
- No additional dependencies required (uses standard library + orchestrator components)

## Usage

### Starting the Server

#### Stdio Mode (Recommended for VSCode/Cline integration)

```bash
# Automatic mode detection and startup
python mcp_startup.py

# Or specify mode explicitly
python mcp_startup.py --mode stdio

# Background startup from orchestrator
from orchestrator import start_mcp_server_if_available
process = start_mcp_server_if_available()
```

#### HTTP Mode (Requires Python 3.10+)

```bash
# Start HTTP server on default port 3000
python mcp_startup.py --mode http

# Custom host/port
python mcp_startup.py --mode http --host 0.0.0.0 --port 8080
```

### Available Tools

#### Command Execution
- **execute_command**: Run commands with failure tracking and automatic retry
- **get_command_failure_stats**: Get statistics about recent command failures

#### Task Management
- **start_task**: Start monitoring a task with timeout enforcement
- **check_task_status**: Check the status of currently monitored tasks
- **stop_task**: Stop monitoring the current task

#### Memory Operations
- **add_memory_entry**: Add entries to persistent memory
- **search_memory**: Search persistent memory for content

#### Mode Management
- **spawn_mode**: Spawn new workflow modes (code, architect, debug, etc.)
- **get_available_modes**: List available workflow modes

### Resources

- **memory://patterns**: Non-obvious implementation patterns
- **memory://commands**: Development and debug commands
- **memory://status**: System updates and status information

## API Examples

### Initialize Connection

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

### Execute Command

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "execute_command",
    "arguments": {
      "command": "echo 'Hello from MCP!'",
      "timeout": 30
    }
  }
}
```

### Add Memory Entry

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "add_memory_entry",
    "arguments": {
      "section": "patterns",
      "content": "New pattern discovered: async processing improves performance"
    }
  }
}
```

## Integration with VSCode/Cline

### MCP Configuration

Add to your MCP settings:

```json
{
  "mcpServers": {
    "loop-orchestrator": {
      "command": "python",
      "args": ["/path/to/Loop-Orchestrator-1/mcp_startup.py"],
      "env": {
        "PYTHONPATH": "/path/to/Loop-Orchestrator-1"
      }
    }
  }
}
```

### Available Capabilities

- **Command Execution**: Run system commands with error recovery
- **Task Monitoring**: Track long-running tasks with timeout enforcement
- **Knowledge Base**: Access and update persistent memory
- **Workflow Management**: Spawn specialized workflow modes
- **System Diagnostics**: Get system status and performance metrics

## Error Handling

### Common Error Codes

- `-32601`: Method not found
- `-32000`: Server error (component not available, etc.)
- `-32700`: Parse error (invalid JSON, etc.)

### Rate Limiting

The server implements rate limiting (100 requests/minute by default) to prevent abuse.

### Component Availability

If orchestrator components are not available, tools will return appropriate error messages. The server gracefully degrades functionality when components are missing.

## Security Considerations

- Command execution is sandboxed to prevent system compromise
- Rate limiting prevents DoS attacks
- Input validation prevents injection attacks
- File operations use proper locking for concurrency safety

## Troubleshooting

### Server Won't Start

1. Check Python version: `python --version`
2. Verify dependencies: `python -c "import orchestrator"`
3. Check file permissions on persistent-memory.md

### Commands Fail

1. Verify command syntax and paths
2. Check timeout settings
3. Review command failure statistics: `get_command_failure_stats`

### Memory Operations Fail

1. Ensure persistent-memory.md exists and is writable
2. Check file permissions
3. Verify orchestrator components are initialized

## Development

### Adding New Tools

For full MCP server:
```python
@mcp.tool()
async def new_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    return result
```

For fallback server:
```python
def new_tool(self, param: str) -> Dict[str, Any]:
    """Tool implementation."""
    # Implementation
    return {"result": result}
```

### Testing

```bash
# Test fallback server
python test_mcp_server_fallback.py

# Test integration
python -c "from orchestrator_integration import get_mcp_server; print('Integration OK')"
```

## Version Compatibility

| Python Version | MCP Server | Features |
|----------------|------------|----------|
| 3.8.x | Fallback | Basic tools, stdio transport |
| 3.9.x | Fallback | Basic tools, stdio transport |
| 3.10+ | Full | All features, HTTP transport, advanced MCP features |

## Performance

- **Latency**: <10ms for most operations
- **Concurrency**: Thread-safe operations with proper locking
- **Memory**: Minimal footprint, efficient buffering
- **Rate Limiting**: 100 requests/minute default

## Contributing

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure backward compatibility
5. Test with both server implementations