# Dream.OS Logging System

## Overview

The Dream.OS logging system provides a comprehensive, configurable logging infrastructure that supports multiple log levels, file rotation, and integration with monitoring systems. This document describes the logging architecture, configuration, and best practices.

## Core Components

### 1. Log Manager
The central component for log management and configuration.

```python
class LogManager:
    def __init__(self):
        self.config = LogConfig()
        self.handlers = {}
        self.formatters = {}
        self.metrics_collector = MetricsCollector()

    async def initialize(self):
        """Initialize logging system"""
        await self._setup_handlers()
        await self._setup_formatters()
        await self.metrics_collector.initialize()

    async def log(self, level: str, message: str, **kwargs):
        """Log message with metadata"""
        await self._process_log(level, message, **kwargs)
        await self.metrics_collector.record_log(level)
```

### 2. Log Aggregator
Handles log collection and aggregation.

```python
class LogAggregator:
    def __init__(self):
        self.collectors = {}
        self.aggregators = {}
        self.storage = LogStorage()

    async def aggregate(self, level: str, message: str, **kwargs):
        """Aggregate log entry"""
        await self._collect_log(level, message, **kwargs)
        await self._aggregate_logs()
        await self.storage.store(level, message, **kwargs)
```

### 3. Log Rotator
Manages log file rotation and cleanup.

```python
class LogRotator:
    def __init__(self):
        self.rotation_config = RotationConfig()
        self.cleanup_manager = CleanupManager()
        self.metrics_collector = MetricsCollector()

    async def rotate(self, log_file: str):
        """Rotate log file"""
        await self._perform_rotation(log_file)
        await self.cleanup_manager.cleanup()
        await self.metrics_collector.record_rotation()
```

## Logging Configuration

### 1. Basic Configuration
```python
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': 'dreamos.log',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
```

### 2. Advanced Configuration
```python
advanced_config = {
    'metrics': {
        'enabled': True,
        'collection_interval': 60,
        'storage': 'prometheus'
    },
    'rotation': {
        'max_size': '10MB',
        'backup_count': 5,
        'compression': True
    },
    'aggregation': {
        'enabled': True,
        'interval': 300,
        'storage': 'elasticsearch'
    }
}
```

## Usage Examples

### 1. Basic Logging
```python
from dreamos.core.logging import get_logger

logger = get_logger(__name__)

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Log with context
logger.info("User action", extra={
    'user_id': '123',
    'action': 'login',
    'ip': '192.168.1.1'
})
```

### 2. Advanced Logging
```python
from dreamos.core.logging import LogManager, LogLevel

# Initialize logger with custom config
log_manager = LogManager()
await log_manager.initialize()

# Log with metrics
async def log_with_metrics(level: LogLevel, message: str, **kwargs):
    await log_manager.log(level, message, **kwargs)
    await log_manager.metrics_collector.record_log(level)

# Log with aggregation
async def log_with_aggregation(level: LogLevel, message: str, **kwargs):
    await log_manager.log(level, message, **kwargs)
    await log_manager.aggregator.aggregate(level, message, **kwargs)
```

## Log Levels

### 1. Standard Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause system failure

### 2. Custom Levels
```python
class CustomLogLevel:
    TRACE = 5
    VERBOSE = 15
    NOTICE = 25
    ALERT = 45
    EMERGENCY = 55
```

## Log Format

### 1. Standard Format
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

### 2. Extended Format
```
%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s: %(message)s
```

### 3. JSON Format
```json
{
    "timestamp": "2024-02-20T10:30:00Z",
    "level": "INFO",
    "logger": "dreamos.core",
    "message": "System started",
    "context": {
        "version": "1.0.0",
        "environment": "production"
    }
}
```

## Log Storage

### 1. File Storage
```python
class FileLogStorage:
    def __init__(self):
        self.config = StorageConfig()
        self.rotator = LogRotator()
        self.metrics_collector = MetricsCollector()

    async def store(self, level: str, message: str, **kwargs):
        """Store log entry in file"""
        await self._write_log(level, message, **kwargs)
        await self.rotator.check_rotation()
        await self.metrics_collector.record_storage()
```

