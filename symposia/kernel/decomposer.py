from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import List

from symposia.models import ClaimBundle, Subclaim, SubclaimKind


_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+|\n+")
_INSTRUCTION_HINTS = (
    "should",
    "must",
    "do not",
    "don't",
    "immediately",
    "avoid",
    "call",
)


class SubclaimDecomposer(ABC):
    @abstractmethod
    def decompose(self, content: str, domain: str) -> ClaimBundle:
        """Split raw content into deterministic subclaims."""


class RuleBasedSubclaimDecomposer(SubclaimDecomposer):
    def decompose(self, content: str, domain: str) -> ClaimBundle:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("content must be non-empty")
        if not domain.strip():
            raise ValueError("domain must be non-empty")

        bundle_hash = hashlib.sha256(
            f"{domain}:{normalized_content}".encode("utf-8")
        ).hexdigest()[:12]
        bundle_id = f"cb_{bundle_hash}"

        chunks = [chunk.strip(" -\t") for chunk in _SENTENCE_SPLIT_REGEX.split(normalized_content)]
        sentences: List[str] = [chunk for chunk in chunks if chunk]

        if not sentences:
            sentences = [normalized_content]

        subclaims: List[Subclaim] = []
        for idx, sentence in enumerate(sentences, start=1):
            lowered = sentence.lower()
            kind = (
                SubclaimKind.INSTRUCTION
                if any(hint in lowered for hint in _INSTRUCTION_HINTS)
                else SubclaimKind.FACT
            )
            subclaims.append(
                Subclaim(
                    subclaim_id=f"sc_{idx:03d}",
                    text=sentence,
                    kind=kind,
                    depends_on=[],
                )
            )

        dependencies = {subclaim.subclaim_id: [] for subclaim in subclaims}
        return ClaimBundle(
            bundle_id=bundle_id,
            raw_content=normalized_content,
            subclaims=subclaims,
            dependencies=dependencies,
        )
