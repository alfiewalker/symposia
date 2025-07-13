"""
Weighted majority voting strategy.
"""

from typing import List, Dict, Any
from .base import VotingStrategy


class WeightedMajorityVote(VotingStrategy):
    """Voting strategy that selects the option with the highest weighted score."""
    
    def tally(self, votes: List[Dict[str, Any]]) -> str:
        """
        Tally votes using weighted majority rule.
        
        Args:
            votes: List of vote dictionaries with 'value' and 'weight' keys
            
        Returns:
            The option with the highest weighted score
        """
        scores: Dict[str, float] = {}
        
        for vote in votes:
            value = vote.get('value')
            weight = vote.get('weight', 1.0)
            
            if value is None:
                continue
                
            scores[value] = scores.get(value, 0) + weight
        
        if not scores:
            return "No valid votes."
            
        return max(scores, key=scores.get) 