# Dream.OS Metrics Dashboard

## Overview

Dream.OS includes a comprehensive metrics and monitoring system that tracks system performance, agent activity, and operational health. This document describes the metrics architecture, available metrics, and how to use them.

## Metrics Architecture

### 1. Core Metrics Components
- **Metrics Server**: Flask application serving Prometheus-formatted metrics
- **Metrics Collection**: Real-time event tracking and performance monitoring
- **Metrics Storage**: Time-series database for metrics persistence
- **Visualization**: Grafana dashboards for metrics display

### 2. Metrics Types

#### System Metrics
- CPU usage
- Memory consumption
- Disk I/O
- Network traffic
- Process counts
- System load

#### Agent Metrics
- Active agents
- Agent response times
- Task completion rates
- Error rates
- Resource usage
- Agent health status

#### Performance Metrics
- Response times
- Queue lengths
- Cache hit rates
- API latencies
- Resource utilization
- Throughput

#### Health Metrics
- Service status
- Error counts
- Warning rates
- Component health
- Dependency status
- System stability

## File Operation Metrics

### Log Events

#### File Write
```python
logger.info(
    "file_write",
    extra={
        "path": str,      # File path
        "bytes": int,     # Content size
        "encoding": str,  # File encoding
    }
)
```

#### File Write Error
```python
logger.error(
    "file_write_error",
    extra={
        "path": str,    # File path
        "error": str,   # Error message
    }
)
```

#### File Read
```python
logger.info(
    "file_read",
    extra={
        "path": str,      # File path
        "bytes": int,     # Content size
        "encoding": str,  # File encoding
    }
)
```

#### File Read Error
```python
logger.error(
    "file_read_error",
    extra={
        "path": str,    # File path
        "error": str,   # Error message
    }
)
```

#### Directory Operations
```python
logger.info(
    "directory_created",  # or "directory_cleared"
    extra={
        "path": str,    # Directory path
    }
)
```

### Metrics Counters

```python
metrics = {
    "file_writes": int,        # Successful writes
    "file_write_errors": int,  # Write failures
    "file_reads": int,         # Successful reads
    "file_read_errors": int,   # Read failures
    "directory_ops": int,      # Directory operations
    "total_bytes": int,        # Total bytes processed
}
```

### Prometheus Integration

```python
from dreamos.core.metrics import Counter, Gauge, Histogram

# File operation counters
file_write_counter = Counter(
    "file_ops_write_total",
    "Total file writes",
    ["path", "operation"]
)

file_read_counter = Counter(
    "file_ops_read_total",
    "Total file reads",
    ["path", "operation"]
)

# File size gauge
file_size_gauge = Gauge(
    "file_size_bytes",
    "File size in bytes",
    ["path"]
)

# Operation duration histogram
operation_duration = Histogram(
    "file_operation_duration_seconds",
    "Time spent on file operations",
    ["operation"]
)

# Usage
with operation_duration.labels(operation="write").time():
    file_write_counter.inc(
        tags={
            "path": "data.txt",
            "operation": "atomic_write"
        }
    )
```

## Setup and Configuration

### 1. Install Dependencies
```bash
pip install -r requirements.txt  # Flask is included
```

### 2. Start Metrics Server
```bash
python -m tools.start_metrics_server
```
The server runs on port `8000` by default.

### 3. Configure Prometheus
Add to your `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'dreamos'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### 4. Import Grafana Dashboard
1. Open Grafana
2. Go to Dashboards > Import
3. Upload `docs/grafana/example_dashboard.json`

## Dashboard Features

### 1. Overview Panel
- System health status
- Active agents
- Recent errors
- Performance summary
- File operation stats
- Resource usage

### 2. Agent Panel
- Agent activity
- Task progress
- Error tracking
- Resource usage
- Response times
- Health status

### 3. Performance Panel
- Response times
- Throughput
- Resource utilization
- Bottleneck analysis
- File operation metrics
- Cache performance

### 4. Health Panel
- Component status
- Error rates
- Warning trends
- Dependency health
- File system health
- Resource health

## Alerting

### 1. Configure Alerts
```yaml
groups:
  - name: dreamos
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.1
        for: 5m
        labels:
          severity: warning
      - alert: HighFileErrorRate
        expr: file_error_rate > 0.05
        for: 5m
        labels:
          severity: warning
```

### 2. Alert Channels
- Email notifications
- Slack integration
- PagerDuty
- Custom webhooks

## Best Practices

### 1. Monitoring
- Regular dashboard review
- Trend analysis
- Capacity planning
- Performance optimization
- File operation monitoring
- Resource tracking

### 2. Maintenance
- Regular metric cleanup
- Dashboard updates
- Alert tuning
- Documentation updates
- File system monitoring
- Performance tuning

### 3. Security
- Secure metrics endpoint
- Access control
- Data retention
- Audit logging
- File operation security
- Resource protection

## Troubleshooting

### Common Issues
1. **Metrics Not Showing**
   - Check server status
   - Verify Prometheus config
   - Check data source
   - Verify file permissions

2. **High Latency**
   - Check network
   - Verify server load
   - Review collection interval
   - Check file system performance

3. **Missing Data**
   - Check retention policy
   - Verify collection
   - Review filters
   - Check file operation logs

## API Reference

### Metrics Endpoint
```
GET /metrics
```
Returns Prometheus-formatted metrics.

### Health Check
```
GET /health
```
Returns system health status.

### File Metrics
```
GET /metrics/file
```
Returns file operation metrics.

## Resources

### Documentation
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Metrics Best Practices](https://prometheus.io/docs/practices/naming/)

### Tools
- Metrics server
- Dashboard templates
- Alert configurations
- Monitoring scripts
- File operation tools
- Performance analysis tools 