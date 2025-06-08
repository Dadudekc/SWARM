"""
Content Loop Integration
-----------------------
Integrates Dreamscribe memory system with content generation and task processing.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dreamos.core.ai.dreamscribe import Dreamscribe

# Configure logging
logger = logging.getLogger("ContentLoop")

class ContentLoop:
    """Manages content generation and memory integration."""
    
    def __init__(self):
        """Initialize the content loop."""
        self.dreamscribe = Dreamscribe()
        self.memory_types = {
            "content_generated": "Content generation event",
            "task_completed": "Task completion event",
            "insight_detected": "System insight event"
        }
        
        # Initialize logging
        logger.info("Content loop initialized with Dreamscribe integration")
    
    def log_content_event(
        self,
        agent_id: str,
        task_id: str,
        content: str,
        event_type: str = "content_generated",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a content generation event to Dreamscribe.
        
        Args:
            agent_id: ID of the agent generating content
            task_id: ID of the task being processed
            content: The generated content
            event_type: Type of content event (default: content_generated)
            context: Additional context for the event
            
        Returns:
            memory_id: ID of the created memory fragment
        """
        if event_type not in self.memory_types:
            raise ValueError(f"Invalid event type: {event_type}")
            
        # Create memory fragment
        memory_fragment = {
            "timestamp": time.time(),
            "agent_id": agent_id,
            "content": content,
            "context": {
                "source": "content_loop",
                "type": event_type,
                "task_id": task_id,
                "context_hash": hash(str(context)) if context else None,
                **(context or {})
            }
        }
        
        # Ingest into Dreamscribe
        memory_id = self.dreamscribe.ingest_devlog(memory_fragment)
        
        logger.info(
            f"Content event logged: {event_type} by {agent_id} "
            f"(task: {task_id}, memory: {memory_id})"
        )
        
        return memory_id
    
    def log_task_completion(
        self,
        agent_id: str,
        task_id: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a task completion event.
        
        Args:
            agent_id: ID of the agent completing the task
            task_id: ID of the completed task
            result: Task completion result
            metadata: Additional task metadata
            
        Returns:
            memory_id: ID of the created memory fragment
        """
        return self.log_content_event(
            agent_id=agent_id,
            task_id=task_id,
            content=result,
            event_type="task_completed",
            context=metadata
        )
    
    def log_insight(
        self,
        agent_id: str,
        task_id: str,
        insight: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a system insight.
        
        Args:
            agent_id: ID of the agent generating the insight
            task_id: ID of the related task
            insight: The insight content
            confidence: Confidence level (0.0 to 1.0)
            metadata: Additional insight metadata
            
        Returns:
            memory_id: ID of the created memory fragment
        """
        context = {
            "confidence": confidence,
            **(metadata or {})
        }
        
        return self.log_content_event(
            agent_id=agent_id,
            task_id=task_id,
            content=insight,
            event_type="insight_detected",
            context=context
        )
    
    def get_content_history(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve content history from Dreamscribe.
        
        Args:
            agent_id: Filter by agent ID
            task_id: Filter by task ID
            event_type: Filter by event type
            limit: Maximum number of results
            
        Returns:
            List of memory fragments matching the criteria
        """
        insights = self.dreamscribe.get_system_insights()
        memories = []
        
        for thread in insights["narratives"]:
            thread_obj = self.dreamscribe.get_thread(thread["thread_id"])
            if not thread_obj:
                continue
                
            for memory_id in thread_obj.memories:
                memory = self.dreamscribe.get_memory(memory_id)
                if not memory:
                    continue
                    
                # Apply filters
                if agent_id and memory.agent_id != agent_id:
                    continue
                if task_id and memory.context.get("task_id") != task_id:
                    continue
                if event_type and memory.context.get("type") != event_type:
                    continue
                    
                memories.append({
                    "memory_id": memory.memory_id,
                    "timestamp": memory.timestamp,
                    "agent_id": memory.agent_id,
                    "content": memory.content,
                    "context": memory.context,
                    "insights": memory.insights,
                    "connections": memory.connections
                })
                
                if len(memories) >= limit:
                    break
                    
            if len(memories) >= limit:
                break
                
        return memories 
