"""File locations of the data layer.

Resolved relative to this file so everything works regardless of the current working directory.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = PROJECT_ROOT / "data" / "pokeapi_source.toml"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pokeapi"
DB_PATH = PROJECT_ROOT / "data" / "teamdraft.sqlite"
CORRECTIONS_PATH = PROJECT_ROOT / "data" / "corrections.toml"
