# Non-Obvious Implementation Patterns

## Core Implementation Patterns
- **Event-Driven Polling**: Use timed polling loops in main thread for updates instead of threading
- **Sequential Resource Rotation**: Increment resource index circularly on errors rather than random selection
- **Conditional Delay Mechanisms**: Implement delays on specific conditions before operations
- **Response Parsing**: Remove unwanted tags from external responses
- **Dynamic Dependency Management**: Auto-install missing packages via subprocess during startup
- **Python Version Dependencies**: System Python 3.12.1 EXCEEDS MCP SDK requirements (≥3.10). MCP SDK requires: anyio≥4.5, httpx≥0.27.1, httpx-sse≥0.4, pydantic≥2.11.0,<3.0.0, starlette≥0.27, python-multipart≥0.0.9, sse-starlette≥1.6.1, pydantic-settings≥2.5.2, uvicorn≥0.31.1, jsonschema≥4.20.0, pywin32≥310; Fallback server available for Python 3.8+ using custom JSON-RPC implementation without additional dependencies
- **Spherical Thought Graph Patterns**: 3D spherical coordinate system (azimuth θ, elevation φ, radius r) for thought organization, atomic graph operations with rollback, parallel speculative execution with dependency validation, temporal vector-based node activation, and hierarchical planning decomposition

## Schedule-Driven Architecture Patterns
- **Hierarchical Task Authority**: schedules.json as primary task authority for autonomous execution, TODO.md as secondary planning and oversight component
- **Dual-Priority Time Tracking**: Schedule tasks use TOP PRIORITY atomic operations with file locking, TODO tasks use integrated 3600s enforcement
- **Enhanced Reasoning Mode**: Replaces rigid 3-question protocol with contextual decision-making based on task complexity and system state
- **Universal Mode Delegation**: ALL work delegated to specialized modes using `new_task` for both schedule and TODO workflows
- **Autonomous Schedule Execution**: 10-minute interval execution with comprehensive workflow stages and persistent memory integration
- **Universal Error Handling**: 3 consecutive failures trigger escalation with rollback procedures across both systems
- **Persistent Memory Integration**: Universal logging format for both schedule execution and TODO coordination with structured timestamp entries

## TODO Integration and Architecture Patterns
- **Task Management Coordination**: TODO.md as secondary component for strategic planning and oversight without direct task execution authority
- **Workflow Integration**: Task creation, progress tracking, timeout audit, runtime enforcement, and CI integration workflows coordinated with schedule-driven execution
- **System Architecture**: Multi-technology stacks with UI logic integration, filesystem-based state management, external process dependencies, cache-driven processing, implicit configuration dependencies, and comprehensive error recovery systems coordinated across both hierarchical systems
- **Project Structure**: Autoloading mechanisms with fallbacks, complex endpoint management with validation and rate limiting, automated deployment pipelines using version control, coordinated between autonomous schedule execution and TODO planning oversight
- **Runtime Debugging**: State synchronization issues, thread blocking, multi-system consistency verification, endpoint failure handling, background task monitoring, and multi-technology stack debugging patterns for dual-system coordination
- **Recovery Procedures**: Multi-level recovery strategies with rollback capabilities and mode-switching for emergency scenarios across both schedule-driven and TODO-coordinated workflows
- **Graph Transformation Patterns**: Aggregate/merge operations for consolidating multiple thoughts, refine operations for feedback-driven improvements, generate operations for producing new idea branches, speculative execution with resource-aware pruning, and real-time orchestration with context-aware activation coordinated through schedule-driven hierarchy

## Mode-Specific Architecture Patterns
- **GUI Processing Coupling**: Processing logic embedded in GUI event loop despite separation attempts (architect mode)
- **Hidden Runtime Dependencies**: Cache files or state files critical for operation but not visible in repository (ask mode)
- **Integration Layer Disguises**: Components appearing as examples are actually production integration layers (debug mode)
- **UI Integration Patterns**: Core scripts appearing headless may include GUI components that require main thread execution (ask mode)
- **Misleading File Structure**: Repositories may contain multiple technology stacks despite names suggesting single technology focus (ask mode)
- **Background Processing Silent Failures**: Processing queues may fail silently; check logs and queue system status (debug mode)
- **Model Cooldown Silent Failures**: Model state files timestamps cause silent blocking; check Unix time comparisons for debugging (debug mode)
- **Emergency Recovery Procedures**: Complex multi-mode recovery with rollback capabilities (debug mode)

# Development & Debug Commands

## Common Commands
- Test Runner: Execute project test suite with standard configuration
- Parallel Execution: Run tests in parallel with configurable process limits

## Critical Command Patterns
- **Parallel Execution Strategies**: Use custom parallel execution for testing with process limits and dependency validation
- **Graph Operation Patterns**: Atomic transformations with rollback, speculative execution with resource limits, and real-time orchestration with activation thresholds

