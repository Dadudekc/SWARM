# Dreamscribe

## Overview

`Dreamscribe` lives under `dreamos/core/dreamscribe.py` and provides the narrative memory system used by Dream.OS. It ingests devlogs and system events, turning them into **memory fragments** that can be connected into narrative threads. It tracks insights and patterns to give the system historical context.

## Core Components

### MemoryFragment
A dataclass representing a single memory item, containing:
- Content
- Timestamp
- Source
- Metadata
- Relationships

### NarrativeThread
A dataclass linking related memories together, providing:
- Thread ID
- Connected memories
- Timeline
- Context
- Insights

### Dreamscribe
The main orchestrator that handles:
- Loading memories
- Updating the memory corpus
- Querying memories
- Generating insights
- Managing narrative threads

## Usage

```python
from dreamos.core.dreamscribe import Dreamscribe

# Initialize
scribe = Dreamscribe()

# Ingest a devlog
memory_id = scribe.ingest_devlog({
    "agent_id": "agent_1",
    "content": "Task completed successfully",
})

# Get system insights
insights = scribe.get_system_insights()

# Query memories
memories = scribe.query_memories(
    agent_id="agent_1",
    time_range=("2025-06-01", "2025-06-12")
)

# Get narrative thread
thread = scribe.get_narrative_thread(memory_id)
```

## Storage

Memory files are stored under `runtime/` in the following structure:
```
runtime/
  memories/
    fragments/
    threads/
    insights/
```

Make sure these directories exist before running Dreamscribe.

## Best Practices

1. **Regular Ingestion**
   - Ingest devlogs as they are created
   - Process system events in real-time
   - Maintain chronological order

2. **Memory Organization**
   - Use clear agent IDs
   - Include relevant metadata
   - Link related memories

3. **Query Optimization**
   - Use specific time ranges
   - Filter by agent ID
   - Include relevant metadata

4. **Resource Management**
   - Clean up old memories
   - Archive inactive threads
   - Monitor storage usage 