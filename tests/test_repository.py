import sqlite3

import pytest

from teamdraft.data.repository import DatabaseError, database_info, list_games, load_game_data


def test_list_games_in_display_order(game_db):
    names = [game.name for game in list_games(game_db)]
    assert names == ["Red", "Blue", "Yellow", "Gold", "Silver", "Crystal", "FireRed", "LeafGreen"]


def test_games_of_one_group_share_version_group(game_db):
    games = {game.identifier: game for game in list_games(game_db)}
    assert games["red"].version_group == games["blue"].version_group
    assert games["yellow"].version_group != games["red"].version_group
    assert games["firered"].generation == 3


def test_load_game_data_returns_one_complete_game(game_db):
    data = load_game_data("yellow", game_db)
    assert data.game.name == "Yellow"
    assert data.ruleset.generation == 1
    assert set(data.availability) == set(data.species)
    assert all(entry.move_id in data.moves for entries in data.learnsets.values() for entry in entries)


def test_unknown_game_raises(game_db):
    with pytest.raises(KeyError, match="ruby"):
        load_game_data("ruby", game_db)


def test_database_info_names_the_source(game_db):
    assert len(database_info(game_db).source_commit) == 40


def test_missing_database_raises(tmp_path):
    with pytest.raises(DatabaseError, match="importer"):
        list_games(tmp_path / "missing.sqlite")


def test_database_of_other_importer_version_raises(tmp_path):
    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        db.execute("INSERT INTO meta VALUES ('schema_version', '0')")
    with pytest.raises(DatabaseError, match="another importer version"):
        list_games(path)
