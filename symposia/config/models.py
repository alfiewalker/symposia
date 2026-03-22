"""
Pydantic models for configuration management.
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator


class CostConfig(BaseModel):
    """Configuration for token costs."""
    input: float
    output: float


class LLMServiceConfig(BaseModel):
    """Configuration for an LLM service provider."""
    provider: str
    model: str
    cost_per_token: Union[float, CostConfig]
    api_key: Optional[str] = None
    
    @field_validator('cost_per_token', mode='before')
    def validate_cost_per_token(cls, v):
        """Validate and normalize cost_per_token field."""
        if isinstance(v, (int, float)):
            # Convert single value to CostConfig with same value for both input/output
            return CostConfig(input=float(v), output=float(v))
        elif isinstance(v, dict):
            # Convert dict to CostConfig
            return CostConfig(**v)
        elif isinstance(v, CostConfig):
            # Already a CostConfig
            return v
        else:
            raise ValueError(f"Invalid cost_per_token format: {v}")


class MemberConfig(BaseModel):
    """Configuration for a committee member."""
    name: str
    service: str
    role_prompt: str
    base_weight: float = Field(1.0, alias='weight')
    initial_reputation: float = 1.0


class PoolConfig(BaseModel):
    """Configuration for an intelligence pool (committee)."""
    name: str
    reputation_management: bool = False
    agreement_bonus: float = 0.05
    dissent_penalty: float = 0.02
    members: List[MemberConfig]


class AppConfig(BaseModel):
    """Top-level application configuration."""
    llm_services: Dict[str, LLMServiceConfig]
    intelligence_pools: Dict[str, PoolConfig]
    decomposition_mode: str = "holistic"