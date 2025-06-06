"""
Memory Querier Module
--------------------
Enables agents to query and analyze their narrative memory corpus.
"""

import time
import difflib
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from .dreamscribe import Dreamscribe

class MemoryQuerier:
    """Provides query interface for agent memory corpus."""
    
    def __init__(self, dreamscribe: Dreamscribe):
        """Initialize the memory querier.
        
        Args:
            dreamscribe: Dreamscribe instance to query
        """
        self.dreamscribe = dreamscribe
        
    def get_recent_memory(
        self,
        agent_id: Optional[str] = None,
        limit: int = 5,
        time_window: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get recent memory fragments.
        
        Args:
            agent_id: Optional agent ID to filter by
            limit: Maximum number of memories to return
            time_window: Optional time window in seconds
            
        Returns:
            List of recent memory fragments
        """
        memories = []
        current_time = time.time()
        cutoff_time = current_time - time_window if time_window is not None else None
        
        # Get all memories from corpus
        for memory_id, memory in self.dreamscribe.memory_corpus.items():
            # Apply filters
            if agent_id and memory["agent_id"] != agent_id:
                continue
                
            # Apply time window filter if specified
            if cutoff_time is not None:
                if memory["timestamp"] < cutoff_time:
                    continue
                
            memories.append({
                "memory_id": memory_id,
                "timestamp": memory["timestamp"],
                "agent_id": memory["agent_id"],
                "content": memory["content"],
                "context": memory["context"],
                "insights": memory["insights"],
                "connections": memory["connections"]
            })
                
        # Sort by timestamp descending and limit
        return sorted(memories, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
    def summarize_topic(
        self,
        topic: str,
        time_window: Optional[int] = None,
        min_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """Summarize memories related to a topic.
        
        Args:
            topic: Topic to search for
            time_window: Optional time window in seconds
            min_confidence: Minimum confidence for insights
            
        Returns:
            Dictionary containing summary and related memories
        """
        memories = []
        current_time = time.time()
        cutoff_time = current_time - time_window if time_window else 0
        topic = topic.lower()
        
        # Collect relevant memories
        for memory_id, memory in self.dreamscribe.memory_corpus.items():
            # Check content and context
            if (topic in memory["content"].lower() or
                any(topic in str(v).lower() for v in memory["context"].values())):
                
                # Apply filters
                if time_window and memory["timestamp"] < cutoff_time:
                    continue
                    
                memories.append({
                    "memory_id": memory_id,
                    "timestamp": memory["timestamp"],
                    "agent_id": memory["agent_id"],
                    "content": memory["content"],
                    "context": memory["context"],
                    "insights": [
                        i for i in memory["insights"]
                        if i.get("confidence", 0) >= min_confidence
                    ],
                    "connections": memory["connections"]
                })
        
        # Sort by timestamp
        memories.sort(key=lambda x: x["timestamp"])
        
        # Generate summary
        summary = {
            "topic": topic,
            "memory_count": len(memories),
            "time_span": (
                memories[-1]["timestamp"] - memories[0]["timestamp"]
                if memories else 0
            ),
            "key_insights": [],
            "related_agents": list(set(m["agent_id"] for m in memories)),
            "memories": memories
        }
        
        # Extract key insights
        for memory in memories:
            for insight in memory["insights"]:
                if insight.get("confidence", 0) >= min_confidence:
                    summary["key_insights"].append({
                        "content": insight["content"],
                        "confidence": insight["confidence"],
                        "timestamp": memory["timestamp"],
                        "agent_id": memory["agent_id"]
                    })
        
        return summary
        
    def find_similar_threads(
        self,
        memory_id: str,
        min_similarity: float = 0.5,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find threads similar to a given memory.
        
        Args:
            memory_id: ID of the reference memory
            min_similarity: Minimum similarity threshold
            limit: Maximum number of threads to return
            
        Returns:
            List of similar threads with similarity scores
        """
        reference = self.dreamscribe.memory_corpus.get(memory_id)
        if not reference:
            return []
            
        similar_threads = []
        
        # Compare with other memories
        for other_id, other_memory in self.dreamscribe.memory_corpus.items():
            if other_id == memory_id:
                continue
                
            # Calculate similarity
            similarity = self._calculate_memory_similarity(reference, other_memory)
            if similarity >= min_similarity:
                similar_threads.append({
                    "memory_id": other_id,
                    "similarity": similarity,
                    "content": other_memory["content"],
                    "context": other_memory["context"]
                })
                
        # Sort by similarity and limit results
        return sorted(
            similar_threads,
            key=lambda x: x["similarity"],
            reverse=True
        )[:limit]
        
    def _calculate_memory_similarity(
        self,
        memory1: Dict[str, Any],
        memory2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two memories.
        
        Args:
            memory1: First memory
            memory2: Second memory
            
        Returns:
            Similarity score between 0 and 1
        """
        # Use SequenceMatcher ratio as a lightweight similarity metric
        content1 = memory1["content"].lower()
        content2 = memory2["content"].lower()

        if not content1 or not content2:
            return 0.0

        return difflib.SequenceMatcher(None, content1, content2).ratio()
        
    def get_agent_insights(
        self,
        agent_id: str,
        time_window: Optional[int] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get insights generated by an agent.
        
        Args:
            agent_id: Agent ID to get insights for
            time_window: Optional time window in seconds
            min_confidence: Minimum confidence for insights
            
        Returns:
            List of agent insights
        """
        insights = []
        current_time = time.time()
        cutoff_time = current_time - time_window if time_window else 0
        
        for memory_id, memory in self.dreamscribe.memory_corpus.items():
            if memory["agent_id"] != agent_id:
                continue
                
            # Apply filters
            if time_window and memory["timestamp"] < cutoff_time:
                continue
                
            for insight in memory["insights"]:
                if insight.get("confidence", 0) >= min_confidence:
                    insights.append({
                        "memory_id": memory_id,
                        "timestamp": memory["timestamp"],
                        "content": insight["content"],
                        "confidence": insight["confidence"],
                        "context": memory["context"],
                        "agent_id": memory["agent_id"]  # Include agent_id in insight
                    })
        
        # Sort by timestamp descending
        return sorted(insights, key=lambda x: x["timestamp"], reverse=True)
        
    def get_task_history(
        self,
        task_id: str,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """Get history of a specific task.
        
        Args:
            task_id: Task ID to get history for
            include_related: Whether to include related tasks
            
        Returns:
            Dictionary containing task history and related information
        """
        memories = []
        related_tasks = set()
        
        for memory_id, memory in self.dreamscribe.memory_corpus.items():
            # Check if memory is related to task
            if memory["context"].get("task_id") == task_id:
                memories.append({
                    "memory_id": memory_id,
                    "timestamp": memory["timestamp"],
                    "agent_id": memory["agent_id"],
                    "content": memory["content"],
                    "context": memory["context"],
                    "insights": memory["insights"],
                    "connections": memory["connections"]
                })
                
                # Track related tasks
                if include_related:
                    for conn in memory["connections"]:
                        related_memory = self.dreamscribe.memory_corpus.get(conn)
                        if related_memory:
                            related_tasks.add(
                                related_memory["context"].get("task_id")
                            )
        
        # Sort by timestamp
        memories.sort(key=lambda x: x["timestamp"])
        
        # Get related task histories
        related_histories = {}
        if include_related:
            for related_id in related_tasks:
                if related_id != task_id:
                    related_histories[related_id] = self.get_task_history(
                        related_id,
                        include_related=False
                    )
        
        return {
            "task_id": task_id,
            "memory_count": len(memories),
            "time_span": (
                memories[-1]["timestamp"] - memories[0]["timestamp"]
                if memories else 0
            ),
            "memories": memories,
            "related_tasks": list(related_tasks),
            "related_histories": related_histories
        } 