"""Whether a species can be obtained in one game without external help (R5a)."""

from dataclasses import dataclass
from enum import StrEnum


class Acquisition(StrEnum):
    WILD = "wild"
    STATIC = "static"  # fixed encounter, e.g. Snorlax
    GIFT = "gift"
    NPC_TRADE = "npc-trade"
    EVOLUTION = "evolution"  # level-up, item or friendship; never trade evolutions
    BREEDING = "breeding"  # Gen 2+


@dataclass(frozen=True)
class Availability:
    """All ways to obtain one species in one game. Empty methods means not obtainable."""

    species_id: int
    methods: frozenset[Acquisition] = frozenset()

    @property
    def is_available(self) -> bool:
        return bool(self.methods)
