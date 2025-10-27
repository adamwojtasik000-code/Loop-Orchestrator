# Task Orchestrator System

## System Overview

The Task Orchestrator is a project-agnostic system centered around TODO.md as the core component for task management, workflow orchestration, and developer checklists. All development activities originate from TODO.md checklist items, with specialized modes handling execution while maintaining persistent state and time enforcement defaults (3600s). The system ensures checklist-driven development with automated time tracking, runtime enforcement, and CI/test integration aligned with TODO.md-centric workflows.

## Core Components

### 1. TODO System (`TODO.md`) - Central Task Management Component
- **Purpose**: Serves as the central component for task tracking, workflow orchestration, developer checklists, and priority-based task organization
- **Structure**:
  - High priority tasks with clear acceptance criteria and deliverables
  - Implementation tasks with specific actionable items, notes, and commands
  - Checklist-driven development with checkbox progress tracking
- **Requirements**:
  - Items must be small, actionable, and marked complete upon successful execution
  - Include specific commands, notes, and deliverable descriptions
  - Time enforcement defaults to 3600s with explicit exception handling
  - All development work originates from TODO.md checklist items
- **Integration**: Drives all development workflows, prioritizes tasks by levels (high, implementation), and ensures checklist-based execution protocols

### 2. Time Tracking System (`task_timing.tsv`)
- **Purpose**: Comprehensive time tracking for all TODO.md tasks and mode executions with runtime enforcement
- **Format**: TSV (tab-separated values) with headers: `timestamp`, `mode`, `task_id`, `start_time`, `end_time`, `duration`, `status`
- **Requirements**:
  - ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SSZ format)
  - Duration calculated in seconds with 3600s default enforcement
  - Status values: "started", "completed", "failed", or task-specific states
  - Automatic logging for all mode transitions and tool executions
  - Runtime guards fail or warn when exceeding 3600s unless explicitly exempted

### 3. Persistent Memory Management (`persistent-memory.md`)
- **Purpose**: Centralized persistent memory for system state, TODO integration patterns, and development workflows
- **Structure**:
  - `# Non-Obvious Implementation Patterns`: TODO-driven architecture and integration strategies
  - `# Development & Debug Commands`: Command sequences aligned with TODO.md workflows
  - `# System Updates & Status`: Timestamped system events and TODO execution findings
- **Requirements**:
  - Must maintain exactly 3 top-level sections
  - Line count must not exceed 300 lines
  - All entries use structured format with timestamps and mode context
  - Historical TODO execution context preserved unless explicitly removed

### 4. Mode Configuration (`.roomodes`)
- **Purpose**: Define specialized modes for executing TODO.md tasks and subtasks
- **Structure**: YAML configuration with custom modes, each containing:
  - Slug identifier
  - Display name with emoji
  - Role definition and responsibilities
  - When to use guidelines aligned with TODO item categories
  - Custom instructions for TODO-centric operation
- **Current Modes Available**:
  - Implementation modes (core, security, performance, features) for executing implementation tasks
  - Validation modes (static, unit, integration, API) for quality checks
  - Quality modes (functional, performance, security, compatibility) for assurance
  - Integration modes (commit, deploy, document, release) for release workflows
  - Planning modes (analysis, priorities, architecture, requirements) for strategic planning
  - Specialized modes (optimization-memory, time-tracking) for system maintenance

## TODO Integration Patterns

### Checklist-Driven Development
- **Task Management Centralization**: TODO.md serves as the primary component for task tracking, workflow orchestration, and developer checklists
- **Priority-Based Task Organization**: Structure tasks by priority levels (high, implementation) with clear acceptance criteria
- **Time Tracking Enforcement**: Implement runtime limits (default 3600s) for tasks with automated checks and enforcement mechanisms
- **Command Documentation in Tasks**: Include specific commands, notes, and deliverables directly in task descriptions for actionable workflows

### TODO-Driven Workflows
- **Task Creation Workflow**: Add new development tasks to TODO.md with specific action items, acceptance criteria, and deliverable descriptions
- **Progress Tracking Workflow**: Update task status using checkboxes, include completion notes and executed commands for transparency
- **Timeout Audit Workflow**: Search repository for timeout configurations (timeout, max_time fields), compile list of tasks needing timeout adjustments or justifications
- **Runtime Enforcement Workflow**: Implement orchestrator guards that monitor task execution time, failing or warning when exceeding 3600s default unless explicitly exempted
- **CI Integration Workflow**: Add automated CI checks that scan configuration files for timeout values exceeding 3600s, providing warnings or failures with review exemption options

## TODO-Centric Operational Protocols

### Session Initialization
1. **Review TODO.md**: Check active checklist items, prioritize by levels (high priority first), and verify acceptance criteria
2. **Read Persistent Memory**: Load `persistent-memory.md` for TODO integration patterns and system state
3. **Check Time Tracking**: Verify `task_timing.tsv` and confirm runtime enforcement with 3600s default
4. **Mode Verification**: Confirm available modes in `.roomodes` for executing TODO tasks

### Task Execution Flow
1. **TODO Item Selection**: Select active task from TODO.md checklist based on priority and acceptance criteria
2. **Time Tracking Start**: Log task start time to `task_timing.tsv` with 3600s enforcement
3. **Mode Delegation**: Use `new_task` to delegate work to specialized modes aligned with TODO item categories
4. **Data Exchange**: Pass all data between subtasks explicitly, maintaining TODO context
5. **Memory Updates**: Append findings to `persistent-memory.md` system updates section during execution
6. **Runtime Enforcement**: Monitor execution time, warn at 3600s, fail if exceeded without exemption
7. **Time Tracking End**: Record completion, calculate duration, and validate against 3600s default
8. **TODO Completion**: Mark checklist item complete upon meeting acceptance criteria and successful execution

