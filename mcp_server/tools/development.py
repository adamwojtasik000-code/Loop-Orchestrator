"""
Development Tools

Tools for system monitoring, mode coordination, validation, and development workflow management.
"""

import os
import sys
import json
import time
import psutil
import subprocess
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..models import (
    SystemStatus, ModeCapabilities, ValidationResult, 
    DelegationRequest, DelegationResult, PriorityType
)
from ..config.settings import get_server_config
from ..utils.helpers import format_timestamp, safe_json_load


logger = logging.getLogger(__name__)


async def get_system_status(
    include_performance: bool = True,
    include_file_health: bool = True,
    include_orchestrator_status: bool = True,
    check_external_dependencies: bool = False
) -> Dict[str, Any]:
    """
    Comprehensive system health check.
    
    Args:
        include_performance: Whether to include performance metrics
        include_file_health: Whether to check file system health
        include_orchestrator_status: Whether to check orchestrator integration
        check_external_dependencies: Whether to check external dependencies
        
    Returns:
        Dictionary containing comprehensive system status
    """
    config = get_server_config()
    
    try:
        # Basic system information
        status = "healthy"
        warnings = []
        errors = []
        health_checks = {}
        
        # Python version check
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if python_version < config.python_version_min:
            status = "degraded"
            errors.append(f"Python version {python_version} is below minimum required {config.python_version_min}")
        health_checks["python_version"] = "pass" if python_version >= config.python_version_min else "fail"
        
        # Workspace accessibility
        workspace_accessible = True
        if not config.workspace_path.exists():
            status = "critical"
            errors.append(f"Workspace directory not accessible: {config.workspace_path}")
            workspace_accessible = False
        health_checks["workspace_access"] = "pass" if workspace_accessible else "fail"
        
        # File health checks
        file_health = {}
        key_files_exist = {}
        file_permissions = {}
        
        if include_file_health and workspace_accessible:
            # Check key orchestrator files
            key_files = {
                "schedules": config.get_schedules_path(),
                "task_timing": config.get_task_timing_path(),
                "persistent_memory": config.get_persistent_memory_path(),
                "todo": config.get_todo_path(),
                "modes": config.get_modes_path(),
            }
            
            for file_name, file_path in key_files.items():
                # Check existence
                exists = file_path.exists()
                key_files_exist[file_name] = exists
                
                # Check permissions if file exists
                if exists:
                    readable = os.access(file_path, os.R_OK)
                    writable = os.access(file_path, os.W_OK)
                    file_permissions[file_name] = {
                        "readable": readable,
                        "writable": writable
                    }
                    file_health[file_name] = "healthy" if readable and writable else "degraded"
                else:
                    file_health[file_name] = "missing"
                    file_permissions[file_name] = {"readable": False, "writable": False}
        
        # Orchestrator integration status
        orchestrator_status = {}
        if include_orchestrator_status and workspace_accessible:
            # Check schedules file
            if key_files_exist.get("schedules", False):
                try:
                    with open(config.get_schedules_path(), 'r') as f:
                        schedules_data = json.load(f)
                    orchestrator_status["schedules"] = "accessible"
                except Exception as e:
                    orchestrator_status["schedules"] = f"error: {str(e)}"
                    status = "degraded"
            else:
                orchestrator_status["schedules"] = "not_found"
            
            # Check time tracking
            if key_files_exist.get("task_timing", False):
                orchestrator_status["time_tracking"] = "active"
            else:
                orchestrator_status["time_tracking"] = "not_found"
            
            # Check persistent memory
            if key_files_exist.get("persistent_memory", False):
                orchestrator_status["persistent_memory"] = "accessible"
            else:
                orchestrator_status["persistent_memory"] = "not_found"
        
        # Performance metrics
        performance_metrics = {}
        if include_performance:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                performance_metrics["cpu_percent"] = cpu_percent
                
                # Memory usage
                memory = psutil.virtual_memory()
                performance_metrics["memory_percent"] = memory.percent
                performance_metrics["memory_available_mb"] = memory.available / (1024 * 1024)
                
                # Disk usage
                disk = psutil.disk_usage(str(config.workspace_path))
                performance_metrics["disk_percent"] = (disk.used / disk.total) * 100
                performance_metrics["disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
                
                # Process information
                process = psutil.Process()
                performance_metrics["process_memory_mb"] = process.memory_info().rss / (1024 * 1024)
                performance_metrics["process_cpu_percent"] = process.cpu_percent()
                
            except Exception as e:
                warnings.append(f"Could not collect performance metrics: {str(e)}")
                performance_metrics["error"] = str(e)
        
        # Check external dependencies if requested
        external_deps = {}
        if check_external_dependencies:
            try:
                # Check git
                try:
                    subprocess.run(["git", "--version"], capture_output=True, check=True)
                    external_deps["git"] = "available"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    external_deps["git"] = "not_found"
                
                # Check common Python packages
                common_packages = ["pip", "python"]
                for package in common_packages:
                    try:
                        subprocess.run([package, "--version"], capture_output=True, check=True)
                        external_deps[package] = "available"
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        external_deps[package] = "not_found"
                        
            except Exception as e:
                warnings.append(f"Could not check external dependencies: {str(e)}")
        
        # Calculate overall status
        if errors:
            status = "critical" if any("critical" in error.lower() for error in errors) else "degraded"
        elif warnings and status == "healthy":
            status = "warning"
        
        # Determine if time tracking is active
        time_tracking_active = config.time_tracking_enabled and key_files_exist.get("task_timing", False)
        
        # Determine if persistent memory is valid
        persistent_memory_valid = key_files_exist.get("persistent_memory", False)
        
        # Create system status model
        system_status = SystemStatus(
            status=status,
            timestamp=format_timestamp(),
            version=config.version,
            python_version=python_version,
            workspace_accessible=workspace_accessible,
            key_files_exist=key_files_exist,
            file_permissions=file_permissions,
            schedules_accessible=key_files_exist.get("schedules", False),
            time_tracking_active=time_tracking_active,
            persistent_memory_valid=persistent_memory_valid,
            performance_metrics=performance_metrics if include_performance else None,
            external_dependencies=external_deps if check_external_dependencies else None,
            health_checks=health_checks,
            warnings=warnings,
            errors=errors
        )
        
        return {
            "success": True,
            "status": system_status.dict(),
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def switch_mode(
    target_mode: str,
    task_context: Optional[Dict[str, Any]] = None,
    priority: PriorityType = PriorityType.NORMAL,
    track_time: bool = True
) -> Dict[str, Any]:
    """
    Coordinate mode transitions with time tracking.
    
    Args:
        target_mode: Target mode to switch to
        task_context: Context information for the mode switch
        priority: Priority level for the mode switch
        track_time: Whether to start time tracking for the mode switch
        
    Returns:
        Dictionary containing mode switch result
    """
    config = get_server_config()
    
    try:
        # Load available modes
        modes_path = config.get_modes_path()
        if not modes_path.exists():
            return {
                "success": False,
                "error": f"Modes file not found: {modes_path}",
                "target_mode": target_mode,
                "timestamp": format_timestamp()
            }
        
        with open(modes_path, 'r', encoding='utf-8') as f:
            modes_data = json.load(f)
        
        mode_capabilities = ModeCapabilities.from_dict(modes_data)
        
        # Check if target mode exists
        target_mode_info = next((m for m in mode_capabilities.modes if m.slug == target_mode), None)
        if not target_mode_info:
            available_modes = [m.slug for m in mode_capabilities.modes]
            return {
                "success": False,
                "error": f"Target mode not found: {target_mode}",
                "available_modes": available_modes,
                "target_mode": target_mode,
                "timestamp": format_timestamp()
            }
        
        # Start time tracking if enabled
        tracking_result = None
        if track_time and config.time_tracking_enabled:
            tracking_result = await track_mode_switch_time(
                target_mode=target_mode,
                priority=priority,
                context=task_context
            )
        
        # Update persistent memory
        await update_mode_switch_memory(
            target_mode=target_mode,
            mode_info=target_mode_info,
            context=task_context,
            priority=priority
        )
        
        return {
            "success": True,
            "mode_switch": {
                "target_mode": target_mode,
                "mode_name": target_mode_info.name,
                "mode_description": target_mode_info.description,
                "mode_role": target_mode_info.role_definition,
                "context": task_context,
                "priority": priority.value,
                "tracking_result": tracking_result
            },
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error switching mode: {e}")
        return {
            "success": False,
            "error": str(e),
            "target_mode": target_mode,
            "timestamp": format_timestamp()
        }


async def track_mode_switch_time(
    target_mode: str,
    priority: PriorityType,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Track mode switch time."""
    config = get_server_config()
    
    try:
        # Import track_task_time function
        from .orchestrator import track_task_time
        
        task_description = f"Mode switch to {target_mode}"
        if context and context.get("task_description"):
            task_description = context["task_description"]
        
        return await track_task_time(
            task_description=task_description,
            mode=target_mode,
            priority=priority,
            start_tracking=True
        )
    except Exception as e:
        logger.error(f"Error tracking mode switch time: {e}")
        return {"success": False, "error": str(e)}


async def update_mode_switch_memory(
    target_mode: str,
    mode_info: Any,
    context: Optional[Dict[str, Any]] = None,
    priority: PriorityType = PriorityType.NORMAL
) -> Dict[str, Any]:
    """Update persistent memory with mode switch information."""
    config = get_server_config()
    
    try:
        from .orchestrator import update_persistent_memory
        from ..models import PersistentMemorySection
        
        content = f"Mode switch initiated to {target_mode}"
        if context:
            content += f" with context: {context}"
        
        return await update_persistent_memory(
            section=PersistentMemorySection.SYSTEM_UPDATES,
            content=content,
            category="mode_switch",
            format_entry=True
        )
    except Exception as e:
        logger.error(f"Error updating mode switch memory: {e}")
        return {"success": False, "error": str(e)}


async def run_validation(
    validation_type: str,
    target_path: Optional[str] = None,
    validation_options: Optional[Dict[str, Any]] = None,
    fail_fast: bool = False
) -> Dict[str, Any]:
    """
    Execute validation workflows.
    
    Args:
        validation_type: Type of validation to perform
        target_path: Path to validate (optional)
        validation_options: Additional options for validation
        fail_fast: Whether to stop on first failure
        
    Returns:
        Dictionary containing validation results
    """
    config = get_server_config()
    
    try:
        validation_result = ValidationResult(
            success=True,
            validation_type=validation_type,
            timestamp=format_timestamp(),
            details={}
        )
        
        if validation_type == "system_health":
            # Run system health validation
            system_result = await get_system_status(
                include_performance=True,
                include_file_health=True,
                include_orchestrator_status=True
            )
            
            validation_result.details["system_health"] = system_result
            
            if not system_result.get("success", False):
                validation_result.success = False
                validation_result.errors.append(f"System health check failed: {system_result.get('error', 'Unknown error')}")
            
        elif validation_type == "file_integrity":
            # Validate file integrity
            if not target_path:
                validation_result.success = False
                validation_result.errors.append("Target path required for file integrity validation")
            else:
                file_result = await validate_file_integrity(target_path, validation_options or {})
                validation_result.details["file_integrity"] = file_result
                
                if not file_result.get("success", False):
                    validation_result.success = False
                    validation_result.errors.append(f"File integrity check failed: {file_result.get('error', 'Unknown error')}")
            
        elif validation_type == "orchestrator_files":
            # Validate orchestrator file structure
            orchestrator_result = await validate_orchestrator_files()
            validation_result.details["orchestrator_files"] = orchestrator_result
            
            if not orchestrator_result.get("success", False):
                validation_result.success = False
                validation_result.errors.extend(orchestrator_result.get("errors", []))
                
        elif validation_type == "modes_configuration":
            # Validate modes configuration
            modes_result = await validate_modes_configuration()
            validation_result.details["modes_config"] = modes_result
            
            if not modes_result.get("success", False):
                validation_result.success = False
                validation_result.errors.extend(modes_result.get("errors", []))
                
        else:
            validation_result.success = False
            validation_result.errors.append(f"Unknown validation type: {validation_type}")
        
        # Calculate metrics
        validation_result.metrics = {
            "total_checks": len(validation_result.details),
            "passed_checks": len([d for d in validation_result.details.values() if d.get("success", False)]),
            "failed_checks": len([d for d in validation_result.details.values() if not d.get("success", False)]),
            "error_count": len(validation_result.errors),
            "warning_count": len(validation_result.warnings)
        }
        
        return {
            "success": validation_result.success,
            "validation_result": validation_result.dict(),
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error running validation: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_type": validation_type,
            "timestamp": format_timestamp()
        }


async def validate_file_integrity(file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Validate file integrity."""
    config = get_server_config()
    
    try:
        workspace_path = config.workspace_path
        target_path = workspace_path / file_path
        
        if not target_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        
        # Check file size
        file_size = target_path.stat().st_size
        max_size = options.get("max_size_mb", 10)
        if file_size > max_size * 1024 * 1024:
            return {
                "success": False,
                "error": f"File too large: {file_size} bytes (max: {max_size} MB)",
                "file_path": file_path,
                "file_size": file_size
            }
        
        # Try to read file
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"File encoding issue: {file_path}",
                "file_path": file_path
            }
        
        # JSON validation if applicable
        if file_path.endswith('.json'):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}",
                    "file_path": file_path
                }
        
        return {
            "success": True,
            "file_path": file_path,
            "file_size": file_size,
            "checks_passed": ["existence", "readability", "size_limit"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


async def validate_orchestrator_files() -> Dict[str, Any]:
    """Validate orchestrator file structure."""
    config = get_server_config()
    
    errors = []
    warnings = []
    
    try:
        # Check schedules.json
        schedules_path = config.get_schedules_path()
        if schedules_path.exists():
            try:
                with open(schedules_path, 'r') as f:
                    schedules_data = json.load(f)
                if "schedules" not in schedules_data:
                    errors.append("schedules.json missing 'schedules' key")
                elif not isinstance(schedules_data["schedules"], list):
                    errors.append("schedules.json 'schedules' must be a list")
            except json.JSONDecodeError as e:
                errors.append(f"schedules.json invalid JSON: {str(e)}")
        else:
            warnings.append("schedules.json not found")
        
        # Check task_timing.tsv
        timing_path = config.get_task_timing_path()
        if timing_path.exists():
            try:
                with open(timing_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if len(lines) < 2:
                    warnings.append("task_timing.tsv appears to be empty or missing header")
            except Exception as e:
                errors.append(f"task_timing.tsv read error: {str(e)}")
        else:
            warnings.append("task_timing.tsv not found")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "success": False,
            "errors": [f"Orchestrator validation error: {str(e)}"],
            "warnings": warnings
        }


async def validate_modes_configuration() -> Dict[str, Any]:
    """Validate modes configuration."""
    config = get_server_config()
    
    errors = []
    warnings = []
    
    try:
        modes_path = config.get_modes_path()
        if not modes_path.exists():
            errors.append(f"Modes file not found: {modes_path}")
            return {"success": False, "errors": errors, "warnings": warnings}
        
        with open(modes_path, 'r', encoding='utf-8') as f:
            modes_data = json.load(f)
        
        if "customModes" not in modes_data:
            errors.append("modes.json missing 'customModes' key")
        elif not isinstance(modes_data["customModes"], dict):
            errors.append("modes.json 'customModes' must be a dictionary")
        else:
            # Validate each mode
            for mode_slug, mode_data in modes_data["customModes"].items():
                required_fields = ["name", "description", "roleDefinition", "whenToUse"]
                for field in required_fields:
                    if field not in mode_data:
                        errors.append(f"Mode {mode_slug} missing required field: {field}")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "success": False,
            "errors": [f"Modes validation error: {str(e)}"],
            "warnings": warnings
        }


async def get_mode_capabilities(
    filter_by_group: Optional[str] = None,
    include_instructions: bool = True
) -> Dict[str, Any]:
    """
    List available modes from .roomodes.
    
    Args:
        filter_by_group: Filter modes by group (optional)
        include_instructions: Whether to include custom instructions
        
    Returns:
        Dictionary containing available modes and their capabilities
    """
    config = get_server_config()
    
    try:
        modes_path = config.get_modes_path()
        if not modes_path.exists():
            return {
                "success": False,
                "error": f"Modes file not found: {modes_path}",
                "timestamp": format_timestamp()
            }
        
        with open(modes_path, 'r', encoding='utf-8') as f:
            modes_data = json.load(f)
        
        mode_capabilities = ModeCapabilities.from_dict(modes_data)
        
        # Filter modes if requested
        filtered_modes = mode_capabilities.modes
        if filter_by_group:
            filtered_modes = [m for m in filtered_modes if filter_by_group in m.groups]
        
        # Format modes for response
        formatted_modes = []
        for mode in filtered_modes:
            mode_info = {
                "slug": mode.slug,
                "name": mode.name,
                "description": mode.description,
                "when_to_use": mode.when_to_use,
                "groups": mode.groups,
                "source": mode.source
            }
            
            if include_instructions:
                mode_info["role_definition"] = mode.role_definition
                mode_info["custom_instructions"] = mode.custom_instructions
            
            formatted_modes.append(mode_info)
        
        # Group modes by category
        mode_groups = {}
        for mode in filtered_modes:
            for group in mode.groups:
                if group not in mode_groups:
                    mode_groups[group] = []
                mode_groups[group].append({
                    "slug": mode.slug,
                    "name": mode.name,
                    "description": mode.description
                })
        
        return {
            "success": True,
            "timestamp": format_timestamp(),
            "total_modes": len(mode_capabilities.modes),
            "filtered_modes": len(filtered_modes),
            "mode_groups": mode_groups,
            "modes": formatted_modes,
            "available_groups": list(set(group for mode in mode_capabilities.modes for group in mode.groups))
        }
        
    except Exception as e:
        logger.error(f"Error getting mode capabilities: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": format_timestamp()
        }


async def error_recovery(
    operation: str,
    error_context: Dict[str, Any],
    recovery_strategy: Optional[str] = None,
    create_checkpoint: bool = True
) -> Dict[str, Any]:
    """
    Handle error scenarios and recovery procedures.
    
    Args:
        operation: Operation that failed
        error_context: Context information about the error
        recovery_strategy: Specific recovery strategy to use
        create_checkpoint: Whether to create a checkpoint before recovery
        
    Returns:
        Dictionary containing recovery result
    """
    config = get_server_config()
    
    try:
        # Log the error to persistent memory
        from .orchestrator import update_persistent_memory
        from ..models import PersistentMemorySection
        
        error_entry = f"Error recovery initiated for operation '{operation}': {error_context.get('error', 'Unknown error')}"
        await update_persistent_memory(
            section=PersistentMemorySection.SYSTEM_UPDATES,
            content=error_entry,
            category="error_recovery",
            format_entry=True
        )
        
        # Determine recovery strategy
        if recovery_strategy is None:
            recovery_strategy = _determine_recovery_strategy(operation, error_context)
        
        recovery_result = {
            "operation": operation,
            "error_context": error_context,
            "recovery_strategy": recovery_strategy,
            "timestamp": format_timestamp()
        }
        
        if recovery_strategy == "retry":
            recovery_result["action"] = "retry_operation"
            recovery_result["delay_seconds"] = error_context.get("retry_delay", 5)
            
        elif recovery_strategy == "rollback":
            recovery_result["action"] = "rollback_changes"
            if "backup_path" in error_context:
                recovery_result["rollback_from"] = error_context["backup_path"]
            
        elif recovery_strategy == "cleanup":
            recovery_result["action"] = "cleanup_resources"
            recovery_result["cleanup_actions"] = _determine_cleanup_actions(operation, error_context)
            
        elif recovery_strategy == "escalate":
            recovery_result["action"] = "escalate_to_manual"
            recovery_result["escalation_reason"] = _determine_escalation_reason(operation, error_context)
            
        else:
            recovery_result["action"] = "no_recovery_needed"
            recovery_result["reason"] = "Error context suggests no recovery is necessary"
        
        # Create checkpoint if requested
        if create_checkpoint:
            checkpoint_result = await create_recovery_checkpoint(operation, error_context)
            recovery_result["checkpoint"] = checkpoint_result
        
        return {
            "success": True,
            "recovery_result": recovery_result,
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error in recovery process: {e}")
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
            "timestamp": format_timestamp()
        }


def _determine_recovery_strategy(operation: str, error_context: Dict[str, Any]) -> str:
    """Determine appropriate recovery strategy based on operation and error."""
    error_msg = error_context.get("error", "").lower()
    
    # File operations
    if operation.startswith("file_"):
        if "permission" in error_msg:
            return "escalate"
        elif "not found" in error_msg:
            return "cleanup"
        else:
            return "retry"
    
    # Network operations
    elif "network" in operation or "http" in operation:
        if "timeout" in error_msg:
            return "retry"
        else:
            return "escalate"
    
    # Default strategies
    if "temporary" in error_msg or "retry" in error_msg:
        return "retry"
    else:
        return "escalate"


def _determine_cleanup_actions(operation: str, error_context: Dict[str, Any]) -> List[str]:
    """Determine cleanup actions based on operation."""
    actions = []
    
    if operation.startswith("file_"):
        actions.extend([
            "remove_temporary_files",
            "clear_caches"
        ])
    
    if "backup" in error_context:
        actions.append("verify_backup_integrity")
    
    return actions


def _determine_escalation_reason(operation: str, error_context: Dict[str, Any]) -> str:
    """Determine escalation reason."""
    error_msg = error_context.get("error", "")
    
    if "permission" in error_msg.lower():
        return "Insufficient permissions for operation"
    elif "not found" in error_msg.lower():
        return "Required resource not found"
    else:
        return f"Unexpected error in {operation}: {error_msg}"


async def create_recovery_checkpoint(operation: str, error_context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a recovery checkpoint."""
    try:
        checkpoint_data = {
            "operation": operation,
            "error_context": error_context,
            "timestamp": format_timestamp(),
            "system_state": await get_system_status(include_performance=False)
        }
        
        # Save checkpoint to file
        config = get_server_config()
        checkpoint_dir = config.get_backups_dir() / "recovery_checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f"checkpoint_{int(time.time())}_{operation.replace('/', '_')}.json"
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        return {
            "success": True,
            "checkpoint_file": str(checkpoint_file.relative_to(config.workspace_path)),
            "checkpoint_id": checkpoint_file.stem
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def sync_environment(
    sync_type: str = "full",
    target_components: Optional[List[str]] = None,
    verify_sync: bool = True
) -> Dict[str, Any]:
    """
    Coordinate environment synchronization.
    
    Args:
        sync_type: Type of sync ("full", "files", "config", "modes")
        target_components: Specific components to sync
        verify_sync: Whether to verify sync was successful
        
    Returns:
        Dictionary containing sync result
    """
    config = get_server_config()
    
    try:
        sync_results = {}
        sync_errors = []
        
        if sync_type in ["full", "files"]:
            # Sync file system
            files_result = await sync_file_system(target_components)
            sync_results["file_system"] = files_result
            if not files_result.get("success", False):
                sync_errors.extend(files_result.get("errors", []))
        
        if sync_type in ["full", "config"]:
            # Sync configuration
            config_result = await sync_configuration()
            sync_results["configuration"] = config_result
            if not config_result.get("success", False):
                sync_errors.extend(config_result.get("errors", []))
        
        if sync_type in ["full", "modes"]:
            # Sync modes configuration
            modes_result = await sync_modes_configuration()
            sync_results["modes"] = modes_result
            if not modes_result.get("success", False):
                sync_errors.extend(modes_result.get("errors", []))
        
        # Verify sync if requested
        verification_result = None
        if verify_sync:
            verification_result = await verify_environment_sync(sync_results)
        
        overall_success = len(sync_errors) == 0
        
        return {
            "success": overall_success,
            "sync_type": sync_type,
            "sync_results": sync_results,
            "verification": verification_result,
            "errors": sync_errors,
            "timestamp": format_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error syncing environment: {e}")
        return {
            "success": False,
            "error": str(e),
            "sync_type": sync_type,
            "timestamp": format_timestamp()
        }


async def sync_file_system(target_components: Optional[List[str]]) -> Dict[str, Any]:
    """Sync file system components."""
    try:
        # Check file integrity
        validation_result = await run_validation("file_integrity")
        return validation_result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def sync_configuration() -> Dict[str, Any]:
    """Sync configuration settings."""
    try:
        # Validate configuration
        config = get_server_config()
        env_validation = config.model_validate({})
        
        return {
            "success": True,
            "config_valid": True,
            "timestamp": format_timestamp()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def sync_modes_configuration() -> Dict[str, Any]:
    """Sync modes configuration."""
    try:
        # Validate modes
        validation_result = await validate_modes_configuration()
        return validation_result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def verify_environment_sync(sync_results: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that environment sync was successful."""
    try:
        # Run comprehensive system check
        system_result = await get_system_status(
            include_performance=True,
            include_file_health=True,
            include_orchestrator_status=True
        )
        
        return {
            "success": system_result.get("success", False),
            "system_health": system_result,
            "sync_verified": True,
            "timestamp": format_timestamp()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sync_verified": False
        }