"""
Dreamscribe: The Narrative Memory System
---------------------------------------
Transforms devlogs into a living memory corpus, enabling system-wide self-awareness
and narrative coherence. Each memory becomes a thread in the system's consciousness.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import hashlib
from uuid import uuid4
from ..keyword_extract import KeywordExtractor
from .gpt_router import Router, Engine

# Constants
MEMORY_CORPUS_PATH = Path("runtime/memory_corpus.json")
NARRATIVE_THREADS_PATH = Path("runtime/narrative_threads/")
INSIGHT_PATTERNS_PATH = Path("runtime/insight_patterns.json")

@dataclass
class MemoryFragment:
    """A single memory fragment from a devlog or system event."""
    timestamp: float
    agent_id: str
    content: str
    context: Dict[str, Any]
    insights: List[str]
    connections: List[str]
    memory_id: str
    type: str = "devlog"  # devlog, system_event, reflection, etc.
    narrative_weight: float = 1.0  # Importance in narrative threads

@dataclass
class NarrativeThread:
    """A connected sequence of memories forming a coherent story."""
    thread_id: str
    title: str
    memories: List[str]  # List of memory_ids
    theme: str
    created_at: float
    last_updated: float
    weight: float = 1.0  # Thread importance

class Dreamscribe:
    """The core memory and narrative system for Dream.OS."""
    
    def __init__(self, scraper=None):
        """Initialize the Dreamscribe system."""
        self.logger = logging.getLogger("dreamscribe")
        self.memory_corpus: Dict[str, Dict[str, Any]] = {}
        self.threads: Dict[str, List[str]] = {}
        self.insight_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.keyword_extractor = KeywordExtractor()
        
        # Initialize GPT routing system
        self.router = Router()
        self.engine = Engine(scraper) if scraper else None
        
        # Ensure directories exist
        NARRATIVE_THREADS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_memory_corpus()
        self._load_threads()
        self._load_insight_patterns()
        
        # Initialize keyword extractor with stop words
        if "stop_words" in self.insight_patterns:
            self.keyword_extractor = KeywordExtractor(
                stop_words=set(self.insight_patterns["stop_words"])
            )
    
    def _load_memory_corpus(self):
        """Load memory corpus from disk."""
        if MEMORY_CORPUS_PATH.exists():
            try:
                with open(MEMORY_CORPUS_PATH, "r") as f:
                    self.memory_corpus = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load memory corpus: {e}")
                self.memory_corpus = {}
    
    def _load_threads(self):
        """Load narrative threads from disk."""
        if NARRATIVE_THREADS_PATH.exists():
            for thread_file in NARRATIVE_THREADS_PATH.glob("*.json"):
                try:
                    with open(thread_file, "r") as f:
                        thread_id = thread_file.stem
                        self.threads[thread_id] = json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to load thread {thread_file.stem}: {e}")
    
    def _load_insight_patterns(self):
        """Load insight patterns from disk."""
        if INSIGHT_PATTERNS_PATH.exists():
            try:
                with open(INSIGHT_PATTERNS_PATH, "r") as f:
                    self.insight_patterns = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load insight patterns: {e}")
                self.insight_patterns = {}
    
    def _save_memory_corpus(self):
        """Save memory corpus to disk."""
        try:
            with open(MEMORY_CORPUS_PATH, "w") as f:
                json.dump(self.memory_corpus, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save memory corpus: {e}")
    
    def _save_thread(self, thread_id: str):
        """Save a narrative thread to disk."""
        try:
            thread_file = NARRATIVE_THREADS_PATH / f"{thread_id}.json"
            with open(thread_file, "w") as f:
                json.dump(self.threads[thread_id], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save thread {thread_id}: {e}")
    
    def _save_insight_patterns(self):
        """Save insight patterns to disk."""
        try:
            with open(INSIGHT_PATTERNS_PATH, "w") as f:
                json.dump(self.insight_patterns, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save insight patterns: {e}")
    
    def _extract_insights(self, fragment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract insights from a memory fragment using keyword extraction.
        
        Args:
            fragment: Memory fragment to analyze
            
        Returns:
            List of extracted insights with frequency ratios
        """
        if not fragment.get("content"):
            return []
            
        # Use keyword extractor to get insights
        keywords = self.keyword_extractor.extract(
            fragment["content"],
            max_keywords=5
        )
        
        return [
            {
                "content": kw["keyword"],
                "frequency_ratio": kw["frequency_ratio"]
            }
            for kw in keywords
        ]
    
    def _find_connections(self, fragment: Dict[str, Any]) -> List[str]:
        """Find connections between memory fragments.
        
        Args:
            fragment: Memory fragment to analyze
            
        Returns:
            List of connected memory IDs
        """
        connections = []
        
        # Connect based on task_id
        if task_id := fragment["context"].get("task_id"):
            for mem_id, mem in self.memory_corpus.items():
                if (mem_id != fragment["memory_id"] and
                    mem["context"].get("task_id") == task_id):
                    connections.append(mem_id)
        
        # Connect based on agent_id
        agent_id = fragment["agent_id"]
        for mem_id, mem in self.memory_corpus.items():
            if (mem_id != fragment["memory_id"] and
                mem["agent_id"] == agent_id and
                abs(mem["timestamp"] - fragment["timestamp"]) < 3600):  # Within 1 hour
                connections.append(mem_id)
        
        return list(set(connections))
    
    def _update_narratives(self, fragment: Dict[str, Any]):
        """Update narrative threads with new memory fragment.
        
        Args:
            fragment: Memory fragment to add to narratives
        """
        # Create new thread if needed
        thread_id = f"thread_{int(time.time())}"
        if thread_id not in self.threads:
            self.threads[thread_id] = []
        
        # Add to thread
        self.threads[thread_id].append(fragment["memory_id"])
        self._save_thread(thread_id)
    
    def process_with_gpt(self, content: str, context: Dict[str, Any]) -> str:
        """Process content using the GPT router system.
        
        Args:
            content: The content to process
            context: Additional context for processing
            
        Returns:
            Processed content from GPT
        """
        if not self.engine:
            self.logger.warning("GPT engine not initialized, skipping processing")
            return content
            
        # Create a context URL that will route to dreamscribe profile
        context_url = f"log/{context.get('agent_id', 'system')}/{context.get('type', 'devlog')}"
        
        # Get the dreamscribe profile
        profile = self.router.decide_prompt(context_url)
        
        # Process with GPT
        result = self.engine.process_conversation(context_url)
        
        return result["reply"]

    def ingest_devlog(self, devlog_entry: Dict[str, Any]) -> str:
        """Ingest a development log entry into the memory corpus.
        
        Args:
            devlog_entry: The devlog entry to ingest
            
        Returns:
            ID of the created memory fragment
        """
        # Process with GPT if available
        if self.engine:
            processed_content = self.process_with_gpt(
                devlog_entry["content"],
                {"type": "devlog", "agent_id": devlog_entry.get("agent_id", "system")}
            )
            devlog_entry["content"] = processed_content
        
        # Create memory fragment
        fragment = MemoryFragment(
            timestamp=time.time(),
            agent_id=devlog_entry.get("agent_id", "system"),
            content=devlog_entry["content"],
            context=devlog_entry.get("context", {}),
            insights=[],
            connections=[],
            memory_id=str(uuid4()),
            type="devlog"
        )
        
        # Extract insights and connections
        fragment.insights = self._extract_insights(asdict(fragment))
        fragment.connections = self._find_connections(asdict(fragment))
        
        # Add to memory corpus
        self.memory_corpus[fragment.memory_id] = asdict(fragment)
        self._save_memory_corpus()
        
        # Update narrative threads
        self._update_narratives(asdict(fragment))
        
        return fragment.memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory fragment by ID.
        
        Args:
            memory_id: ID of the memory fragment
            
        Returns:
            Memory fragment if found, None otherwise
        """
        return self.memory_corpus.get(memory_id)
    
    def get_thread(self, thread_id: str) -> Optional[List[str]]:
        """Get a narrative thread by ID.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            List of memory IDs in the thread if found, None otherwise
        """
        return self.threads.get(thread_id)
    
    def get_system_insights(self) -> Dict[str, Any]:
        """Get system-wide insights and narrative patterns.
        
        Returns:
            Dictionary containing insights and narrative patterns
        """
        return {
            "narratives": [
                {
                    "thread_id": thread_id,
                    "memory_count": len(memories),
                    "memories": memories
                }
                for thread_id, memories in self.threads.items()
            ],
            "patterns": self.insight_patterns
        }

    # ------------------------------------------------------------------
    # New Beta API ------------------------------------------------------
    # ------------------------------------------------------------------
    def query_memories(
        self,
        agent_id: Optional[str] = None,
        start: Optional[float] = None,
        end: Optional[float] = None,
        keyword: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return memory fragments filtered by agent, time range, and keyword."""

        results = []
        for frag in self.memory_corpus.values():
            if agent_id and frag.get("agent_id") != agent_id:
                continue
            if start and frag.get("timestamp", 0) < start:
                continue
            if end and frag.get("timestamp", 0) > end:
                continue
            if keyword and keyword.lower() not in frag.get("content", "").lower():
                continue
            results.append(frag)

        return results
