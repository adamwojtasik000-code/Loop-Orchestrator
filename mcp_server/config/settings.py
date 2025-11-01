"""
MCP Server Configuration Settings

Central configuration management for the Loop-Orchestrator MCP Server.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """
    Server configuration settings for Loop-Orchestrator MCP Server.
    """
    
    # Server basic configuration
    name: str = Field(default="Loop-Orchestrator MCP Server", description="Server name")
    instructions: str = Field(
        default="Comprehensive MCP server providing orchestrator management, "
                "file system access, and development tools for the Loop-Orchestrator project",
        description="Server instructions"
    )
    version: str = Field(default="1.0.0", description="Server version")
    
    # Transport configuration
    transport: str = Field(
        default="stdio",
        description="Transport type (stdio, sse, streamable-http)",
        pattern="^(stdio|sse|streamable-http)$"
    )
    base_port: int = Field(default=8080, ge=1024, le=65535, description="Base port for HTTP modes")
    
    # File paths - relative to workspace
    workspace_path: Path = Field(default_factory=lambda: Path("/workspaces/Loop-Orchestrator"))
    schedules_file: Path = Field(default_factory=lambda: Path(".roo/schedules.json"))
    task_timing_file: Path = Field(default="task_timing.tsv")
    persistent_memory_file: Path = Field(default="persistent-memory.md")
    todo_file: Path = Field(default="TODO.md")
    modes_file: Path = Field(default=".roomodes")
    backups_dir: Path = Field(default="backups")
    
    # System integration settings
    python_version_min: str = Field(default="3.10.0", description="Minimum Python version required")
    command_failure_limit: int = Field(default=3, ge=1, le=10, description="Command failure limit before escalation")
    time_tracking_enabled: bool = Field(default=True, description="Enable automatic time tracking")
    persistent_memory_max_lines: int = Field(default=300, ge=100, le=1000, description="Max lines in persistent memory")
    
    # Logging and error handling
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    error_recovery_enabled: bool = Field(default=True, description="Enable automatic error recovery")
    backup_before_modify: bool = Field(default=True, description="Create backups before file modifications")
    
    # Timeout and performance settings
    operation_timeout: int = Field(default=300, ge=30, le=3600, description="Default operation timeout in seconds")
    max_concurrent_operations: int = Field(default=5, ge=1, le=20, description="Maximum concurrent operations")
    cache_enabled: bool = Field(default=True, description="Enable result caching")
    cache_ttl: int = Field(default=300, ge=60, le=3600, description="Cache TTL in seconds")
    
    # Development workflow settings
    workflow_stages: List[str] = Field(
        default=["Implementation", "Validation", "Quality", "Integration", "Planning"],
        description="Development workflow stages"
    )
    mode_delegation_enabled: bool = Field(default=True, description="Enable automatic mode delegation")
    enhanced_reasoning_enabled: bool = Field(default=True, description="Enable enhanced reasoning mode")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("schedules_file", "task_timing_file", "persistent_memory_file", 
               "todo_file", "modes_file", "backups_dir")
    @classmethod
    def validate_paths(cls, v):
        """Ensure paths are relative to workspace."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @field_validator("workspace_path")
    @classmethod
    def validate_workspace_path(cls, v):
        """Ensure workspace path exists."""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_absolute_path(self, relative_path: Path) -> Path:
        """Get absolute path for a relative path."""
        return self.workspace_path / relative_path
    
    def get_schedules_path(self) -> Path:
        """Get absolute path to schedules file."""
        return self.get_absolute_path(self.schedules_file)
    
    def get_task_timing_path(self) -> Path:
        """Get absolute path to task timing file."""
        return self.get_absolute_path(self.task_timing_file)
    
    def get_persistent_memory_path(self) -> Path:
        """Get absolute path to persistent memory file."""
        return self.get_absolute_path(self.persistent_memory_file)
    
    def get_todo_path(self) -> Path:
        """Get absolute path to TODO file."""
        return self.get_absolute_path(self.todo_file)
    
    def get_modes_path(self) -> Path:
        """Get absolute path to modes file."""
        return self.get_absolute_path(self.modes_file)
    
    def get_backups_dir(self) -> Path:
        """Get absolute path to backups directory."""
        return self.get_absolute_path(self.backups_dir)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "instructions": self.instructions,
            "version": self.version,
            "transport": self.transport,
            "base_port": self.base_port,
            "workspace_path": str(self.workspace_path),
            "file_paths": {
                "schedules": str(self.schedules_file),
                "task_timing": str(self.task_timing_file),
                "persistent_memory": str(self.persistent_memory_file),
                "todo": str(self.todo_file),
                "modes": str(self.modes_file),
                "backups": str(self.backups_dir)
            },
            "system_settings": {
                "python_version_min": self.python_version_min,
                "command_failure_limit": self.command_failure_limit,
                "time_tracking_enabled": self.time_tracking_enabled,
                "persistent_memory_max_lines": self.persistent_memory_max_lines
            },
            "performance_settings": {
                "operation_timeout": self.operation_timeout,
                "max_concurrent_operations": self.max_concurrent_operations,
                "cache_enabled": self.cache_enabled,
                "cache_ttl": self.cache_ttl
            },
            "workflow_settings": {
                "workflow_stages": self.workflow_stages,
                "mode_delegation_enabled": self.mode_delegation_enabled,
                "enhanced_reasoning_enabled": self.enhanced_reasoning_enabled
            }
        }


# Global configuration instance
_config_instance: Optional[ServerConfig] = None


def get_server_config() -> ServerConfig:
    """Get the global server configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ServerConfig()
    return _config_instance


def get_default_config() -> ServerConfig:
    """Get default server configuration."""
    return ServerConfig()


def validate_environment() -> Dict[str, bool]:
    """Validate that the environment meets server requirements."""
    config = get_server_config()
    
    validation_results = {
        "python_version": _check_python_version(config.python_version_min),
        "workspace_exists": config.workspace_path.exists(),
        "backups_dir": _ensure_backups_dir(config.get_backups_dir()),
        "file_access": _check_file_access(config),
    }
    
    return validation_results


def _check_python_version(min_version: str) -> bool:
    """Check if Python version meets minimum requirement."""
    import sys
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return current_version >= min_version


def _ensure_backups_dir(backups_path: Path) -> bool:
    """Ensure backups directory exists."""
    try:
        backups_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def _check_file_access(config: ServerConfig) -> bool:
    """Check if server has proper file access."""
    try:
        # Check key files exist and are readable
        files_to_check = [
            config.get_schedules_path(),
            config.get_task_timing_path(),
            config.get_persistent_memory_path(),
            config.get_todo_path(),
            config.get_modes_path(),
        ]
        
        for file_path in files_to_check:
            if not file_path.exists():
                continue  # File doesn't exist yet, that's okay for some files
            if not os.access(file_path, os.R_OK):
                return False
        
        return True
    except Exception:
        return False


def setup_logging(config: Optional[ServerConfig] = None) -> logging.Logger:
    """Setup logging configuration for the MCP server."""
    if config is None:
        config = get_server_config()
    
    # Create logger
    logger = logging.getLogger("mcp_server")
    
    # Only setup if not already configured
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    return logger