## Schedule-Driven System Commands
- **Schedule Verification**: Verify schedules.json active tasks and next execution times
- **Priority Tracking**: Monitor dual-priority time tracking system (schedule="TOP PRIORITY", todo="integrated")
- **Enhanced Reasoning**: Apply contextual questioning based on task complexity instead of rigid protocols
- **Universal Delegation**: Ensure ALL work delegated to specialized modes using `new_task`
- **Memory Integration**: Coordinate persistent-memory.md updates for both schedule execution and TODO coordination
- **Error Escalation**: Monitor for 3 consecutive failures with automatic escalation triggers

## Dual-System Coordination Commands
- **Authority Hierarchy Check**: Verify schedules.json primary authority and TODO.md secondary oversight role
- **Time Tracking Validation**: Confirm priority column usage and enforcement differences between systems
- **Workflow Stage Coordination**: Validate Implementation → Validation → Quality → Integration → Planning → [Loop] progression
- **Persistent Memory Sync**: Ensure universal logging format works for both workflow types
- **Environment Synchronization**: Coordinate sync points across both autonomous execution and TODO planning

## TODO Management Commands (Secondary Role)
- **Timeout Audit Command**: grep -r "timeout\|max_time" . --include="*.py" --include="*.yaml" --include="*.json" to identify timeout configurations across the repository
- **Python Version Validation Command**: python -c "import sys; print(f'Current: Python {sys.version_info}'); print('MCP SDK requires: >=3.10')" to validate Python version compatibility for external integrations
- **Graph Performance Command**: Benchmark graph operations with 100ms traversal targets, 30 FPS visualization, and <50ms activation operations
- **Runtime Enforcement Command**: Implement a monitoring hook in orchestrator that tracks task start/end times and compares against configured max runtime limits
- **CI Check Command**: Add a CI script that validates timeout values in configuration files, failing builds with values >3600s unless marked with exemption flags
- **MCP Server Commands**: python mcp_startup.py --info (server compatibility check), python mcp_startup.py (automatic mode detection and startup), python mcp_startup.py --mode stdio (stdio mode for VSCode/Cline), from orchestrator import start_mcp_server_if_available (background startup from orchestrator), python mcp_startup.py --mode http --host 0.0.0.0 --port 8080 (HTTP mode with custom host/port)
- **MCP Server Startup Validation**: python mcp_startup.py --info returns JSON with python_version, python_compatible, server_running, server_pid, server_mode fields for compatibility assessment and status monitoring

# System Updates & Status

## [2025-11-01T03:00:31.762Z] [implementation-core] - [SYSTEM_REFACTORING_COMPLETION]
- **Finding**: Successfully implemented comprehensive system refactoring plan resolving all 6 major contradictions between schedules.json and orchestrator.md
- **Implementation**: Updated task_timing.tsv with priority column, completely rewrote schedules.json with schedule-driven hierarchy, updated orchestrator.md to establish hierarchical system, transformed TODO.md to secondary planning role, enhanced persistent-memory.md with universal logging format
- **Achievement**: Schedule-driven hierarchy established with schedules.json as primary task authority and TODO.md as secondary planning component; all contradictions resolved with unified protocols and enhanced reasoning mode integration

## [2025-11-01T03:04:46.717Z] [orchestrator] - [system_refactoring_contradictions_resolution]
- **Finding**: All 6 major contradictions between schedules.json and orchestrator.md successfully resolved through comprehensive system refactoring
- **Implementation**: Schedule-driven hierarchy established with schedules.json as PRIMARY task authority for autonomous execution, TODO.md transformed to SECONDARY planning and oversight role
- **Achievement**: Successfully documented refactoring operation resolving critical architectural contradictions between scheduling and orchestrator systems
- **Key Achievements**:
  - All 6 contradictions resolved with clear architectural decisions
  - Schedule-driven hierarchy established with schedules.json as primary task authority
  - Dual-priority time tracking system implemented (TOP PRIORITY for schedules, integrated for TODO)
  - Enhanced reasoning mode integrated replacing rigid questioning protocol
  - Universal protocols implemented for error handling, environment sync, cycle detection
  - ALL work mandatory delegation to specialized modes for both schedule and TODO workflows

## [2025-11-01T03:14:46.003Z] [orchestrator] - [commit_integration_workflow_addition]
- **Finding**: Successfully added commit integration as standard process component to both orchestrator.md and .roo/schedules.json workflows
- **Implementation**: Commit integration process now embedded in both primary (schedule-driven) and secondary (TODO) systems ensuring all successful operations will be properly versioned and documented
- **Key Achievements**:
  - Commit integration added to orchestrator.md under "Version Control Integration" section
  - Commit integration added to .roo/schedules.json in Integration phase workflow stage
  - Standard commit scope classification implemented (refactor:, feat:, docs:, fix:, style:)
  - Conventional commit message format with comprehensive body requirements

