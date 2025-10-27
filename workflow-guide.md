# TODO-Driven Workflow Guide

*See TODO.md for current task management and persistent-memory.md for commands, achievements, and operational insights*

## Core TODO-Centric Workflow

**MANDATORY**: TODO.md serves as the central task management mechanism for all development work. All tasks must be documented in TODO.md with priority levels, checklist tracking, acceptance criteria, and time enforcement (default 3600s max runtime).

**TODO-Driven Workflow Stages**: Planning Stage → Implementation Stage → Validation Stage → Quality Stage → Integration Stage → [Loop]

**Granular Modes with TODO Integration**:
- **Implementation**: `🔧 Core Development`, `🛡️ Security Development`, `⚡ Performance Development`, `✨ Feature Development`
- **Validation**: `🔍 Static Analysis`, `🧪 Unit Analysis`, `🔗 Integration Analysis`, `🌐 API Analysis`
- **Quality**: `✅ Functional Assurance`, `📊 Performance Assurance`, `🔒 Security Assurance`, `🔄 Compatibility Assurance`
- **Integration**: `💾 Version Control`, `🚀 Deployment`, `📝 Documentation`, `🎯 Release`
- **Planning**: `📈 Analysis`, `🎯 Prioritization`, `🏗️ Architecture`, `📋 Requirements`

**TODO Management Conventions**:
- **Priority Levels**: High priority (time-sensitive, blocking), Implementation (core development tasks)
- **Checklist Tracking**: Use checkboxes for progress, include specific commands and deliverables
- **Time Enforcement**: Default 3600s runtime limit, with automated checks and documented exceptions
- **Acceptance Criteria**: Clear deliverables and completion conditions in each TODO item

## Checklist-Based Execution Protocols

**TODO-Driven Execution Protocol**:
1. **TODO Creation (MANDATORY)**: Create detailed TODO.md entry with priority level, acceptance criteria, time limit (default 3600s), and checklist items before any work
2. **Time Tracking (TOP PRIORITY)**: Start `⏱️ Task Time Tracking` and validate against TODO time limits during execution
3. **Checklist Progress**: Update TODO.md checkboxes as each subtask completes, include specific commands executed
4. **Complete Context**: Include ALL TODO requirements and acceptance criteria in subtask delegation
5. **Contextual Data**: Read from TODO.md and persistent-memory.md for context, update findings in TODO notes
6. **Clarifying Questions**: Ask feature requirements and user stories before major transitions (focus on acceptance criteria)
7. **Subtask Delegation**: Use `new_task` with TODO-specific instructions, priority levels, and time constraints
8. **Recursive Pattern**: Subtasks create subtasks for complex work (max depth 5), all tracked in parent TODO
9. **Environment Sync**: Sync at TODO checklist checkpoints (implementation, validation, integration)
10. **TODO Completion**: Mark TODO complete only when all acceptance criteria met, include final deliverables

**Checklist Execution Steps**:
- [ ] **Pre-Execution**: Verify TODO exists with clear acceptance criteria and time limits
- [ ] **Time Validation**: Confirm task runtime within 3600s default (or documented exception)
- [ ] **Priority Check**: Ensure high-priority tasks complete before implementation tasks
- [ ] **Delegate to Mode**: Spawn appropriate specialized mode with TODO context
- [ ] **Progress Tracking**: Update checkboxes for each completed action
- [ ] **Time Monitoring**: Monitor against time limits, abort if exceeded without exception
- [ ] **Acceptance Validation**: Confirm deliverables meet TODO criteria
- [ ] **Documentation**: Update TODO with completion notes and executed commands

## TODO-Driven Workflow Stages

### Stage 1: Planning (Priority-Based TODO Creation)
- [ ] **TODO Creation**: Add task to TODO.md with priority level (high vs implementation)
- [ ] **Acceptance Criteria**: Define clear deliverables and completion conditions
- [ ] **Time Limits**: Set runtime expectations (default 3600s, document exceptions)
- [ ] **Checklist Breakdown**: Decompose into actionable checkbox items
- [ ] **Mode Assignment**: Determine appropriate specialized mode for execution
- **Time Limit**: Complete within 1800s (30min) or document extension in TODO

