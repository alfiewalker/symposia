"""
Committee orchestration and deliberation logic.
"""

import asyncio
import logging
from typing import List, Optional

from ..strategies.base import VotingStrategy
from ..utils.parsing import parse_llm_json_response
from .member import CommitteeMember
from .reputation import ReputationManager
from .result import DeliberationResult

logger = logging.getLogger(__name__)


class Committee:
    """Orchestrates deliberation among committee members using a voting strategy."""
    
    def __init__(self, name: str, members: List[CommitteeMember], 
                 voting_strategy: VotingStrategy, 
                 reputation_manager: Optional[ReputationManager] = None):
        self.name = name
        self.members = members
        self.voting_strategy = voting_strategy
        self.reputation_manager = reputation_manager
    
    async def deliberate(self, topic_prompt: str) -> DeliberationResult:
        """
        Conduct a deliberation on the given topic.
        
        Args:
            topic_prompt: The topic for deliberation
            
        Returns:
            DeliberationResult containing the outcome and full trace
        """
        logger.info(f"Deliberation started for committee '{self.name}' on topic: {topic_prompt[:50]}...")
        
        # Collect votes from all members concurrently
        full_trace = []
        parsed_votes = []
        total_tokens = 0
        total_cost = 0.0
        
        # Execute all votes in parallel
        results = await asyncio.gather(*[member.cast_vote(topic_prompt) for member in self.members])
        
        # Process results
        for i, result in enumerate(results):
            member = self.members[i]
            status = "Success"
            
            # Handle errors
            if result.get("error"):
                status = f"Failed: {result['error']}"
                logger.warning(f"Member '{member.name}' failed to vote: {result['error']}")
            
            # Parse the response
            raw_opinion = result.get('response', '')
            parsed_opinion = parse_llm_json_response(raw_opinion)
            
            # Use current effective weight for voting
            vote_weight = member.effective_weight
            
            # Add successful votes to the tally
            if status == "Success":
                parsed_votes.append({
                    'value': parsed_opinion.get('vote'),
                    'weight': vote_weight
                })
            
            # Track costs and tokens
            cost = result.get('cost', 0.0)
            tokens = result.get('tokens_used', 0)
            total_cost += cost
            total_tokens += tokens
            
            # Add to trace
            full_trace.append({
                "member_object": member,
                "member_name": member.name,
                "reputation": member.reputation,
                "effective_weight": vote_weight,
                "llm_service": member.llm_service.config.model,
                "raw_opinion": raw_opinion,
                "parsed_vote": parsed_opinion,
                "status": status,
                "cost": cost,
                "tokens_used": tokens
            })
        
        # Calculate final result using voting strategy
        final_result = self.voting_strategy.tally(parsed_votes)
        
        # Update reputations if manager exists
        if self.reputation_manager:
            deliberation_result = DeliberationResult(
                topic_prompt, 
                self.voting_strategy.__class__.__name__, 
                final_result, 
                full_trace, 
                total_tokens, 
                total_cost
            )
            self.reputation_manager.update_reputations(deliberation_result)
        
        logger.info(f"Deliberation for '{self.name}' complete. Final result: {final_result}")
        
        return DeliberationResult(
            topic_prompt,
            self.voting_strategy.__class__.__name__,
            final_result,
            full_trace,
            total_tokens,
            total_cost
        ) 