"""Overview of one game's data for display: summary numbers and the Pokédex table."""

from dataclasses import dataclass

from teamdraft.domain.game_data import GameData
from teamdraft.domain.mechanics import Stat

STAT_LABELS = {
    Stat.HP: "HP",
    Stat.ATTACK: "Atk",
    Stat.DEFENSE: "Def",
    Stat.SPECIAL_ATTACK: "SpA",
    Stat.SPECIAL_DEFENSE: "SpD",
    Stat.SPEED: "Spe",
    Stat.SPECIAL: "Spc",
}
NOT_OBTAINABLE = "–"


@dataclass(frozen=True)
class GameSummary:
    name: str
    generation: int
    version_group: str
    species: int
    obtainable: int
    moves: int
    learnset_entries: int


def game_summary(data: GameData) -> GameSummary:
    return GameSummary(
        name=data.game.name,
        generation=data.game.generation,
        version_group=data.game.version_group.identifier,
        species=len(data.species),
        obtainable=sum(data.is_available(species_id) for species_id in data.species),
        moves=len(data.moves),
        learnset_entries=sum(len(entries) for entries in data.learnsets.values()),
    )


def pokedex_rows(data: GameData) -> list[dict[str, object]]:
    """One row per species, with the stats of the game's generation (Gen 1: a single Special)."""
    rows = []
    for species in data.species.values():
        availability = data.availability.get(species.id)
        methods = sorted(method.value for method in availability.methods) if availability else []
        row = {"No.": species.id, "Name": species.name, "Types": " / ".join(t.capitalize() for t in species.types)}
        row |= {STAT_LABELS[stat]: species.base_stats.get(stat) for stat in data.ruleset.stats}
        row["Obtainable"] = ", ".join(methods) or NOT_OBTAINABLE
        rows.append(row)
    return rows
