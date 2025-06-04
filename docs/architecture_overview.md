# System Architecture Overview

This document summarizes the high level architecture of Dream.OS.

## Core Layers
1. **System Orchestrator** – coordinates all agents and services.
2. **Messaging Layer** – provides the `CellPhone` and `CaptainPhone` channels with history tracking.
3. **Task Manager** – assigns and monitors tasks across agents.
4. **Logging/Devlog** – central log manager with optional Discord mirroring.
5. **Extensions** – modules such as StealthBrowser and Dreamscribe extend core capabilities.

```
Agent <-> CellPhone <-> UnifiedMessageSystem <-> Agent
                     ^
                     |
                  Captain
```

External services (Discord, trading APIs, web automation) plug into the orchestrator via adapters. Dreamscribe stores narrative memory under `runtime/`, while StealthBrowser enables low-detection browser automation for the ChatGPT and Codex bridges.
