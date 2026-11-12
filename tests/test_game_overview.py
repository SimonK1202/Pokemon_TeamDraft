from teamdraft.domain.availability import Acquisition, Availability
from teamdraft.domain.game import Game, VersionGroup
from teamdraft.domain.game_data import GameData
from teamdraft.domain.mechanics import Ruleset, Stat, TypeChart
from teamdraft.domain.move import LearnMethod, LearnsetEntry
from teamdraft.domain.species import Species
from teamdraft.reporting.game_overview import NOT_OBTAINABLE, game_summary, pokedex_rows

GEN1_STATS = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL, Stat.SPEED)
DATA = GameData(
    game=Game(1, "red", "Red", VersionGroup(1, "red-blue", 1)),
    ruleset=Ruleset(1, GEN1_STATS, TypeChart(("grass", "poison")), damage_class_by_type=True),
    species={
        1: Species(1, "bulbasaur", "Bulbasaur", ("grass", "poison"), dict(zip(GEN1_STATS, (45, 49, 49, 65, 45)))),
        151: Species(151, "mew", "Mew", ("psychic",), dict(zip(GEN1_STATS, (100,) * 5))),
    },
    moves={},
    learnsets={1: (LearnsetEntry(33, LearnMethod.LEVEL_UP, level=1),)},
    availability={1: Availability(1, frozenset({Acquisition.GIFT})), 151: Availability(151)},
)


def test_game_summary_counts():
    summary = game_summary(DATA)
    assert (summary.species, summary.obtainable, summary.learnset_entries) == (2, 1, 1)


def test_pokedex_rows_use_the_generations_stats():
    bulbasaur, mew = pokedex_rows(DATA)
    assert bulbasaur["Types"] == "Grass / Poison"
    assert bulbasaur["Spc"] == 65
    assert "SpA" not in bulbasaur
    assert bulbasaur["Obtainable"] == "gift"
    assert mew["Obtainable"] == NOT_OBTAINABLE
