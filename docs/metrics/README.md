# Dream.OS Metrics Documentation

## Overview
This document outlines the metrics collection, monitoring, and analysis system for Dream.OS. It covers both system-wide metrics and specific component metrics.

## System Metrics

### Core Metrics
1. Performance Metrics
   - CPU Usage
   - Memory Usage
   - Disk I/O
   - Network I/O
   - Response Times

2. Resource Metrics
   - Available Memory
   - Disk Space
   - Network Bandwidth
   - Thread Count
   - Process Count

3. Health Metrics
   - System Uptime
   - Service Health
   - Error Rates
   - Warning Rates
   - Recovery Times

### Agent Metrics
1. Performance
   - Message Processing Time
   - Queue Length
   - Processing Rate
   - Error Rate
   - Recovery Time

2. Resource Usage
   - Memory Usage
   - CPU Usage
   - Network Usage
   - Disk Usage
   - Thread Count

3. Health
   - Agent Status
   - Last Heartbeat
   - Error Count
   - Warning Count
   - Recovery Count

## File Operations Metrics

### Log Events
1. File Writes
   ```python
   {
       "event": "file_write",
       "path": "string",
       "size": "integer",
       "timestamp": "datetime",
       "status": "success|failure",
       "error": "string (optional)"
   }
   ```

2. File Reads
   ```python
   {
       "event": "file_read",
       "path": "string",
       "size": "integer",
       "timestamp": "datetime",
       "status": "success|failure",
       "error": "string (optional)"
   }
   ```

3. Directory Operations
   ```python
   {
       "event": "dir_operation",
       "path": "string",
       "operation": "create|delete|list",
       "timestamp": "datetime",
       "status": "success|failure",
       "error": "string (optional)"
   }
   ```

### Metrics Counters
1. Success Counters
   - `file_write_success_total`
   - `file_read_success_total`
   - `dir_operation_success_total`

2. Failure Counters
   - `file_write_failure_total`
   - `file_read_failure_total`
   - `dir_operation_failure_total`

3. Performance Metrics
   - `file_operation_duration_seconds`
   - `file_size_bytes`
   - `file_operation_queue_length`

### Prometheus Integration
```python
from prometheus_client import Counter, Histogram

# Counters
FILE_WRITE_SUCCESS = Counter(
    'file_write_success_total',
    'Total successful file writes'
)

FILE_WRITE_FAILURE = Counter(
    'file_write_failure_total',
    'Total failed file writes'
)

# Histograms
FILE_OPERATION_DURATION = Histogram(
    'file_operation_duration_seconds',
    'Time spent on file operations',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)
```

## Monitoring Dashboard

### System Overview
1. Performance Dashboard
   - CPU Usage Graph
   - Memory Usage Graph
   - Disk I/O Graph
   - Network I/O Graph
   - Response Time Graph

2. Resource Dashboard
   - Available Resources Graph
   - Resource Usage Trends
   - Resource Alerts
   - Resource Predictions

3. Health Dashboard
   - System Health Status
   - Service Health Status
   - Error Rate Graph
   - Warning Rate Graph
   - Recovery Time Graph

### Agent Dashboard
1. Performance View
   - Message Processing Time
   - Queue Length
   - Processing Rate
   - Error Rate
   - Recovery Time

2. Resource View
   - Memory Usage
   - CPU Usage
   - Network Usage
   - Disk Usage
   - Thread Count

3. Health View
   - Agent Status
   - Last Heartbeat
   - Error Count
   - Warning Count
   - Recovery Count

## Best Practices

### Metrics Collection
1. Consistent Naming
   - Use clear, descriptive names
   - Follow naming conventions
   - Include units in names
   - Use consistent prefixes

2. Error Context
   - Include error details
   - Add stack traces
   - Log related events
   - Track error chains

3. Path Normalization
   - Use absolute paths
   - Normalize separators
   - Handle special characters
   - Validate paths

4. Operation Tracking
   - Track operation types
   - Log operation details
   - Monitor operation duration
   - Track operation success

### Example Usage
```python
def save_data(data: dict, path: str) -> bool:
    """Save data to file with metrics."""
    start_time = time.time()
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
        
        # Log success
        FILE_WRITE_SUCCESS.inc()
        FILE_OPERATION_DURATION.observe(time.time() - start_time)
        return True
        
    except Exception as e:
        # Log failure
        FILE_WRITE_FAILURE.inc()
        logger.error(f"Failed to save data: {e}")
        return False
```

## Alerting

### Alert Rules
1. Performance Alerts
   - High CPU Usage
   - High Memory Usage
   - Slow Response Time
   - High Error Rate
   - Resource Exhaustion

2. Health Alerts
   - Service Down
   - High Error Rate
   - Slow Recovery
   - Resource Depletion
   - System Instability

3. File Operation Alerts
   - High Failure Rate
   - Slow Operations
   - Disk Space Low
   - Permission Issues
   - Path Problems

### Alert Configuration
```yaml
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High CPU usage detected
          description: CPU usage is above 80% for 5 minutes

      - alert: HighMemoryUsage
        expr: memory_usage > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage detected
          description: Memory usage is above 90% for 5 minutes
```

## Visualization

### Grafana Dashboards
1. System Overview
   - Performance Graphs
   - Resource Usage
   - Health Status
   - Error Rates
   - Response Times

2. Agent Overview
   - Performance Metrics
   - Resource Usage
   - Health Status
   - Error Rates
   - Processing Times

3. File Operations
   - Operation Rates
   - Success/Failure Rates
   - Operation Duration
   - File Sizes
   - Path Statistics

## Maintenance

### Regular Tasks
1. Metric Review
   - Check metric relevance
   - Update metric names
   - Adjust thresholds
   - Clean up old metrics

2. Dashboard Updates
   - Update visualizations
   - Add new metrics
   - Remove old metrics
   - Optimize queries

3. Alert Tuning
   - Review alert rules
   - Adjust thresholds
   - Update notifications
   - Test alert conditions

## Troubleshooting

### Common Issues
1. Metric Collection
   - Missing metrics
   - Incorrect values
   - High cardinality
   - Performance impact

2. Visualization
   - Missing data
   - Incorrect graphs
   - Slow loading
   - Query timeouts

3. Alerting
   - False positives
   - Missing alerts
   - Alert storms
   - Notification issues

### Solutions
1. Metric Issues
   - Check collectors
   - Verify configurations
   - Review cardinality
   - Optimize collection

2. Visualization Issues
   - Check data sources
   - Verify queries
   - Optimize dashboards
   - Cache results

3. Alert Issues
   - Review rules
   - Check thresholds
   - Test notifications
   - Monitor alerting

## Future Improvements

### Planned Enhancements
1. Metric Collection
   - Add new metrics
   - Improve collection
   - Reduce overhead
   - Better sampling

2. Visualization
   - New dashboards
   - Better graphs
   - More insights
   - Custom views

3. Alerting
   - Smarter rules
   - Better notifications
   - More context
   - Automated responses 