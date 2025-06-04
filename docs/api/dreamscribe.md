# Dreamscribe API

`Dreamscribe` lives under `dreamos/core/dreamscribe.py` and provides the narrative memory system used by Dream.OS.

## Purpose
Dreamscribe ingests devlogs and system events, turning them into **memory fragments** that can be connected into narrative threads. It tracks insights and patterns to give the system historical context.

## Main Classes
- **MemoryFragment** – dataclass representing a single memory item.
- **NarrativeThread** – dataclass linking related memories together.
- **Dreamscribe** – orchestrates loading, updating and querying the memory corpus.

## Example
```python
from dreamos.core.dreamscribe import Dreamscribe

scribe = Dreamscribe()
memory_id = scribe.ingest_devlog({
    "agent_id": "agent_1",
    "content": "Task completed successfully",
})
info = scribe.get_system_insights()
```

Memory files are stored under `runtime/` so make sure those directories exist before running.
