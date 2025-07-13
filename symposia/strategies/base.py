"""
Base class for voting strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VotingStrategy(ABC):
    """Abstract base class for voting strategies."""
    
    @abstractmethod
    def tally(self, votes: List[Dict[str, Any]]) -> Any:
        """
        Tally votes and return the final result.
        
        Args:
            votes: List of vote dictionaries containing 'value' and 'weight' keys
            
        Returns:
            The aggregated result based on the strategy
        """
        pass 