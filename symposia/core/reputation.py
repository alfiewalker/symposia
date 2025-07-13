"""
Reputation management for committee members.
"""

import logging
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .member import CommitteeMember
    from .result import DeliberationResult

logger = logging.getLogger(__name__)


class ReputationManager:
    """Manages reputation scores for committee members based on voting patterns."""
    
    def __init__(self, members: List['CommitteeMember'], 
                 agreement_bonus: float = 0.05, dissent_penalty: float = 0.02):
        self.agreement_bonus = agreement_bonus
        self.dissent_penalty = dissent_penalty
        logger.info(f"ReputationManager initialized with bonus={agreement_bonus}, penalty={dissent_penalty}")
    
    def update_reputations(self, result: 'DeliberationResult') -> None:
        """
        Update member reputations based on internal consistency with the final outcome.
        
        Args:
            result: The deliberation result containing voting trace
        """
        final_outcome = result.final_result
        logger.info(f"Updating reputations based on final outcome: '{final_outcome}'")
        
        for trace_step in result.trace:
            member = trace_step['member_object']
            
            # Skip technical failures
            if trace_step['status'] != "Success":
                continue
            
            member_vote = trace_step['parsed_vote'].get('vote')
            
            if member_vote == final_outcome:
                member.reputation += self.agreement_bonus
                logger.debug(f"Member '{member.name}' agreed. Reputation increased to {member.reputation:.3f}")
            else:
                member.reputation -= self.dissent_penalty
                logger.debug(f"Member '{member.name}' dissented. Reputation decreased to {member.reputation:.3f}")
            
            # Prevent reputation from dropping too low
            member.reputation = max(0.1, member.reputation) 