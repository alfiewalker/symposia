from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import List, Optional

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
        """Build a deterministic claim bundle for adjudication."""


def _build_bundle_id(content: str, domain: str) -> tuple[str, str]:
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("content must be non-empty")
    if not domain.strip():
        raise ValueError("domain must be non-empty")

    bundle_hash = hashlib.sha256(
        f"{domain}:{normalized_content}".encode("utf-8")
    ).hexdigest()[:12]
    return normalized_content, f"cb_{bundle_hash}"


class HolisticSubclaimDecomposer(SubclaimDecomposer):
    def decompose(self, content: str, domain: str) -> ClaimBundle:
        normalized_content, bundle_id = _build_bundle_id(content, domain)
        lowered = normalized_content.lower()
        kind = (
            SubclaimKind.INSTRUCTION
            if any(hint in lowered for hint in _INSTRUCTION_HINTS)
            else SubclaimKind.FACT
        )
        subclaim = Subclaim(
            subclaim_id="sc_001",
            text=normalized_content,
            kind=kind,
            depends_on=[],
        )
        return ClaimBundle(
            bundle_id=bundle_id,
            raw_content=normalized_content,
            subclaims=[subclaim],
            dependencies={subclaim.subclaim_id: []},
        )


# ── Decomposer resolution ────────────────────────────────────────────

DECOMPOSITION_MODES: dict[str, type[SubclaimDecomposer]] = {}
"""Populated after class definitions below."""


def resolve_decomposer(mode: str = "holistic") -> SubclaimDecomposer:
    """Return a decomposer instance for the given mode string.

    Allowed modes: ``"holistic"`` (default), ``"rule_based"``.
    """
    cls = DECOMPOSITION_MODES.get(mode)
    if cls is None:
        raise ValueError(
            f"Unknown decomposition mode {mode!r}. "
            f"Allowed: {sorted(DECOMPOSITION_MODES)}"
        )
    return cls()


def resolve_decomposition_mode(
    *,
    cli: Optional[str] = None,
    param: Optional[str] = None,
    config_default: Optional[str] = None,
) -> str:
    """Resolve decomposition mode with strict precedence: CLI > param > config > holistic."""
    for candidate in (cli, param, config_default):
        if candidate is not None:
            if candidate not in DECOMPOSITION_MODES:
                raise ValueError(
                    f"Unknown decomposition mode {candidate!r}. "
                    f"Allowed: {sorted(DECOMPOSITION_MODES)}"
                )
            return candidate
    return "holistic"


class RuleBasedSubclaimDecomposer(SubclaimDecomposer):
    def decompose(self, content: str, domain: str) -> ClaimBundle:
        normalized_content, bundle_id = _build_bundle_id(content, domain)

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


# Populate mode registry now that both classes are defined.
DECOMPOSITION_MODES.update({
    "holistic": HolisticSubclaimDecomposer,
    "rule_based": RuleBasedSubclaimDecomposer,
})
