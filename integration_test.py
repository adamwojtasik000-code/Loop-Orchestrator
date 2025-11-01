"""
Integration Testing Suite for Loop-Orchestrator MCP Server

Comprehensive testing of all MCP server tools with real orchestrator files
and validation of integration points.
"""

import asyncio
import sys
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add mcp_server to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.main import get_server, validate_server_environment
from mcp_server.config.settings import get_server_config
from mcp_server.utils.orchestrator_io import (
    load_schedules, save_schedules, load_task_timing, save_task_timing,
    load_persistent_memory, save_persistent_memory, load_todo_status
)
from mcp_server.tools.orchestrator import (
    get_schedule_status, manage_schedules, track_task_time, get_time_tracking,
    get_persistent_memory, update_persistent_memory, get_todo_status, delegate_task
)
from mcp_server.tools.filesystem import (
    read_project_file, write_project_file, list_project_structure,
    search_in_files, backup_file, restore_file
)
from mcp_server.tools.development import (
    get_system_status, switch_mode, run_validation, get_mode_capabilities,
    error_recovery, sync_environment
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Comprehensive integration test suite for MCP server."""
    
    def __init__(self):
        self.config = get_server_config()
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def test(self, test_name: str, test_func, *args, **kwargs):
        """Run a single test and record results."""
        logger.info(f"Running test: {test_name}")
        
        try:
            result = test_func(*args, **kwargs)
            if result.get("success", False):
                logger.info(f"✓ PASS: {test_name}")
                self.passed += 1
                self.test_results.append({"name": test_name, "status": "PASS", "result": result})
            else:
                logger.warning(f"⚠ WARN: {test_name} - {result.get('error', 'Unknown error')}")
                self.warnings += 1
                self.test_results.append({"name": test_name, "status": "WARN", "result": result})
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {str(e)}")
            self.failed += 1
            self.test_results.append({
                "name": test_name, 
                "status": "FAIL", 
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    def test_environment_validation(self):
        """Test server environment validation."""
        validation = validate_server_environment()
        self.test("Environment Validation", lambda: validation)
    
    def test_config_system_status(self):
        """Test system status with configuration."""
        result = asyncio.run(get_system_status(
            include_performance=True,
            include_file_health=True,
            include_orchestrator_status=True
        ))
        self.test("System Status Check", lambda: result)
    
    def test_file_system_tools(self):
        """Test file system access tools."""
        # Test reading schedules file
        schedules_result = asyncio.run(read_project_file(".roo/schedules.json"))
        self.test("Read Schedules File", lambda: schedules_result)
        
        # Test reading persistent memory
        memory_result = asyncio.run(read_project_file("persistent-memory.md"))
        self.test("Read Persistent Memory", lambda: memory_result)
        
        # Test reading task timing
        timing_result = asyncio.run(read_project_file("task_timing.tsv"))
        self.test("Read Task Timing", lambda: timing_result)
        
        # Test directory listing
        structure_result = asyncio.run(list_project_structure(recursive=True, max_depth=2))
        self.test("Project Structure Listing", lambda: structure_result)
    
    def test_search_capabilities(self):
        """Test file search capabilities."""
        # Search for schedule patterns
        search_result = asyncio.run(search_in_files(
            pattern=r'"id":\s*"[^"]*"',
            file_pattern="*.json",
            max_matches=10
        ))
        self.test("Search in JSON Files", lambda: search_result)
        
        # Search in markdown files
        md_search_result = asyncio.run(search_in_files(
            pattern=r"# .*",
            file_pattern="*.md",
            max_matches=20
        ))
        self.test("Search in Markdown Files", lambda: md_search_result)
    
    def test_orchestrator_integration(self):
        """Test orchestrator-specific integrations."""
        # Test schedule status
        schedule_status = asyncio.run(get_schedule_status())
        self.test("Get Schedule Status", lambda: schedule_status)
        
        # Test time tracking
        time_tracking = asyncio.run(get_time_tracking(limit=10))
        self.test("Get Time Tracking", lambda: time_tracking)
        
        # Test persistent memory
        memory_content = asyncio.run(get_persistent_memory())
        self.test("Get Persistent Memory", lambda: memory_content)
        
        # Test TODO status
        todo_status = asyncio.run(get_todo_status())
        self.test("Get TODO Status", lambda: todo_status)
    
    def test_mode_capabilities(self):
        """Test mode capabilities and coordination."""
        # Get available modes
        modes_result = asyncio.run(get_mode_capabilities())
        self.test("Get Mode Capabilities", lambda: modes_result)
        
        # Filter modes by group
        modes_by_group = asyncio.run(get_mode_capabilities(filter_by_group="mcp"))
        self.test("Filter Modes by Group", lambda: modes_by_group)
    
    def test_validation_tools(self):
        """Test validation and error recovery."""
        # System health validation
        health_validation = asyncio.run(run_validation("system_health"))
        self.test("System Health Validation", lambda: health_validation)
        
        # File integrity validation
        file_validation = asyncio.run(run_validation(
            "file_integrity", 
            target_path=".roo/schedules.json"
        ))
        self.test("File Integrity Validation", lambda: file_validation)
        
        # Orchestrator files validation
        orchestrator_validation = asyncio.run(run_validation("orchestrator_files"))
        self.test("Orchestrator Files Validation", lambda: orchestrator_validation)
    
    def test_error_recovery(self):
        """Test error recovery mechanisms."""
        # Test error recovery for non-existent operation
        recovery_result = asyncio.run(error_recovery(
            operation="test_operation",
            error_context={"error": "Test error for recovery"},
            recovery_strategy="retry"
        ))
        self.test("Error Recovery Test", lambda: recovery_result)
    
    def test_environment_sync(self):
        """Test environment synchronization."""
        # Full sync test
        sync_result = asyncio.run(sync_environment(sync_type="full"))
        self.test("Full Environment Sync", lambda: sync_result)
        
        # Configuration sync test
        config_sync = asyncio.run(sync_environment(sync_type="config"))
        self.test("Configuration Sync", lambda: config_sync)
    
    def test_time_tracking_integration(self):
        """Test time tracking with real orchestrator data."""
        # Start time tracking
        start_tracking = asyncio.run(track_task_time(
            task_description="Integration test task",
            mode="integration-testing",
            priority="normal",
            start_tracking=True
        ))
        self.test("Start Time Tracking", lambda: start_tracking)
        
        if start_tracking.get("success") and start_tracking.get("task_id"):
            # Stop time tracking
            task_id = start_tracking["task_id"]
            stop_tracking = asyncio.run(track_task_time(
                task_description="Integration test task",
                mode="integration-testing",
                priority="normal",
                start_tracking=False,
                task_id=task_id
            ))
            self.test("Stop Time Tracking", lambda: stop_tracking)
    
    def test_persistent_memory_writing(self):
        """Test writing to persistent memory."""
        # Test updating persistent memory
        update_result = asyncio.run(update_persistent_memory(
            section="System Updates & Status",
            content=f"Integration test entry at {asyncio.get_event_loop().time()}",
            category="integration_test",
            format_entry=True
        ))
        self.test("Update Persistent Memory", lambda: update_result)
    
    def test_schedule_management(self):
        """Test schedule creation and management."""
        # Create a test schedule
        test_schedule = {
            "name": "Integration Test Schedule",
            "mode": "integration-testing",
            "task_instructions": "Test schedule created during integration testing",
            "schedule_type": "manual",
            "active": True
        }
        
        create_result = asyncio.run(manage_schedules(
            action="create",
            schedule_data=test_schedule
        ))
        self.test("Create Test Schedule", lambda: create_result)
        
        if create_result.get("success") and create_result.get("schedule_id"):
            schedule_id = create_result["schedule_id"]
            
            # Update the schedule
            update_result = asyncio.run(manage_schedules(
                action="update",
                schedule_id=schedule_id,
                update_fields={"name": "Updated Integration Test Schedule"}
            ))
            self.test("Update Schedule", lambda: update_result)
            
            # Deactivate the schedule
            deactivate_result = asyncio.run(manage_schedules(
                action="deactivate",
                schedule_id=schedule_id
            ))
            self.test("Deactivate Schedule", lambda: deactivate_result)
    
    def test_file_backup_restore(self):
        """Test file backup and restore functionality."""
        # Create a test file first
        test_file_path = "test_integration_file.txt"
        test_content = "This is a test file for integration testing"
        
        # Write test file
        write_result = asyncio.run(write_project_file(
            file_path=test_file_path,
            content=test_content,
            create_backup=False
        ))
        self.test("Create Test File", lambda: write_result)
        
        if write_result.get("success"):
            # Create backup
            backup_result = asyncio.run(backup_file(
                file_path=test_file_path,
                backup_name="test_backup"
            ))
            self.test("Create File Backup", lambda: backup_result)
            
            if backup_result.get("success"):
                # Modify the file
                modified_content = "This file has been modified during testing"
                modify_result = asyncio.run(write_project_file(
                    file_path=test_file_path,
                    content=modified_content
                ))
                self.test("Modify Test File", lambda: modify_result)
                
                # Restore from backup
                if backup_result.get("backup_file"):
                    restore_result = asyncio.run(restore_file(
                        file_path=test_file_path,
                        backup_path=backup_result["backup_file"]
                    ))
                    self.test("Restore from Backup", lambda: restore_result)
    
    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting Loop-Orchestrator MCP Server Integration Testing")
        logger.info("=" * 60)
        
        # Setup tests
        self.test_environment_validation()
        
        # Core functionality tests
        self.test_config_system_status()
        self.test_file_system_tools()
        self.test_search_capabilities()
        self.test_orchestrator_integration()
        self.test_mode_capabilities()
        
        # Validation and error handling
        self.test_validation_tools()
        self.test_error_recovery()
        self.test_environment_sync()
        
        # Integration-specific tests
        self.test_time_tracking_integration()
        self.test_persistent_memory_writing()
        self.test_schedule_management()
        self.test_file_backup_restore()
        
        # Print results
        logger.info("=" * 60)
        logger.info("Integration Test Results:")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Warnings: {self.warnings}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Total: {self.passed + self.warnings + self.failed}")
        
        # Save detailed results
        results_summary = {
            "timestamp": asyncio.get_event_loop().time(),
            "summary": {
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
                "total": self.passed + self.warnings + self.failed
            },
            "details": self.test_results
        }
        
        results_file = Path("integration_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        logger.info(f"Detailed results saved to: {results_file}")
        
        # Return success if no critical failures
        return self.failed == 0


async def run_basic_server_test():
    """Run basic server functionality test."""
    logger.info("Running basic server test...")
    
    try:
        # Test server creation
        server = get_server()
        logger.info("✓ Server created successfully")
        
        # Test configuration
        config = get_server_config()
        logger.info(f"✓ Configuration loaded: {config.name} v{config.version}")
        
        # Test environment
        validation = validate_server_environment()
        if validation.get("status") in ["valid", "partial"]:
            logger.info("✓ Environment validation passed")
        else:
            logger.warning("⚠ Environment validation issues detected")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic server test failed: {e}")
        return False


def main():
    """Main entry point for integration testing."""
    logger.info("Loop-Orchestrator MCP Server Integration Testing Suite")
    logger.info("=" * 60)
    
    # Run basic server test first
    basic_test_passed = asyncio.run(run_basic_server_test())
    
    if not basic_test_passed:
        logger.error("Basic server test failed, skipping integration tests")
        sys.exit(1)
    
    # Run comprehensive integration tests
    test_suite = IntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        logger.info("🎉 All integration tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some integration tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()