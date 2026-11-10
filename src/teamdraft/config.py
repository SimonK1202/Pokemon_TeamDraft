"""Loads user settings from config.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Resolved relative to this file so the app works regardless of the current working directory.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"

MIN_LEVEL = 1
MAX_LEVEL = 100


@dataclass(frozen=True)
class Settings:
    level: int = 50


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Read settings from a TOML file. A missing file or key falls back to the defaults."""
    if not path.exists():
        return Settings()

    with path.open("rb") as file:
        raw = tomllib.load(file)

    level = raw.get("team", {}).get("level", Settings.level)
    # bool is a subclass of int, so exclude it explicitly ("level = true" is a config error).
    if not isinstance(level, int) or isinstance(level, bool) or not MIN_LEVEL <= level <= MAX_LEVEL:
        raise ValueError(f"{path}: team.level must be an integer between {MIN_LEVEL} and {MAX_LEVEL}, got {level!r}.")

    return Settings(level=level)
