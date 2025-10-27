# AGENTS.md

This file provides ask mode specific guidance when working with code in this repository.

## 📋 **Non-Obvious Inquiry Patterns**

### Project Structure Patterns
- **Misleading File Structure**: Repositories may contain multiple technology stacks despite names suggesting single technology focus
- **Hidden Runtime Dependencies**: Cache files or state files critical for operation but not visible in repository
- **Integration Layer Disguises**: Components appearing as examples are actually production integration layers
- **UI Integration Patterns**: Core scripts appearing headless may include GUI components that require main thread execution
- **Autoloading with Fallbacks**: Systems using standard autoloading with fallback mechanisms for missing dependencies
- **Endpoint Complexity**: Multiple endpoints with complex validation and rate limiting across architectures

### System Architecture Patterns
- **Multi-Technology Architecture**: Combining legacy and modern systems in single repository despite technological diversity
- **Hidden Runtime Dependencies**: Cache files or state files critical for operation but not visible in repository
- **Integration Layer Disguises**: Components appearing as examples are actually production integration layers
- **Background Processing Systems**: Multiple queuing mechanisms with graceful degradation fallback
- **Comprehensive Error Recovery System**: Multi-layer error handling with autoloading fallbacks and endpoint redundancy