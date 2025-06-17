import argparse, json, os
from pathlib import Path

PROFILES = ("windows", "mac")


def _cfg() -> Path:
    b = Path("config") / "bridge"
    return (Path("config") / "bridge_agent_coords.json") if b.is_file() else b / "agent_coords.json"


def _read(p: Path):
    return json.loads(p.read_text()) if p.exists() else {k: {} for k in PROFILES}


def _write(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def record(agent: int, profile: str, *, p: Path | None = None):
    if profile not in PROFILES:
        raise ValueError(profile)
    p = p or _cfg()
    import pyautogui  # patched in tests
    x, y = pyautogui.position()
    db = _read(p)
    db.setdefault(profile, {})[f"Agent-{agent}"] = {"x": x, "y": y}
    _write(p, db)
    print("saved", p, profile, agent, x, y)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Record one UI coordinate")
    a.add_argument("--agent", type=int, required=True)
    a.add_argument("--profile", choices=PROFILES, default=os.getenv("UI_PROFILE", "windows"))
    args = a.parse_args()
    record(args.agent, args.profile) 