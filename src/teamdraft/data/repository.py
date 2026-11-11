"""Loads game data from the SQLite file built by the importer. The only place that reads it."""

import sqlite3
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from teamdraft.data.importer import SCHEMA_VERSION
from teamdraft.data.paths import DB_PATH
from teamdraft.domain.availability import Acquisition, Availability
from teamdraft.domain.game import Game, VersionGroup
from teamdraft.domain.game_data import GameData
from teamdraft.domain.mechanics import DamageClass, Ruleset, Stat, TypeChart
from teamdraft.domain.move import LearnMethod, LearnsetEntry, Move
from teamdraft.domain.species import Evolution, EvolutionTrigger, Species


class DatabaseError(Exception):
    """The SQLite file is missing or was built by another importer version: run the importer."""


@dataclass(frozen=True)
class DatabaseInfo:
    source_commit: str
    imported_at: str


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise DatabaseError(f"No game data at {db_path}. Run the importer first.")
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # read-only: the app never writes
    version = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    if version is None or int(version[0]) != SCHEMA_VERSION:
        connection.close()
        raise DatabaseError(f"{db_path} was built by another importer version. Run the importer again.")
    return connection


def database_info(db_path: Path = DB_PATH) -> DatabaseInfo:
    with closing(_connect(db_path)) as db:
        meta = dict(db.execute("SELECT key, value FROM meta"))
    return DatabaseInfo(source_commit=meta["source_commit"], imported_at=meta["imported_at"])


def list_games(db_path: Path = DB_PATH) -> tuple[Game, ...]:
    with closing(_connect(db_path)) as db:
        rows = db.execute(
            "SELECT id, identifier, name, version_group_id, version_group, generation FROM game ORDER BY sort_order"
        ).fetchall()
    return tuple(_game(row) for row in rows)


def load_game_data(game_identifier: str, db_path: Path = DB_PATH) -> GameData:
    with closing(_connect(db_path)) as db:
        row = db.execute(
            "SELECT id, identifier, name, version_group_id, version_group, generation FROM game WHERE identifier = ?",
            (game_identifier,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown game {game_identifier!r}.")
        game = _game(row)
        return GameData(
            game=game,
            ruleset=_ruleset(db, game.generation),
            species=_species(db, game.id),
            moves=_moves(db, game.id),
            learnsets=_learnsets(db, game.id),
            availability=_availability(db, game.id),
        )


def _game(row) -> Game:
    game_id, identifier, name, group_id, group_identifier, generation = row
    return Game(game_id, identifier, name, VersionGroup(group_id, group_identifier, generation))


def _ruleset(db: sqlite3.Connection, generation: int) -> Ruleset:
    stats, by_type = db.execute(
        "SELECT stats, damage_class_by_type FROM ruleset WHERE generation = ?", (generation,)
    ).fetchone()
    types = db.execute("SELECT identifier, is_special FROM type WHERE generation = ? ORDER BY rowid", (generation,))
    types = types.fetchall()
    factors = {
        (attacking, defending): factor
        for attacking, defending, factor in db.execute(
            "SELECT attacking, defending, factor FROM type_factor WHERE generation = ?", (generation,)
        )
    }
    return Ruleset(
        generation=generation,
        stats=tuple(Stat(stat) for stat in stats.split(",")),
        type_chart=TypeChart(types=tuple(name for name, _ in types), factors=factors),
        damage_class_by_type=bool(by_type),
        special_types=frozenset(name for name, is_special in types if is_special),
    )


def _species(db: sqlite3.Connection, game_id: int) -> dict[int, Species]:
    stats = defaultdict(dict)
    for species_id, stat, value in db.execute(
        "SELECT species_id, stat, value FROM base_stat WHERE game_id = ?", (game_id,)
    ):
        stats[species_id][Stat(stat)] = value
    evolutions = {
        row[0]: Evolution(
            from_species_id=row[1],
            trigger=EvolutionTrigger(row[2]),
            min_level=row[3],
            item=row[4],
            min_happiness=row[5],
            time_of_day=row[6],
        )
        for row in db.execute(
            "SELECT species_id, from_species_id, trigger, min_level, item, min_happiness, time_of_day "
            "FROM evolution WHERE game_id = ?",
            (game_id,),
        )
    }
    return {
        species_id: Species(
            id=species_id,
            identifier=identifier,
            name=name,
            types=(type1,) if type2 is None else (type1, type2),
            base_stats=stats[species_id],
            evolves_from=evolutions.get(species_id),
        )
        for species_id, identifier, name, type1, type2 in db.execute(
            "SELECT id, identifier, name, type1, type2 FROM species WHERE game_id = ? ORDER BY id", (game_id,)
        )
    }


def _moves(db: sqlite3.Connection, game_id: int) -> dict[int, Move]:
    return {
        row[0]: Move(*row[:-1], damage_class=DamageClass(row[-1]))
        for row in db.execute(
            "SELECT id, identifier, name, type, power, accuracy, pp, damage_class FROM move WHERE game_id = ? "
            "ORDER BY id",
            (game_id,),
        )
    }


def _learnsets(db: sqlite3.Connection, game_id: int) -> dict[int, tuple[LearnsetEntry, ...]]:
    learnsets = defaultdict(list)
    for species_id, move_id, method, level, machine in db.execute(
        "SELECT species_id, move_id, method, level, machine FROM learnset WHERE game_id = ? "
        "ORDER BY species_id, method, level, machine, move_id",
        (game_id,),
    ):
        learnsets[species_id].append(LearnsetEntry(move_id, LearnMethod(method), level=level, machine=machine))
    return {species_id: tuple(entries) for species_id, entries in learnsets.items()}


def _availability(db: sqlite3.Connection, game_id: int) -> dict[int, Availability]:
    methods = defaultdict(set)
    for species_id, method in db.execute("SELECT species_id, method FROM availability WHERE game_id = ?", (game_id,)):
        methods[species_id].add(Acquisition(method))
    species_ids = [row[0] for row in db.execute("SELECT id FROM species WHERE game_id = ?", (game_id,))]
    return {species_id: Availability(species_id, frozenset(methods[species_id])) for species_id in species_ids}
