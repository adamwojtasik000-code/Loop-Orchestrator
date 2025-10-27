# AGENTS.md

This file provides debug mode specific guidance when working with code in this repository.

## 🔧 **Non-Obvious Debugging Patterns**

### Runtime Debugging Patterns
- **Model Cooldown Silent Failures**: Model state files timestamps cause silent blocking; check Unix time comparisons for debugging
- **GUI Update Freezes**: UI update calls in main thread prevent locks, but block event processing unexpectedly
- **Multi-Technology Stack Debugging**: Hybrid technology systems require checking multiple state files for consistency
- **Endpoint Validation Debugging**: Multiple endpoints with complex validation; check rate limiting and fallback mechanisms when endpoints fail
- **Background Processing Silent Failures**: Processing queues may fail silently; check logs and queue system status

### System Architecture Patterns
- **Multi-Technology Stack Architecture**: Legacy GUI + modern plugin production system despite single-repo structure
- **Hidden Cache File Dependencies**: Cache files critical for operation but not visible in repo
- **Example Components as Production Layers**: Framework components appear as examples but are live integration layers
- **Multi-Queue Processing Systems**: Scheduler + custom queue system with graceful degradation fallback
- **Comprehensive Error Recovery System**: Multi-layer error handling with autoloading fallbacks and endpoint redundancy

### Emergency Recovery Procedures
- **Complex Multi-Mode Recovery**: Multi-mode recovery with rollback capabilities