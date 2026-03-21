from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from symposia.providers import ProviderRegistry
from symposia.round0 import InitialReviewEngine
from symposia.routing import (
    build_routed_llm_service_factory,
    get_route_set,
    routed_llm_timeout_seconds,
)
from symposia.tracing import (
    export_adjudication_trace_json,
    export_adjudication_trace_markdown,
)


@dataclass(frozen=True)
class OpenAIRound0SmokeCase:
    case_id: str
    domain: str
    content: str
    expected_direction: str


def default_openai_round0_smoke_cases() -> list[OpenAIRound0SmokeCase]:
    return [
        OpenAIRound0SmokeCase(
            case_id="general_supported_baseline",
            domain="general",
            content=(
                "Under standard atmospheric pressure, pure water freezes at 0 degrees Celsius."
            ),
            expected_direction="likely_round0_decisive",
        ),
        OpenAIRound0SmokeCase(
            case_id="general_unsafe_overclaim",
            domain="general",
            content=(
                "This supplement is guaranteed safe for everyone, has no side effects, "
                "and always works immediately."
            ),
            expected_direction="likely_escalation_candidate",
        ),
    ]


def build_openai_round0_engine(
    *,
    provider_registry: ProviderRegistry | None = None,
    route_set_id: str = "default_round0_openai",
) -> tuple[InitialReviewEngine, object]:
    route_set = get_route_set(route_set_id)
    juror_profiles = [assignment.profile_id for assignment in route_set.assignments]
    factory = build_routed_llm_service_factory(
        route_set,
        provider_registry=provider_registry,
    )

    engine = InitialReviewEngine(
        juror_mode="llm",
        llm_service_factory=factory,
        juror_profiles=juror_profiles,
        route_set_id=route_set.route_set_id,
        llm_timeout_seconds=routed_llm_timeout_seconds(route_set),
        llm_retries=1,
        llm_retry_delay_seconds=0.0,
        max_juror_dropouts_per_subclaim=1,
    )
    return engine, route_set


def run_openai_round0_live_smoke(
    *,
    output_dir: str,
    provider_registry: ProviderRegistry | None = None,
    route_set_id: str = "default_round0_openai",
    cases: list[OpenAIRound0SmokeCase] | None = None,
) -> list[dict[str, object]]:
    engine, route_set = build_openai_round0_engine(
        provider_registry=provider_registry,
        route_set_id=route_set_id,
    )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, object]] = []
    for case in cases or default_openai_round0_smoke_cases():
        result = engine.run(content=case.content, domain=case.domain)
        json_path = output_root / f"{case.case_id}.trace.json"
        markdown_path = output_root / f"{case.case_id}.trace.md"
        export_adjudication_trace_json(result.adjudication_trace, str(json_path))
        export_adjudication_trace_markdown(result.adjudication_trace, str(markdown_path))
        summaries.append(
            {
                "case": asdict(case),
                "route_set_id": route_set.route_set_id,
                "run_id": result.run_id,
                "should_stop": result.completion.should_stop,
                "completion_reason": result.completion.reason,
                "dropouts": result.runtime_stats.get("total_dropouts", 0),
                "trace_json": str(json_path),
                "trace_markdown": str(markdown_path),
            }
        )

    summary_path = output_root / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summaries