### Stage 2: Implementation (Checklist Execution)
- [ ] **Mode Delegation**: Spawn specialized mode with TODO requirements
- [ ] **Progress Tracking**: Update checkboxes as sub-tasks complete
- [ ] **Time Enforcement**: Monitor against 3600s default, abort on exceedance
- [ ] **Command Documentation**: Record executed commands in TODO notes
- [ ] **Acceptance Validation**: Verify deliverables match criteria
- **Time Limit**: Complete within configured TODO time limit

### Stage 3: Validation (Automated Checks)
- [ ] **Static Analysis**: Run linting and type checking
- [ ] **Unit Tests**: Execute test suite for new/changed code
- [ ] **Integration Tests**: Validate system-level interactions
- [ ] **TODO Updates**: Mark validation checkboxes complete
- **Time Limit**: Complete within 900s (15min) per validation cycle

### Stage 4: Quality Assurance (Standards Compliance)
- [ ] **Performance Review**: Check performance metrics against benchmarks
- [ ] **Security Audit**: Validate security compliance
- [ ] **Compatibility Testing**: Ensure cross-platform compatibility
- [ ] **Documentation**: Update inline docs and external docs
- **Time Limit**: Complete within 1800s (30min)

### Stage 5: Integration (Final Delivery)
- [ ] **Version Control**: Commit changes with descriptive messages
- [ ] **Deployment Prep**: Validate deployment readiness
- [ ] **Release Notes**: Update release documentation
- [ ] **TODO Completion**: Mark all checkboxes complete with final notes
- **Time Limit**: Complete within 900s (15min)

**Loop Back Protocol**: If any stage fails acceptance criteria, loop back to appropriate stage with updated TODO checklist

## Key TODO Protocols

**Time Enforcement Priority**:
- MUST validate TODO time limits before execution
- On exceedance: abort operation, document exception in TODO, require approval for continuation
- Atomic operations with TODO tracking; complete checklists required for progression
- Failed time enforcement marks tasks as "time-limit-pending"

**Subtask Patterns with TODO Tracking**:
- Max depth 5 levels; deeper nesting triggers TODO consolidation
- Termination: objectives met, acceptance criteria satisfied, or time limits exceeded (default 3600s)
- Cycle detection prevents infinite recursion through TODO parent-child relationships
- Resource bounds: 50% of parent TODO allocation

**Information Flow with TODO Integration**:
- Forward: Implementation → Validation → Quality → Integration → Planning (tracked via TODO progression)
- Backward: Failed validations → new TODO items for fixes; merge conflicts → resolution TODOs
- All inter-subtask data exchange validated against TODO acceptance criteria

## TODO-Centric Environment Management

**Synchronization Protocol with TODO Tracking**: All operations require successful sync before TODO checklist progression; failures create new TODO items for resolution

**Synchronization Checkpoints**:
- Implementation: Sync relevant files after code changes, update TODO with sync status
- Validation: Sync before validation runs, document sync results in TODO notes
- Integration: Sync before integration testing, verify sync completion in checklist

**Environment Requirements**: Define project-specific runtime requirements and dependencies in TODO acceptance criteria
**Common Commands** (documented in TODO notes):
- Test Runner: Execute project test suite with standard configuration
- Parallel Execution: Run tests in parallel with configurable process limits

## TODO-Driven Task Coordination

**Inter-Mode Communication via TODO**: Clear protocols for data exchange with TODO validation and acknowledgment

**Dependency Resolution**: TODO parent-child relationships ensure dependent tasks complete before starting; high priority tasks block implementation tasks

**Error Propagation with TODO Tracking**: Handle/report errors across mode boundaries with new TODO items and escalation procedures

**Rollback Procedures**: Recovery steps for process failures with automatic TODO creation for remediation

## TODO-Focused Clarification Protocol

- **Pre-Transition**: Ask feature requirements and user stories to refine TODO acceptance criteria
- **Post-Completion**: Validate deliverables against TODO criteria after each phase
- **Backtrack Triggers**: Create new TODO items for root cause analysis when loops occur
- **Knowledge Preservation**: Update persistent-memory.md and TODO notes with insights to preserve

*This guide outlines a TODO-driven approach to workflow management, emphasizing checklist-based execution, priority levels, time enforcement, and iterative improvement through TODO.md integration.*