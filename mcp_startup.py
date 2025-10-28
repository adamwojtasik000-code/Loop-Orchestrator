#!/usr/bin/env python3
"""
MCP Server Startup Script

This script handles MCP server initialization and startup for the Loop Orchestrator.
It automatically detects Python version and starts the appropriate server implementation.
"""

import os
import sys
import subprocess
import signal
import time
from typing import Optional


class MCPServerManager:
    """Manages MCP server startup and lifecycle."""

    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.python_version = sys.version_info
        self.is_python_compatible = self.python_version >= (3, 10)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        if self.is_python_compatible:
            try:
                import mcp
                return True
            except ImportError:
                print("MCP SDK not available, falling back to compatibility mode")
                return False
        else:
            # Check for fallback server
            try:
                import mcp_server_fallback
                return True
            except ImportError:
                print("Fallback MCP server not available")
                return False

    def start_server(self, mode: str = "stdio", port: int = 3000, host: str = "localhost") -> bool:
        """
        Start the MCP server.

        Args:
            mode: Server mode ("stdio" or "http")
            port: Port for HTTP mode
            host: Host for HTTP mode

        Returns:
            True if server started successfully
        """
        if not self.check_dependencies():
            print("MCP server dependencies not available")
            return False

        try:
            if mode == "stdio":
                return self._start_stdio_server()
            elif mode == "http":
                return self._start_http_server(port, host)
            else:
                print(f"Unknown server mode: {mode}")
                return False

        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            return False

    def _start_stdio_server(self) -> bool:
        """Start MCP server in stdio mode."""
        if self.is_python_compatible:
            # Try full MCP server
            try:
                cmd = [sys.executable, "mcp_server.py"]
                self.server_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd()
                )
                print("Started full MCP server (stdio mode)")
                return True
            except Exception as e:
                print(f"Full MCP server failed: {e}, trying fallback")

        # Fallback server
        try:
            cmd = [sys.executable, "mcp_server_fallback.py"]
            self.server_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            print("Started fallback MCP server (stdio mode)")
            return True
        except Exception as e:
            print(f"Fallback MCP server failed: {e}")
            return False

    def _start_http_server(self, port: int, host: str) -> bool:
        """Start MCP server in HTTP mode."""
        if not self.is_python_compatible:
            print("HTTP mode requires Python 3.10+")
            return False

        try:
            cmd = [sys.executable, "orchestrator_integration.py", "serve", "--port", str(port), "--host", host]
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            print(f"Started MCP server (HTTP mode on {host}:{port})")
            return True
        except Exception as e:
            print(f"HTTP server failed: {e}")
            return False

    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            try:
                if os.name == 'nt':  # Windows
                    self.server_process.terminate()
                else:
                    self.server_process.send_signal(signal.SIGTERM)
                    time.sleep(0.1)
                    if self.server_process.poll() is None:
                        self.server_process.kill()

                self.server_process.wait(timeout=5)
                print("MCP server stopped")
            except Exception as e:
                print(f"Error stopping MCP server: {e}")
                try:
                    self.server_process.kill()
                except:
                    pass
            finally:
                self.server_process = None

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.server_process is not None and self.server_process.poll() is None

    def get_server_info(self) -> dict:
        """Get information about the server."""
        return {
            "python_version": f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            "python_compatible": self.is_python_compatible,
            "server_running": self.is_running(),
            "server_pid": self.server_process.pid if self.server_process else None,
            "server_mode": "full" if self.is_python_compatible else "fallback"
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server Startup Manager")
    parser.add_argument("--mode", choices=["stdio", "http"], default="stdio",
                       help="Server mode (default: stdio)")
    parser.add_argument("--port", type=int, default=3000,
                       help="Port for HTTP mode (default: 3000)")
    parser.add_argument("--host", default="localhost",
                       help="Host for HTTP mode (default: localhost)")
    parser.add_argument("--info", action="store_true",
                       help="Show server information and exit")

    args = parser.parse_args()

    manager = MCPServerManager()

    if args.info:
        import json
        print(json.dumps(manager.get_server_info(), indent=2))
        return

    try:
        if manager.start_server(args.mode, args.port, args.host):
            print("MCP server started successfully")

            # Keep running until interrupted
            def signal_handler(signum, frame):
                print("\nStopping MCP server...")
                manager.stop_server()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Wait for server to finish
            if manager.server_process:
                manager.server_process.wait()
        else:
            print("Failed to start MCP server")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nStopping MCP server...")
        manager.stop_server()


if __name__ == "__main__":
    main()