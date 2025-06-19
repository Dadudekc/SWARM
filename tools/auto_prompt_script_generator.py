#!/usr/bin/env python3
"""Auto-Prompt Script Generator
-----------------------------
Create runnable prompt scripts for multi-agent workflows.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Dict, List

import yaml


TEMPLATE = textwrap.dedent(
    """
    import asyncio
    from dreamos.core.bridge.chatgpt.bridge import ChatGPTBridge

    async def main() -> None:
        async with ChatGPTBridge() as bridge:
    {agent_sections}
            print("All prompts executed")

    if __name__ == "__main__":
        asyncio.run(main())
    """
)


def _format_section(system: str, user: str) -> str:
    system_line = f"{{'role': 'system', 'content': {system!r}}}"
    user_line = f"{{'role': 'user', 'content': {user!r}}}"
    return "\n".join(
        [
            "            await bridge.chat([",
            f"                {system_line},",
            f"                {user_line}
            ], max_tokens=200)",
        ]
    )


def generate_script(config: Path, output: Path) -> None:
    data: Dict[str, List[Dict[str, str]]] = yaml.safe_load(config.read_text())
    sections: List[str] = []
    for agent in data.get("agents", []):
        system_prompt = agent.get("system_prompt", "")
        user_prompt = agent.get("user_prompt", "")
        sections.append(_format_section(system_prompt, user_prompt))
    script = TEMPLATE.format(agent_sections="\n".join(sections))
    output.write_text(script)
    print(f"Generated script written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate prompt script from YAML config")
    parser.add_argument("config", type=Path, help="YAML file describing agent prompts")
    parser.add_argument("output", type=Path, help="Path for generated Python script")
    args = parser.parse_args()
    generate_script(args.config, args.output)


if __name__ == "__main__":
    main()
