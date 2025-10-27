# AGENTS.md

This file provides code mode specific guidance when working with code in this repository.

## 🔄 **Non-Obvious Coding Patterns**

### Core Implementation Patterns
- **Event-Driven Polling**: Use timed polling loops in main thread for updates instead of threading
- **Sequential Resource Rotation**: Increment resource index circularly on errors rather than random selection
- **Conditional Delay Mechanisms**: Implement delays on specific conditions before operations
- **Response Parsing**: Remove unwanted tags from external responses
- **Dynamic Dependency Management**: Auto-install missing packages via subprocess during startup

### System Architecture Patterns
- **UI Logic Integration**: Processing logic embedded in UI event loop despite separation attempts
- **Filesystem-Based State**: Runtime files replace database despite backend availability
- **External Process Dependencies**: Missing packages installed via external processes instead of proper management
- **Cache-Driven Processing**: Architecture centered around cache misses rather than data flow optimization
- **Multi-Technology Architecture**: Legacy GUI + modern plugin production system despite single-repo structure
- **Implicit Configuration Dependencies**: Configuration files critical for operation but not visible in repo
- **Framework Integration Layers**: Framework components appear as examples but are live integration layers
- **Multi-Queue Processing Systems**: Scheduler + custom queue system with graceful degradation fallback
- **Comprehensive Error Recovery System**: Multi-layer error handling with autoloading fallbacks and endpoint redundancy

### Project Structure Patterns
- **Autoloading Mechanisms with Fallbacks**: Framework uses autoloading with fallback mechanisms for missing dependencies
- **Endpoint Management Complexity**: Multiple endpoints with complex validation and rate limiting across architecture

### Critical Command Patterns
- **Parallel Execution Strategies**: Use custom parallel execution for testing with process limits