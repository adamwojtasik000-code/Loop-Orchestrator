# Non-Obvious Implementation Patterns

## Core Implementation Patterns
- **Event-Driven Polling**: Use timed polling loops in main thread for updates instead of threading
- **Sequential Resource Rotation**: Increment resource index circularly on errors rather than random selection
- **Conditional Delay Mechanisms**: Implement delays on specific conditions before operations
- **Response Parsing**: Remove unwanted tags from external responses
- **Dynamic Dependency Management**: Auto-install missing packages via subprocess during startup

## TODO Integration Patterns
- **Task Management Centralization**: TODO.md serves as the central component for task tracking, workflow orchestration, and developer checklists
- **Checklist-Driven Development**: Maintain developer-focused checklists with small, actionable items and checkbox progress tracking
- **Time Tracking Enforcement**: Implement runtime limits (default 3600s) for tasks with automated checks and enforcement mechanisms
- **Priority-Based Task Organization**: Structure tasks by priority levels (high, implementation) with clear acceptance criteria
- **Command Documentation in Tasks**: Include specific commands, notes, and deliverables directly in task descriptions for actionable workflows

## System Architecture Patterns
- **UI Logic Integration**: Processing logic embedded in UI event loop despite separation attempts
- **Filesystem-Based State**: Runtime files replace database despite backend availability
- **External Process Dependencies**: Missing packages installed via external processes instead of proper management
- **Cache-Driven Processing**: Architecture centered around cache misses rather than data flow optimization
- **Multi-Technology Architecture**: Legacy GUI + modern plugin production system despite single-repo structure
- **Implicit Configuration Dependencies**: Configuration files critical for operation but not visible in repo
- **Framework Integration Layers**: Framework components appear as examples but are live integration layers
- **Multi-Queue Processing Systems**: Scheduler + custom queue system with graceful degradation fallback
- **Comprehensive Error Recovery System**: Multi-layer error handling with autoloading fallbacks and endpoint redundancy

## Project Structure Patterns
- **Autoloading Mechanisms with Fallbacks**: Framework uses autoloading with fallback mechanisms for missing dependencies
- **Endpoint Management Complexity**: Multiple endpoints with complex validation and rate limiting across architecture

## Deployment Patterns
- **Automated Deployment Pipeline**: Continuous deployment using version control and authentication mechanisms

## Runtime Debugging Patterns
- **State Synchronization Issues**: Check timestamp comparisons for timing-related failures
- **UI Thread Blocking**: Main thread operations causing interface freezes
- **Multi-System Consistency**: Verify state across different technology components
- **Endpoint Failure Handling**: Inspect rate limiting and fallback logic during service failures
- **Background Task Failures**: Monitor queue systems and logging for silent errors
- **Model Cooldown Silent Failures**: Model state files timestamps cause silent blocking; check Unix time comparisons for debugging
- **GUI Update Freezes**: GUI update calls in main thread prevent locks, but block event processing unexpectedly
- **Multi-Technology Stack Debugging**: Hybrid technology systems require checking multiple state files for consistency

## Emergency Recovery Procedures
- **Multi-Level Recovery Strategies**: Implement recovery procedures with rollback and mode-switching capabilities
- **Complex Multi-Mode Recovery**: Multi-mode recovery with rollback capabilities

## TODO Integration Workflows
- **Task Creation Workflow**: Add new development tasks to TODO.md with specific action items, acceptance criteria, and deliverable descriptions
- **Progress Tracking Workflow**: Update task status using checkboxes, include completion notes and executed commands for transparency
- **Timeout Audit Workflow**: Search repository for timeout configurations (timeout, max_time fields), compile list of tasks needing timeout adjustments or justifications
- **Runtime Enforcement Workflow**: Implement orchestrator guards that monitor task execution time, failing or warning when exceeding 3600s default unless explicitly exempted
- **CI Integration Workflow**: Add automated CI checks that scan configuration files for timeout values exceeding 3600s, providing warnings or failures with review exemption options

# Development & Debug Commands

## Common Commands
- Test Runner: Execute project test suite with standard configuration
- Parallel Execution: Run tests in parallel with configurable process limits

## Critical Command Patterns
- **Parallel Execution Strategies**: Use custom parallel execution for testing with process limits

## TODO Management Commands
- **Timeout Audit Command**: grep -r "timeout\|max_time" . --include="*.py" --include="*.yaml" --include="*.json" to identify timeout configurations across the repository
- **Runtime Enforcement Command**: Implement a monitoring hook in orchestrator that tracks task start/end times and compares against configured max runtime limits
- **CI Check Command**: Add a CI script that validates timeout values in configuration files, failing builds with values >3600s unless marked with exemption flags

# System Updates & Status

