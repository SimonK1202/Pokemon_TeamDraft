from teamdraft.domain.game import Game, VersionGroup
from teamdraft.domain.mechanics import Ruleset, Stat, TypeChart
from teamdraft.reporting.team_draft import build_draft_view, is_draft_supported

GEN1_STATS = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL, Stat.SPEED)
GEN2_STATS = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL_ATTACK, Stat.SPECIAL_DEFENSE, Stat.SPEED)
YELLOW = Game(3, "yellow", "Yellow", VersionGroup(2, "yellow", 1))
CRYSTAL = Game(6, "crystal", "Crystal", VersionGroup(4, "crystal", 2))
GEN1_RULES = Ruleset(1, GEN1_STATS, TypeChart(("normal",)), damage_class_by_type=True)
GEN2_RULES = Ruleset(2, GEN2_STATS, TypeChart(("normal",)), damage_class_by_type=True)


def test_draft_is_supported_for_gen_1_only():
    assert is_draft_supported(YELLOW)
    assert not is_draft_supported(CRYSTAL)


def test_view_has_6_team_and_2_option_slots():
    view = build_draft_view(YELLOW, GEN1_RULES, level=50)
    assert [slot.label for slot in view.team_slots] == [f"Team {n}" for n in range(1, 7)]
    assert [slot.label for slot in view.option_slots] == ["Option 1", "Option 2"]


def test_each_pokemon_has_4_moves_and_2_option_moves():
    view = build_draft_view(YELLOW, GEN1_RULES, level=50)
    assert sum(not move.is_option for move in view.moves) == 4
    assert sum(move.is_option for move in view.moves) == 2


def test_stats_follow_the_generation():
    assert build_draft_view(YELLOW, GEN1_RULES, 50).stat_labels == ("HP", "Atk", "Def", "Spc", "Spe")
    assert "SpA" in build_draft_view(CRYSTAL, GEN2_RULES, 50).stat_labels


def test_details_not_in_gen_1_are_marked():
    gen1 = {d.label: d.available for d in build_draft_view(YELLOW, GEN1_RULES, 50).details}
    gen2 = {d.label: d.available for d in build_draft_view(CRYSTAL, GEN2_RULES, 50).details}
    assert gen1 == {"Nature": False, "Ability": False, "Held item": False}
    assert gen2 == {"Nature": False, "Ability": False, "Held item": True}


def test_level_and_iv_are_passed_through():
    view = build_draft_view(YELLOW, GEN1_RULES, level=42)
    assert (view.level, view.iv) == (42, 0)


def test_coverage_areas():
    view = build_draft_view(YELLOW, GEN1_RULES, 50)
    assert [a.label for a in view.offensive] == ["Per move", "Per Pokémon", "Team"]
    assert [a.label for a in view.defensive] == ["Per Pokémon", "Team"]
