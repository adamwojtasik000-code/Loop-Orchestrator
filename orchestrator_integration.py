#!/usr/bin/env python3
"""
Orchestrator MCP Server Integration Module

This module provides integration between the Loop Orchestrator and MCP server,
enabling external systems to interact with orchestrator functionality.

Usage:
    from orchestrator_integration import get_mcp_server
    server = get_mcp_server()
    server.run_stdio()
"""

import os
import sys
import subprocess
from typing import Optional

# Try to import the full MCP server, fall back to fallback if needed
try:
    from mcp_server import mcp
    FULL_MCP_AVAILABLE = True
except ImportError:
    FULL_MCP_AVAILABLE = False
    try:
        from mcp_server_fallback import FallbackMCPServer
    except ImportError:
        FallbackMCPServer = None


def check_python_version_for_mcp() -> bool:
    """Check if Python version supports full MCP SDK."""
    return sys.version_info >= (3, 10)


def get_mcp_server():
    """
    Get the appropriate MCP server instance based on Python version and availability.

    Returns the full MCP server if Python 3.10+ and SDK available,
    otherwise returns the fallback server for Python 3.8 compatibility.
    """
    if FULL_MCP_AVAILABLE and check_python_version_for_mcp():
        print("Using full MCP server with official SDK", file=sys.stderr)
        return mcp
    elif FallbackMCPServer:
        print("Using fallback MCP server (Python 3.8 compatible)", file=sys.stderr)
        return FallbackMCPServer()
    else:
        raise RuntimeError("No MCP server implementation available")


def start_mcp_server_background(port: int = 3000, host: str = "localhost") -> subprocess.Popen:
    """
    Start MCP server in background process.

    Args:
        port: Port to run the server on
        host: Host to bind to

    Returns:
        subprocess.Popen: Background process handle
    """
    cmd = [sys.executable, __file__, "serve", "--port", str(port), "--host", host]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )


def serve_mcp_server(port: int = 3000, host: str = "localhost"):
    """
    Serve MCP server with HTTP transport (if full SDK available).

    Args:
        port: Port to serve on
        host: Host to bind to
    """
    if FULL_MCP_AVAILABLE and check_python_version_for_mcp():
        # Use the full MCP SDK server
        import uvicorn
        from mcp_server import mcp

        print(f"Starting MCP server on {host}:{port}", file=sys.stderr)
        uvicorn.run(mcp, host=host, port=port)
    else:
        print("HTTP server mode not available with fallback implementation", file=sys.stderr)
        print("Use stdio mode instead: python orchestrator_integration.py", file=sys.stderr)


def main():
    """Main entry point for MCP server."""
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # HTTP server mode
        port = 3000
        host = "localhost"

        # Parse arguments
        if "--port" in sys.argv:
            port_idx = sys.argv.index("--port")
            if port_idx + 1 < len(sys.argv):
                port = int(sys.argv[port_idx + 1])

        if "--host" in sys.argv:
            host_idx = sys.argv.index("--host")
            if host_idx + 1 < len(sys.argv):
                host = sys.argv[host_idx + 1]

        serve_mcp_server(port=port, host=host)
    else:
        # Stdio mode (default)
        server = get_mcp_server()
        if hasattr(server, 'run_stdio'):
            server.run_stdio()
        else:
            # Full MCP server uses different interface
            import asyncio
            asyncio.run(server.run())


if __name__ == "__main__":
    main()