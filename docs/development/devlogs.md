# Dream.OS Development Logs

## Overview
Development logs (devlogs) are used to track progress, document changes, and generate marketing content for the Dream.OS project.

## Devlog Pitcher

The Devlog Pitcher is a tool that converts development logs into marketing pitches using the ChatGPT bridge.

### Usage
```bash
python tools/devlog_pitcher.py path/to/devlog.md --limit 5 --out pitch.md
```

#### Arguments
- **`devlog`**: Path to the markdown log
- **`--limit`**: Number of recent entries to convert (default: 3)
- **`--out`**: Optional file to save the generated pitch. If omitted, the pitch is printed to stdout.

### How It Works
1. The script parses headings in the devlog
2. ChatGPT creates a brief marketing snippet for each entry
3. Results are returned in simple Markdown format

## Devlog Management

### Structure
Devlogs are stored in markdown format with the following structure:
```markdown
# [Date] - [Title]

## Changes
- Change 1
- Change 2

## Notes
Additional context and notes about the changes
```

### Best Practices
1. **Regular Updates**
   - Log changes daily
   - Include all significant updates
   - Document both successes and challenges

2. **Content Guidelines**
   - Use clear, descriptive titles
   - Include technical details
   - Add context for non-technical readers
   - Link to related issues or PRs

3. **Formatting**
   - Use proper markdown syntax
   - Include code snippets when relevant
   - Add screenshots for UI changes
   - Keep entries concise but informative

## Integration

### Discord Integration
Devlogs can be automatically posted to Discord channels using the Discord bridge:
```python
from dreamos.core.devlog import DiscordDevlog

devlog = DiscordDevlog()
devlog.update_devlog(content)
```

### Social Media
The Devlog Pitcher can generate social media content from devlogs:
```bash
# Generate Twitter posts
python tools/devlog_pitcher.py devlog.md --platform twitter

# Generate Reddit posts
python tools/devlog_pitcher.py devlog.md --platform reddit
```

## Tools

### Devlog Manager
The `DevlogManager` class provides utilities for managing devlogs:
```python
from dreamos.core.agent_control.devlog_manager import DevLogManager

manager = DevLogManager()
manager.add_entry(title, content)
manager.get_recent_entries(limit=5)
```

### Devlog Watcher
The `DevlogWatcher` monitors devlog changes and triggers actions:
```python
from dreamos.core.devlog import DevlogWatcher

watcher = DevlogWatcher()
watcher.start()
```

## Testing

### Unit Tests
Devlog-related tests are located in:
- `tests/devlog_manager.py`
- `tests/devlog_bridge_test.py`
- `tests/devlog_bridge_isolated_test.py`

### Integration Tests
Devlog integration tests verify:
- Discord posting
- Social media generation
- File system operations
- Content formatting

## Future Improvements

1. **Automation**
   - Auto-generate devlogs from git commits
   - Schedule regular updates
   - Integrate with CI/CD pipeline

2. **Content Generation**
   - Improve marketing pitch quality
   - Add support for more platforms
   - Generate technical documentation

3. **Analytics**
   - Track devlog engagement
   - Measure content effectiveness
   - Generate progress reports 