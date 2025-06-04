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
    
    def __init__(self):
        """Initialize the Dreamscribe system."""
        self.memory_corpus: Dict[str, MemoryFragment] = {}
        self.narrative_threads: List[NarrativeThread] = []
        self.insight_patterns: Dict[str, Any] = {}
        
        # Ensure directories exist
        NARRATIVE_THREADS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Load existing memory if available
        self._load_memory_corpus()
        self._load_narrative_threads()
        self._load_insight_patterns()
        
        # Initialize logging
        self.logger = logging.getLogger("dreamscribe")
        
    def _load_memory_corpus(self):
        """Load existing memory corpus from disk."""
        if MEMORY_CORPUS_PATH.exists():
            try:
                with open(MEMORY_CORPUS_PATH, 'r') as f:
                    data = json.load(f)
                    self.memory_corpus = {
                        k: MemoryFragment(**v) for k, v in data.items()
                    }
            except Exception as e:
                self.logger.error(f"Failed to load memory corpus: {e}")
                self.memory_corpus = {}
    
    def _load_narrative_threads(self):
        """Load existing narrative threads from disk."""
        if NARRATIVE_THREADS_PATH.exists():
            for thread_file in NARRATIVE_THREADS_PATH.glob("*.json"):
                try:
                    with open(thread_file, 'r') as f:
                        data = json.load(f)
                        self.narrative_threads.append(NarrativeThread(**data))
                except Exception as e:
                    self.logger.error(f"Failed to load thread {thread_file}: {e}")
    
    def _load_insight_patterns(self):
        """Load existing insight patterns from disk."""
        if INSIGHT_PATTERNS_PATH.exists():
            try:
                with open(INSIGHT_PATTERNS_PATH, 'r') as f:
                    self.insight_patterns = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load insight patterns: {e}")
                self.insight_patterns = {}
    
    def _save_memory_corpus(self):
        """Save memory corpus to disk."""
        try:
            with open(MEMORY_CORPUS_PATH, 'w') as f:
                json.dump(
                    {k: asdict(v) for k, v in self.memory_corpus.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            self.logger.error(f"Failed to save memory corpus: {e}")
    
    def _save_narrative_thread(self, thread: NarrativeThread):
        """Save a narrative thread to disk."""
        try:
            thread_file = NARRATIVE_THREADS_PATH / f"{thread.thread_id}.json"
            with open(thread_file, 'w') as f:
                json.dump(asdict(thread), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save thread {thread.thread_id}: {e}")
    
    def _save_insight_patterns(self):
        """Save insight patterns to disk."""
        try:
            with open(INSIGHT_PATTERNS_PATH, 'w') as f:
                json.dump(self.insight_patterns, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save insight patterns: {e}")
    
    def _generate_memory_id(self, content: str, timestamp: float) -> str:
        """Generate a unique memory ID."""
        # Combine content and timestamp for uniqueness
        unique_str = f"{content}{timestamp}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
    
    def _extract_insights(self, devlog: Dict[str, Any]) -> List[str]:
        """Extract key insights from a devlog.
        
        TODO: Implement proper NLP-based insight extraction.
        For now, use basic pattern matching.
        """
        insights = []
        content = devlog.get('content', '')
        
        # Basic insight patterns
        if 'error' in content.lower():
            insights.append("Error encountered and handled")
        if 'success' in content.lower():
            insights.append("Task completed successfully")
        if 'learned' in content.lower():
            insights.append("New knowledge acquired")
            
        return insights
    
    def _find_connections(self, memory: MemoryFragment) -> List[str]:
        """Find connections to existing memories.
        
        TODO: Implement semantic similarity search.
        For now, use basic keyword matching.
        """
        connections = []
        
        # Look for related memories based on content
        for mem_id, existing_mem in self.memory_corpus.items():
            if (memory.agent_id == existing_mem.agent_id and
                abs(memory.timestamp - existing_mem.timestamp) < 3600):  # Within 1 hour
                connections.append(mem_id)
                
        return connections
    
    def _update_narratives(self, memory: MemoryFragment):
        """Update narrative threads with new memory."""
        # Check if memory fits into existing threads
        for thread in self.narrative_threads:
            if self._memory_fits_thread(memory, thread):
                thread.memories.append(memory.memory_id)
                thread.last_updated = time.time()
                self._save_narrative_thread(thread)
                return
        
        # Create new thread if needed
        if memory.narrative_weight > 0.5:  # Only create threads for significant memories
            new_thread = NarrativeThread(
                thread_id=self._generate_memory_id(memory.content, memory.timestamp),
                title=f"Thread from {datetime.fromtimestamp(memory.timestamp)}",
                memories=[memory.memory_id],
                theme=self._extract_theme(memory),
                created_at=time.time(),
                last_updated=time.time()
            )
            self.narrative_threads.append(new_thread)
            self._save_narrative_thread(new_thread)
    
    def _memory_fits_thread(self, memory: MemoryFragment, thread: NarrativeThread) -> bool:
        """Check if a memory fits into an existing thread."""
        # TODO: Implement proper thread matching logic
        # For now, use basic agent and time-based matching
        if not thread.memories:
            return False
            
        last_memory = self.memory_corpus[thread.memories[-1]]
        return (memory.agent_id == last_memory.agent_id and
                abs(memory.timestamp - last_memory.timestamp) < 3600)
    
    def _extract_theme(self, memory: MemoryFragment) -> str:
        """Extract the theme of a memory.
        
        TODO: Implement proper theme extraction.
        For now, use basic categorization.
        """
        if 'error' in memory.content.lower():
            return "Error Resolution"
        if 'success' in memory.content.lower():
            return "Task Completion"
        return "General Activity"
    
    def _analyze_patterns(self, memory: MemoryFragment):
        """Analyze patterns across memories."""
        # Update insight patterns based on new memory
        for insight in memory.insights:
            if insight not in self.insight_patterns:
                self.insight_patterns[insight] = {
                    'count': 0,
                    'first_seen': memory.timestamp,
                    'last_seen': memory.timestamp,
                    'related_memories': []
                }
            else:
                self.insight_patterns[insight]['count'] += 1
                self.insight_patterns[insight]['last_seen'] = memory.timestamp
                self.insight_patterns[insight]['related_memories'].append(memory.memory_id)
        
        self._save_insight_patterns()
    
    def ingest_devlog(self, devlog: Dict[str, Any]):
        """Transform a devlog into a memory fragment and integrate it into the system."""
        # Create memory fragment
        memory = MemoryFragment(
            timestamp=devlog.get('timestamp', time.time()),
            agent_id=devlog.get('agent_id', 'unknown'),
            content=devlog.get('content', ''),
            context=devlog.get('context', {}),
            insights=self._extract_insights(devlog),
            connections=[],
            memory_id=self._generate_memory_id(
                devlog.get('content', ''),
                devlog.get('timestamp', time.time())
            )
        )
        
        # Find connections
        memory.connections = self._find_connections(memory)
        
        # Add to memory corpus
        self.memory_corpus[memory.memory_id] = memory
        
        # Update narratives
        self._update_narratives(memory)
        
        # Analyze patterns
        self._analyze_patterns(memory)
        
        # Save changes
        self._save_memory_corpus()
        
        self.logger.info(
            f"Memory ingested: {memory.memory_id} from agent {memory.agent_id}"
        )
        
        return memory.memory_id
    
    def get_system_insights(self) -> Dict[str, Any]:
        """Get current system insights and patterns."""
        return {
            'patterns': self.insight_patterns,
            'narratives': [
                {
                    'thread_id': t.thread_id,
                    'title': t.title,
                    'theme': t.theme,
                    'memory_count': len(t.memories)
                }
                for t in self.narrative_threads
            ],
            'memory_state': {
                'total_memories': len(self.memory_corpus),
                'active_threads': len(self.narrative_threads),
                'insight_count': len(self.insight_patterns)
            }
        }
    
    def get_memory(self, memory_id: str) -> Optional[MemoryFragment]:
        """Retrieve a specific memory by ID."""
        return self.memory_corpus.get(memory_id)
    
    def get_thread(self, thread_id: str) -> Optional[NarrativeThread]:
        """Retrieve a specific narrative thread by ID."""
        for thread in self.narrative_threads:
            if thread.thread_id == thread_id:
                return thread
        return None 