# Discord Notification System

A unified notification system for Dream.OS that provides a centralized way to send notifications to Discord channels and webhooks.

## Features

- Unified notification interface for both channels and webhooks
- Asynchronous notification queue for better performance
- Support for text messages, embeds, and file attachments
- Built-in error handling and logging
- Prometheus metrics for monitoring
- Comprehensive test coverage

## Installation

1. Install the required dependencies:
```bash
pip install discord.py prometheus-client
```

2. Configure webhooks in `config/webhooks.json`:
```json
{
    "system_alerts": "YOUR_SYSTEM_ALERTS_WEBHOOK_URL",
    "error_reports": "YOUR_ERROR_REPORTS_WEBHOOK_URL",
    "success_notifications": "YOUR_SUCCESS_NOTIFICATIONS_WEBHOOK_URL",
    "debug_logs": "YOUR_DEBUG_LOGS_WEBHOOK_URL"
}
```

## Usage

### Basic Usage

```python
from discord_bot.notifier import DiscordNotifier
from discord.ext import commands

# Initialize with a Discord bot
bot = commands.Bot(command_prefix='!')
notifier = DiscordNotifier(bot=bot)

# Send a simple message to a channel
await notifier.send_notification(
    content="Hello, world!",
    channel_id=123456789
)

# Send a message to a webhook
await notifier.send_notification(
    content="Hello, world!",
    webhook_name="system_alerts"
)
```

### Sending Error Notifications

```python
try:
    # Some code that might raise an exception
    raise ValueError("Something went wrong")
except Exception as e:
    await notifier.send_error(
        error=e,
        context="Error occurred while processing user request",
        channel_id=123456789
    )
```

### Sending Success Notifications

```python
await notifier.send_success(
    message="Task completed successfully",
    details="Processed 100 items in 5 seconds",
    channel_id=123456789
)
```

### Sending Notifications with Embeds

```python
embed_data = {
    'title': 'Task Status',
    'description': 'Current progress',
    'color': 0x00ff00,
    'fields': [
        {
            'name': 'Progress',
            'value': '75%',
            'inline': True
        },
        {
            'name': 'Time Remaining',
            'value': '5 minutes',
            'inline': True
        }
    ],
    'footer': 'Last updated',
    'timestamp': datetime.now().isoformat()
}

await notifier.send_notification(
    content="Task update",
    embed=embed_data,
    channel_id=123456789
)
```

### Sending Notifications with Files

```python
await notifier.send_notification(
    content="Here's the report",
    files=['path/to/report.pdf'],
    channel_id=123456789
)
```

## Monitoring

The notification system exposes the following Prometheus metrics:

- `discord_notification_processing_seconds`: Time spent processing notifications
- `discord_notification_errors_total`: Total number of notification errors
- `discord_notification_queue_size`: Current size of the notification queue

## Error Handling

The notification system includes built-in error handling:

1. Invalid notification targets (missing channel_id or webhook_name)
2. Non-existent channels or webhooks
3. File access errors
4. Network errors
5. Rate limiting

All errors are logged and can be monitored through Prometheus metrics.

## Testing

Run the test suite:

```bash
pytest tests/discord/test_notifier.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 