# Dream.OS Feature Analysis and LLM Prompt Guide

This guide summarizes the most important pieces of Dream.OS and explains how they fit together.  Each section highlights the primary modules and design choices so another developer or language model can reproduce the architecture.  At the end you'll find a set of prompts that can be fed to an LLM to iteratively recreate the core features.

## Major Features

### Agent Control and Coordination
- Central management of multiple agents with lifecycle controls.
- Agents communicate via inbox files and specialized channels.
- Supports auto‑restart and monitoring via Discord.
- Key modules: `dreamos/core/agent_control/agent_manager.py`,
  `agent_restarter.py`, and `agent_onboarder.py`.
- Agents are registered with unique IDs and maintain persistent state files.

### Messaging System
- Mailbox-based message routing with delivery confirmation and retries.
- Direct agent-to-agent communication through the **CellPhone** interface.
- Dedicated **CaptainPhone** channel for high-priority tasks.
- Messages are stored under `dreamos/mailbox/<agent>/inbox.json`.
- `MessageHandler` and `CellPhone` classes handle routing and retries.
- Sequence numbers and cleanup routines keep the mailbox tidy.

### Task Management
- `TaskManager` class creates and assigns tasks with priorities and dependencies.
- Tracks task history and integrates with agent status monitoring.
- Tasks are stored in JSON files under `config/agent_comms/`.
- Supports categories (agent, bridge, system) and priority levels.
- Provides helper functions like `create_task` and `start_task` for agents.

### Logging and Monitoring
- `LogManager` handles structured logs for system, agents, and tasks.
- Supports log rotation and archival with metrics collection.
- Optional GUI dashboard and Discord log summaries.
- Metrics are collected by `dreamos/core/monitoring/metrics` and visualized with Grafana.
- Log files live under `runtime/logs/` and can be tailed from Discord.

### Bridge Architecture
- `BridgeManager` coordinates connections to external services.
- Includes connection lifecycle management, message routing, and security layers.
- ChatGPT integration lives in `dreamos/core/bridge/chatgpt/bridge.py` with handlers and processors.
- Health monitoring ensures bridge sessions stay alive and will retry on failure.

### Social Media Automation
- Modules for automating posts across Twitter, Facebook, Reddit, Instagram, LinkedIn, and StockTwits.
- Scheduling and engagement tracking are part of the roadmap.
- Located under `social/` with helpers for OAuth and API requests.
- Can be triggered via tasks or Discord commands.

### Voice Integration
- Text-to-speech and voice channel support via `discord_bot/voicebot.py`.
- Multiple TTS engines (gTTS, Edge TTS) managed by `discord_bot/tts.py`.
- Useful for audio notifications or narrated summaries.

### Dreamscribe Narrative Memory
- `Dreamscribe` ingests devlogs and system events into memory fragments.
- Enables historical context for agents by connecting memories into narrative threads.
- Stored under `runtime/memories/` with APIs for querying and insight generation.
- Provides chronological narrative threads that agents can reference for context.

### Discord Control Interface
- Provides commands for listing, resuming, and verifying agents.
- Supports broadcasting messages and viewing log summaries from Discord.
- Includes voice features for text-to-speech via `discord_bot/voicebot.py`.
- Administrators can manage agents directly from Discord channels.

### UI Automation and Dashboard
- PyQt-based dashboard for monitoring agents and running commands.
- `dreamos/core/automation/ui` contains cursor helpers, menu builders, and the
  `AgentDashboard` window.
- Supports agent status panels, on-screen controls, and scriptable UI flows.

### Browser Automation
- Stealth browser integration under `agent_tools/swarm/browser` for undetected
  web automation.
- Handles login flows, cookie management, and anti-detection headers.
- Enables web scraping and external service interaction without official APIs.

### Metrics and Grafana Dashboard
- Metrics server collects system performance and health data.
- Time-series metrics are exported to Prometheus and visualized with Grafana.
- Dashboard panels show agent activity, resource usage, and alert conditions.

### Security Architecture
- Authentication and authorization layers protect agent operations.
- Encryption utilities manage secrets and secure communication channels.
- Security monitoring hooks produce audit logs and alerts.

### Code Duplication Analysis
- Utilities in `agent_tools/swarm/analyzers` scan for duplicate code and config.
- Helps keep the project maintainable by highlighting redundant logic.

### Additional Modules
- `crime_report_generator/` demonstrates a specialized standalone module.
- `tools/life_os_dashboard.py` offers a personal dashboard for quick agent
  access and monitoring.

## Implementation Logic by Feature

