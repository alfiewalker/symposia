from __future__ import annotations

import pytest

pytestmark = pytest.mark.core

from pathlib import Path

from symposia.env import load_env


def test_load_env_explicit_path_loads_requested_file(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    loaded = load_env(str(env_path), override=True)

    assert loaded == [str(env_path)]


def test_load_env_default_search_prefers_cwd(tmp_path, monkeypatch) -> None:
    cwd_env = tmp_path / ".env"
    cwd_env.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    loaded = load_env()

    assert str(cwd_env) in loaded
