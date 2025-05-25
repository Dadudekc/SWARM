import time
from typing import Dict, Any, List
from collections import deque
from dreamos.social.log_writer import logger

class PerformanceMetrics:
    """Tracks and manages performance metrics for driver sessions."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics = {
            "page_loads": deque(maxlen=max_history),
            "element_waits": deque(maxlen=max_history),
            "js_executions": deque(maxlen=max_history),
            "memory_usage": deque(maxlen=max_history),
            "dom_nodes": deque(maxlen=max_history),
            "errors": {
                "network": [],
                "timeouts": [],
                "javascript": [],
                "other": []
            },
            "success_rate": 1.0,
            "total_requests": 0
        }
    
    def update_page_load(self, load_time: float) -> None:
        """Update page load time metrics."""
        self.metrics["page_loads"].append(load_time)
        self._update_success_rate()
    
    def update_element_wait(self, wait_time: float) -> None:
        """Update element wait time metrics."""
        self.metrics["element_waits"].append(wait_time)
        self._update_success_rate()
    
    def update_javascript_execution(self, exec_time: float) -> None:
        """Update JavaScript execution time metrics."""
        self.metrics["js_executions"].append(exec_time)
        self._update_success_rate()
    
    def update_memory(self, heap_size: int, dom_nodes: int) -> None:
        """Update memory usage metrics."""
        self.metrics["memory_usage"].append(heap_size)
        self.metrics["dom_nodes"].append(dom_nodes)
    
    def record_error(self, error_type: str, error_msg: str) -> None:
        """Record an error occurrence."""
        if error_type in self.metrics["errors"]:
            self.metrics["errors"][error_type].append({
                "timestamp": time.time(),
                "message": error_msg
            })
        else:
            self.metrics["errors"]["other"].append({
                "timestamp": time.time(),
                "message": error_msg
            })
        self._update_success_rate()
    
    def _update_success_rate(self) -> None:
        """Update the overall success rate."""
        total_requests = len(self.metrics["page_loads"]) + len(self.metrics["element_waits"]) + len(self.metrics["js_executions"])
        total_errors = sum(len(errors) for errors in self.metrics["errors"].values())
        
        if total_requests > 0:
            self.metrics["success_rate"] = 1 - (total_errors / total_requests)
            self.metrics["total_requests"] = total_requests
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "avg_page_load": self._get_average(self.metrics["page_loads"]),
            "avg_element_wait": self._get_average(self.metrics["element_waits"]),
            "avg_js_execution": self._get_average(self.metrics["js_executions"]),
            "avg_memory_usage": self._get_average(self.metrics["memory_usage"]),
            "avg_dom_nodes": self._get_average(self.metrics["dom_nodes"]),
            "success_rate": self.metrics["success_rate"],
            "total_requests": self.metrics["total_requests"],
            "error_counts": {
                error_type: len(errors)
                for error_type, errors in self.metrics["errors"].items()
            }
        }
    
    def _get_average(self, values: deque) -> float:
        """Calculate average of a deque of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def reset(self) -> None:
        """Reset all metrics."""
        for key in self.metrics:
            if isinstance(self.metrics[key], deque):
                self.metrics[key].clear()
            elif isinstance(self.metrics[key], dict):
                for subkey in self.metrics[key]:
                    self.metrics[key][subkey] = [] if isinstance(self.metrics[key][subkey], list) else 0.0 