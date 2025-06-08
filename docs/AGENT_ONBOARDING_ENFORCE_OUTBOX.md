# Enforcing `bridge_outbox` Writes for Cursor Agents

This document outlines the onboarding requirement for all Cursor-based agents to
record completion status in the runtime outbox directory. Each response loop must
write a JSON record when an agent finishes processing a prompt.

## Required Write
At the tail end of every response cycle, agents must call:

```python
save_json({
    "status": "complete",
    "response": full_text,
    "started_at": ts_start,
    "completed_at": ts_end
}, f"runtime/bridge_outbox/agent-{agent_id}.json")
```

The `started_at` and `completed_at` timestamps should be UNIX epoch seconds. The
`response` field contains the full text returned by the agent.

## Staleness Handling
Agents should check the modification time of their outbox file on each loop
iteration. If the file is older than five minutes, the agent must mark the file
as stale by overwriting it with `{"status": "stale"}` and trigger its own resume
logic.

This mechanism allows external watchdogs to verify progress even if prompting
fails.
