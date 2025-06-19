# Dream.OS

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

Dream.OS is an AI-agent operating system built by Victor to orchestrate swarms of autonomous workers. Agents communicate through a unified messaging layer, store narrative history in the **Dreamscribe** memory system, and can integrate with external tools such as Discord or browser automation.

## Features
- **Agent lifecycle management** with persistent task queues and recovery
- **Messaging hub** for inter-agent communication, including prioritized channels
- **Bridge system** connecting to ChatGPT and cursor-based automation
- **Dreamscribe** narrative memory service for tracking agent context
- **Discord bot** for monitoring and control

## Repository Structure
```
agent_tools/        # Helper utilities for scanning and agent management
config/             # YAML and JSON configuration files
/docs/              # Architecture and development documentation
/dreamos/           # Core library and applications
/runtime/           # Generated queues and runtime artifacts
/scripts/           # Test runner and maintenance tools
/tests/             # Unit and integration tests
```

## Setup
1. Install Python 3.11+ and clone the repository.
2. (Optional) create a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the test suite to verify:
   ```bash
   python run_tests.py
   ```

## Usage Example
```python
from dreamos.core.agent.control.agent_controller import AgentController

controller = AgentController("agent-0")
controller.start()
```

## Architecture Overview
Dream.OS centers around an **Agent System** orchestrated by a System Orchestrator. Agents exchange messages via a **Unified Message System** which persists history and manages priorities. The **Bridge** module routes requests to external services like ChatGPT. **Dreamscribe** stores narrative memories for long-term context. Monitoring utilities collect metrics and health information under `dreamos/core/monitoring`.

For more detail see [docs/architecture/core.md](docs/architecture/core.md).

## What This Project Demonstrates
- Designing a modular Python platform for coordinating many agents
- Integrating LLM services and external automation through a clean bridge layer
- Emphasizing testability with a structured test runner and documentation

## License
No license specified. Use at your own risk.