[2025-10-27T10:06:36.829Z] [optimization-memory] - [creation]: Created persistent-memory.md with required 3-section structure and migrated patterns from project-memory.md
[2025-10-27T10:07:20.238Z] [optimization-memory] - [migration]: Migrated additional patterns from .roo/rules-*/AGENTS.md files and consolidated content
[2025-10-27T10:07:46.419Z] [optimization-memory] - [cleanup]: Archived project-memory.md as project-memory.md.archived after migration
[2025-10-27T10:11:02.227Z] [integration-commit] - [commit]: Committed .roomodes with message "Loop 4: Further generalize custom-modes.yaml"
- Finding: User clarified that .roomodes is the file to commit, not custom-modes.yaml
- Command: git add .roomodes && git commit -m "Loop 4: Further generalize custom-modes.yaml"
- Achievement: Successfully committed with hash 88c288e
- Insight: File was staged and committed despite commit message referencing incorrect filename
## [2025-10-27T10:12:37.622Z] [integration-commit] - [commit]
- Finding: Final commit staged all remaining changes as requested
- Command: git add . && git commit -m "Loop 5: Final project-agnostic refinements"
- Achievement: Committed with hash ae894ce
- Insight: Successfully staged and committed 3 files with changes including new archived file and renamed workflow guide

## [2025-10-27T10:12:49.432Z] [integration-commit] - [push]
- Finding: Pushed commit to GitHub repository as specified
- Command: git push origin main
- Achievement: Push successful from commit 88c288e to ae894ce
- Insight: Repository updated with final refinements, 4 objects pushed with 1 delta
## [2025-10-27T10:48:10.557Z] [time-tracking] - [initialization]
- Finding: Initialized time tracking for orchestrator analysis session
- Command: Generated task ID c25e8085 and appended start entry to task_timing.tsv
- Achievement: Task tracking started with status 'started'
- Insight: Time tracking system initialized for current session

## [2025-10-27T10:49:56.955Z] [time-tracking] - [completion]
- Finding: Completed time tracking for orchestrator analysis session
- Command: Updated task_timing.tsv with end time 2025-10-27T10:49:32.068Z, calculated duration 81 seconds, marked status as completed
- Achievement: Task c25e8085 successfully closed with completion status
- Insight: Orchestrator analysis session completed in 81 seconds, demonstrating efficient time tracking implementation

## [2025-10-27T10:52:04.409Z] [time-tracking] - [initialization]
- Finding: Initialized time tracking for system initialization implementation task
- Command: Generated task ID 56bf2dbd and appended start entry to task_timing.tsv
- Achievement: Task tracking started with status 'started'
- Insight: Time tracking system initialized for current system initialization implementation session

## [2025-10-27T18:18:39.799Z] [time-tracking] - [completion]
- Finding: Completed time tracking for system initialization implementation task
- Command: Updated task_timing.tsv with end time 2025-10-27T18:18:10.648Z, calculated duration 26766 seconds, marked status as completed
- Achievement: Task 56bf2dbd successfully closed with completion status
- Insight: System initialization implementation session completed in 26766 seconds (approximately 7 hours 26 minutes), demonstrating comprehensive task tracking implementation
[2025-10-27T18:28:59.026Z] [optimization-memory] - [rewrite]: Rewrote persistent-memory.md to integrate TODO.md as central task management component, added TODO integration patterns and workflows, aligned all procedures with TODO.md-centric operations
## [2025-10-27T18:30:18.263Z] [implementation-core] - [task_delegation]
- Finding: Delegated workflow-guide.md rewrite to implementation-features mode with comprehensive TODO.md integration requirements
- Command: Spawned new_task in implementation-features mode for workflow guide rewrite
- Achievement: Successfully initiated feature implementation task for TODO.md workflow integration
- Insight: Delegation ensures specialized mode handles complex documentation rewrite with TODO-centric focus
## [2025-10-27T18:33:54.929Z] [implementation-core] - [completion_verification]
- Finding: Verified workflow-guide.md rewrite completed successfully, integrating TODO.md as central task management
- Command: Read rewritten workflow-guide.md, confirmed TODO-driven stages and checklist protocols implemented
- Achievement: Workflow guide now centers on TODO.md with checklist-based execution and time enforcement
- Insight: All procedural guidance now aligns with TODO.md-centric operations as required
## [2025-10-27T18:33:39.471Z] [implementation-features] - [rewrite]
- Finding: Rewrote workflow-guide.md to integrate TODO.md as central task management mechanism, emphasizing checklist-based execution with priority levels and time enforcement
- Command: Multiple apply_diff operations to restructure document around TODO.md centrality
- Achievement: Successfully transformed workflow-guide.md into TODO-driven guide with checklist protocols, stage-by-stage checklists, and updated all procedural guidance
- Insight: Document now centers on TODO.md as primary management tool, with clear acceptance criteria, time limits, and progress tracking integration

## [2025-10-27T18:39:15.882Z] [debug] - [timeout_enforcement_audit]
- Finding: Completed timeout enforcement audit with no current config violations, one historical task exceeding 3600s limit (26766s), runtime guard implemented with warnings and failure mechanisms
- Command: Audited task definitions, analyzed historical data, implemented orchestrator runtime enforcement, updated documentation
- Achievement: Time tracking timeout enforcement implemented with 3600s limit, automated checks and runtime guards operational
- Insight: System now enforces 3600s default timeout with warnings for exceedances and failures for violations unless explicitly exempted
