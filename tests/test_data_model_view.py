from collections.abc import Mapping

from teamdraft.domain.mechanics import Stat
from teamdraft.reporting.data_model import build_data_model_view, readable_type, to_dot

VIEW = build_data_model_view()
ENTITIES = {entity.name: entity for entity in VIEW.entities}


def test_readable_type_drops_module_paths():
    assert readable_type(Mapping[Stat, int]) == "Mapping[Stat, int]"
    assert readable_type(int | None) == "int | None"
    assert readable_type(int) == "int"


def test_entities_show_fields_from_the_code():
    fields = {f.name: f.type for f in ENTITIES["Species"].fields}
    assert fields["types"] == "tuple[str, ...]"
    assert fields["evolves_from"] == "Evolution | None"


def test_relations_follow_typed_references():
    relations = {(r.source, r.target, r.label) for r in VIEW.relations}
    assert ("GameData", "Species", "species") in relations
    assert ("Game", "VersionGroup", "version_group") in relations
    assert ("PokemonBuild", "Move", "moves") in relations


def test_entities_list_their_raw_files():
    assert "pokemon_stats_past.csv" in ENTITIES["Species"].sources
    assert ENTITIES["Team"].sources == ()  # built by the user, not imported


def test_value_lists_use_identifier_style():
    learn_methods = next(v for v in VIEW.value_lists if v.name == "LearnMethod")
    assert learn_methods.values == ("level-up", "machine", "tutor", "egg")


def test_dot_contains_every_entity_and_relation():
    dot = to_dot(VIEW)
    assert dot.startswith("digraph")
    assert all(name in dot for name in ENTITIES)
    assert dot.count("->") == len(VIEW.relations)
