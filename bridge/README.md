# Bridge Response Loop Daemon

The Bridge Response Loop Daemon automates the communication loop between Cursor agents and ChatGPT. It monitors agent responses, processes them through ChatGPT, and injects the validated responses back into Cursor.

## Features

- 🔄 Automatic response processing
- 🤖 ChatGPT integration
- 📝 Template-based prompts
- 📊 Monitoring & metrics
- 🔔 Discord notifications
- 🗄️ Response archiving
- ⚡ Async operation

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   export CHATGPT_API_KEY="your-api-key"
   export DISCORD_TOKEN="your-discord-token"  # Optional
   export RESPONSE_LOOP_CONFIG="path/to/config.json"  # Optional
   ```

3. Create required directories:
   ```bash
   mkdir -p data/{bridge_outbox,archive,failed,runtime/memory}
   ```

## Usage

Start the daemon:
   ```bash
   python -m bridge.run_response_loop
   ```

The daemon will:
1. Watch for new agent responses in `data/bridge_outbox/`
2. Process them through ChatGPT
3. Write validated responses to `data/bridge_outbox/validated/`
4. Inject responses back into Cursor
5. Archive processed files

## Configuration

The daemon is configured via `config/response_loop_config.json`:

```json
{
    "paths": {
        "bridge_outbox": "data/bridge_outbox",
        "archive": "data/archive",
        "failed": "data/failed",
        "runtime": "data/runtime"
    },
    "chatgpt": {
        "max_retries": 3,
        "response_wait": 5,
        "timeout": 30
    },
    "monitoring": {
        "enabled": true,
        "metrics_interval": 60
    },
    "discord": {
        "enabled": true,
        "notify_errors": true,
        "notify_success": false
    }
}
```

## Response Templates

The daemon uses Jinja2 templates to format prompts for ChatGPT. Templates are located in `prompt_templates/`:

- `general.j2`: Default template for general responses
- `patch_submission.j2`: Template for code patch submissions
- `code_review.j2`: Template for code reviews
- `test_result.j2`: Template for test results
- `next_task_request.j2`: Template for next task requests

## Monitoring

The daemon provides monitoring through:
- Logging to `logs/response_loop.log`
- Discord notifications (if enabled)
- Metrics collection (if enabled)

## Error Handling

- Failed responses are moved to `data/failed/`
- Retries for ChatGPT API calls
- Detailed error logging
- Discord notifications for critical errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 