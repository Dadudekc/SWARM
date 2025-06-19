# Dream.OS Autonomous Operations Guide

> **Reference Protocol**: This document extends the [Master Onboarding Guide](00_agent_onboarding.md)
> **Version**: 1.0.0
> **Last Updated**: 2024-03-19
> **Status**: ✅ Aligned with master onboarding

## Overview
This guide details how to operate autonomously within the Dream.OS network.

## Autonomous Operation

### 1. Self-Learning System
- Experience accumulation
- Knowledge sharing
- Performance optimization
- Error prevention

### 2. Code Reuse System
- Search before implementation
- Adapt existing solutions
- Share new solutions
- Document patterns

### 3. Task Management
- Validate tasks
- Check existing solutions
- Execute with monitoring
- Update knowledge

### 4. Error Handling
- System errors
- Task errors
- Resource errors
- Communication errors
- Security errors

## CLI Operations

### 1. Core Commands
```bash
# Task Management
task list              # List all tasks
task create <type>     # Create new task
task status <id>       # Check task status
task cancel <id>       # Cancel task

# System Management
system status          # Check system status
system restart         # Restart system
system update          # Update system

# Resource Management
resource list          # List resources
resource allocate <id> # Allocate resource
resource free <id>     # Free resource

# Debug Operations
debug start            # Start debug mode
debug stop             # Stop debug mode
debug log <level>      # Set log level
```

## Code Reuse Patterns

### 1. Utility Functions
- Input validation
- Error handling
- Resource management
- State persistence

### 2. Base Classes
- Common initialization
- Shared functionality
- Standard interfaces
- Error handling

## Next Steps
1. Review [System Integration](03_system_integration.md)
2. Return to [Core Guide](01_agent_core.md)
3. Study [Advanced Topics](04_advanced_topics.md)

Remember: Your ability to reuse code and prevent duplication is crucial to the network's success. Always check for existing solutions before implementing new ones.

### Discord Event Schema (v2)

All scripts should construct **DiscordEvent** payloads before handing them to
`agent_tools.discord.post_status()`.  The helper accepts plain strings too, but
using the schema unlocks richer embeds and future automation.

```py
from dreamos.discord.events import make_event
from agent_tools.discord import post_status

ev = make_event(title="Task Completed", body="Parser refactor merged", level="info", agent="Agent-2")
post_status("Agent-2", ev)
```

Field reference:
| key       | type                 | notes                                   |
|-----------|----------------------|-----------------------------------------|
| title     | str                  | Embed title                             |
| body      | str                  | Main content (markdown ok)              |
| tags      | list[str]            | Optional hashtags / metadata            |
| level     | "info"\|"warn"\|"error" | Controls embed colour                 |
| timestamp | str (ISO-8601 UTC)   | Auto-filled by `make_event()`           |
| agent     | str                  | Source identifier (optional)            |

> Colour map: info → blue, warn → yellow, error → red 