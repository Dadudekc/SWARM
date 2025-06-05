# Directory Overview

This document describes the purpose of the main folders in the repository to make navigation easier.

## Core Components

- `dreamos/` - Core system implementation including orchestrator, messaging and agent management modules.
- `agent_tools/` - Helper utilities for scanning and managing agents.
- `discord_bot/` - Discord integration including the bot and command handlers.
- `crime_report_generator/` - Stand‑alone module used for generating crime reports.

## Utilities and Scripts

- `tools/` - Assorted helper scripts used in development and operations.
- `docs/examples/` - Small code samples demonstrating library usage.
- `docs/` - Project documentation.

## Data and Runtime

- `config/` - Configuration templates and environment files.
- `runtime/` - Temporary runtime files (queues, logs, etc.).
- `data/` - Data artifacts including dev logs and generated reports.

## Testing

- `tests/` - Unit and integration tests.
- `requirements-test.txt` - Additional dependencies needed for testing.

## Miscellaneous

- `gui/` - Simple GUI components used by the project.
- `social/` - Social media automation code.
- `docs/episodes/` - Sample content loops and scenarios.
- `prompts/` - Prompt templates and examples.

For a quick visual overview you can run:

```bash
tree -L 2
```
