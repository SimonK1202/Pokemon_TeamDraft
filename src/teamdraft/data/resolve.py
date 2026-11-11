"""Pure helpers that resolve PokeAPI's historical values ("as of game X"). No I/O."""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def value_as_of(current: T, past: Iterable[tuple[int, T]], when: int) -> T:
    """Value valid at point `when`.

    `past` holds (valid_until, value) pairs: the value was valid up to and including `valid_until`.
    This is how PokeAPI's *_past files work (valid_until = generation). The closest entry that is
    still valid wins; without one the current value applies.
    """
    candidates = [(until, value) for until, value in past if until >= when]
    if not candidates:
        return current
    return min(candidates, key=lambda candidate: candidate[0])[1]


def value_before_changes(current: T, changes: Iterable[tuple[int, T]], when: int) -> T:
    """Value valid at point `when`, given a changelog.

    `changes` holds (changed_at, old_value) pairs: old_value was valid *before* changed_at.
    This is how PokeAPI's move_changelog works (changed_at = version group order).
    """
    return value_as_of(current, ((changed_at - 1, old) for changed_at, old in changes), when)


def machine_label(machine_number: int) -> str:
    """PokeAPI numbers HMs from 101: 26 -> 'TM26', 103 -> 'HM03'."""
    if machine_number > 100:
        return f"HM{machine_number - 100:02d}"
    return f"TM{machine_number:02d}"
