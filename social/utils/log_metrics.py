"""Deprecated metrics utilities."""

from dreamos.core.monitoring.metrics import LogMetrics

metrics = LogMetrics()
record_metric = metrics.record_metric
get_metric = metrics.get_metrics
clear_metrics = metrics.clear_metrics

__all__ = ["LogMetrics", "metrics", "record_metric", "get_metric", "clear_metrics"]
