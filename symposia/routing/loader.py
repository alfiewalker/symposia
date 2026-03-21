from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from symposia.models.routing import JurorRoutingConfig, JurorRoutingIndex


@dataclass(frozen=True)
class LoadedJurorRouting:
    version: str
    output_schema: str
    routes: dict[str, JurorRoutingConfig]


def _routing_root() -> Path:
    return Path(__file__).resolve().parent


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML document must be a mapping: {path}")
    return data


def load_juror_routing() -> LoadedJurorRouting:
    """Canonical loader: YAML -> strict typed routing models."""

    root = _routing_root()
    index = JurorRoutingIndex(**_read_yaml(root / "juror_routing.yaml"))

    routes: dict[str, JurorRoutingConfig] = {}
    output_schema: str | None = None

    for route_file in index.route_files:
        cfg = JurorRoutingConfig(**_read_yaml(root / route_file))
        if cfg.version != index.version:
            raise ValueError(
                f"Routing version mismatch for {route_file}: "
                f"route={cfg.version}, index={index.version}"
            )

        if output_schema is None:
            output_schema = cfg.output_schema
        elif cfg.output_schema != output_schema:
            raise ValueError(
                "All routing files must use identical output schema. "
                f"Expected {output_schema}, got {cfg.output_schema}"
            )

        if cfg.route_set_id in routes:
            raise ValueError(f"Duplicate route_set_id in routing config: {cfg.route_set_id}")

        routes[cfg.route_set_id] = cfg

    if output_schema is None:
        raise ValueError("Routing index must include at least one route file")

    return LoadedJurorRouting(
        version=index.version,
        output_schema=output_schema,
        routes=routes,
    )
