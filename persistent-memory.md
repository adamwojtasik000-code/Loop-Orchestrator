# Non-Obvious Implementation Patterns

This section documents implementation patterns that are not immediately obvious from code inspection.

## Core Implementation Patterns
- **Event-Driven Polling**: Use timed polling loops in main thread for updates instead of threading
- **Sequential Resource Rotation**: Increment resource index circularly on errors rather than random selection
- **Conditional Delay Mechanisms**: Implement delays on specific conditions before operations
- **Response Parsing**: Remove unwanted tags from external responses
- **Dynamic Dependency Management**: Auto-install missing packages via subprocess during startup

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

## Emergency Recovery Procedures
- **Multi-Level Recovery Strategies**: Implement recovery procedures with rollback and mode-switching capabilities

# Development & Debug Commands

This section contains commands useful for development and debugging.

## Common Commands
- Test Runner: Execute project test suite with standard configuration
- Parallel Execution: Run tests in parallel with configurable process limits

## Critical Command Patterns
- **Parallel Execution Strategies**: Use custom parallel execution for testing with process limits

# System Updates & Status

This section tracks system updates and status changes using apache-style log format.

[2025-10-27T09:45:30.412Z] [optimization-memory] - [creation]: Created persistent-memory.md file with required 3-section structure