### Agent Control
1. `AgentManager` keeps a dictionary of `agent_id -> subprocess` to track running agents.
2. Agents start via `start_agent()` which launches their Python entry point and creates a mailbox in `runtime/mailbox/<agent>`.
3. Monitoring threads check process health and use `agent_restarter.py` to auto-restart crashed agents.
4. Commands like resume or verify write JSON messages to `inbox.json` and wait for acknowledgements.

### Messaging System
1. Messages store `mode`, `content`, and `timestamp` fields.
2. The `CellPhone` class writes messages to each agent's inbox and polls for reply files.
3. Sequence numbers prevent duplicate processing and old messages are pruned.
4. `CaptainPhone` wraps `CellPhone` for high-priority routing.

### Task Management
1. `TaskManager` loads definitions from `config/agent_comms/<agent>.json`.
2. Each task contains an ID, priority, and dependency list.
3. Agents call `start_task(task_id)` to update history and progress.
4. Completed tasks are archived and metrics updated for Dreamscribe.

### Logging and Monitoring
1. Operations write through `LogManager.write()` which rotates files daily.
2. Metrics counters are incremented with each entry and exported to Prometheus.
3. Discord commands and the dashboard can stream the latest logs.

### Bridge Architecture
1. `BridgeManager` maintains asynchronous connections to external services.
2. Each bridge inherits from `BaseBridge` with `connect`, `send`, and `disconnect` hooks.
3. Health checks reconnect failing bridges and validate authentication tokens.

### Dreamscribe Narrative Memory
1. `Dreamscribe` parses logs into `MemoryFragment` objects.
2. Fragments link into `NarrativeThread` histories that agents can query.

### UI Dashboard
1. `AgentDashboard` is a PyQt window composed of dockable panels showing agent status and logs.
2. Buttons trigger the same operations as CLI utilities for consistent behavior.

### Browser Automation
1. `StealthBrowser` wraps `undetected-chromedriver` with anti-detection headers.
2. Cookies in `runtime/browser_cookies/` allow session reuse and scripted logins.

### Security & Duplication Checks
1. Access rules reside in `config/security/policies.yaml`.
2. `agent_tools/swarm/analyzers` scans the codebase for duplicate files or settings.

## Example LLM Prompts

The following prompts can be used (individually or in sequence) to request an LLM to generate the main features of Dream.OS.

1. **Agent Management Skeleton**
   ```text
   Write Python classes that implement an agent manager with start, stop, and auto-restart capabilities. Include a mailbox-based messaging interface so agents can exchange JSON messages.
   ```

2. **Task and Logging Modules**
   ```text
   Extend the agent system with a TaskManager that tracks task priorities and statuses. Also add a LogManager that stores system, agent, and task logs with rotation and optional metrics.
   ```

3. **Bridge Integration**
   ```text
   Provide an asynchronous BridgeManager that routes messages to external services. Include connection pooling, authentication hooks, and a security layer for verifying access tokens.
   ```

4. **Discord Command Layer**
   ```text
   Create a Discord bot that can list active agents, resume them, and broadcast messages. The bot should display recent logs on request.
   ```

5. **Dreamscribe Memory System**
   ```text
   Implement a Dreamscribe component that converts log entries into memory fragments and organizes them into narrative threads with timestamps and metadata.
   ```

6. **Voice and Discord Integration**
   ```text
   Add a Discord bot that can manage agents and provide text-to-speech output. Include commands for joining a voice channel and narrating log summaries.
   ```

7. **Social Automation Modules**
   ```text
   Create modules that post updates to Twitter, Reddit, and LinkedIn. Allow scheduling posts via the TaskManager and expose basic OAuth helpers.
   ```

8. **UI Dashboard**
   ```text
   Build a PyQt dashboard that shows agent status, allows starting or stopping agents, and streams log entries in real time.
   ```

9. **Stealth Browser Automation**
   ```text
   Implement a StealthBrowser class that manages headless sessions, cookie persistence, and anti-detection headers for automated web tasks.
   ```

10. **Metrics and Security Hooks**
    ```text
    Add a metrics server exposing Prometheus endpoints and integrate authentication checks for agent commands. Include a Grafana dashboard definition.
    ```

11. **Testing Harness and Configuration**
    ```text
    Provide a pytest-based test harness that mocks external services and loads agent settings from YAML files. Include fixtures for the TaskManager and BridgeManager so features can be validated in isolation.
    ```

12. **Lean Beta Deployment**
    ```text
    Combine the above modules into a minimal CLI entrypoint that launches an agent swarm, starts the bridge server, and exposes metrics. Document the environment variables required for local deployment.
    ```

Using these prompts sequentially encourages the LLM to build out the major Dream.OS features in manageable steps. Each step focuses on an isolated subsystem so that the resulting PRD can be organized feature by feature.
