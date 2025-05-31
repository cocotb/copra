# Complex CPU Example

A comprehensive example demonstrating copra's capabilities with a multi-core CPU design featuring AXI/APB interfaces, debug support, and performance monitoring.

## Design Overview

- **4-core CPU** with individual clock gating
- **AXI4 master interfaces** (instruction fetch and data memory)
- **APB slave interface** for control/status registers
- **16 interrupt sources** with handling
- **Debug interface** for register access
- **Performance counters** for monitoring

### Module Hierarchy

