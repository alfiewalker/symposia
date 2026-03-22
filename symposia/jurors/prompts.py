from __future__ import annotations

from textwrap import dedent

from symposia.models.claim import Subclaim
from symposia.profile_sets import get_profile_set
from symposia.profiles import get_profile


# ---------------------------------------------------------------------------
# Shared adjudication contract
# ---------------------------------------------------------------------------

COMMON_SYSTEM_PROMPT = dedent(
    """
    You are a juror in a structured adjudication system.

    Your job is to judge whether the review unit is trustworthy enough to rely on
    under the current review task.

    Judge the review unit itself, not what you imagine the user hopes is true.

    Core rules:
    1. Prefer careful judgment over bold certainty.
    2. Distinguish what is directly supported, what is contradicted, and what is
       still insufficiently supported.
    3. Do not force a review unit into supported or contradicted if the better
       answer is uncertainty or insufficiency.
    4. Preserve caveats, scope limits, and dependency relationships. Do not
       flatten a contextual statement into a simplistic verdict.
    5. For advice or action-guiding content, consider whether it would be safe
       to rely on as stated.
    6. Do not reward rhetoric, confidence, or polished wording. Judge the
       actual content.
    7. Be explicit through your booleans about when support is missing.
    8. Use the required output schema only.
    """
).strip()


# ---------------------------------------------------------------------------
# Output schema contract
# ---------------------------------------------------------------------------

OUTPUT_CONTRACT_PROMPT = dedent(
    """
    Return exactly one JSON object with exactly these keys:
    - supported: boolean
    - contradicted: boolean
    - sufficient: boolean
    - issuable: boolean
    - confidence: number from 0.0 to 1.0

    Interpretation rules:
    - supported = true only when the review unit is meaningfully sustained
    - contradicted = true only when the review unit is meaningfully undermined
    - sufficient = true only when the evidence or reasoning is strong enough to rely on
    - issuable = true only when presenting the review unit as stated would be acceptable

    Output rules:
    - Return JSON only.
    - Do not add markdown, prose, evidence lists, arrays, or extra keys.
    - supported, contradicted, sufficient, and issuable must be JSON booleans.
    - confidence must be a JSON number between 0.0 and 1.0.
    """
).strip()


def _domain_block(profile_set_id: str) -> str:
    profile_set = get_profile_set(profile_set_id)
    return profile_set.domain_guidance.strip()


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

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
        profile = get_profile(profile_id)
        behavior = profile.behavior
        domain_block = _domain_block(profile_set_id)
        role_sections = [COMMON_SYSTEM_PROMPT]
        if domain_block:
            role_sections.append(domain_block)
        role_sections.extend(
            [
                f"Profile: {profile.label}. {profile.purpose}",
                (
                    "Behavior settings: "
                    f"stance={behavior.stance}; "
                    f"literalism={behavior.literalism}; "
                    f"evidence_demand={behavior.evidence_demand}; "
                    f"safety_bias={behavior.safety_bias}."
                ),
                OUTPUT_CONTRACT_PROMPT,
            ]
        )
        role_prompt = "\n\n".join(
            role_sections
        )
        prompt = dedent(
            f"""
            Assess the review unit below.

            Domain: {domain}
            Profile ID: {profile_id}
            Profile set: {profile_set_id}
            Review unit ID: {subclaim.subclaim_id}
            Review unit kind: {subclaim.kind}

            Review unit text:
            {subclaim.text}

            Return JSON only using the required schema.

            Example valid output:
            {{"supported": false, "contradicted": true, "sufficient": false, "issuable": false, "confidence": 0.2}}
            """
        ).strip()
        return role_prompt, prompt
