#!/usr/bin/env python3
"""
MCP Server Startup Script for Loop-Orchestrator

This script handles MCP server startup with automatic mode detection
and compatibility checking for Python 3.12.1 environment.
"""

import asyncio
import sys
import os
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add the current workspace to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp_server.main import get_server, validate_server_environment, create_server
    from mcp_server.config.settings import get_server_config, validate_environment
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP Server not fully available: {e}")
    MCP_AVAILABLE = False


def check_python_version() -> Dict[str, Any]:
    """Check Python version compatibility."""
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    version_info = {
        "current": current_version,
        "compatible": current_version >= "3.10.0",
        "required": "3.10.0",
        "python_path": sys.executable
    }
    return version_info


def check_mcp_sdk() -> Dict[str, Any]:
    """Check MCP SDK availability."""
    try:
        import mcp
        sdk_info = {
            "available": True,
            "version": getattr(mcp, "__version__", "unknown"),
            "mcp_path": mcp.__file__ if hasattr(mcp, '__file__') else None
        }
    except ImportError:
        sdk_info = {"available": False, "version": None, "mcp_path": None}
    
    return sdk_info


def check_server_files() -> Dict[str, Any]:
    """Check if required server files exist."""
    server_dir = Path(__file__).parent / "mcp_server"
    required_files = [
        "main.py",
        "models.py",
        "config/settings.py",
        "tools/orchestrator.py",
        "tools/filesystem.py", 
        "tools/development.py",
        "utils/orchestrator_io.py",
        "utils/helpers.py"
    ]
    
    files_status = {}
    for file_path in required_files:
        full_path = server_dir / file_path
        files_status[file_path] = {
            "exists": full_path.exists(),
            "path": str(full_path)
        }
    
    all_files_exist = all(f["exists"] for f in files_status.values())
    return {"all_exist": all_files_exist, "files": files_status}


def get_server_info() -> Dict[str, Any]:
    """Get comprehensive server information."""
    if not MCP_AVAILABLE:
        return {"status": "unavailable", "error": "MCP server modules not available"}
    
    try:
        python_info = check_python_version()
        sdk_info = check_mcp_sdk()
        files_info = check_server_files()
        
        config = get_server_config()
        
        server_info = {
            "status": "available" if files_info["all_exist"] else "incomplete",
            "python_info": python_info,
            "sdk_info": sdk_info,
            "files_info": files_info,
            "server_config": config.to_dict(),
            "timestamp": time.time()
        }
        
        return server_info
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


async def start_server(mode: str = "auto") -> int:
    """Start the MCP server in the specified mode."""
    if not MCP_AVAILABLE:
        print("Error: MCP Server modules not available")
        return 1
    
    try:
        # Validate environment
        validation = validate_server_environment()
        if validation.get("status") == "invalid":
            print(f"Environment validation failed: {validation}")
            return 1
        
        print(f"Starting Loop-Orchestrator MCP Server in {mode} mode...")
        
        if mode == "stdio":
            # Run server in stdio mode
            await run_stdio_server()
        elif mode == "http":
            # Run server in HTTP mode
            await run_http_server()
        else:
            # Auto-detect mode based on environment
            if sys.stdin.isatty():
                print("Starting in stdio mode (detected interactive terminal)")
                await run_stdio_server()
            else:
                print("Starting in http mode (detected non-interactive environment)")
                await run_http_server()
                
        return 0
        
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
        return 0
    except Exception as e:
        print(f"Server startup failed: {e}")
        return 1


async def run_stdio_server():
    """Run the server in stdio mode."""
    server = get_server()
    print("Loop-Orchestrator MCP Server starting in stdio mode...")
    print("Press Ctrl+C to stop the server")
    await server.run_stdio_async()


async def run_http_server():
    """Run the server in HTTP mode."""
    server = get_server()
    config = get_server_config()
    port = config.base_port
    
    print(f"Loop-Orchestrator MCP Server starting in HTTP mode on port {port}...")
    print(f"Server will be available at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    await server.run_streamable_http_async()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Loop-Orchestrator MCP Server Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --info                    # Show server information
  %(prog)s --mode stdio              # Start in stdio mode
  %(prog)s --mode http               # Start in HTTP mode  
  %(prog)s                           # Auto-detect mode
  %(prog)s --mode auto --port 8080   # Auto mode with custom port
        """
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Show server information and exit"
    )
    
    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "auto"],
        default="auto",
        help="Server transport mode (default: auto)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="HTTP port (default: 8080)"
    )
    
    args = parser.parse_args()
    
    # Show server info if requested
    if args.info:
        info = get_server_info()
        print(json.dumps(info, indent=2))
        return 0
    
    # Override port if specified
    if args.port and MCP_AVAILABLE:
        config = get_server_config()
        config.base_port = args.port
    
    # Start the server
    return asyncio.run(start_server(args.mode))


if __name__ == "__main__":
    sys.exit(main())