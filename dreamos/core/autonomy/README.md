# Enhanced Response Loop Daemon

## Overview

The Enhanced Response Loop Daemon implements a hybrid completion detection system that combines:

1. Bridge Outbox Monitoring
2. Visual Screen Region Monitoring

This provides redundant completion detection to ensure reliable agent response handling.

## Architecture

### 1. Bridge Outbox Monitoring

- Monitors `bridge_outbox/agent-{id}.json` files
- Expects completion status in format:
```json
{
    "status": "complete",
    "response": "full_text",
    "started_at": "timestamp",
    "completed_at": "timestamp"
}
```

### 2. Visual Monitoring

- Monitors screen regions for each agent
- Detects completion when:
  - Screen region stabilizes for 5+ seconds
  - No text changes detected
  - Cursor stops blinking

### 3. Hybrid Detection Protocol

```yaml
completion_detection:
  mode: hybrid
  method_order:
    - 1. Check bridge_outbox/agent-{id}.json for "status: complete"
    - 2. If missing or stale:
        - Trigger visual hash scan for agent's screen region
        - If screen stable for >5s, assume complete
        - Log fallback flag
    - 3. If no completion by 10 min, force re-prompt
```

## Configuration

### Agent Regions

Configure screen regions in `config/agent_regions.json`:

```json
{
    "agent-1": {
        "top_left": {
            "x": 0,
            "y": 0
        },
        "bottom_right": {
            "x": 800,
            "y": 600
        }
    }
}
```

## Usage

1. Initialize the daemon:
```python
daemon = EnhancedResponseLoopDaemon(config_path="path/to/config.json")
```

2. Start monitoring:
```python
await daemon.start()
```

3. Check completion:
```python
is_complete, method = await daemon._check_completion(agent_id)
```

## Error Handling

- Failed outbox writes trigger auto-resume within 5 minutes
- Stale outbox files (>5 min old) trigger re-prompt
- Visual monitoring failures fall back to outbox monitoring
- All errors are logged with full context

## Dependencies

- pyautogui: Screen capture
- opencv-python: Image processing
- watchdog: File system monitoring
- numpy: Array operations

## Best Practices

1. Always write to bridge_outbox first
2. Use visual monitoring as backup only
3. Configure accurate screen regions
4. Monitor completion logs for fallback usage
5. Keep agent regions updated if window positions change 