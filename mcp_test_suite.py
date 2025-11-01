#!/usr/bin/env python3
"""
Loop-Orchestrator MCP Server Test Suite

Comprehensive testing script for all MCP server tools and integration points.
Tests all 20 tools across orchestrator management, file system, and development categories.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add the current workspace to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.main import get_server, validate_server_environment
from mcp_server.config.settings import get_server_config, setup_logging
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


class MCPTestSuite:
    """Comprehensive test suite for MCP server functionality."""
    
    def __init__(self):
        self.config = get_server_config()
        self.logger = setup_logging(self.config)
        self.test_results = []
        self.server = get_server()
        
    def log_test(self, test_name: str, category: str, status: str, details: str = "", duration: float = 0.0):
        """Log test result."""
        result = {
            "test_name": test_name,
            "category": category,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.logger.info(f"{status_emoji} {category}: {test_name} - {status} ({duration:.2f}s)")
        if details:
            self.logger.info(f"   Details: {details}")
    
    async def test_orchestrator_tools(self):
        """Test all 8 orchestrator management tools."""
        self.logger.info("🧪 Testing Orchestrator Management Tools...")
        
        # Test 1: get_schedule_status
        start_time = time.time()
        try:
            result = await get_schedule_status()
            self.log_test("get_schedule_status", "Orchestrator", "PASS", 
                         f"Found {len(result.get('schedules', []))} schedules", time.time() - start_time)
        except Exception as e:
            self.log_test("get_schedule_status", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 2: manage_schedules (create)
        start_time = time.time()
        try:
            test_schedule = {
                "name": "MCP Test Schedule",
                "mode": "implementation-features",
                "taskInstructions": "Testing MCP server integration",
                "active": True
            }
            result = await manage_schedules("create", test_schedule)
            self.log_test("manage_schedules_create", "Orchestrator", "PASS", 
                         f"Created schedule: {result.get('schedule_id', 'N/A')}", time.time() - start_time)
        except Exception as e:
            self.log_test("manage_schedules_create", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 3: track_task_time
        start_time = time.time()
        try:
            result = await track_task_time(
                "Testing MCP tool execution",
                "implementation-features",
                priority="normal",
                start_tracking=True
            )
            self.log_test("track_task_time", "Orchestrator", "PASS", 
                         f"Time tracking started: {result.get('tracking_started', False)}", time.time() - start_time)
        except Exception as e:
            self.log_test("track_task_time", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 4: get_time_tracking
        start_time = time.time()
        try:
            result = await get_time_tracking(limit=5)
            self.log_test("get_time_tracking", "Orchestrator", "PASS", 
                         f"Found {len(result.get('tracking_records', []))} records", time.time() - start_time)
        except Exception as e:
            self.log_test("get_time_tracking", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 5: get_persistent_memory
        start_time = time.time()
        try:
            result = await get_persistent_memory()
            sections_found = len(result.get('sections', {}))
            self.log_test("get_persistent_memory", "Orchestrator", "PASS", 
                         f"Found {sections_found} sections", time.time() - start_time)
        except Exception as e:
            self.log_test("get_persistent_memory", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 6: update_persistent_memory
        start_time = time.time()
        try:
            result = await update_persistent_memory(
                "system_updates",
                "MCP Server Test - Tool validation in progress",
                "test_validation"
            )
            self.log_test("update_persistent_memory", "Orchestrator", "PASS", 
                         f"Entry added at line: {result.get('line_number', 'N/A')}", time.time() - start_time)
        except Exception as e:
            self.log_test("update_persistent_memory", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 7: get_todo_status
        start_time = time.time()
        try:
            result = await get_todo_status()
            todos_found = len(result.get('todos', []))
            self.log_test("get_todo_status", "Orchestrator", "PASS", 
                         f"Found {todos_found} TODO items", time.time() - start_time)
        except Exception as e:
            self.log_test("get_todo_status", "Orchestrator", "FAIL", str(e), time.time() - start_time)
        
        # Test 8: delegate_task
        start_time = time.time()
        try:
            result = await delegate_task(
                "Test MCP tool validation",
                "implementation-features"
            )
            self.log_test("delegate_task", "Orchestrator", "PASS", 
                         f"Delegated to mode: {result.get('mode', 'N/A')}", time.time() - start_time)
        except Exception as e:
            self.log_test("delegate_task", "Orchestrator", "FAIL", str(e), time.time() - start_time)
    
    async def test_filesystem_tools(self):
        """Test all 6 file system tools."""
        self.logger.info("🧪 Testing File System Tools...")
        
        # Test 9: read_project_file
        start_time = time.time()
        try:
            result = await read_project_file("README.md")
            self.log_test("read_project_file", "File System", "PASS", 
                         f"Read {len(result.get('content', ''))} characters", time.time() - start_time)
        except Exception as e:
            self.log_test("read_project_file", "File System", "FAIL", str(e), time.time() - start_time)
        
        # Test 10: list_project_structure
        start_time = time.time()
        try:
            result = await list_project_structure(directory="mcp_server", max_depth=2)
            items_found = len(result.get('items', []))
            self.log_test("list_project_structure", "File System", "PASS", 
                         f"Found {items_found} items", time.time() - start_time)
        except Exception as e:
            self.log_test("list_project_structure", "File System", "FAIL", str(e), time.time() - start_time)
        
        # Test 11: search_in_files
        start_time = time.time()
        try:
            result = await search_in_files(
                pattern="MCP",
                directory="mcp_server",
                file_pattern="*.py",
                max_matches=5
            )
            matches_found = len(result.get('matches', []))
            self.log_test("search_in_files", "File System", "PASS", 
                         f"Found {matches_found} matches", time.time() - start_time)
        except Exception as e:
            self.log_test("search_in_files", "File System", "FAIL", str(e), time.time() - start_time)
        
        # Test 12: write_project_file
        start_time = time.time()
        try:
            test_content = f"# MCP Test File\nCreated at {time.time()}\n"
            result = await write_project_file(
                "mcp_test_file.txt",
                test_content,
                create_backup=False
            )
            self.log_test("write_project_file", "File System", "PASS", 
                         f"File written: {result.get('success', False)}", time.time() - start_time)
        except Exception as e:
            self.log_test("write_project_file", "File System", "FAIL", str(e), time.time() - start_time)
        
        # Test 13: backup_file
        start_time = time.time()
        try:
            result = await backup_file("mcp_test_file.txt", include_timestamp=True)
            backup_created = result.get('success', False)
            self.log_test("backup_file", "File System", "PASS", 
                         f"Backup created: {backup_created}", time.time() - start_time)
        except Exception as e:
            self.log_test("backup_file", "File System", "FAIL", str(e), time.time() - start_time)
        
        # Test 14: restore_file
        start_time = time.time()
        try:
            result = await restore_file("mcp_test_file.txt")
            self.log_test("restore_file", "File System", "PASS", 
                         f"Restore successful: {result.get('success', False)}", time.time() - start_time)
        except Exception as e:
            self.log_test("restore_file", "File System", "FAIL", str(e), time.time() - start_time)
    
    async def test_development_tools(self):
        """Test all 6 development tools."""
        self.logger.info("🧪 Testing Development Tools...")
        
        # Test 15: get_system_status
        start_time = time.time()
        try:
            result = await get_comprehensive_system_status()
            self.log_test("get_system_status", "Development", "PASS", 
                         f"Status: {result.get('overall_status', 'unknown')}", time.time() - start_time)
        except Exception as e:
            self.log_test("get_system_status", "Development", "FAIL", str(e), time.time() - start_time)
        
        # Test 16: get_mode_capabilities
        start_time = time.time()
        try:
            result = await get_mode_capabilities()
            modes_found = len(result.get('modes', []))
            self.log_test("get_mode_capabilities", "Development", "PASS", 
                         f"Found {modes_found} modes", time.time() - start_time)
        except Exception as e:
            self.log_test("get_mode_capabilities", "Development", "FAIL", str(e), time.time() - start_time)
        
        # Test 17: switch_mode
        start_time = time.time()
        try:
            result = await switch_mode("implementation-features")
            self.log_test("switch_mode", "Development", "PASS", 
                         f"Mode switched to: {result.get('mode', 'N/A')}", time.time() - start_time)
        except Exception as e:
            self.log_test("switch_mode", "Development", "FAIL", str(e), time.time() - start_time)
        
        # Test 18: run_validation
        start_time = time.time()
        try:
            result = await run_validation("syntax", target_path="mcp_server")
            validation_passed = result.get('validation_passed', False)
            self.log_test("run_validation", "Development", "PASS", 
                         f"Validation passed: {validation_passed}", time.time() - start_time)
        except Exception as e:
            self.log_test("run_validation", "Development", "FAIL", str(e), time.time() - start_time)
        
        # Test 19: error_recovery
        start_time = time.time()
        try:
            test_error = {"error": "test_error", "operation": "test_operation"}
            result = await error_recovery("test_operation", test_error)
            self.log_test("error_recovery", "Development", "PASS", 
                         f"Recovery action: {result.get('recovery_action', 'none')}", time.time() - start_time)
        except Exception as e:
            self.log_test("error_recovery", "Development", "FAIL", str(e), time.time() - start_time)
        
        # Test 20: sync_environment
        start_time = time.time()
        try:
            result = await sync_environment("files")
            self.log_test("sync_environment", "Development", "PASS", 
                         f"Sync completed: {result.get('sync_completed', False)}", time.time() - start_time)
        except Exception as e:
            self.log_test("sync_environment", "Development", "FAIL", str(e), time.time() - start_time)
    
    async def test_integration_points(self):
        """Test integration with Loop-Orchestrator files."""
        self.logger.info("🧪 Testing Integration Points...")
        
        # Test Loop-Orchestrator file access
        integration_tests = [
            (".roo/schedules.json", "schedules"),
            ("task_timing.tsv", "time tracking"),
            ("persistent-memory.md", "persistent memory"),
            ("TODO.md", "todo"),
            ("mcp_server", "server files")
        ]
        
        for file_path, description in integration_tests:
            start_time = time.time()
            try:
                if Path(file_path).is_dir():
                    result = await list_project_structure(directory=file_path, max_depth=1)
                    item_count = len(result.get('items', []))
                    self.log_test(f"integrate_{description.replace(' ', '_')}", "Integration", "PASS", 
                                 f"Accessed {item_count} items", time.time() - start_time)
                else:
                    result = await read_project_file(file_path)
                    content_size = len(result.get('content', ''))
                    self.log_test(f"integrate_{description.replace(' ', '_')}", "Integration", "PASS", 
                                 f"Read {content_size} characters", time.time() - start_time)
            except Exception as e:
                self.log_test(f"integrate_{description.replace(' ', '_')}", "Integration", "FAIL", 
                             str(e), time.time() - start_time)
    
    async def test_error_handling(self):
        """Test error handling and recovery procedures."""
        self.logger.info("🧪 Testing Error Handling...")
        
        error_tests = [
            ("Invalid file path", lambda: read_project_file("nonexistent_file.txt")),
            ("Invalid schedule ID", lambda: get_schedule_status("invalid_id")),
            ("Invalid validation type", lambda: run_validation("invalid_type")),
        ]
        
        for test_name, test_func in error_tests:
            start_time = time.time()
            try:
                await test_func()
                self.log_test(test_name, "Error Handling", "FAIL", 
                             "Expected error but none occurred", time.time() - start_time)
            except Exception as e:
                error_caught = "error" in str(e).lower() or "not found" in str(e).lower()
                status = "PASS" if error_caught else "PARTIAL"
                self.log_test(test_name, "Error Handling", status, 
                             f"Error handled: {type(e).__name__}", time.time() - start_time)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"PASS": 0, "FAIL": 0, "PARTIAL": 0, "tests": []}
            categories[category][result["status"]] += 1
            categories[category]["tests"].append(result)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "partial_tests": partial_tests,
                "success_rate": f"{success_rate:.1f}%",
                "timestamp": time.time()
            },
            "categories": categories,
            "detailed_results": self.test_results,
            "server_config": self.config.to_dict()
        }
        
        return report
    
    async def run_all_tests(self):
        """Run complete test suite."""
        self.logger.info("🚀 Starting MCP Server Test Suite...")
        
        start_time = time.time()
        
        # Validate environment first
        validation = validate_server_environment()
        if validation.get("status") == "invalid":
            self.logger.error("❌ Environment validation failed")
            return False
        
        # Run all test categories
        await self.test_orchestrator_tools()
        await self.test_filesystem_tools()
        await self.test_development_tools()
        await self.test_integration_points()
        await self.test_error_handling()
        
        total_duration = time.time() - start_time
        self.logger.info(f"🏁 Test Suite Completed in {total_duration:.2f}s")
        
        # Generate and save report
        report = self.generate_report()
        return report


async def main():
    """Main test execution."""
    test_suite = MCPTestSuite()
    report = await test_suite.run_all_tests()
    
    # Save report to file
    report_file = Path("mcp_test_results.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Test Report Summary:")
    print(f"   Total Tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed_tests']}")
    print(f"   Failed: {report['summary']['failed_tests']}")
    print(f"   Partial: {report['summary']['partial_tests']}")
    print(f"   Success Rate: {report['summary']['success_rate']}")
    print(f"\n📁 Detailed report saved to: {report_file}")
    
    return report['summary']['failed_tests'] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)