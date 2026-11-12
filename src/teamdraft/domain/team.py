"""What the user drafts: Pokémon builds and the team."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from teamdraft.domain.game import Game
from teamdraft.domain.mechanics import Stat
from teamdraft.domain.move import Move
from teamdraft.domain.species import Species

MAX_MOVES = 4
MAX_TEAM_SIZE = 6


@dataclass(frozen=True)
class PokemonBuild:
    """One team member: a species with up to 4 chosen moves (R8)."""

    species: Species
    level: int
    moves: tuple[Move, ...] = ()
    # Ignored for now (R3), but already part of the model so they can be added without refactoring.
    ivs: Mapping[Stat, int] = field(default_factory=dict)  # missing stat = 0
    evs: Mapping[Stat, int] = field(default_factory=dict)  # missing stat = 0
    ability: str | None = None
    held_item: str | None = None
    nature: str | None = None

    def __post_init__(self):
        if len(self.moves) > MAX_MOVES:
            raise ValueError(f"A Pokémon can have at most {MAX_MOVES} moves, got {len(self.moves)}.")
        if len({move.id for move in self.moves}) != len(self.moves):
            raise ValueError("A Pokémon cannot have the same move twice.")


@dataclass(frozen=True)
class Team:
    """Up to 6 builds for one game (R5)."""

    game: Game
    members: tuple[PokemonBuild, ...] = ()

    def __post_init__(self):
        if len(self.members) > MAX_TEAM_SIZE:
            raise ValueError(f"A team can have at most {MAX_TEAM_SIZE} Pokémon, got {len(self.members)}.")
