#!/usr/bin/env python3
"""Example starter for a self-healing Dream.OS swarm."""

from dreamos.core.agent.control.agent_controller import AgentController


def main() -> None:
    controller = AgentController()
    controller.resume_all(auto_heal=True)


if __name__ == "__main__":
    main()
