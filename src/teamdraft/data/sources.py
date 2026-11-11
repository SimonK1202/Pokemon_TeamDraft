"""Which raw source files exist and are needed. The manifest is data/pokeapi_source.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Resolved relative to this file so it works regardless of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = PROJECT_ROOT / "data" / "pokeapi_source.toml"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "pokeapi"


@dataclass(frozen=True)
class SourceFile:
    name: str
    purpose: str
    feeds: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class SourceManifest:
    repository: str
    commit: str
    files: tuple[SourceFile, ...]

    @property
    def required_files(self) -> tuple[SourceFile, ...]:
        return tuple(file for file in self.files if file.required)

    def missing_files(self, raw_dir: Path = RAW_DIR) -> tuple[SourceFile, ...]:
        """Required files that are not in raw_dir."""
        return tuple(file for file in self.required_files if not (raw_dir / file.name).is_file())


def load_manifest(path: Path = MANIFEST_PATH) -> SourceManifest:
    with path.open("rb") as file:
        raw = tomllib.load(file)
    files = tuple(
        SourceFile(
            name=entry["name"],
            purpose=entry["purpose"],
            feeds=tuple(entry["feeds"]),
            required=entry.get("required", True),
        )
        for entry in raw["files"]
    )
    return SourceManifest(repository=raw["source"]["repository"], commit=raw["source"]["commit"], files=files)
