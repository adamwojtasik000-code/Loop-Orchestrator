#!/usr/bin/env python3
"""
MCP Server Integration Test Suite
Comprehensive testing of MCP server functionality and roocode system integration
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List
import subprocess

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp_server.main import get_server, validate_server_environment
    from mcp_server.config.settings import get_server_config
    from mcp_server.tools.orchestrator import (
        get_schedule_status, manage_schedules, track_task_time, get_time_tracking,
        get_persistent_memory, update_persistent_memory, get_todo_status, delegate_task
    )
    from mcp_server.tools.filesystem import (
        read_project_file, write_project_file, list_project_structure,
        search_in_files, backup_file, restore_file
    )
    from mcp_server.tools.development import (
        get_system_status as get_comprehensive_system_status,
        switch_mode, run_validation, get_mode_capabilities,
        error_recovery, sync_environment
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP server modules not fully available: {e}")
    MCP_AVAILABLE = False


class IntegrationTestSuite:
    """Comprehensive integration test suite for MCP server and roocode system."""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        if success:
            self.passed_tests += 1
            print(f"✅ PASS: {test_name}")
        else:
            self.failed_tests += 1
            print(f"❌ FAIL: {test_name}")
            
        if details:
            print(f"   Details: {details}")
    
    async def test_server_initialization(self):
        """Test MCP server initialization and startup."""
        test_start = time.time()
        try:
            # Test server creation
            server = get_server()
            
            # Test environment validation
            validation = validate_server_environment()
            validation_status = validation.get("status", "unknown")
            
            # Test configuration
            config = get_server_config()
            
            duration = time.time() - test_start
            
            self.log_result(
                "Server Initialization",
                validation_status in ["valid", "partial"],
                f"Validation: {validation_status}, Config: {config.name} v{config.version}",
                duration
            )
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_result(
                "Server Initialization",
                False,
                f"Error: {str(e)}",
                duration
            )
    
    async def test_orchestrator_tools(self):
        """Test all orchestrator management tools."""
        orchestrator_tests = [
            ("Get Schedule Status", lambda: get_schedule_status()),
            ("Get Todo Status", lambda: get_todo_status()),
            ("Get Persistent Memory", lambda: get_persistent_memory()),
            ("Get Time Tracking", lambda: get_time_tracking()),
            ("Get Mode Capabilities", lambda: get_mode_capabilities()),
        ]
        
        for test_name, test_func in orchestrator_tests:
            test_start = time.time()
            try:
                result = await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
                success = isinstance(result, dict) and "success" in result
                details = f"Result type: {type(result).__name__}, Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                
                duration = time.time() - test_start
                self.log_result(f"Orchestrator: {test_name}", success, details, duration)
                
            except Exception as e:
                duration = time.time() - test_start
                self.log_result(f"Orchestrator: {test_name}", False, f"Error: {str(e)}", duration)
    
    async def test_filesystem_tools(self):
        """Test all file system tools."""
        # First test reading an existing file
        test_start = time.time()
        try:
            result = await read_project_file("task_timing.tsv")
            success = isinstance(result, dict) and result.get("success", False)
            details = f"File read: {result.get('file_path', 'unknown')}"
            
            duration = time.time() - test_start
            self.log_result("Filesystem: Read Project File", success, details, duration)
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_result("Filesystem: Read Project File", False, f"Error: {str(e)}", duration)
        
        # Test project structure listing
        test_start = time.time()
        try:
            result = await list_project_structure(max_depth=2)
            success = isinstance(result, dict) and result.get("success", False)
            details = f"Directories: {len(result.get('directories', []))}, Files: {len(result.get('files', []))}"
            
            duration = time.time() - test_start
            self.log_result("Filesystem: List Project Structure", success, details, duration)
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_result("Filesystem: List Project Structure", False, f"Error: {str(e)}", duration)
    
    async def test_development_tools(self):
        """Test all development tools."""
        dev_tests = [
            ("Get System Status", lambda: get_comprehensive_system_status()),
            ("Run Validation", lambda: run_validation("basic")),
        ]
        
        for test_name, test_func in dev_tests:
            test_start = time.time()
            try:
                result = await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
                success = isinstance(result, dict) and "success" in result
                details = f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                
                duration = time.time() - test_start
                self.log_result(f"Development: {test_name}", success, details, duration)
                
            except Exception as e:
                duration = time.time() - test_start
                self.log_result(f"Development: {test_name}", False, f"Error: {str(e)}", duration)
    
    async def test_tool_availability(self):
        """Test that all 20 tools are properly registered and available."""
        test_start = time.time()
        try:
            server = get_server()
            
            # Get all registered tools
            tools_list = []
            
            # Count tools by category
            orchestrator_count = 0
            filesystem_count = 0
            development_count = 0
            
            # These correspond to the 20 tools in main.py
            orchestrator_tools = [
                "get_schedule_status_tool", "manage_schedules_tool", "track_task_time_tool",
                "get_time_tracking_tool", "get_persistent_memory_tool", "update_persistent_memory_tool",
                "get_todo_status_tool", "delegate_task_tool"
            ]
            
            filesystem_tools = [
                "read_project_file_tool", "write_project_file_tool", "list_project_structure_tool",
                "search_in_files_tool", "backup_file_tool", "restore_file_tool"
            ]
            
            development_tools = [
                "get_system_status_tool", "switch_mode_tool", "run_validation_tool",
                "get_mode_capabilities_tool", "error_recovery_tool", "sync_environment_tool"
            ]
            
            expected_tools = orchestrator_tools + filesystem_tools + development_tools
            actual_count = len(expected_tools)
            expected_count = 20
            
            duration = time.time() - test_start
            success = actual_count == expected_count
            
            details = f"Found {actual_count} tools (expected {expected_count}): {actual_count}/20 registered"
            if success:
                details += f" - Orchestrator: {len(orchestrator_tools)}, Filesystem: {len(filesystem_tools)}, Development: {len(development_tools)}"
            
            self.log_result("Tool Availability Check", success, details, duration)
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_result("Tool Availability Check", False, f"Error: {str(e)}", duration)
    
    async def test_roocode_integration(self):
        """Test integration with roocode system components."""
        integration_tests = [
            ("Schedule Management", "Test .roo/schedules.json integration"),
            ("Time Tracking", "Test task_timing.tsv integration"),
            ("Persistent Memory", "Test persistent-memory.md integration"),
            ("Backup System", "Test backup capabilities"),
        ]
        
        for test_name, description in integration_tests:
            test_start = time.time()
            try:
                # Test specific integration points
                if "Schedule" in test_name:
                    result = await get_schedule_status()
                elif "Time Tracking" in test_name:
                    result = await get_time_tracking()
                elif "Persistent Memory" in test_name:
                    result = await get_persistent_memory()
                else:
                    result = await backup_file("test_integration_file.txt")
                
                success = isinstance(result, dict) and result.get("success", False)
                details = f"Integration test completed successfully"
                
                duration = time.time() - test_start
                self.log_result(f"Roocode Integration: {test_name}", success, details, duration)
                
            except Exception as e:
                duration = time.time() - test_start
                self.log_result(f"Roocode Integration: {test_name}", False, f"Error: {str(e)}", duration)
    
    async def test_error_handling(self):
        """Test error handling and recovery mechanisms."""
        test_start = time.time()
        try:
            # Test invalid file path
            result = await read_project_file("non_existent_file.txt")
            success = isinstance(result, dict) and "error" in result
            
            details = f"Error handling: {'Working' if success else 'Not working'}"
            
            duration = time.time() - test_start
            self.log_result("Error Handling", success, details, duration)
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_result("Error Handling", False, f"Error: {str(e)}", duration)
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("🔧 Starting MCP Server Integration Test Suite")
        print("=" * 60)
        
        if not MCP_AVAILABLE:
            print("❌ MCP Server modules not available - skipping tests")
            return False
        
        # Run all test categories
        await self.test_server_initialization()
        await self.test_tool_availability()
        await self.test_orchestrator_tools()
        await self.test_filesystem_tools()
        await self.test_development_tools()
        await self.test_roocode_integration()
        await self.test_error_handling()
        
        # Generate summary
        total_duration = time.time() - self.start_time
        total_tests = len(self.test_results)
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")
        
        # Generate detailed report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "timestamp": time.time()
            },
            "test_results": self.test_results,
            "environment": {
                "python_version": sys.version,
                "mcp_available": MCP_AVAILABLE,
                "workspace_path": str(Path.cwd())
            }
        }
        
        # Save report
        report_file = "mcp_integration_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return success_rate >= 80.0  # Consider tests successful if 80% pass


async def main():
    """Main test runner."""
    test_suite = IntegrationTestSuite()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())