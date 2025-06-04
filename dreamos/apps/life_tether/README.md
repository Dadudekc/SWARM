# Life Tether Module

Life Tether ensures that autonomous agents remain responsive while the system is running. It acts as a watchdog that monitors each agent's message activity and automatically issues resume or restart commands when an agent becomes idle.

## Purpose

- Detect stalled or unresponsive agents.
- Send keep‑alive pings and resume prompts through the unified message system.
- Trigger `AgentManager` or `PeriodicRestart` logic to re‑onboard agents when needed.
- Record uptime metrics for the performance monitor.

## Usage

1. Instantiate `LifeTether` with references to the `MessageSystem` and `AgentManager`.
2. Start the tether as a background task alongside the agent loop:

```python
from pathlib import Path
import asyncio
from dreamos.apps.life_tether.tether import LifeTether
from dreamos.core.messaging.unified_message_system import MessageSystem
from dreamos.core.agent_control.periodic_restart import AgentManager

ums = MessageSystem(runtime_dir=Path("runtime"))
manager = AgentManager(...)

tether = LifeTether(message_system=ums, agent_manager=manager)
asyncio.create_task(tether.run())
```

## Link to the Agent Loop

`LifeTether` observes messages processed by `AgentLoop` and checks for gaps in communication. When a gap exceeds the configured timeout, it sends a resume message to the agent or calls the manager to restart the agent's loop. This keeps long‑running conversations alive and ensures tasks continue without manual intervention.

## Directory Structure

```
dreamos/
└── apps/
    └── life_tether/
        └── README.md
```
