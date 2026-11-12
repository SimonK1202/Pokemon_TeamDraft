import pytest

from teamdraft.data.resolve import machine_label, value_as_of, value_before_changes

# Butterfree-like example: special attack was 80 up to Gen 5, 90 since Gen 6.
PAST = [(5, 80)]


@pytest.mark.parametrize(("when", "expected"), [(1, 80), (5, 80), (6, 90), (9, 90)])
def test_value_as_of_uses_past_value_up_to_and_including_its_generation(when, expected):
    assert value_as_of(90, PAST, when) == expected


def test_value_as_of_picks_the_closest_valid_past_entry():
    # e.g. a value changed twice: 'a' until Gen 1, 'b' until Gen 5, then 'c'.
    past = [(5, "b"), (1, "a")]
    assert value_as_of("c", past, 1) == "a"
    assert value_as_of("c", past, 2) == "b"
    assert value_as_of("c", past, 6) == "c"


def test_value_as_of_without_history_is_current():
    assert value_as_of("fire", [], 1) == "fire"


def test_value_before_changes_applies_old_value_before_the_change():
    # Bite: 'normal' before version group order 5 (Gold/Silver), 'dark' since.
    changes = [(5, "normal")]
    assert value_before_changes("dark", changes, 3) == "normal"  # Red/Blue
    assert value_before_changes("dark", changes, 4) == "normal"  # Yellow
    assert value_before_changes("dark", changes, 5) == "dark"  # Gold/Silver


@pytest.mark.parametrize(("number", "label"), [(1, "TM01"), (50, "TM50"), (101, "HM01"), (105, "HM05")])
def test_machine_label(number, label):
    assert machine_label(number) == label
