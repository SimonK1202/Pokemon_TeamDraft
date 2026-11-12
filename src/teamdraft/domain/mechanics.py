"""Generation mechanics: stats, damage classes, type chart and the ruleset that bundles them."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class Stat(StrEnum):
    HP = "hp"
    ATTACK = "attack"
    DEFENSE = "defense"
    SPECIAL_ATTACK = "special-attack"
    SPECIAL_DEFENSE = "special-defense"
    SPEED = "speed"
    SPECIAL = "special"  # Gen 1 only: one stat for special attack and defense


class DamageClass(StrEnum):
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


@dataclass(frozen=True)
class TypeChart:
    """Damage multipliers of one generation. Only non-neutral pairs are stored."""

    types: tuple[str, ...]
    # (attacking type, defending type) -> multiplier; a missing pair means x1.
    factors: Mapping[tuple[str, str], float] = field(default_factory=dict)

    def factor(self, attacking: str, defending: str) -> float:
        for type_ in (attacking, defending):
            if type_ not in self.types:
                raise KeyError(f"Type {type_!r} does not exist in this generation.")
        return self.factors.get((attacking, defending), 1.0)


@dataclass(frozen=True)
class Ruleset:
    """Mechanics of one generation. New generation = new ruleset; calculators stay unchanged."""

    generation: int
    stats: tuple[Stat, ...]
    type_chart: TypeChart
    # Gen 1-3: a damaging move is physical or special by its type, not by the move itself.
    damage_class_by_type: bool
    special_types: frozenset[str] = frozenset()

    def damage_class(self, move_type: str, move_damage_class: DamageClass) -> DamageClass:
        """Damage class a move really has in this generation."""
        if move_damage_class is DamageClass.STATUS or not self.damage_class_by_type:
            return move_damage_class
        return DamageClass.SPECIAL if move_type in self.special_types else DamageClass.PHYSICAL
