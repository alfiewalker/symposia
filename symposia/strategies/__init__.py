"""
Voting strategies for committee deliberation.
"""

from .base import VotingStrategy
from .majority import WeightedMajorityVote
from .mean import WeightedMeanScore
from .median import MedianScore

__all__ = ['VotingStrategy', 'WeightedMajorityVote', 'WeightedMeanScore', 'MedianScore'] 