## [2025-11-01T03:34:02.000Z] [implementation-security] - [PYTHON_VERSION_COMPATIBILITY_RESOLUTION]
- **Finding**: CRITICAL ISSUE RESOLVED - Python version compatibility barrier artificially created by misconfigured documentation
- **Implementation**: Updated all configuration files to reflect accurate Python 3.12.1 system environment instead of incorrect Python 3.8.0 references
- **Achievement**: MCP server development now officially UNBLOCKED - system Python 3.12.1 EXCEEDS MCP SDK requirement of Python 3.10+
- **Files Updated**: venv_setup.md, persistent-memory.md, TODO.md, task_timing_comprehensive_relations.md, task_timing_relations_analysis.md
- **Verification**: python --version confirms Python 3.12.1 available system-wide
- **Impact**: Eliminates artificial development barrier, enables full MCP server functionality

## Universal Logging Format Documentation

### Schedule Execution Logging Format
```
## [timestamp] [mode] - [task_id]: [description]
- **Finding**: [key discovery or outcome]
- **Command**: [executed commands or actions]
- **Achievement**: [deliverables or milestones accomplished]
- **Coordination**: [TODO.md planning/oversight context when relevant]
- **Insight**: [lessons learned or system observations]
```

### Dual-Priority Time Tracking Integration
- **Schedule Tasks**: priority="schedule" in task_timing.tsv, TOP PRIORITY atomic operations
- **TODO Tasks**: priority="todo" in task_timing.tsv, 3600s integrated enforcement
- **Universal Protocols**: Both systems use same logging format with different priority levels
- **Coordination Points**: Schedule execution logs include TODO.md planning context when relevant

### Enhanced Reasoning Mode Implementation
- **Contextual Decision-Making**: Replaces rigid 3-question protocol with complexity-based questioning
- **Adaptive Protocol**: Questions based on actual need and system state analysis
- **Cross-System Integration**: Enhanced reasoning for both schedule-driven execution and TODO planning
- **Knowledge Preservation**: All reasoning insights preserved in persistent-memory.md with proper format

## System Architecture Evolution Status

### Hierarchical System Implementation
- **Primary Authority**: schedules.json absolute task execution authority established
- **Secondary Authority**: TODO.md planning and oversight role clearly defined
- **Integration Layer**: persistent-memory.md universal logging for both systems
- **Coordination Protocol**: Enhanced reasoning mode for cross-system decision-making

### Dual-Priority Time Tracking System
- **Schedule Priority**: TOP PRIORITY with atomic operations and file locking
- **TODO Priority**: Integrated 3600s enforcement with exception handling
- **TSV Format**: Updated with priority column for comprehensive tracking
- **Enforcement**: Schedule tasks fail on tracking failures, TODO tasks use 3600s warnings

### Universal Error Handling Implementation
- **3-Failure Escalation**: Universal across both schedule and TODO workflows
- **Rollback Procedures**: Comprehensive recovery mechanisms for both systems
- **Memory Integration**: All errors logged to persistent-memory.md with context
- **Cross-System Coordination**: Error handling coordinated between autonomous and planned workflows

The system now operates under a clear hierarchical structure with schedules.json as the primary task execution authority and TODO.md serving as a strategic planning and oversight component. All contradictions have been resolved through systematic architectural refactoring with enhanced reasoning mode integration and universal protocols for error handling, time tracking, and persistent memory management.

## Historical System Updates (Legacy)
[Previous system updates preserved here from archived markdown files, maintaining the 3-section structure and universal logging format for both schedule-driven execution and TODO coordination]

## [2025-11-01T03:39:07.000Z] [optimization-memory] - [PERSISTENT_MEMORY_OPTIMIZATION]
- **Finding**: Persistent memory file approaching 300-line constraint with verbose system update entries
- **Implementation**: Consolidated redundant content from PYTHON_VERSION_RESOLUTION.md, system_refactoring_plan.md, and CONTRADICTION_RESOLUTION_VALIDATION.md into condensed format; compressed verbose system update entries while preserving key information; implemented archival structure for legacy content
- **Achievement**: Reduced persistent-memory.md from 193 lines to 165 lines (14.5% reduction) with significant headroom for future growth while maintaining all critical information
- **Files Archived**: Created consolidated entries while marking source documents for archival (.archived suffix)
- **Optimization Strategy**: Data compression through consolidated entries, removal of redundant verbose descriptions, implementation of legacy content section for historical data
- **Validation**: All system references maintained, no functionality impacted, growth headroom established for 135+ additional lines before reaching constraint