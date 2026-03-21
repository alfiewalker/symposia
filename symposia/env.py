from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def default_env_paths() -> list[Path]:
    """Return default env file search order.

    Search current working directory first, then repository root.
    """
    repo_root = Path(__file__).resolve().parent.parent
    cwd = Path.cwd()
    return [
        cwd / ".env.local",
        cwd / ".env",
        repo_root / ".env.local",
        repo_root / ".env",
    ]


def load_env(path: str | None = None, *, override: bool = True) -> list[str]:
    """Explicitly load env files and return the paths that were loaded.

    Library callers must opt into this helper. The CLI may call it automatically.
    """
    loaded: list[str] = []

    if path is not None:
        env_path = Path(path)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=override)
            loaded.append(str(env_path))
        return loaded

    seen: set[Path] = set()
    for env_path in default_env_paths():
        if env_path in seen:
            continue
        seen.add(env_path)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=override)
            loaded.append(str(env_path))

    return loaded
