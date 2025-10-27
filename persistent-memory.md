# Non-Obvious Implementation Patterns

This section documents implementation patterns that are not immediately obvious from code inspection.

## Core Implementation Patterns
- **Event-Driven Polling**: Use timed polling loops in main thread for updates instead of threading
- **Sequential Resource Rotation**: Increment resource index circularly on errors rather than random selection
- **Conditional Delay Mechanisms**: Implement delays on specific conditions before operations
- **Response Parsing**: Remove unwanted tags from external responses
- **Dynamic Dependency Management**: Auto-install missing packages via subprocess during startup

## System Architecture Patterns
- **GUI Processing Coupling**: Processing logic embedded in GUI event loop despite separation attempts
- **File-Based State Management**: Runtime files replace database despite available backends
- **Runtime Dependency Management**: Missing packages installed via subprocess instead of proper dependency management
- **Cache-Centric Processing**: Architecture centered around cache misses rather than data flow optimization
- **Multi-Technology Architecture**: Legacy GUI + plugin production system despite single-repo structure
- **Hidden Configuration Dependencies**: Critical configuration files not visible in repository
- **Integration Layer Disguise**: Components appearing as examples but serving as live integration layers
- **Multi-Queue Background Processing**: Multiple queue systems with graceful degradation fallback
- **Robust Error Recovery System**: Multi-layer error handling with fallback mechanisms and endpoint redundancy

## Project Structure Patterns
- **Autoloading with Fallbacks**: Uses autoloading standards with fallback mechanisms for missing dependencies
- **Complex Endpoint Management**: Multiple endpoints with validation and rate limiting across architecture

## Deployment Patterns
- **Git-Based Continuous Deployment**: `git push` deployment using authentication tokens

## Runtime Debugging Patterns
- **Model Cooldown Silent Failures**: Model state files timestamps cause silent blocking; check Unix time comparisons for debugging
- **GUI Update Freezes**: UI update calls in main thread prevent locks, but block event processing unexpectedly
- **Multi-Technology Stack Debugging**: Hybrid technology systems require checking multiple state files for consistency
- **Endpoint Validation Debugging**: Multiple endpoints with complex validation; check rate limiting and fallback mechanisms when endpoints fail
- **Background Processing Silent Failures**: Processing queues may fail silently; check logs and queue system status

## Emergency Recovery Procedures
- **Complex Multi-Mode Recovery**: Multi-mode recovery with rollback capabilities

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