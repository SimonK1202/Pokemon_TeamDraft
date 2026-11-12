"""Species (one Pokédex entry, values as in the selected generation) and how it evolves."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from teamdraft.domain.mechanics import Stat


class EvolutionTrigger(StrEnum):
    LEVEL_UP = "level-up"  # also friendship and time of day (Gen 2+)
    USE_ITEM = "use-item"  # e.g. evolution stones
    TRADE = "trade"  # needs a second cartridge, so not available on its own (R5a)
    OTHER = "other"


@dataclass(frozen=True)
class Evolution:
    """How a species evolves from its previous stage."""

    from_species_id: int
    trigger: EvolutionTrigger
    min_level: int | None = None
    item: str | None = None
    min_happiness: int | None = None
    time_of_day: str | None = None


@dataclass(frozen=True)
class Species:
    """One Pokédex entry with types and base stats as they were in the selected generation."""

    id: int  # national Pokédex number
    identifier: str
    name: str
    types: tuple[str, ...]
    base_stats: Mapping[Stat, int]
    evolves_from: Evolution | None = None

    def __post_init__(self):
        if not 1 <= len(self.types) <= 2 or len(set(self.types)) != len(self.types):
            raise ValueError(f"{self.identifier}: needs one or two different types, got {self.types}.")
