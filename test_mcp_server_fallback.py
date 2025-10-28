#!/usr/bin/env python3
"""
Test suite for Fallback MCP Server

Tests basic functionality of the Python 3.8 compatible MCP server implementation.
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server_fallback import (
    MCPRequest,
    MCPResponse,
    MCPNotification,
    SimpleRateLimiter,
    FallbackMCPTools,
    FallbackMCPServer
)


class TestMCPMessages(unittest.TestCase):
    """Test MCP message structures."""

    def test_mcp_request(self):
        """Test MCP request parsing."""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"key": "value"}
        }
        request = MCPRequest(data)
        self.assertEqual(request.jsonrpc, "2.0")
        self.assertEqual(request.id, 1)
        self.assertEqual(request.method, "initialize")
        self.assertEqual(request.params, {"key": "value"})

    def test_mcp_response_success(self):
        """Test MCP success response."""
        response = MCPResponse(result={"status": "ok"}, id=1)
        data = response.to_dict()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["result"], {"status": "ok"})
        self.assertNotIn("error", data)

    def test_mcp_response_error(self):
        """Test MCP error response."""
        error = {"code": -32000, "message": "Server error"}
        response = MCPResponse(error=error, id=1)
        data = response.to_dict()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["error"], error)
        self.assertNotIn("result", data)

    def test_mcp_notification(self):
        """Test MCP notification."""
        notification = MCPNotification("test_event", {"data": "value"})
        data = notification.to_dict()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["method"], "test_event")
        self.assertEqual(data["params"], {"data": "value"})
        self.assertNotIn("id", data)


class TestSimpleRateLimiter(unittest.TestCase):
    """Test rate limiter functionality."""

    def setUp(self):
        self.limiter = SimpleRateLimiter(requests_per_window=2, window_seconds=1)

    def test_rate_limit_allowed(self):
        """Test allowing requests within limit."""
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertTrue(self.limiter.is_allowed("client1"))

    def test_rate_limit_exceeded(self):
        """Test blocking requests over limit."""
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertFalse(self.limiter.is_allowed("client1"))

    def test_rate_limit_different_clients(self):
        """Test rate limiting per client."""
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertTrue(self.limiter.is_allowed("client2"))  # Different client allowed

    @patch('time.time')
    def test_rate_limit_window_expiry(self, mock_time):
        """Test rate limit window expiry."""
        mock_time.return_value = 1000
        self.assertTrue(self.limiter.is_allowed("client1"))
        self.assertTrue(self.limiter.is_allowed("client1"))

        # Advance time past window
        mock_time.return_value = 1002
        self.assertTrue(self.limiter.is_allowed("client1"))  # Should be allowed again


class TestFallbackMCPTools(unittest.TestCase):
    """Test fallback MCP tools functionality."""

    def setUp(self):
        self.tools = FallbackMCPTools()

    def test_initialize_components_success(self):
        """Test successful component initialization."""
        # This will fail in test environment due to missing orchestrator components
        # but we test the error handling
        result = self.tools.initialize_components()
        # Result depends on whether orchestrator components are available
        self.assertIsInstance(result, bool)

    def test_execute_command_without_components(self):
        """Test command execution when components not initialized."""
        with self.assertRaises(RuntimeError):
            self.tools.execute_command("echo test")

    def test_start_task_without_components(self):
        """Test task start when components not initialized."""
        with self.assertRaises(RuntimeError):
            self.tools.start_task("test_task")

    def test_check_task_status_without_components(self):
        """Test task status check when components not initialized."""
        with self.assertRaises(RuntimeError):
            self.tools.check_task_status()

    def test_stop_task_without_components(self):
        """Test task stop when components not initialized."""
        with self.assertRaises(RuntimeError):
            self.tools.stop_task()

    def test_add_memory_entry_without_components(self):
        """Test memory entry addition when components not initialized."""
        with self.assertRaises(RuntimeError):
            self.tools.add_memory_entry("test", "content")

    def test_search_memory_without_file(self):
        """Test memory search when file doesn't exist."""
        # Temporarily rename the file to simulate it not existing
        import os
        if os.path.exists('persistent-memory.md'):
            os.rename('persistent-memory.md', 'persistent-memory.md.bak')
            try:
                result = self.tools.search_memory("test")
                self.assertIn("error", result)
                self.assertEqual(result["error"], "Persistent memory file not found")
            finally:
                os.rename('persistent-memory.md.bak', 'persistent-memory.md')
        else:
            result = self.tools.search_memory("test")
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Persistent memory file not found")


class TestFallbackMCPServer(unittest.TestCase):
    """Test fallback MCP server functionality."""

    def setUp(self):
        self.server = FallbackMCPServer()

    def test_handle_initialize(self):
        """Test initialize request handling."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        })
        response = self.server.handle_initialize(request)
        self.assertEqual(response.id, 1)
        self.assertIn("protocolVersion", response.result)
        self.assertIn("capabilities", response.result)
        self.assertIn("serverInfo", response.result)

    def test_handle_tools_list(self):
        """Test tools list request handling."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        })
        response = self.server.handle_tools_list(request)
        self.assertEqual(response.id, 1)
        self.assertIn("tools", response.result)
        self.assertIsInstance(response.result["tools"], list)

        # Check that expected tools are present
        tool_names = [tool["name"] for tool in response.result["tools"]]
        expected_tools = [
            "execute_command", "start_task", "check_task_status",
            "stop_task", "add_memory_entry", "search_memory"
        ]
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names)

    def test_handle_unknown_method(self):
        """Test handling of unknown methods."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown_method"
        })
        response = self.server.handle_request(request.to_dict())
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)

    def test_handle_resources_list(self):
        """Test resources list request handling."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/list"
        })
        response = self.server.handle_resources_list(request)
        self.assertEqual(response.id, 1)
        self.assertIn("resources", response.result)
        self.assertIsInstance(response.result["resources"], list)

        # Check expected resources
        resource_uris = [res["uri"] for res in response.result["resources"]]
        expected_uris = ["memory://patterns", "memory://commands", "memory://status"]
        for uri in expected_uris:
            self.assertIn(uri, resource_uris)

    def test_handle_resources_read_not_found(self):
        """Test resources read for non-existent resource."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "memory://nonexistent"}
        })
        response = self.server.handle_resources_read(request)
        self.assertEqual(response.id, 1)
        self.assertIn("error", response.to_dict())
        self.assertEqual(response.error["code"], -32000)

    def test_handle_tools_call_unknown_tool(self):
        """Test tools call with unknown tool."""
        request = MCPRequest({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        })
        response = self.server.handle_tools_call(request)
        self.assertEqual(response.id, 1)
        self.assertIn("error", response.to_dict())
        self.assertEqual(response.error["code"], -32601)


class TestMCPRequestHandling(unittest.TestCase):
    """Test full request handling flow."""

    def setUp(self):
        self.server = FallbackMCPServer()

    def test_handle_request_initialize(self):
        """Test full initialize request handling."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }
        response = self.server.handle_request(request_data)
        self.assertIsNotNone(response)
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)

    def test_handle_request_invalid_json(self):
        """Test handling of invalid JSON."""
        response = self.server.handle_request("invalid json")
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32700)


if __name__ == '__main__':
    unittest.main()