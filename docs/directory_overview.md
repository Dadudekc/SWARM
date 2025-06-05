# Directory Overview

This document describes the purpose of the main folders in the repository to make navigation easier.

## Core Components

- `dreamos/` - Core system implementation including orchestrator, messaging, agent management, and self-discovery modules.
- `tools/` - All utility scripts, automation tools, and helper functions for development and operations.
- `discord_bot/` - Discord integration including the bot and command handlers.
- `crime_report_generator/` - Stand‑alone module used for generating crime reports.

## Documentation and Examples

- `docs/` - Project documentation and guides.
- `docs/examples/` - Code samples and examples demonstrating library usage.

## Configuration and Data

- `config/` - Configuration files, templates, and environment settings.
- `runtime/` - Temporary runtime files (queues, logs, etc.).
- `data/` - Data artifacts including dev logs.

## Testing

- `tests/` - Unit and integration tests.
- `requirements-test.txt` - Additional dependencies needed for testing.

## Miscellaneous

- `gui/` - Simple GUI components used by the project.
- `social/` - Social media automation code.
- `prompts/` - Prompt templates and examples.

For a quick visual overview you can run:

```bash
tree -L 2
```
