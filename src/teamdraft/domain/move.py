"""Moves (values as in the selected version group) and how a species learns them."""

from dataclasses import dataclass
from enum import IntEnum

from teamdraft.domain.mechanics import DamageClass


@dataclass(frozen=True)
class Move:
    """A move with type, power and accuracy as they were in the selected version group."""

    id: int
    identifier: str
    name: str
    type: str
    power: int | None  # None for status moves and fixed-damage moves
    accuracy: int | None  # None if the move never misses
    pp: int
    # As the source stores it today. Use Ruleset.damage_class() for the class in a given generation.
    damage_class: DamageClass


class LearnMethod(IntEnum):
    """Values define the display order of R6."""

    LEVEL_UP = 1
    MACHINE = 2
    TUTOR = 3
    EGG = 4


@dataclass(frozen=True)
class LearnsetEntry:
    """One way a species learns one move in the selected version group."""

    move_id: int
    method: LearnMethod
    level: int | None = None  # only for LEVEL_UP
    machine: str | None = None  # only for MACHINE, e.g. "TM26" or "HM03"

    def __post_init__(self):
        if (self.level is not None) != (self.method is LearnMethod.LEVEL_UP):
            raise ValueError("A level is required for level-up moves and not allowed otherwise.")
        if self.machine is not None and self.method is not LearnMethod.MACHINE:
            raise ValueError("A machine label is only allowed for TM/HM moves.")
