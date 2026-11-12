"""Overview of the domain data model for display.

Built by introspecting the domain classes, so the overview cannot drift from the code.
"""

import dataclasses
import inspect
import re
import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from teamdraft.data.paths import RAW_DIR
from teamdraft.data.sources import SourceManifest, load_manifest
from teamdraft.domain.availability import Acquisition, Availability
from teamdraft.domain.game import Game, VersionGroup
from teamdraft.domain.game_data import GameData
from teamdraft.domain.mechanics import DamageClass, Ruleset, Stat, TypeChart
from teamdraft.domain.move import LearnMethod, LearnsetEntry, Move
from teamdraft.domain.species import Evolution, EvolutionTrigger, Species
from teamdraft.domain.team import PokemonBuild, Team

GAME_DATA_GROUP = "Game data (loaded per game)"
DRAFT_GROUP = "Draft (built by the user)"

# Display order. GameData first: it is the root the repository returns.
ENTITY_GROUPS: dict[type, str] = {
    GameData: GAME_DATA_GROUP,
    Game: GAME_DATA_GROUP,
    VersionGroup: GAME_DATA_GROUP,
    Ruleset: GAME_DATA_GROUP,
    TypeChart: GAME_DATA_GROUP,
    Species: GAME_DATA_GROUP,
    Evolution: GAME_DATA_GROUP,
    Move: GAME_DATA_GROUP,
    LearnsetEntry: GAME_DATA_GROUP,
    Availability: GAME_DATA_GROUP,
    Team: DRAFT_GROUP,
    PokemonBuild: DRAFT_GROUP,
}
VALUE_LISTS: tuple[type[Enum], ...] = (Stat, DamageClass, EvolutionTrigger, LearnMethod, Acquisition)


@dataclass(frozen=True)
class FieldView:
    name: str
    type: str


@dataclass(frozen=True)
class EntityView:
    name: str
    group: str
    summary: str
    fields: tuple[FieldView, ...]
    sources: tuple[str, ...]  # raw files this entity is imported from


@dataclass(frozen=True)
class RelationView:
    source: str
    target: str
    label: str  # field name that holds the reference


@dataclass(frozen=True)
class ValueListView:
    name: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class RawDataStatus:
    repository: str
    commit: str
    required: int
    missing: tuple[str, ...]


@dataclass(frozen=True)
class DataModelView:
    entities: tuple[EntityView, ...]
    relations: tuple[RelationView, ...]
    value_lists: tuple[ValueListView, ...]
    raw_data: RawDataStatus


def readable_type(annotation: object) -> str:
    """'collections.abc.Mapping[teamdraft.domain.mechanics.Stat, int]' -> 'Mapping[Stat, int]'."""
    text = annotation.__name__ if isinstance(annotation, type) else str(annotation)
    return re.sub(r"\b(?:\w+\.)+(\w+)", r"\1", text)


def _summary(cls: type) -> str:
    return (inspect.getdoc(cls) or "").splitlines()[0]


def _sources(cls: type, manifest: SourceManifest) -> tuple[str, ...]:
    return tuple(file.name for file in manifest.files if cls.__name__ in file.feeds)


def build_data_model_view(manifest: SourceManifest | None = None, raw_dir: Path = RAW_DIR) -> DataModelView:
    manifest = manifest or load_manifest()
    names = {cls.__name__ for cls in ENTITY_GROUPS}
    entities, relations = [], []

    for cls, group in ENTITY_GROUPS.items():
        hints = typing.get_type_hints(cls)
        fields = tuple(FieldView(f.name, readable_type(hints[f.name])) for f in dataclasses.fields(cls))
        entities.append(EntityView(cls.__name__, group, _summary(cls), fields, _sources(cls, manifest)))
        for field in fields:
            for target in sorted(names & set(re.findall(r"\w+", field.type))):
                relations.append(RelationView(cls.__name__, target, field.name))

    return DataModelView(
        entities=tuple(entities),
        relations=tuple(relations),
        value_lists=tuple(ValueListView(enum.__name__, tuple(m.name.lower().replace("_", "-") for m in enum)) for enum in VALUE_LISTS),
        raw_data=RawDataStatus(
            repository=manifest.repository,
            commit=manifest.commit,
            required=len(manifest.required_files),
            missing=tuple(file.name for file in manifest.missing_files(raw_dir)),
        ),
    )


def to_dot(view: DataModelView) -> str:
    """Graphviz DOT text of the entities and their references."""
    lines = [
        "digraph DataModel {",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=11];',
        '  edge [fontname="sans-serif", fontsize=9];',
    ]
    for entity in view.entities:
        colour = "#dbeafe" if entity.group == GAME_DATA_GROUP else "#fde68a"
        lines.append(f'  {entity.name} [fillcolor="{colour}"];')
    for relation in view.relations:
        lines.append(f'  {relation.source} -> {relation.target} [label="{relation.label}"];')
    lines.append("}")
    return "\n".join(lines)
