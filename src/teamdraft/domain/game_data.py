"""Everything the drafter needs for one game, as the repository will load it."""

from collections.abc import Mapping
from dataclasses import dataclass

from teamdraft.domain.availability import Availability
from teamdraft.domain.game import Game
from teamdraft.domain.mechanics import Ruleset
from teamdraft.domain.move import LearnsetEntry, Move
from teamdraft.domain.species import Species


@dataclass(frozen=True)
class GameData:
    """All data of one game; values are already resolved to that game (no history lookups needed)."""

    game: Game
    ruleset: Ruleset
    species: Mapping[int, Species]  # whole Pokédex of the game (R5)
    moves: Mapping[int, Move]
    learnsets: Mapping[int, tuple[LearnsetEntry, ...]]  # species id -> entries
    availability: Mapping[int, Availability]  # species id -> availability

    def learnset(self, species_id: int) -> tuple[LearnsetEntry, ...]:
        return self.learnsets.get(species_id, ())

    def is_available(self, species_id: int) -> bool:
        entry = self.availability.get(species_id)
        return entry is not None and entry.is_available
