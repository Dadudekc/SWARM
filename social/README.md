# Dream.OS Social Media Automation

A robust, API-free social media automation system that uses undetected Chrome to post across multiple platforms without triggering bot detection.

## Features

- **Zero API Usage**: Uses browser automation instead of APIs to avoid rate limits and fees
- **Multi-Platform Support**: Facebook, Twitter, Instagram, Reddit, LinkedIn, StockTwits
- **Cookie Management**: Persistent sessions with automatic cookie restoration
- **Parallel Posting**: Posts to all platforms simultaneously using threading
- **Comprehensive Logging**: JSON logs for all operations with detailed metadata
- **Proxy Support**: Optional proxy rotation for IP diversity
- **Headless Mode**: Run in background on servers
- **Error Recovery**: Automatic retries and fallback to manual login

## Directory Structure

```
social/
├── dispatcher.py                  # Main automation loop
├── driver_manager.py              # Chrome driver session management
├── social_config.py               # Platform credentials and settings
├── cookies/                       # Session cookies (.pkl)
├── logs/                          # JSON operation logs
└── strategies/                    # Platform-specific handlers
    ├── platform_strategy_base.py  # Base strategy class
    ├── facebook_strategy.py       # Facebook implementation
    ├── twitter_strategy.py        # Twitter implementation
    ├── instagram_strategy.py      # Instagram implementation
    ├── reddit_strategy.py         # Reddit implementation
    ├── stocktwits_strategy.py     # StockTwits implementation
    └── linkedin_strategy.py       # LinkedIn implementation
```

## Setup

1. Install dependencies:
```bash
pip install undetected-chromedriver selenium webdriver-manager
```

2. Set environment variables for platform credentials:
```bash
# Facebook
FACEBOOK_EMAIL=your_email
FACEBOOK_PASSWORD=your_password

# Twitter
TWITTER_EMAIL=your_email
TWITTER_PASSWORD=your_password

# Instagram
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Reddit
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# LinkedIn
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password

# StockTwits
STOCKTWITS_USERNAME=your_username
STOCKTWITS_PASSWORD=your_password
```

3. Configure platform settings in `social_config.py`:
- Enable/disable platforms
- Set posting intervals
- Configure hashtags
- Adjust timeouts and retry attempts

## Usage

```python
from social.dispatcher import SocialPlatformDispatcher

# Create memory update with content
memory_update = {
    "quest_completions": ["New Feature Launch"],
    "newly_unlocked_protocols": ["Enhanced Automation"],
    "feedback_loops_triggered": ["Social Media Sync"]
}

# Initialize and run dispatcher
dispatcher = SocialPlatformDispatcher(
    memory_update=memory_update,
    headless=False  # Set to True for production
)
dispatcher.dispatch_all()
```

## Platform Strategy Implementation

Each platform strategy must implement:

```python
class PlatformStrategy:
    def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        pass

    def login(self) -> bool:
        """Attempt to log in."""
        pass

    def post(self, content: str) -> bool:
        """Post content to platform."""
        pass

    def create_post(self) -> str:
        """Generate platform-specific content."""
        pass
```

## Logging

All operations are logged using the core logging system:
- Centralized logging through `dreamos.core.logging`
- Platform-specific log files in `logs/`
- Daily log rotation
- Detailed metadata and error tracking
- AI output and response logging

## Security

- Credentials stored in environment variables
- Cookie encryption
- Proxy rotation support
- Rate limiting per platform
- Automatic session cleanup

## Error Handling

- Automatic retry on failure
- Fallback to manual login
- Detailed error logging
- Screenshot capture on failure
- Graceful shutdown

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details 