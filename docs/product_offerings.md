# Dream.OS Product Offerings

This page outlines optional packages built on top of Dream.OS. These micro projects help teams quickly integrate core features without adopting the entire platform.

## Self-Healing Agent Swarm Starter Template

A lightweight starter project aimed at engineering teams who use the Cursor environment. It ships with:

- Preconfigured agent orchestration using Dream.OS messaging loops.
- Automatic detection and restart of stalled agents.
- Example configuration files for deploying a small swarm in Cursor.

### Quick Start

1. Install Dream.OS following the [Setup Guide](setup.md).
2. Copy the starter template from `docs/examples/self_healing_swarm/`.
3. Run `python start_swarm.py` to launch the default agents.

This template provides a minimal, self-healing swarm that companies can extend with their own agents and tasks.

## Auto-Prompt Script Generator for Multi-Agent Systems

A command line tool that converts a YAML description of agent prompts into an executable Python script. The generated script uses `ChatGPTBridge` to send prompts to the LLM and can be plugged into existing workflows.

### Key Features

- Supports multiple agent roles with distinct system and user prompts.
- Produces a ready-to-run Python script using Dream.OS bridge utilities.
- Ideal for quickly testing new agent interactions or batch prompt workflows.

### Usage

```bash
python tools/auto_prompt_script_generator.py prompts.yaml out_script.py
python out_script.py  # executes the generated prompts
```

These spin-offs demonstrate how Dream.OS can be packaged into bite-sized tools that organizations can adopt incrementally.
