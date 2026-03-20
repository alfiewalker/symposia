from __future__ import annotations

import json
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class DeterministicModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def to_canonical_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
