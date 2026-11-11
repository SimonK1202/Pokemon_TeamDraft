import pytest

from teamdraft.domain.availability import Acquisition, Availability
from teamdraft.domain.game import Game, VersionGroup
from teamdraft.domain.game_data import GameData
from teamdraft.domain.mechanics import DamageClass, Ruleset, Stat, TypeChart
from teamdraft.domain.move import LearnMethod, LearnsetEntry, Move
from teamdraft.domain.species import Species
from teamdraft.domain.team import PokemonBuild, Team

RED = Game(1, "red", "Red", VersionGroup(1, "red-blue", generation=1))
# Gen 1 quirk as test data: Ghost does nothing against Psychic.
GEN1_CHART = TypeChart(types=("normal", "ghost", "psychic", "fire"), factors={("ghost", "psychic"): 0.0})
GEN1 = Ruleset(
    generation=1,
    stats=(Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL, Stat.SPEED),
    type_chart=GEN1_CHART,
    damage_class_by_type=True,
    special_types=frozenset({"fire", "psychic"}),
)


def species(id_=1, types=("normal",)):
    return Species(id_, f"species-{id_}", f"Species {id_}", types, base_stats={Stat.HP: 50})


def move(id_, type_="normal", damage_class=DamageClass.PHYSICAL):
    return Move(id_, f"move-{id_}", f"Move {id_}", type_, power=40, accuracy=100, pp=35, damage_class=damage_class)


def test_game_knows_its_generation():
    assert RED.generation == 1


def test_type_chart_returns_stored_factor_and_neutral_default():
    assert GEN1_CHART.factor("ghost", "psychic") == 0.0
    assert GEN1_CHART.factor("fire", "normal") == 1.0


def test_type_chart_rejects_types_of_other_generations():
    with pytest.raises(KeyError, match="steel"):
        GEN1_CHART.factor("steel", "normal")


@pytest.mark.parametrize(
    ("move_type", "stored", "expected"),
    [
        ("fire", DamageClass.PHYSICAL, DamageClass.SPECIAL),  # Gen 1-3: the type decides
        ("normal", DamageClass.SPECIAL, DamageClass.PHYSICAL),
        ("fire", DamageClass.STATUS, DamageClass.STATUS),  # status moves stay status
    ],
)
def test_ruleset_damage_class_by_type(move_type, stored, expected):
    assert GEN1.damage_class(move_type, stored) is expected


def test_ruleset_damage_class_by_move_from_gen_4():
    gen4 = Ruleset(4, GEN1.stats, GEN1_CHART, damage_class_by_type=False, special_types=GEN1.special_types)
    assert gen4.damage_class("fire", DamageClass.PHYSICAL) is DamageClass.PHYSICAL


@pytest.mark.parametrize("types", [(), ("fire", "water", "grass"), ("fire", "fire")])
def test_species_needs_one_or_two_different_types(types):
    with pytest.raises(ValueError, match="types"):
        species(types=types)


def test_learn_methods_sort_in_display_order():
    assert sorted(reversed(LearnMethod)) == [LearnMethod.LEVEL_UP, LearnMethod.MACHINE, LearnMethod.TUTOR, LearnMethod.EGG]


def test_level_up_entry_needs_a_level():
    with pytest.raises(ValueError, match="level"):
        LearnsetEntry(1, LearnMethod.LEVEL_UP)
    with pytest.raises(ValueError, match="level"):
        LearnsetEntry(1, LearnMethod.EGG, level=5)


def test_machine_label_only_for_machines():
    assert LearnsetEntry(1, LearnMethod.MACHINE, machine="TM01").machine == "TM01"
    with pytest.raises(ValueError, match="machine"):
        LearnsetEntry(1, LearnMethod.TUTOR, machine="TM01")


def test_availability_is_empty_when_not_obtainable():
    assert not Availability(151).is_available
    assert Availability(1, frozenset({Acquisition.GIFT})).is_available


def test_game_data_lookups():
    data = GameData(
        game=RED,
        ruleset=GEN1,
        species={1: species(1), 2: species(2)},
        moves={1: move(1)},
        learnsets={1: (LearnsetEntry(1, LearnMethod.LEVEL_UP, level=1),)},
        availability={1: Availability(1, frozenset({Acquisition.WILD}))},
    )
    assert len(data.learnset(1)) == 1
    assert data.learnset(2) == ()
    assert data.is_available(1)
    assert not data.is_available(2)


def test_build_allows_at_most_four_different_moves():
    PokemonBuild(species(), level=50, moves=tuple(move(i) for i in range(4)))
    with pytest.raises(ValueError, match="at most 4"):
        PokemonBuild(species(), level=50, moves=tuple(move(i) for i in range(5)))
    with pytest.raises(ValueError, match="same move"):
        PokemonBuild(species(), level=50, moves=(move(1), move(1)))


def test_build_has_slots_for_later_simplifications():
    build = PokemonBuild(species(), level=50)
    assert build.ivs == {} and build.evs == {}
    assert build.ability is build.held_item is build.nature is None


def test_team_allows_at_most_six_members():
    Team(RED, tuple(PokemonBuild(species(i), level=50) for i in range(6)))
    with pytest.raises(ValueError, match="at most 6"):
        Team(RED, tuple(PokemonBuild(species(i), level=50) for i in range(7)))
