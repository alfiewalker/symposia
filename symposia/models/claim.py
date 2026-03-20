from __future__ import annotations

from enum import Enum
from typing import Dict, List

from pydantic import Field

from symposia.models.base import DeterministicModel


class SubclaimKind(str, Enum):
    FACT = "fact"
    INSTRUCTION = "instruction"
    INFERENCE = "inference"
    DEFINITION = "definition"
    NORMATIVE = "normative"


class Criticality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Subclaim(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    kind: SubclaimKind = SubclaimKind.FACT
    criticality: Criticality = Criticality.MEDIUM
    depends_on: List[str] = Field(default_factory=list)


class ClaimBundle(DeterministicModel):
    bundle_id: str = Field(min_length=1)
    raw_content: str = Field(min_length=1)
    subclaims: List[Subclaim] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
