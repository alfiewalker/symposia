from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import Field

from symposia.models.base import DeterministicModel
from symposia.models.profile import ProfileSet, ProfileSetThresholds


class ProfileSetDefaultsConfig(DeterministicModel):
    domain_default: bool
    registry_group: str = Field(min_length=1)


class ProfileSetYamlConfig(DeterministicModel):
    version: str = Field(min_length=1)
    id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    profiles: list[str] = Field(min_length=1)
    juror_count: int = Field(ge=1)
    thresholds: ProfileSetThresholds
    max_rounds: int = Field(ge=1)
    issuance_policy: str = Field(min_length=1)
    defaults: ProfileSetDefaultsConfig
    trace_level: str = Field(default="standard", min_length=1)
    calibration_snapshot: str | None = None
    notes: str | None = None

    def to_profile_set(self) -> ProfileSet:
        if self.juror_count != len(self.profiles):
            raise ValueError(
                "Profile-set schema mismatch: juror_count must equal number of profiles"
            )

        return ProfileSet(
            profile_set_id=self.id,
            domain=self.domain,
            purpose=self.purpose,
            juror_count=self.juror_count,
            profiles=self.profiles,
            thresholds=self.thresholds,
            max_rounds=self.max_rounds,
            issuance_policy=self.issuance_policy,
            calibration_snapshot=self.calibration_snapshot,
            version=self.version,
            trace_level=self.trace_level,
            notes=self.notes,
        )


class ProfileSetRegistryDefaults(DeterministicModel):
    active_registry: str = Field(min_length=1)
    trace_level: str = Field(min_length=1)
    issuance_policy: str = Field(min_length=1)


class ProfileSetRegistryConfig(DeterministicModel):
    version: str = Field(min_length=1)
    defaults: ProfileSetRegistryDefaults
    domain_defaults: dict[str, str] = Field(min_length=1)


@dataclass(frozen=True)
class LoadedProfileSetRegistry:
    profile_sets: dict[str, ProfileSet]
    domain_defaults: dict[str, str]
    registry_version: str


def _profile_sets_root() -> Path:
    return Path(__file__).resolve().parent


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML document must be a mapping: {path}")
    return data


def load_profile_set_registry() -> LoadedProfileSetRegistry:
    """Load stable profile-set policy from YAML -> typed models.

    This is the canonical loader path for profile sets.
    """

    root = _profile_sets_root()
    registry_cfg = ProfileSetRegistryConfig(**_read_yaml(root / "registry" / "defaults.yaml"))

    stable_dir = root / registry_cfg.defaults.active_registry
    if not stable_dir.exists() or not stable_dir.is_dir():
        raise ValueError(f"Active profile-set registry directory not found: {stable_dir}")

    profile_sets: dict[str, ProfileSet] = {}
    for yaml_path in sorted(stable_dir.glob("*.yaml")):
        cfg = ProfileSetYamlConfig(**_read_yaml(yaml_path))
        if cfg.version != registry_cfg.version:
            raise ValueError(
                f"Registry version mismatch for {yaml_path.name}: "
                f"set={cfg.version}, registry={registry_cfg.version}"
            )
        if cfg.defaults.registry_group != registry_cfg.defaults.active_registry:
            raise ValueError(
                f"Registry group mismatch for {yaml_path.name}: "
                f"set={cfg.defaults.registry_group}, "
                f"registry={registry_cfg.defaults.active_registry}"
            )
        if cfg.id in profile_sets:
            raise ValueError(f"Duplicate profile_set id in YAML registry: {cfg.id}")

        profile_sets[cfg.id] = cfg.to_profile_set()

    missing_defaults = [
        profile_set_id
        for profile_set_id in registry_cfg.domain_defaults.values()
        if profile_set_id not in profile_sets
    ]
    if missing_defaults:
        raise ValueError(
            "Registry defaults reference unknown profile-set ids: "
            + ", ".join(sorted(missing_defaults))
        )

    return LoadedProfileSetRegistry(
        profile_sets=profile_sets,
        domain_defaults=dict(registry_cfg.domain_defaults),
        registry_version=registry_cfg.version,
    )
