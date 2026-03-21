from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from symposia.core.providers.base import LLMService
from symposia.models.claim import Subclaim
from symposia.models.juror import JurorDecision


def _degraded_decision(juror_id: str, profile_id: str, subclaim_id: str) -> JurorDecision:
    """Return a safe fallback decision used for provider/parser failures."""
    return JurorDecision(
        juror_id=juror_id,
        profile_id=profile_id,
        subclaim_id=subclaim_id,
        supported=False,
        contradicted=False,
        sufficient=False,
        issuable=False,
        confidence=0.0,
    )


@dataclass(frozen=True)
class JurorExecutionRecord:
    juror_id: str
    provider_model: str
    raw_response: str
    parsed_ok: bool
    error_code: str | None = None
    error_message: str | None = None
    retries_used: int | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None


class JurorPromptBuilder:
    """Builds bounded prompts for LLM jurors with fixed decision schema."""

    OUTPUT_SCHEMA = {
        "supported": "boolean",
        "contradicted": "boolean",
        "sufficient": "boolean",
        "issuable": "boolean",
        "confidence": "float_0_to_1",
    }

    def build(
        self,
        *,
        subclaim: Subclaim,
        domain: str,
        profile_id: str,
        profile_set_id: str,
    ) -> tuple[str, str]:
        role_prompt = (
            "You are a bounded juror. Return exactly one JSON object only. "
            "Do not add explanation outside JSON. "
            "The fields supported, contradicted, sufficient, and issuable must be JSON booleans only. "
            "Do not return arrays, strings, objects, evidence lists, markdown, or extra keys."
        )
        prompt = (
            f"Domain: {domain}\n"
            f"Profile: {profile_id}\n"
            f"Profile set: {profile_set_id}\n"
            f"Subclaim: {subclaim.text}\n"
            "Return JSON with exactly these keys: supported, contradicted, sufficient, issuable, confidence. "
            "supported, contradicted, sufficient, and issuable must each be either true or false. "
            "confidence must be a number between 0.0 and 1.0. "
            "If you believe a claim is unsupported or contradicted, express that using booleans only. "
            "Do not place explanations or evidence lists inside any field. "
            "Example valid output: "
            '{"supported": false, "contradicted": true, "sufficient": false, "issuable": false, "confidence": 0.2}'
        )
        return role_prompt, prompt


class JurorResponseParser:
    """Parse and validate LLM juror responses into deterministic decisions."""

    def parse(self, *, raw_response: str) -> dict[str, Any]:
        text = (raw_response or "").strip()
        if not text:
            raise ValueError("empty_response")

        lowered = text.lower()
        if "cannot assist" in lowered or "can't assist" in lowered or "refuse" in lowered:
            raise ValueError("refusal")

        payload = self._load_json_payload(text)

        for key in ("supported", "contradicted", "sufficient", "issuable", "confidence"):
            if key not in payload:
                raise ValueError(f"missing_field:{key}")

        return {
            "supported": self._as_bool(payload["supported"]),
            "contradicted": self._as_bool(payload["contradicted"]),
            "sufficient": self._as_bool(payload["sufficient"]),
            "issuable": self._as_bool(payload["issuable"]),
            "confidence": self._as_confidence(payload["confidence"]),
        }

    def _load_json_payload(self, text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        # Near-valid fallback: extract first object-like span and parse it.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("invalid_json")

        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("invalid_json") from exc

        if not isinstance(data, dict):
            raise ValueError("invalid_json_object")
        return data

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0"}:
                return False
        raise ValueError("invalid_boolean")

    @staticmethod
    def _as_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_confidence") from exc

        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("invalid_confidence")
        return confidence


class LLMJuror:
    """LLM-backed juror implementation with safe degradation semantics."""

    def __init__(
        self,
        *,
        juror_id: str,
        profile_id: str,
        llm_service: LLMService,
        prompt_builder: JurorPromptBuilder | None = None,
        response_parser: JurorResponseParser | None = None,
    ):
        self.juror_id = juror_id
        self.profile_id = profile_id
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder or JurorPromptBuilder()
        self.response_parser = response_parser or JurorResponseParser()

    def decide(
        self,
        subclaim: Subclaim,
        *,
        domain: str,
        profile_set_id: str,
        timeout_seconds: float = 15.0,
        retries: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> tuple[JurorDecision, JurorExecutionRecord]:
        return asyncio.run(
            self.decide_async(
                subclaim,
                domain=domain,
                profile_set_id=profile_set_id,
                timeout_seconds=timeout_seconds,
                retries=retries,
                retry_delay_seconds=retry_delay_seconds,
            )
        )

    async def decide_async(
        self,
        subclaim: Subclaim,
        *,
        domain: str,
        profile_set_id: str,
        timeout_seconds: float = 15.0,
        retries: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> tuple[JurorDecision, JurorExecutionRecord]:
        role_prompt, prompt = self.prompt_builder.build(
            subclaim=subclaim,
            domain=domain,
            profile_id=self.profile_id,
            profile_set_id=profile_set_id,
        )

        provider_model = self.llm_service.config.model
        try:
            result = await asyncio.wait_for(
                self.llm_service.query(
                    prompt=prompt,
                    role_prompt=role_prompt,
                    retries=retries,
                    delay=retry_delay_seconds,
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            return (
                _degraded_decision(self.juror_id, self.profile_id, subclaim.subclaim_id),
                JurorExecutionRecord(
                    juror_id=self.juror_id,
                    provider_model=provider_model,
                    raw_response="",
                    parsed_ok=False,
                    error_code="timeout",
                    error_message=(
                        "llm_juror_timeout: query exceeded timeout_seconds="
                        f"{timeout_seconds}"
                    ),
                    retries_used=retries,
                ),
            )

        raw_response = (result.get("response") or "").strip()

        if result.get("error"):
            return (
                _degraded_decision(self.juror_id, self.profile_id, subclaim.subclaim_id),
                JurorExecutionRecord(
                    juror_id=self.juror_id,
                    provider_model=provider_model,
                    raw_response=raw_response,
                    parsed_ok=False,
                    error_code="provider_error",
                    error_message=str(result.get("error")),
                    retries_used=retries,
                    tokens_used=_safe_int(result.get("tokens_used")),
                    cost_usd=_safe_float(result.get("cost")),
                ),
            )

        try:
            parsed = self.response_parser.parse(raw_response=raw_response)
            decision = JurorDecision(
                juror_id=self.juror_id,
                profile_id=self.profile_id,
                subclaim_id=subclaim.subclaim_id,
                supported=parsed["supported"],
                contradicted=parsed["contradicted"],
                sufficient=parsed["sufficient"],
                issuable=parsed["issuable"],
                confidence=parsed["confidence"],
            )
            return (
                decision,
                JurorExecutionRecord(
                    juror_id=self.juror_id,
                    provider_model=provider_model,
                    raw_response=raw_response,
                    parsed_ok=True,
                    retries_used=retries,
                    tokens_used=_safe_int(result.get("tokens_used")),
                    cost_usd=_safe_float(result.get("cost")),
                ),
            )
        except ValueError as exc:
            return (
                _degraded_decision(self.juror_id, self.profile_id, subclaim.subclaim_id),
                JurorExecutionRecord(
                    juror_id=self.juror_id,
                    provider_model=provider_model,
                    raw_response=raw_response,
                    parsed_ok=False,
                    error_code="parse_error",
                    error_message=str(exc),
                    retries_used=retries,
                    tokens_used=_safe_int(result.get("tokens_used")),
                    cost_usd=_safe_float(result.get("cost")),
                ),
            )


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