### 2. Database Storage
```python
class DatabaseLogStorage:
    def __init__(self):
        self.db = Database()
        self.cleanup_manager = CleanupManager()
        self.metrics_collector = MetricsCollector()

    async def store(self, level: str, message: str, **kwargs):
        """Store log entry in database"""
        await self.db.insert_log(level, message, **kwargs)
        await self.cleanup_manager.cleanup_old_logs()
        await self.metrics_collector.record_storage()
```

## Log Analysis

### 1. Log Parsing
```python
class LogParser:
    def __init__(self):
        self.patterns = {}
        self.metrics_collector = MetricsCollector()

    async def parse(self, log_entry: str) -> Dict:
        """Parse log entry"""
        result = await self._extract_fields(log_entry)
        await self.metrics_collector.record_parse()
        return result
```

### 2. Log Analysis
```python
class LogAnalyzer:
    def __init__(self):
        self.parser = LogParser()
        self.metrics_collector = MetricsCollector()

    async def analyze(self, log_entries: List[str]) -> Analysis:
        """Analyze log entries"""
        parsed = await self.parser.parse_batch(log_entries)
        analysis = await self._analyze_patterns(parsed)
        await self.metrics_collector.record_analysis()
        return analysis
```

## Best Practices

### 1. Logging Guidelines
- Use appropriate log levels
- Include context in log messages
- Avoid sensitive data in logs
- Use structured logging
- Implement log rotation
- Monitor log size

### 2. Performance
- Use async logging
- Implement log buffering
- Configure appropriate batch sizes
- Monitor log performance
- Optimize storage

### 3. Security
- Secure log storage
- Implement access control
- Encrypt sensitive logs
- Regular log auditing
- Secure log transmission

## Monitoring

### 1. Log Metrics
```python
class LogMetrics:
    def __init__(self):
        self.metrics = {
            'log_count': 0,
            'error_count': 0,
            'storage_size': 0,
            'rotation_count': 0
        }
        self.collector = MetricsCollector()

    async def record_log(self, level: str):
        """Record log metrics"""
        self.metrics['log_count'] += 1
        if level == 'ERROR':
            self.metrics['error_count'] += 1
        await self.collector.record('log_metrics')
```

### 2. Health Monitoring
```python
class LogHealthMonitor:
    def __init__(self):
        self.checks = {
            'storage': StorageHealthCheck(),
            'rotation': RotationHealthCheck(),
            'aggregation': AggregationHealthCheck()
        }
        self.metrics_collector = MetricsCollector()

    async def check_health(self) -> HealthStatus:
        """Check logging system health"""
        status = await self._run_checks()
        await self.metrics_collector.record('health_check')
        return status
```

## Troubleshooting

### 1. Common Issues
1. **Log File Growth**
   - Check rotation configuration
   - Verify cleanup policies
   - Monitor disk space

2. **Performance Issues**
   - Check log level configuration
   - Verify buffer settings
   - Monitor system resources

3. **Missing Logs**
   - Verify logger configuration
   - Check file permissions
   - Validate storage settings

### 2. Debugging
```python
class LogDebugger:
    def __init__(self):
        self.tracer = LogTracer()
        self.metrics_collector = MetricsCollector()

    async def debug(self, issue: str) -> DebugResult:
        """Debug logging issue"""
        trace = await self.tracer.trace(issue)
        result = await self._analyze_trace(trace)
        await self.metrics_collector.record('debug')
        return result
```

## Resources

### Documentation
- [API Reference](api.md)
- [Configuration Guide](config.md)
- [Best Practices](best_practices.md)
- [Troubleshooting Guide](troubleshooting.md)

### Tools
- Log viewer
- Log analyzer
- Monitoring dashboard
- Debug tools
- Performance analyzer 