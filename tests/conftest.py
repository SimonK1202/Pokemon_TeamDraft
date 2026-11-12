import pytest

from teamdraft.data.importer import build_database
from teamdraft.data.paths import RAW_DIR
from teamdraft.data.sources import load_manifest


@pytest.fixture(scope="session")
def game_db(tmp_path_factory):
    """SQLite file built from the real raw files, once per test run (about 4 s)."""
    if load_manifest().missing_files(RAW_DIR):
        pytest.skip("Raw PokeAPI files missing in data/raw/pokeapi/ (see README).")
    db_path = tmp_path_factory.mktemp("db") / "teamdraft.sqlite"
    build_database(db_path=db_path)
    return db_path
