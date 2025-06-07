# Metrics Dashboard

Phase 3 introduces a lightweight metrics feed for monitoring agent activity.

## Running the Metrics Server

Install dependencies (Flask is already in requirements) and run:

```bash
python -m tools.start_metrics_server
```

This starts a small Flask app on port `8000` that serves the contents of
`logs/metrics.json` at `/metrics`. The `LogMetrics` class in
`dreamos.core.monitoring.metrics` writes this file whenever log events
occur.

## Integrating with Grafana/Prometheus

Point Prometheus to `http://localhost:8000/metrics` to scrape metrics.
Then import the provided example dashboard JSON under `docs/grafana/example_dashboard.json`.
