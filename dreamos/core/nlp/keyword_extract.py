"""
Keyword Extraction Module
------------------------
Provides keyword extraction functionality for memory analysis.
Currently implements a basic frequency-based approach as a placeholder
for more sophisticated NLP methods.
"""

from typing import List, Dict, Any, Set, Optional
from collections import Counter

class KeywordExtractor:
    """Extracts keywords from text using frequency analysis."""
    
    def __init__(self, stop_words: Optional[Set[str]] = None):
        """Initialize the keyword extractor.
        
        Args:
            stop_words: Optional set of stop words to filter out
        """
        self.stop_words = stop_words or set()
    
    def extract(
        self,
        text: str,
        max_keywords: int = 5,
        min_length: int = 3
    ) -> List[Dict[str, Any]]:
        """Extract keywords from text.
        
        TODO: Replace with RAKE or rapidfuzz for better quality
        - RAKE: Rapid Automatic Keyword Extraction
        - rapidfuzz: Fuzzy string matching for better recall
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
            min_length: Minimum word length to consider
            
        Returns:
            List of keywords with frequency ratios
        """
        if not text:
            return []
            
        # Basic tokenization
        words = [
            w.strip(".,!?\"'()").lower()
            for w in text.split()
            if len(w.strip(".,!?\"'()")) >= min_length
        ]
        
        # Filter stop words and count frequencies
        word_counts = Counter(
            word for word in words
            if word and word not in self.stop_words
        )
        
        total = sum(word_counts.values())
        if not total:
            return []
            
        # Get top keywords by frequency
        top_words = word_counts.most_common(max_keywords)
        
        return [
            {
                "keyword": word,
                "frequency_ratio": min(count / total, 1.0)
            }
            for word, count in top_words
        ] 
