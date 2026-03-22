"""
Factory for creating committees from configuration.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import ValidationError

from .models import AppConfig
from ..core.providers.openai_service import OpenAIService
from ..core.providers.claude_service import ClaudeService
from ..core.providers.gemini_service import GeminiService
from ..core.member import CommitteeMember
from ..core.reputation import ReputationManager
from ..core.committee import Committee
from ..strategies import WeightedMajorityVote, WeightedMeanScore, MedianScore
from ..utils.cache import SimpleCache

if TYPE_CHECKING:
    from ..core.providers.base import LLMService

logger = logging.getLogger(__name__)


class CommitteeFactory:
    """Factory for creating committees from configuration."""
    
    PROVIDER_MAP = {
        'openai': OpenAIService,
        'anthropic': ClaudeService,
        'google': GeminiService
    }
    
    STRATEGY_MAP = {
        'WeightedMajorityVote': WeightedMajorityVote,
        'WeightedMeanScore': WeightedMeanScore,
        'MedianScore': MedianScore
    }
    
    def __init__(self, config_dict: Dict[str, Any], cache: Optional[SimpleCache] = None):
        """
        Initialize the factory with configuration.
        
        Args:
            config_dict: Raw configuration dictionary
            cache: Optional cache instance for LLM services
        """
        try:
            self.config = AppConfig(**config_dict)
        except ValidationError as e:
            logger.error(f"Configuration validation failed:\n{e}")
            raise
        
        self.cache = cache
        self._init_services()
    
    def _init_services(self) -> None:
        """Initialize LLM services from configuration."""
        self.services = {}
        
        for name, cfg in self.config.llm_services.items():
            provider_class = self.PROVIDER_MAP.get(cfg.provider)
            if not provider_class:
                raise ValueError(f"Unknown provider '{cfg.provider}' for service '{name}'")
            
            self.services[name] = provider_class(cfg, cache=self.cache)
    
    def create_committee(self, pool_name: str, strategy_name: str) -> Committee:
        """
        Create a committee from configuration.
        
        Args:
            pool_name: Name of the intelligence pool in configuration
            strategy_name: Name of the voting strategy to use
            
        Returns:
            Configured Committee instance
        """
        # Get pool configuration
        pool_config = self.config.intelligence_pools.get(pool_name)
        if not pool_config:
            raise ValueError(f"Pool '{pool_name}' not found.")
        
        # Create committee members
        members = []
        for member_config in pool_config.members:
            service = self.services.get(member_config.service)
            if not service:
                raise ValueError(f"Service '{member_config.service}' not found for member '{member_config.name}'")
            
            member = CommitteeMember(
                name=member_config.name,
                role_prompt=member_config.role_prompt,
                llm_service=service,
                base_weight=member_config.base_weight,
                initial_reputation=member_config.initial_reputation
            )
            members.append(member)
        
        # Create reputation manager if enabled
        reputation_manager = None
        if pool_config.reputation_management:
            reputation_manager = ReputationManager(
                members=members,
                agreement_bonus=pool_config.agreement_bonus,
                dissent_penalty=pool_config.dissent_penalty
            )
        
        # Get voting strategy
        strategy_class = self.STRATEGY_MAP.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Strategy '{strategy_name}' not found.")
        
        return Committee(
            name=pool_config.name,
            members=members,
            voting_strategy=strategy_class(),
            reputation_manager=reputation_manager
        ) 