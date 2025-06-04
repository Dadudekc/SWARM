# StealthBrowser API

This document provides a brief reference for the `StealthBrowser` module located under `agent_tools/general_tools/browser`.

## Overview
The `StealthBrowser` wraps an undetected Chromium instance with helper classes for automated web interaction. It manages login flows, cookie persistence and provides helper methods for sending messages to Codex or other platforms while avoiding detection.

## Key Classes
- **StealthBrowser** - main controller for launching and managing the browser session.
- **LoginHandler** - performs multi step login and message input.
- **CookieManager** - loads and saves session cookies.
- **StealthBrowserBridge** - integrates the browser with Dream.OS messaging via a request queue.

## Basic Usage
```python
from agent_tools.general_tools.browser import StealthBrowser, DEFAULT_CONFIG

browser = StealthBrowser(DEFAULT_CONFIG)
browser.start()
browser.navigate_to("https://example.com")
# interact via browser.login_handler
browser.stop()
```

For integration into the orchestration system see `agent_tools/general_tools/browser/integration.py`.
