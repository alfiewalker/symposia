"""
Median scoring strategy.
"""

from typing import List, Dict, Any
from .base import VotingStrategy


class MedianScore(VotingStrategy):
    """Voting strategy that calculates the median of numerical scores."""
    
    def tally(self, votes: List[Dict[str, Any]]) -> float:
        """
        Calculate median of numerical votes.
        
        Args:
            votes: List of vote dictionaries with 'value' and 'weight' keys
            
        Returns:
            The median score
        """
        scores = []
        
        for vote in votes:
            value = vote.get('value')
            if value is not None and isinstance(value, (int, float)):
                scores.append(value)
        
        if not scores:
            return 0.0
        
        scores.sort()
        mid = len(scores) // 2
        
        if len(scores) % 2 == 0:
            return (scores[mid - 1] + scores[mid]) / 2
        else:
            return scores[mid] 