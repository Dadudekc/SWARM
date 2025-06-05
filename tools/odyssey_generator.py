#!/usr/bin/env python3
"""
odyssey_generator.py — Dream.OS scaffold
---------------------------------------
Auto-creates a 3-path Odyssey Plan (Current / Freedom / Wildcard) for an agent.

Usage
-----
python tools/odyssey_generator.py \
    --agent-id 2 \
    --devlog runtime/devlog/agents/agent_2/devlog.md \
    --out runtime/planning/odyssey/agent_2_odyssey.yaml
"""
import argparse
from pathlib import Path
import datetime as _dt
import yaml   # PyYAML is already in the core requirements.txt

_DEFAULT_TEMPLATE = {
    "odyssey_plan": [
        {
            "id": "CURRENT_PATH",
            "name": "Momentum",
            "description": "Where life is headed if nothing changes.",
            "location": "",
            "daily_rhythm": "",
            "focus": "",
            "success_looks_like": "",
            "fear": ""
        },
        {
            "id": "FREEDOM_PATH",
            "name": "Unconstrained",
            "description": "What you'd pursue if money / status were irrelevant.",
            "location": "",
            "daily_rhythm": "",
            "focus": "",
            "success_looks_like": "",
            "fear": ""
        },
        {
            "id": "WILDCARD_PATH",
            "name": "Parallel Universe",
            "description": "Radical reinvention, new identity / geography.",
            "location": "",
            "daily_rhythm": "",
            "focus": "",
            "success_looks_like": "",
            "fear": ""
        }
    ],
    "generated_at": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
}


def _extract_identity(devlog_path: Path) -> str:
    """
    Pull the first non-empty line of the devlog as a crude identity seed.
    You can upgrade this to a proper NLP summary later.
    """
    try:
        for line in devlog_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip()[:160]
    except FileNotFoundError:
        pass
    return "Unknown Agent Identity"


def generate_odyssey(agent_id: int, devlog: Path) -> dict:
    plan = _DEFAULT_TEMPLATE.copy()
    identity = _extract_identity(devlog)

    # Inject identity seed into each path for flavour
    for track in plan["odyssey_plan"]:
        track["identity_seed"] = identity
    return plan


def main():
    ap = argparse.ArgumentParser(description="Generate a 5-year 3-path Odyssey Plan")
    ap.add_argument("--agent-id", type=int, required=True)
    ap.add_argument("--devlog", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    plan = generate_odyssey(args.agent_id, args.devlog)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.dump(plan, sort_keys=False), encoding="utf-8")
    print(f"[odyssey_generator] ✅ wrote {args.out}")


if __name__ == "__main__":
    main() 