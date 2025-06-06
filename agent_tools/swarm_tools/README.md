# DevLog Watcher

Automatically syncs local devlog entries to Discord using webhooks.

## Features

- Monitors local devlog files for changes
- Extracts tags and metadata from entries
- Posts updates to Discord with proper formatting
- Handles multiple agents simultaneously
- Prevents duplicate posts
- Async I/O for better performance

## Usage

1. Ensure your webhook configuration is set up in `agent_webhooks.json`:

```json
{
    "Agent-1": {
        "webhook_url": "YOUR_WEBHOOK_URL",
        "footer": "The Dream Architect | Agent-1",
        "avatar_url": "OPTIONAL_AVATAR_URL"
    }
    // ... other agents
}
```

2. Run the watcher:

```bash
python -m agent_tools.swarm_tools.devlog_watcher
```

## DevLog Format

Entries should follow this format:

```markdown
# Title of Update

Content of the update with #tags for metadata.

#done #update #error:description
```

### Supported Tags

- `#done` - Task completed
- `#update` - Progress update
- `#error` - Error or issue
- `#wip` - Work in progress
- `#blocked` - Blocked by dependency
- `#idea` - New idea or proposal

## Configuration

The watcher uses the following configuration:

- `agent_webhooks.json` - Webhook URLs and metadata
- `agent_tools/mailbox/{agent_id}/logs/` - Devlog file locations

## Dependencies

- watchdog - File system monitoring
- aiofiles - Async file I/O
- aiohttp - Async HTTP client
- python-dotenv - Environment variable management 