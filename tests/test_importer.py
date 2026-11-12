"""Checks the imported data against reference values from the games (pret disassemblies, Bulbapedia)."""

import pytest

from teamdraft.data.importer import load_corrections
from teamdraft.data.repository import load_game_data
from teamdraft.domain.availability import Acquisition
from teamdraft.domain.mechanics import DamageClass, Stat
from teamdraft.domain.move import LearnMethod


@pytest.fixture(scope="module")
def games(game_db):
    return {name: load_game_data(name, game_db) for name in ("red", "blue", "gold", "crystal", "firered", "leafgreen")}


def species(data, identifier):
    return next(s for s in data.species.values() if s.identifier.startswith(identifier))


def move(data, identifier):
    return next(m for m in data.moves.values() if m.identifier == identifier)


def test_pokedex_size_per_generation(games):
    assert len(games["red"].species) == 151
    assert len(games["gold"].species) == 251
    assert len(games["firered"].species) == 386


def test_gen1_has_single_special_stat(games):
    mewtwo = games["red"].species[150].base_stats
    assert mewtwo == {Stat.HP: 106, Stat.ATTACK: 110, Stat.DEFENSE: 90, Stat.SPECIAL: 154, Stat.SPEED: 130}
    assert Stat.SPECIAL_ATTACK in games["gold"].species[150].base_stats


def test_types_as_in_the_generation(games):
    assert games["red"].species[81].types == ("electric",)  # Magnemite got Steel in Gen 2
    assert games["gold"].species[81].types == ("electric", "steel")
    assert games["firered"].species[35].types == ("normal",)  # Clefairy is Fairy only from Gen 6


def test_type_chart_per_generation(games):
    gen1, gen2 = games["red"].ruleset.type_chart, games["gold"].ruleset.type_chart
    assert gen1.factor("ghost", "psychic") == 0.0
    assert gen2.factor("ghost", "psychic") == 2.0
    assert gen1.factor("bug", "poison") == 2.0
    assert gen1.factor("ice", "fire") == 1.0
    assert "steel" not in gen1.types and "steel" in gen2.types
    assert "fairy" not in games["firered"].ruleset.type_chart.types


def test_gen1_to_3_damage_class_by_type(games):
    ruleset = games["firered"].ruleset
    assert ruleset.damage_class_by_type
    assert ruleset.damage_class("fire", DamageClass.PHYSICAL) is DamageClass.SPECIAL
    assert ruleset.damage_class("ghost", DamageClass.SPECIAL) is DamageClass.PHYSICAL


def test_move_values_as_in_the_version_group(games):
    assert move(games["red"], "bite").type == "normal"
    assert move(games["gold"], "bite").type == "dark"
    assert move(games["red"], "dig").power == 100  # 60 in Gen 2-3


def test_corrections_are_applied(games):
    assert move(games["red"], "rest").pp == 10
    assert move(games["firered"], "luster-purge").power == 70
    assert games["gold"].species[196].evolves_from.min_happiness == 220  # Espeon


def test_learnset_methods_levels_and_machines(games):
    red = games["red"]
    blastoise = red.learnset(9)
    skull_bash = move(red, "skull-bash").id
    methods = {(e.method, e.level, e.machine) for e in blastoise if e.move_id == skull_bash}
    assert methods == {(LearnMethod.LEVEL_UP, 42, None), (LearnMethod.MACHINE, None, "TM40")}  # R6 example
    surf = move(red, "surf").id
    assert any(e.move_id == surf and e.machine == "HM03" for e in red.learnset(7))  # Squirtle


def test_version_exclusives_and_external_help(games):
    ekans = 23
    assert games["red"].availability[ekans].methods == {Acquisition.WILD}
    assert not games["blue"].is_available(ekans)
    assert not games["red"].is_available(151)  # Mew: event only
    assert not games["red"].is_available(65)  # Alakazam: trade evolution
    assert Acquisition.EVOLUTION in games["red"].availability[64].methods  # Kadabra


def test_breeding_from_gen_2(games):
    assert games["gold"].availability[172].methods == {Acquisition.BREEDING}  # Pichu
    assert Acquisition.BREEDING in games["leafgreen"].availability[298].methods  # Azurill (Marill in LeafGreen)
    assert not games["firered"].is_available(298)


def test_mareep_is_trade_only_in_crystal(games):
    assert not games["crystal"].is_available(179)
    assert games["gold"].is_available(179)


def test_deoxys_form_per_game(games):
    assert species(games["firered"], "deoxys").identifier == "deoxys-attack"
    assert games["firered"].species[386].base_stats[Stat.ATTACK] == 180
    assert games["leafgreen"].species[386].base_stats[Stat.DEFENSE] == 160
    assert games["firered"].learnset(386)


def test_event_only_pokemon_are_not_obtainable(games):
    assert not games["crystal"].is_available(251)  # Celebi (GS Ball)
    assert not games["firered"].is_available(249)  # Lugia (Mystic Ticket)
    assert not games["leafgreen"].is_available(386)  # Deoxys (Aurora Ticket)
    assert games["gold"].is_available(249)  # Lugia is a normal fixed encounter in Gold


def test_load_corrections():
    corrections = load_corrections()
    assert corrections.moves[("rest", 1)] == {"pp": 10}
    assert ("rest", 4) not in corrections.moves
    assert corrections.min_happiness == {2: 220, 3: 220}
    assert ("crystal", "celebi") in corrections.unobtainable
