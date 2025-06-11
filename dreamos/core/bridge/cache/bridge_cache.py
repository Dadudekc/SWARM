import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class BridgeCache:
    """Manages caching of bridge interactions."""
    
    def __init__(self, cache_dir: str = "runtime/cache"):
        """Initialize bridge cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = 5
        
    def _get_cache_path(self, agent_id: str) -> Path:
        """Get cache file path for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / f"bridge_cache_{agent_id}.json"
        
    def add_interaction(self, agent_id: str, response: str, latency_ms: float) -> None:
        """Add a bridge interaction to cache.
        
        Args:
            agent_id: Agent identifier
            response: Bridge response
            latency_ms: Response latency in milliseconds
        """
        cache_path = self._get_cache_path(agent_id)
        
        # Load existing cache
        entries = []
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    entries = json.load(f)
            except Exception:
                entries = []
                
        # Add new entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "response": response,
            "latency_ms": latency_ms
        }
        
        # Keep only last N entries
        entries = [entry] + entries[:self.max_entries-1]
        
        # Save cache
        with open(cache_path, 'w') as f:
            json.dump(entries, f, indent=2)
            
    def get_interactions(self, agent_id: str) -> List[Dict]:
        """Get cached interactions for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of cached interactions
        """
        cache_path = self._get_cache_path(agent_id)
        if not cache_path.exists():
            return []
            
        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception:
            return []
            
    def get_average_latency(self, agent_id: str) -> Optional[float]:
        """Get average response latency for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Average latency in milliseconds or None if no data
        """
        entries = self.get_interactions(agent_id)
        if not entries:
            return None
            
        latencies = [e["latency_ms"] for e in entries]
        return sum(latencies) / len(latencies) 