### Time Enforcement and Exception Handling
- **Default Limit**: 3600s (1 hour) maximum runtime for all tasks unless explicitly exempted in TODO.md
- **Runtime Guards**: Orchestrator monitors task execution, issues warnings at 3600s, failures for violations
- **Exception Process**: Tasks exceeding 3600s must be justified in TODO.md with acceptance criteria documentation
- **CI Checks**: Automated scans for timeout values >3600s in configurations, with warnings/failures and exemption options
- **Audit Requirements**: Repository-wide search for timeout configurations to ensure compliance with 3600s default

### Error Handling
- **Command Failures**: Track consecutive failures (max 3) before resorting to documented commands in TODO workflows
- **Memory Integrity**: Verify 3-section structure and 300-line limit before TODO operations
- **Synchronization**: Ensure file operations complete successfully before progressing through TODO stages

## Checklist-Based Execution Protocols

### Priority Levels and Execution Order
- **High Priority**: Critical tasks with immediate acceptance criteria - execute first
- **Implementation Tasks**: Feature development with specific deliverables - execute in priority order
- **Checklist Protocol**: All tasks follow checkbox marking upon completion, with notes and commands included

### Execution Stages
1. **Planning**: Review TODO.md for active items, prioritize by level, verify acceptance criteria
2. **Delegation**: Spawn specialized modes using `new_task` for execution
3. **Monitoring**: Track time with 3600s enforcement, monitor progress against deliverables
4. **Completion**: Mark checkboxes complete, append findings to persistent memory
5. **Verification**: CI checks scan for timeout violations, validate acceptance criteria

### Mandatory TODO-Driven Workflows
- **MANDATORY**: All development work originates from TODO.md checklist items
- **MANDATORY**: Delegate work to specialized modes using `new_task` with explicit data passing
- **MANDATORY**: Maintain persistent memory integrity and 3600s time enforcement
- **MANDATORY**: Track all activities in time tracking system with TODO context
- **MANDATORY**: Include CI/test guidance referencing TODO.md conventions and 3600s default

### Subtask Management
- Maximum depth: 5 levels with TODO context preservation
- Resource allocation: 50% of parent allocation with time enforcement inheritance
- Cycle detection to prevent infinite recursion in TODO execution flows
- Clear termination conditions: objectives met per acceptance criteria, resources exhausted, or 3600s time limits reached

## System Architecture Patterns

### TODO-Driven Architecture Patterns
- **Checklist-Driven Development**: All development work originates from TODO.md checklist items with priority levels and acceptance criteria
- **Time-Enforced Task Execution**: Runtime limits default to 3600s with automated enforcement and exception handling
- **File-Based State Management**: Uses TODO.md, markdown, and TSV files for persistence aligned with checklist protocols
- **Mode-Based Processing**: Delegates TODO tasks through specialized modes with explicit data passing
- **Autoloading with Fallbacks**: Framework uses autoloading with fallback mechanisms for TODO workflow continuity
- **Git-Based Continuous Deployment**: Uses git push for deployment with authentication and CI checks for 3600s compliance

### Key Integration Points
- **Environment Synchronization**: Required at planning, implementation, validation, and integration stages per TODO workflows
- **Cross-Mode Communication**: Standardized data formats and acknowledgment protocols with TODO context
- **Error Propagation**: Escalation procedures across mode boundaries with TODO exception documentation
- **Rollback Procedures**: Recovery mechanisms for failed operations aligned with checklist protocols

## Monitoring and Maintenance

### Time Tracking Integration with TODO Enforcement
- Automatic start/stop on mode transitions with 3600s default enforcement
- Duration calculation and storage with runtime guard monitoring
- Task ID generation and management aligned with TODO item tracking
- Performance metrics calculation with timeout audit workflows

### Memory Optimization and TODO Integration
- Line count monitoring (300 line limit) for persistent memory
- Content migration and archival preserving TODO execution history
- Pattern consolidation and cleanup aligned with TODO integration patterns
- Integrity verification protocols with TODO workflow consistency

## Development Status

### Completed Components
- TODO.md system as central task management component with checklist protocols
- Persistent memory structure with TODO integration patterns and 3-section format
- Time tracking TSV with 3600s runtime enforcement and proper headers
- Comprehensive mode definitions in `.roomodes` for TODO execution
- TODO-driven workflow guide and operational protocols

### Current TODO.md Status
- **Active High Priority**: Time tracking enforcement implementation (completed)
- **Implementation Tasks**: Task definition audit (completed), runtime enforcement (completed), CI check (optional - pending)
- **Completion Tracking**: Items marked complete upon successful execution and acceptance criteria verification

### Identified Gaps and Active TODO Items
- [ ] Add automated CI check (optional) - CI step scanning configs for timeout values >3600s with warnings/failures
- [ ] Rewrite orchestrator.md to integrate with TODO.md system (active - this task)
- Remaining items follow checklist protocols with priority levels and acceptance criteria

## Next Steps - TODO-Driven Roadmap
1. **Execute Remaining TODO.md Implementation Tasks**: Add automated CI check with 3600s timeout scanning
2. **Execute Active TODO.md Task**: Complete orchestrator.md rewrite with full TODO integration
3. **Validate Acceptance Criteria**: Ensure PR updates only orchestrator.md with TODO-centric sections, 3600s default, and CI/tests referencing TODO.md
4. **Maintain Checklist Protocols**: All future development originates from TODO.md with time enforcement and mode delegation