# AGENTS.md

This file provides architect mode specific guidance when working with code in this repository.

## 🏗️ **Non-Obvious Architecture Patterns**

### System Architecture Patterns
- **GUI Processing Coupling**: Processing logic embedded in GUI event loop despite separation attempts
- **File-Based State Management**: Runtime files replace database despite available backends
- **Runtime Dependency Management**: Missing packages installed via subprocess instead of proper dependency management
- **Cache-Centric Processing**: Architecture centered around cache misses rather than data flow optimization
- **Multi-Technology Architecture**: Legacy GUI + plugin production system despite single-repo structure
- **Hidden Configuration Dependencies**: Critical configuration files not visible in repository
- **Integration Layer Disguise**: Components appearing as examples but serving as live integration layers
- **Multi-Queue Background Processing**: Multiple queue systems with graceful degradation fallback
- **Robust Error Recovery System**: Multi-layer error handling with fallback mechanisms and endpoint redundancy

### Project Structure Patterns
- **Autoloading with Fallbacks**: Uses autoloading standards with fallback mechanisms for missing dependencies
- **Complex Endpoint Management**: Multiple endpoints with validation and rate limiting across architecture

### Deployment Patterns
- **Git-Based Continuous Deployment**: `git push` deployment using authentication tokens