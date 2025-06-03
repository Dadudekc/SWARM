"""
Performance Monitoring System

Tracks and optimizes system performance metrics in real-time.
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List
import psutil
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, metrics_dir: str = "metrics"):
        self.metrics_dir = metrics_dir
        self.metrics_file = os.path.join(metrics_dir, "system_metrics.json")
        self.initialize_metrics()
        
    def initialize_metrics(self):
        """Initialize metrics tracking."""
        if not os.path.exists(self.metrics_dir):
            os.makedirs(self.metrics_dir)
            
        initial_metrics = {
            "system_metrics": {
                "cpu_usage": [],
                "memory_usage": [],
                "disk_io": [],
                "network_io": []
            },
            "agent_metrics": {
                "message_processing_time": [],
                "agent_response_time": [],
                "queue_length": []
            },
            "optimization_metrics": {
                "message_routing_efficiency": [],
                "agent_coordination_overhead": [],
                "system_latency": []
            }
        }
        
        with open(self.metrics_file, 'w') as f:
            json.dump(initial_metrics, f, indent=4)
            
    def collect_system_metrics(self) -> Dict:
        """Collect current system metrics."""
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict(),
            "network_io": psutil.net_io_counters()._asdict()
        }
        
    def update_metrics(self):
        """Update metrics with current system state."""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
                
            # Add new metrics
            current_metrics = self.collect_system_metrics()
            timestamp = datetime.utcnow().isoformat()
            
            for category in metrics["system_metrics"]:
                metrics["system_metrics"][category].append({
                    "timestamp": timestamp,
                    "value": current_metrics[category]
                })
                
            # Keep only last 1000 measurements
            for category in metrics["system_metrics"]:
                metrics["system_metrics"][category] = metrics["system_metrics"][category][-1000:]
                
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=4)
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            
    def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on metrics."""
        recommendations = []
        
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
                
            # Analyze CPU usage
            cpu_usage = [m["value"] for m in metrics["system_metrics"]["cpu_usage"][-10:]]
            if sum(cpu_usage) / len(cpu_usage) > 80:
                recommendations.append("High CPU usage detected - Consider optimizing agent processing")
                
            # Analyze memory usage
            memory_usage = [m["value"] for m in metrics["system_metrics"]["memory_usage"][-10:]]
            if sum(memory_usage) / len(memory_usage) > 80:
                recommendations.append("High memory usage detected - Review memory management")
                
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error analyzing metrics - Check system logs"]
            
    def run_monitoring_loop(self, interval: int = 60):
        """Run continuous monitoring loop."""
        while True:
            self.update_metrics()
            recommendations = self.get_optimization_recommendations()
            
            if recommendations:
                logger.info("Optimization recommendations:")
                for rec in recommendations:
                    logger.info(f"- {rec}")
                    
            time.sleep(interval)

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run_monitoring_loop() 