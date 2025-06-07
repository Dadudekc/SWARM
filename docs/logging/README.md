# Dream.OS Logging System

## Overview

The Dream.OS logging system provides a unified, configurable logging infrastructure for all components. It supports multiple log levels, file rotation, and integration with monitoring systems.

## Usage

```python
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel

# Initialize logger
config = LogConfig(
    level=LogLevel.INFO,
    log_dir="logs",
    max_size_mb=10,
    backup_count=5
)
logger = LogManager(config)

# Log messages
logger.info("System initialized")
logger.error("Failed to connect", exc_info=True)
```

### Basic Usage

```python
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel

# Initialize logging
log_manager = LogManager()
log_config = LogConfig(
    level=LogLevel.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log_manager.configure(log_config)

# Log messages
log_manager.info("This is an info message")
log_manager.warning("This is a warning message")
log_manager.error("This is an error message")
```

### Advanced Usage

```python
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel
from dreamos.core.monitoring.metrics import LogMetrics

# Initialize logging with metrics
log_manager = LogManager()
log_config = LogConfig(
    level=LogLevel.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    metrics_enabled=True
)
log_manager.configure(log_config)

# Get metrics
metrics = LogMetrics()
log_manager.set_metrics(metrics)

# Log with metrics
log_manager.info("This is an info message", metrics=True)
```

## Configuration

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical messages for fatal errors

### Log Format

The default log format is:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

You can customize the format by setting the `format` parameter in `LogConfig`.

### Metrics

Metrics are collected for:
- Number of log messages by level
- Average message length
- Logging frequency
- Error rate

## Best Practices

1. Use appropriate log levels
2. Include context in log messages
3. Enable metrics for monitoring
4. Configure logging at application startup
5. Use structured logging for complex data

## Migration

If you're migrating from the old logging system, update your imports:

```python
# Old
from social.utils.log_manager import LogManager, LogConfig, LogLevel

# New
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel
```

## Architecture

The logging system is designed to be:
- Modular: Components can be used independently
- Extensible: New features can be added easily
- Performant: Minimal overhead
- Thread-safe: Safe for concurrent use

## Contributing

When adding new logging features:
1. Follow the existing patterns
2. Add appropriate tests
3. Update documentation
4. Consider performance impact

## Viewing Logs

### GUI Monitor

```python
from dreamos.core.log_manager import LogManager
from gui.components.log_monitor import LogMonitor

# Initialize logging
log_manager = LogManager()

# Create monitor
monitor = LogMonitor(log_manager)
monitor.show()
```

### Command Line

```bash
# View all logs
tail -f logs/dreamos.log

# View error logs
grep ERROR logs/dreamos.log

# View agent logs
tail -f logs/agents/*.log
```

### Metrics Dashboard

```python
from dreamos.core.log_manager import LogManager
from dreamos.core.monitoring.metrics import LogMetrics

# Initialize logging with metrics
log_manager = LogManager()
metrics = LogMetrics()
log_manager.set_metrics(metrics)

# View metrics
print(metrics.get_summary())
```

## Troubleshooting

### Common Issues

1. **Missing Log Files**
   - Check log directory permissions
   - Verify log configuration
   - Ensure log rotation is working

2. **High Log Volume**
   - Adjust log levels
   - Enable log rotation
   - Use structured logging

3. **Performance Issues**
   - Disable metrics if not needed
   - Use async logging
   - Configure batch size

### Getting Help

For issues with the logging system:
1. Check the documentation
2. Search existing issues
3. Create a new issue
4. Contact the maintainers 