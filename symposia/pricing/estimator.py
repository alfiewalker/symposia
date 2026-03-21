from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files

import yaml


@dataclass(frozen=True)
class ModelCostEstimate:
    estimated_cost_usd: float | None
    price_version: str
    missing_price: bool


@lru_cache(maxsize=1)
def _load_openai_price_map() -> dict:
    path = files("symposia.pricing").joinpath("openai_token_prices.v1.yaml")
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("OpenAI token price map must be a YAML mapping")
    if "version" not in data or "models" not in data:
        raise ValueError("OpenAI token price map missing required keys: version, models")
    return data


def estimate_openai_total_token_cost(model: str, tokens_used: int) -> ModelCostEstimate:
    """Estimate run cost from token usage using a versioned, explicit price map.

    Runtime truth is the observed token usage.
    Pricing assumptions are read from a versioned config file and may drift from
    eventual billing details.
    """

    price_map = _load_openai_price_map()
    version = str(price_map["version"])
    models = price_map.get("models", {})
    if model not in models:
        return ModelCostEstimate(
            estimated_cost_usd=None,
            price_version=version,
            missing_price=True,
        )

    model_cfg = models[model]
    rate = float(model_cfg["usd_per_million_total_tokens_estimate"])
    estimated = (max(tokens_used, 0) / 1_000_000.0) * rate
    return ModelCostEstimate(
        estimated_cost_usd=estimated,
        price_version=version,
        missing_price=False,
    )