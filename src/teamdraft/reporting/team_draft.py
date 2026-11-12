"""View model for the team draft screen: which slots, stats, details, moves and coverage areas to show.

Only the layout skeleton for now (placeholders). Selection and calculators fill it later.
"""

from dataclasses import dataclass

from teamdraft.domain.game import Game
from teamdraft.domain.mechanics import Ruleset
from teamdraft.domain.team import MAX_MOVES, MAX_TEAM_SIZE
from teamdraft.reporting.game_overview import STAT_LABELS

# Gen 1 first; a generation is added here once its draft screen is checked.
DRAFT_GENERATIONS = frozenset({1})
OPTION_SLOTS = 2  # R5: bench Pokémon, not part of team coverage
OPTION_MOVES = 2  # per Pokémon, not part of coverage (R8 says 1; widened on request)
DEFAULT_IV = 0  # R3: IVs are ignored for now

# Generation in which each build detail first exists in the games.
DETAIL_INTRODUCED = {"Nature": 3, "Ability": 3, "Held item": 2}


@dataclass(frozen=True)
class DetailSlot:
    label: str
    available: bool  # False: the mechanic does not exist in this generation


@dataclass(frozen=True)
class PokemonSlot:
    label: str
    is_option: bool


@dataclass(frozen=True)
class MoveSlot:
    label: str
    is_option: bool


@dataclass(frozen=True)
class CoverageArea:
    label: str
    description: str


@dataclass(frozen=True)
class DraftView:
    game_name: str
    generation: int
    level: int
    iv: int
    stat_labels: tuple[str, ...]
    details: tuple[DetailSlot, ...]
    slots: tuple[PokemonSlot, ...]
    moves: tuple[MoveSlot, ...]
    offensive: tuple[CoverageArea, ...]
    defensive: tuple[CoverageArea, ...]

    @property
    def team_slots(self) -> tuple[PokemonSlot, ...]:
        return tuple(slot for slot in self.slots if not slot.is_option)

    @property
    def option_slots(self) -> tuple[PokemonSlot, ...]:
        return tuple(slot for slot in self.slots if slot.is_option)


def is_draft_supported(game: Game) -> bool:
    return game.generation in DRAFT_GENERATIONS


def build_draft_view(game: Game, ruleset: Ruleset, level: int) -> DraftView:
    return DraftView(
        game_name=game.name,
        generation=game.generation,
        level=level,
        iv=DEFAULT_IV,
        stat_labels=tuple(STAT_LABELS[stat] for stat in ruleset.stats),
        details=tuple(
            DetailSlot(label, game.generation >= introduced) for label, introduced in DETAIL_INTRODUCED.items()
        ),
        slots=tuple(PokemonSlot(f"Team {n}", False) for n in range(1, MAX_TEAM_SIZE + 1))
        + tuple(PokemonSlot(f"Option {n}", True) for n in range(1, OPTION_SLOTS + 1)),
        moves=tuple(MoveSlot(f"Move {n}", False) for n in range(1, MAX_MOVES + 1))
        + tuple(MoveSlot(f"Option move {n}", True) for n in range(1, OPTION_MOVES + 1)),
        offensive=(
            CoverageArea("Per move", "Types each single move hits super effectively."),
            CoverageArea("Per Pokémon", "Combined coverage of the 4 moves of one Pokémon."),
            CoverageArea("Team", "Combined coverage of all team moves. Option slots and option moves excluded."),
        ),
        defensive=(
            CoverageArea("Per Pokémon", "Weaknesses and resistances from the Pokémon's types."),
            CoverageArea("Team", "Weaknesses and resistances summed over the team. Option slots excluded."),
        ),
    )
