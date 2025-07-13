"""
Weighted mean scoring strategy.
"""

from typing import List, Dict, Any
from .base import VotingStrategy


class WeightedMeanScore(VotingStrategy):
    """Voting strategy that calculates the weighted mean of numerical scores."""
    
    def tally(self, votes: List[Dict[str, Any]]) -> float:
        """
        Calculate weighted mean of numerical votes.
        
        Args:
            votes: List of vote dictionaries with 'value' and 'weight' keys
            
        Returns:
            The weighted mean score
        """
        total_score = 0.0
        total_weight = 0.0
        
        for vote in votes:
            score = vote.get('value')
            weight = vote.get('weight', 1.0)
            
            if score is None or not isinstance(score, (int, float)):
                continue
                
            total_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
            
        return total_score / total_weight 