# Workflow Guide

*See documentation for commands, achievements, and operational insights*

## Core Workflow

**MANDATORY**: Delegate ALL work to specialized modes using `new_task`. Subtasks create subtasks for complex work. Pass ALL data between subtasks.

**Workflow Stages**: Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5 → [Loop]

**Granular Modes**:
- **Implementation**: `🔧 Core Implementation`, `🛡️ Security Implementation`, `⚡ Performance Implementation`, `✨ Feature Implementation`
- **Validation**: `🔍 Static Validation`, `🧪 Unit Validation`, `🔗 Integration Validation`, `🌐 API Validation`
- **Quality**: `✅ Functional Quality`, `📊 Performance Quality`, `🔒 Security Quality`, `🔄 Compatibility Quality`
- **Integration**: `💾 Commit Integration`, `🚀 Deploy Integration`, `📝 Document Integration`, `🎯 Release Integration`
- **Planning**: `📈 Planning Analysis`, `🎯 Planning Priorities`, `🏗️ Planning Architecture`, `📋 Planning Requirements`

## Execution Protocol

**Core Execution Protocol**:
1. **Time Tracking (TOP PRIORITY)**: Start `⏱️ Task Time Tracking` and record timing before any task execution
2. **Graph Analysis**: Identify optimal execution path
3. **Complete Context**: Include ALL data, configurations, and history
4. **Contextual Data**: Read from relevant sources for context, update with findings
5. **Clarifying Questions**: Ask ≥3 clarifying questions before each major transition
6. **Subtask Delegation**: Use `new_task` with comprehensive instructions to granular modes
7. **Recursive Pattern**: Subtasks create subtasks for complex work (max depth 5)
8. **Environment Sync**: Sync at key points (implementation, validation, integration)
9. **Finalize Time Tracking**: Write end timestamp to task_timing.tsv before completion

## Key Protocols

**Time Tracking Priority**:
- MUST be initiated before any task execution
- On failure: abort operation, log to relevant sources, retry up to 3 times with exponential backoff
- Atomic operations with file locking; complete pairs required for analysis
- Failed recordings mark tasks as "finalization-pending"

**Subtask Patterns**:
- Max depth 5 levels; deeper nesting triggers consolidation
- Termination: objectives met, resources exhausted, or time limits exceeded (max 2 hours)
- Cycle detection prevents infinite recursion
- Resource bounds: 50% of parent allocation

**Information Flow**:
- Forward: Implementation → Validation → Quality → Integration → Planning
- Backward: Failed tests → fixes; merge conflicts → resolution
- All inter-subtask data exchange validated with acknowledgment

## Environment Management

**Synchronization Protocol**: All operations require successful sync before progression; failures block advancement

**Synchronization Points**:
- Implementation: Sync relevant files after code changes
- Validation: Sync before validation, run necessary checks after
- Integration: Sync before integration testing

**Environment Requirements**: Define project-specific runtime requirements and dependencies
**Common Commands**:
- Test Runner: Execute project test suite with standard configuration
- Parallel Execution: Run tests in parallel with configurable process limits

## Task Coordination

**Inter-Mode Communication**: Clear protocols for data exchange with validation and acknowledgment

**Dependency Resolution**: Automatic prerequisite checking; ensure dependent tasks complete before starting

**Error Propagation**: Handle/report errors across mode boundaries with escalation procedures

**Rollback Procedures**: Recovery steps for process failures with automatic triggers

## Clarification Protocol

- **Pre-Transition**: ≥3 clarifying questions before each major process transition
- **Post-Completion**: Validate understanding after each phase completion
- **Backtrack Triggers**: Questions about root causes when loops occur
- **Knowledge Preservation**: Questions about what insights to preserve

*This guide outlines a structured approach to workflow management, emphasizing task delegation, data flow, and iterative improvement.*