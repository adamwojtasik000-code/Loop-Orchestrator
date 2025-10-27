# Task Orchestrator System

## System Overview

The Task Orchestrator is an efficient, project-agnostic system designed to manage dynamic modes, execute approved tasks, and maintain persistent state across sessions. It serves as the central coordination layer for complex multi-step development workflows.

## Core Components

### 1. Persistent Memory Management (`persistent-memory.md`)
- **Purpose**: Centralized persistent memory for system state, goals, constraints, and unresolved issues
- **Structure**:
  - `# Non-Obvious Implementation Patterns`: Architecture patterns and implementation strategies
  - `# Development & Debug Commands`: Command sequences and troubleshooting procedures
  - `# System Updates & Status`: Timestamped system events, decisions, and changes
- **Requirements**:
  - Must maintain exactly 3 top-level sections
  - Line count must not exceed 300 lines
  - All entries use Apache-style log format with timestamps
  - Historical context preserved unless explicitly removed

### 2. Task Time Tracking (`task_timing.tsv`)
- **Purpose**: Comprehensive time tracking for all tasks and tool executions
- **Format**: TSV (tab-separated values) with headers: `timestamp`, `mode`, `task_id`, `start_time`, `end_time`, `duration`, `status`
- **Requirements**:
  - ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SSZ format)
  - Duration calculated in seconds
  - Status values: "started", "completed", "failed", or task-specific states
  - Automatic logging for all mode transitions and tool executions

### 3. Mode Configuration (`.roomodes`)
- **Purpose**: Define specialized modes for different development activities
- **Structure**: YAML configuration with custom modes, each containing:
  - Slug identifier
  - Display name with emoji
  - Role definition and responsibilities
  - When to use guidelines
  - Custom instructions for operation
- **Current Modes Available**:
  - Implementation modes (core, security, performance, features)
  - Validation modes (static, unit, integration, API)
  - Quality modes (functional, performance, security, compatibility)
  - Integration modes (commit, deploy, document, release)
  - Planning modes (analysis, priorities, architecture, requirements)
  - Specialized modes (optimization-memory, time-tracking, etc.)

## Operational Protocols

### Session Initialization
1. **Read Persistent Memory**: Load `persistent-memory.md` at start of each session
2. **Check Time Tracking**: Verify `task_timing.tsv` exists and is properly formatted
3. **Mode Verification**: Confirm available modes in `.roomodes` are accessible

### Task Execution Flow
1. **Time Tracking Start**: Log task start time to `task_timing.tsv`
2. **Mode Delegation**: Use `new_task` to delegate work to specialized modes
3. **Data Exchange**: Pass all data between subtasks explicitly
4. **Memory Updates**: Append findings to `persistent-memory.md` during execution
5. **Time Tracking End**: Record completion and calculate duration

### Error Handling
- **Command Failures**: Track consecutive failures (max 3) before resorting to documented commands
- **Memory Integrity**: Verify 3-section structure and 300-line limit before operations
- **Synchronization**: Ensure file operations complete successfully before progression

## Workflow Integration

### Mandatory Workflows
- **MANDATORY**: Delegate ALL work to specialized modes using `new_task`
- **MANDATORY**: Pass ALL data between subtasks
- **MANDATORY**: Maintain persistent memory integrity
- **MANDATORY**: Track all activities in time tracking system

### Subtask Management
- Maximum depth: 5 levels
- Resource allocation: 50% of parent allocation
- Cycle detection to prevent infinite recursion
- Clear termination conditions (objectives met, resources exhausted, time limits)

## System Architecture Patterns

### Current Implementation Patterns
- **File-Based State Management**: Uses markdown and TSV files for persistence
- **Mode-Based Processing**: Delegates tasks through specialized modes
- **Autoloading with Fallbacks**: Framework uses autoloading with fallback mechanisms
- **Git-Based Continuous Deployment**: Uses git push for deployment with authentication

### Key Integration Points
- **Environment Synchronization**: Required at implementation, validation, and integration stages
- **Cross-Mode Communication**: Standardized data formats and acknowledgment protocols
- **Error Propagation**: Escalation procedures across mode boundaries
- **Rollback Procedures**: Recovery mechanisms for failed operations

## Monitoring and Maintenance

### Time Tracking Integration
- Automatic start/stop on mode transitions
- Duration calculation and storage
- Task ID generation and management
- Performance metrics calculation

### Memory Optimization
- Line count monitoring (300 line limit)
- Content migration and archival
- Pattern consolidation and cleanup
- Integrity verification protocols

## Development Status

### Completed Components
- Basic persistent memory structure with 3-section format
- Time tracking TSV with proper headers
- Comprehensive mode definitions in `.roomodes`
- Workflow guide and operational protocols

### Identified Gaps
- Missing orchestrator-specific operational procedures
- Incomplete time tracking automation
- Need for initialization and startup procedures
- Missing mode transition protocols
- Incomplete error recovery mechanisms

## Next Steps
1. Complete missing orchestrator.md content with operational procedures
2. Implement time tracking automation
3. Develop system initialization protocols
4. Create mode transition mechanisms
5. Enhance error handling and recovery procedures