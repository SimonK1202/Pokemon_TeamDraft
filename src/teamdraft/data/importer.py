"""Imports the raw PokeAPI CSV files into one SQLite file holding the data of every game in scope.

Run from the project root:  python -m teamdraft.data.importer

All historical values (older stats, types, type chart, move values) are resolved here, once.
Every table is keyed by game, so the repository only does simple lookups.
"""

import csv
import sqlite3
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

from teamdraft.data.paths import CORRECTIONS_PATH, DB_PATH, RAW_DIR
from teamdraft.data.resolve import machine_label, value_as_of, value_before_changes
from teamdraft.data.sources import SourceManifest, load_manifest
from teamdraft.domain.availability import Acquisition
from teamdraft.domain.mechanics import DamageClass, Stat
from teamdraft.domain.move import LearnMethod
from teamdraft.domain.species import EvolutionTrigger

SCHEMA_VERSION = 1
GAMES_IN_SCOPE = ("red", "blue", "yellow", "gold", "silver", "crystal", "firered", "leafgreen")  # R1, display order
ENGLISH = "9"
LAST_GEN_WITH_DAMAGE_CLASS_BY_TYPE = 3

# Deoxys has a different form per game. PokeAPI has no game -> form link, but its
# FireRed/LeafGreen learnsets exist only for these two forms.
FORM_BY_GAME = {"firered": {386: "deoxys-attack"}, "leafgreen": {386: "deoxys-defense"}}

STATS_BY_ID = {
    "1": Stat.HP,
    "2": Stat.ATTACK,
    "3": Stat.DEFENSE,
    "4": Stat.SPECIAL_ATTACK,
    "5": Stat.SPECIAL_DEFENSE,
    "6": Stat.SPEED,
    "9": Stat.SPECIAL,
}
GEN1_STATS = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL, Stat.SPEED)
SPLIT_STATS = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPECIAL_ATTACK, Stat.SPECIAL_DEFENSE, Stat.SPEED)
DAMAGE_CLASSES_BY_ID = {"1": DamageClass.STATUS, "2": DamageClass.PHYSICAL, "3": DamageClass.SPECIAL}
SPECIAL_DAMAGE_CLASS_ID = "3"

# Other PokeAPI learn methods (e.g. Stadium's Surfing Pikachu) need something outside the game.
LEARN_METHODS = {
    "level-up": LearnMethod.LEVEL_UP,
    "machine": LearnMethod.MACHINE,
    "tutor": LearnMethod.TUTOR,
    "egg": LearnMethod.EGG,
}
EVOLUTION_TRIGGERS = {
    "level-up": EvolutionTrigger.LEVEL_UP,
    "use-item": EvolutionTrigger.USE_ITEM,
    "trade": EvolutionTrigger.TRADE,
}
ENCOUNTER_METHODS = {
    "walk": Acquisition.WILD,
    "surf": Acquisition.WILD,
    "old-rod": Acquisition.WILD,
    "good-rod": Acquisition.WILD,
    "super-rod": Acquisition.WILD,
    "rock-smash": Acquisition.WILD,
    "headbutt-low": Acquisition.WILD,
    "headbutt-normal": Acquisition.WILD,
    "headbutt-high": Acquisition.WILD,
    "roaming-grass": Acquisition.WILD,
    "roaming-water": Acquisition.WILD,
    "static": Acquisition.STATIC,
    "pokeflute": Acquisition.STATIC,
    "squirt-bottle": Acquisition.STATIC,
    "gift": Acquisition.GIFT,
    "gift-egg": Acquisition.GIFT,
    "npc-trade": Acquisition.NPC_TRADE,
}
# Need another game or device, so they do not count as "without external help" (R5a).
EXTERNAL_ENCOUNTER_METHODS = {"colosseum-bonus-disc-jpn", "colosseum-bonus-disc-us"}

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE game (
    id INTEGER PRIMARY KEY, identifier TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
    version_group_id INTEGER NOT NULL, version_group TEXT NOT NULL,
    generation INTEGER NOT NULL, sort_order INTEGER NOT NULL);
CREATE TABLE ruleset (generation INTEGER PRIMARY KEY, stats TEXT NOT NULL, damage_class_by_type INTEGER NOT NULL);
CREATE TABLE type (
    generation INTEGER NOT NULL, identifier TEXT NOT NULL, is_special INTEGER NOT NULL,
    PRIMARY KEY (generation, identifier));
CREATE TABLE type_factor (
    generation INTEGER NOT NULL, attacking TEXT NOT NULL, defending TEXT NOT NULL, factor REAL NOT NULL,
    PRIMARY KEY (generation, attacking, defending));
CREATE TABLE species (
    game_id INTEGER NOT NULL, id INTEGER NOT NULL, identifier TEXT NOT NULL, name TEXT NOT NULL,
    type1 TEXT NOT NULL, type2 TEXT, PRIMARY KEY (game_id, id));
CREATE TABLE base_stat (
    game_id INTEGER NOT NULL, species_id INTEGER NOT NULL, stat TEXT NOT NULL, value INTEGER NOT NULL,
    PRIMARY KEY (game_id, species_id, stat));
CREATE TABLE evolution (
    game_id INTEGER NOT NULL, species_id INTEGER NOT NULL, from_species_id INTEGER NOT NULL,
    trigger TEXT NOT NULL, min_level INTEGER, item TEXT, min_happiness INTEGER, time_of_day TEXT,
    PRIMARY KEY (game_id, species_id));
CREATE TABLE move (
    game_id INTEGER NOT NULL, id INTEGER NOT NULL, identifier TEXT NOT NULL, name TEXT NOT NULL,
    type TEXT NOT NULL, power INTEGER, accuracy INTEGER, pp INTEGER NOT NULL, damage_class TEXT NOT NULL,
    PRIMARY KEY (game_id, id));
CREATE TABLE learnset (
    game_id INTEGER NOT NULL, species_id INTEGER NOT NULL, move_id INTEGER NOT NULL,
    method INTEGER NOT NULL, level INTEGER, machine TEXT);
CREATE INDEX learnset_by_species ON learnset (game_id, species_id);
CREATE TABLE availability (
    game_id INTEGER NOT NULL, species_id INTEGER NOT NULL, method TEXT NOT NULL,
    PRIMARY KEY (game_id, species_id, method));
"""


@dataclass(frozen=True)
class ImportSummary:
    games: int
    species: int
    moves: int
    learnset_entries: int
    size_bytes: int


class _Raw:
    """Reads the raw CSV files; every file is read at most once per import."""

    def __init__(self, raw_dir: Path):
        self._dir = raw_dir
        self.rows = cache(self._read)

    def _read(self, name: str) -> list[dict[str, str]]:
        with (self._dir / f"{name}.csv").open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def english_names(self, name: str, id_column: str) -> dict[str, str]:
        return {row[id_column]: row["name"] for row in self.rows(name) if row["local_language_id"] == ENGLISH}


def _int_or_none(text: str) -> int | None:
    return int(text) if text else None


@dataclass(frozen=True)
class Corrections:
    """Hand-made corrections from data/corrections.toml."""

    moves: dict[tuple[str, int], dict[str, int | str]]  # (move identifier, generation) -> fields, e.g. {"pp": 10}
    min_happiness: dict[int, int]  # generation -> friendship threshold
    unobtainable: frozenset[tuple[str, str]] = frozenset()  # (game, species identifier): event-only (R5a)


def load_corrections(path: Path = CORRECTIONS_PATH) -> Corrections:
    with path.open("rb") as file:
        raw = tomllib.load(file)
    moves = {}
    for entry in raw.get("move", []):
        fields = {key: entry[key] for key in ("type", "power", "accuracy", "pp") if key in entry}
        for generation in entry["generations"]:
            moves[(entry["identifier"], generation)] = fields
    evolution = raw.get("evolution", {})
    min_happiness = {generation: evolution["min_happiness"] for generation in evolution.get("generations", [])}
    unobtainable = frozenset(
        (game, entry["species"]) for entry in raw.get("unobtainable", []) for game in entry["games"]
    )
    return Corrections(moves=moves, min_happiness=min_happiness, unobtainable=unobtainable)


def build_database(
    raw_dir: Path = RAW_DIR,
    db_path: Path = DB_PATH,
    manifest: SourceManifest | None = None,
    corrections_path: Path = CORRECTIONS_PATH,
) -> ImportSummary:
    """Build the SQLite file from the raw files. Replaces an existing file only after a successful import."""
    manifest = manifest or load_manifest()
    missing = manifest.missing_files(raw_dir)
    if missing:
        raise FileNotFoundError(f"Missing raw files in {raw_dir}: {', '.join(file.name for file in missing)}")

    temp_path = db_path.with_suffix(".tmp")
    temp_path.unlink(missing_ok=True)
    connection = sqlite3.connect(temp_path)
    try:
        connection.executescript(SCHEMA)
        _Importer(_Raw(raw_dir), connection, load_corrections(corrections_path)).run()
        connection.executemany(
            "INSERT INTO meta VALUES (?, ?)",
            [
                ("schema_version", str(SCHEMA_VERSION)),
                ("source_commit", manifest.commit),
                ("imported_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
            ],
        )
        connection.commit()
        summary = ImportSummary(
            games=_count(connection, "game"),
            species=_count(connection, "species"),
            moves=_count(connection, "move"),
            learnset_entries=_count(connection, "learnset"),
            size_bytes=0,
        )
    finally:
        connection.close()
    temp_path.replace(db_path)
    return ImportSummary(**{**summary.__dict__, "size_bytes": db_path.stat().st_size})


def _count(connection: sqlite3.Connection, table: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


class _Importer:
    def __init__(self, raw: _Raw, connection: sqlite3.Connection, corrections: Corrections):
        self.raw = raw
        self.db = connection
        self.corrections = corrections
        self.groups = {row["id"]: row for row in raw.rows("version_groups")}
        self.type_names = {row["id"]: row["identifier"] for row in raw.rows("types")}
        self.species = {row["id"]: row for row in raw.rows("pokemon_species")}
        self.pokemon = {row["id"]: row for row in raw.rows("pokemon")}
        self.pokemon_by_identifier = {row["identifier"]: row["id"] for row in raw.rows("pokemon")}

    def run(self) -> None:
        versions = {row["identifier"]: row for row in self.raw.rows("versions")}
        names = self.raw.english_names("version_names", "version_id")
        for generation in sorted({self._generation(versions[game]) for game in GAMES_IN_SCOPE}):
            self._import_ruleset(generation)
        for sort_order, identifier in enumerate(GAMES_IN_SCOPE):
            version = versions[identifier]
            group = self.groups[version["version_group_id"]]
            self.db.execute(
                "INSERT INTO game VALUES (?, ?, ?, ?, ?, ?, ?)",
                (int(version["id"]), identifier, names[version["id"]], int(group["id"]), group["identifier"],
                 int(group["generation_id"]), sort_order),
            )
            _GameImporter(self, identifier, version, group).run()

    def _generation(self, version: dict[str, str]) -> int:
        return int(self.groups[version["version_group_id"]]["generation_id"])

    def _import_ruleset(self, generation: int) -> None:
        stats = GEN1_STATS if generation == 1 else SPLIT_STATS
        self.db.execute(
            "INSERT INTO ruleset VALUES (?, ?, ?)",
            (generation, ",".join(stats), int(generation <= LAST_GEN_WITH_DAMAGE_CLASS_BY_TYPE)),
        )
        types = [
            row for row in self.raw.rows("types")
            if int(row["id"]) < 10000 and int(row["generation_id"]) <= generation  # ids >= 10000: unknown, shadow
        ]
        self.db.executemany(
            "INSERT INTO type VALUES (?, ?, ?)",
            [(generation, row["identifier"], int(row["damage_class_id"] == SPECIAL_DAMAGE_CLASS_ID)) for row in types],
        )
        current = {(r["damage_type_id"], r["target_type_id"]): int(r["damage_factor"])
                   for r in self.raw.rows("type_efficacy")}
        past = defaultdict(list)
        for r in self.raw.rows("type_efficacy_past"):
            past[(r["damage_type_id"], r["target_type_id"])].append((int(r["generation_id"]), int(r["damage_factor"])))
        for attacking in types:
            for defending in types:
                key = (attacking["id"], defending["id"])
                factor = value_as_of(current.get(key, 100), past[key], generation)
                if factor != 100:
                    self.db.execute(
                        "INSERT INTO type_factor VALUES (?, ?, ?, ?)",
                        (generation, attacking["identifier"], defending["identifier"], factor / 100),
                    )


class _GameImporter:
    """Imports everything of one game, with all values resolved to that game."""

    def __init__(self, parent: _Importer, identifier: str, version: dict[str, str], group: dict[str, str]):
        self.p = parent
        self.raw = parent.raw
        self.db = parent.db
        self.identifier = identifier
        self.game_id = int(version["id"])
        self.version_id = version["id"]
        self.group_id = group["id"]
        self.generation = int(group["generation_id"])
        self.order = int(group["order"])
        # Whole Pokédex of the game (R5): every species introduced up to its generation.
        self.dex = sorted(
            (int(sid) for sid, row in parent.species.items() if int(row["generation_id"]) <= self.generation)
        )
        overrides = FORM_BY_GAME.get(identifier, {})
        self.pokemon_id = {
            sid: parent.pokemon_by_identifier[overrides[sid]] if sid in overrides else str(sid) for sid in self.dex
        }

    def run(self) -> None:
        self._import_species()
        evolutions = self._import_evolutions()
        self._import_moves()
        self._import_learnsets()
        self._import_availability(evolutions)

    def _import_species(self) -> None:
        names = self.raw.english_names("pokemon_species_names", "pokemon_species_id")
        stats_now = {(r["pokemon_id"], r["stat_id"]): int(r["base_stat"]) for r in self.raw.rows("pokemon_stats")}
        stats_past = defaultdict(list)
        for r in self.raw.rows("pokemon_stats_past"):
            stats_past[(r["pokemon_id"], r["stat_id"])].append((int(r["generation_id"]), int(r["base_stat"])))
        types_now = defaultdict(list)
        for r in self.raw.rows("pokemon_types"):
            types_now[r["pokemon_id"]].append((int(r["slot"]), self.p.type_names[r["type_id"]]))
        types_past = defaultdict(lambda: defaultdict(list))
        for r in self.raw.rows("pokemon_types_past"):
            types_past[r["pokemon_id"]][int(r["generation_id"])].append((int(r["slot"]), self.p.type_names[r["type_id"]]))
        stat_ids = {stat: stat_id for stat_id, stat in STATS_BY_ID.items()}
        stats = GEN1_STATS if self.generation == 1 else SPLIT_STATS

        for sid in self.dex:
            pid = self.pokemon_id[sid]
            current = tuple(t for _, t in sorted(types_now[pid]))
            past = [(gen, tuple(t for _, t in sorted(entries))) for gen, entries in types_past[pid].items()]
            types = value_as_of(current, past, self.generation)
            self.db.execute(
                "INSERT INTO species VALUES (?, ?, ?, ?, ?, ?)",
                (self.game_id, sid, self.p.pokemon[pid]["identifier"], names[str(sid)], types[0],
                 types[1] if len(types) > 1 else None),
            )
            for stat in stats:
                key = (pid, stat_ids[stat])
                value = value_as_of(stats_now.get(key), stats_past[key], self.generation)
                if value is None:
                    raise ValueError(f"No {stat} base stat for pokemon {pid} in generation {self.generation}.")
                self.db.execute("INSERT INTO base_stat VALUES (?, ?, ?, ?)", (self.game_id, sid, stat.value, value))

    def _import_evolutions(self) -> dict[int, tuple[int, EvolutionTrigger]]:
        triggers = {r["id"]: r["identifier"] for r in self.raw.rows("evolution_triggers")}
        items = {r["id"]: r["identifier"] for r in self.raw.rows("items")}
        rows_by_species = defaultdict(list)
        for r in self.raw.rows("pokemon_evolution"):
            # version_group_id = the version group in which this way of evolving was introduced.
            introduced = int(self.p.groups[r["version_group_id"]]["order"]) if r["version_group_id"] else 0
            if introduced <= self.order:
                rows_by_species[int(r["evolved_species_id"])].append((introduced, r))

        evolutions = {}
        for sid in self.dex:
            from_id = self.p.species[str(sid)]["evolves_from_species_id"]
            if not from_id or int(from_id) not in self.pokemon_id:
                continue  # base stage, or the previous stage was introduced later (e.g. Pichu in Gen 1)
            candidates = rows_by_species[sid]
            # The latest way of evolving that exists in this game wins.
            row = max(candidates, key=lambda c: c[0])[1] if candidates else None
            trigger = EVOLUTION_TRIGGERS.get(triggers.get(row["evolution_trigger_id"], ""), EvolutionTrigger.OTHER) \
                if row else EvolutionTrigger.OTHER
            item_id = (row["trigger_item_id"] or row["held_item_id"]) if row else ""
            min_happiness = _int_or_none(row["minimum_happiness"]) if row else None
            if min_happiness is not None:
                min_happiness = self.p.corrections.min_happiness.get(self.generation, min_happiness)
            self.db.execute(
                "INSERT INTO evolution VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self.game_id, sid, int(from_id), trigger.value,
                 _int_or_none(row["minimum_level"]) if row else None,
                 items.get(item_id),
                 min_happiness,
                 (row["time_of_day"] or None) if row else None),
            )
            evolutions[sid] = (int(from_id), trigger)
        return evolutions

    def _import_moves(self) -> None:
        names = self.raw.english_names("move_names", "move_id")
        changes = defaultdict(lambda: defaultdict(list))
        for r in self.raw.rows("move_changelog"):
            changed_at = int(self.p.groups[r["changed_in_version_group_id"]]["order"])
            for column in ("type_id", "power", "pp", "accuracy"):
                if r[column]:
                    changes[r["move_id"]][column].append((changed_at, r[column]))

        for r in self.raw.rows("moves"):
            if int(r["id"]) >= 10000 or int(r["generation_id"]) > self.generation:
                continue  # ids >= 10000: Shadow moves of Colosseum/XD
            value = {c: value_before_changes(r[c], changes[r["id"]][c], self.order)
                     for c in ("type_id", "power", "pp", "accuracy")}
            move = {
                "type": self.p.type_names[value["type_id"]],
                "power": _int_or_none(value["power"]),
                "accuracy": _int_or_none(value["accuracy"]),
                "pp": int(value["pp"]),
            }
            move |= self.p.corrections.moves.get((r["identifier"], self.generation), {})  # data/corrections.toml
            self.db.execute(
                "INSERT INTO move VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.game_id, int(r["id"]), r["identifier"], names[r["id"]], move["type"], move["power"],
                 move["accuracy"], move["pp"], DAMAGE_CLASSES_BY_ID[r["damage_class_id"]].value),
            )

    def _import_learnsets(self) -> None:
        methods = {r["id"]: LEARN_METHODS.get(r["identifier"]) for r in self.raw.rows("pokemon_move_methods")}
        machines = {r["move_id"]: machine_label(int(r["machine_number"]))
                    for r in self.raw.rows("machines") if r["version_group_id"] == self.group_id}
        species_by_pokemon = {pid: sid for sid, pid in self.pokemon_id.items()}
        entries = set()
        for r in self.raw.rows("pokemon_moves"):
            if r["version_group_id"] != self.group_id or r["pokemon_id"] not in species_by_pokemon:
                continue
            method = methods[r["pokemon_move_method_id"]]
            if method is None:
                continue
            level = int(r["level"]) if method is LearnMethod.LEVEL_UP else None
            machine = machines.get(r["move_id"]) if method is LearnMethod.MACHINE else None
            entries.add((self.game_id, species_by_pokemon[r["pokemon_id"]], int(r["move_id"]), int(method), level, machine))
        self.db.executemany("INSERT INTO learnset VALUES (?, ?, ?, ?, ?, ?)", sorted(entries, key=str))

    def _import_availability(self, evolutions: dict[int, tuple[int, EvolutionTrigger]]) -> None:
        method_names = {r["id"]: r["identifier"] for r in self.raw.rows("encounter_methods")}
        slot_methods = {r["id"]: method_names[r["encounter_method_id"]] for r in self.raw.rows("encounter_slots")}
        available: dict[int, set[Acquisition]] = defaultdict(set)
        for r in self.raw.rows("encounters"):
            if r["version_id"] != self.version_id:
                continue
            method = slot_methods[r["encounter_slot_id"]]
            if method in EXTERNAL_ENCOUNTER_METHODS:
                continue
            if method not in ENCOUNTER_METHODS:
                raise ValueError(f"Unknown encounter method {method!r} in {self.identifier}: decide how it counts (R5a).")
            sid = int(self.p.pokemon[r["pokemon_id"]]["species_id"])
            if sid not in self.pokemon_id:
                continue
            if (self.identifier, self.p.species[str(sid)]["identifier"]) in self.p.corrections.unobtainable:
                continue  # event-only, see data/corrections.toml
            available[sid].add(ENCOUNTER_METHODS[method])

        # Evolution and breeding can unlock further species, which can unlock more: repeat until stable.
        changed = True
        while changed:
            changed = False
            for sid, (from_id, trigger) in evolutions.items():
                if trigger is not EvolutionTrigger.TRADE and available.get(from_id) \
                        and Acquisition.EVOLUTION not in available[sid]:
                    available[sid].add(Acquisition.EVOLUTION)
                    changed = True
            if self.generation >= 2:
                for sid in [s for s, methods in available.items() if methods and self._can_breed(s)]:
                    root = self._first_stage(sid, evolutions)
                    if root != sid and Acquisition.BREEDING not in available[root]:
                        available[root].add(Acquisition.BREEDING)
                        changed = True

        self.db.executemany(
            "INSERT INTO availability VALUES (?, ?, ?)",
            [(self.game_id, sid, method.value) for sid, methods in sorted(available.items()) for method in methods],
        )

    def _can_breed(self, sid: int) -> bool:
        # Simplified: legendary and mythical Pokémon cannot breed. Egg groups are not checked (yet).
        row = self.p.species[str(sid)]
        return row["is_legendary"] == "0" and row["is_mythical"] == "0"

    @staticmethod
    def _first_stage(sid: int, evolutions: dict[int, tuple[int, EvolutionTrigger]]) -> int:
        while sid in evolutions:
            sid = evolutions[sid][0]
        return sid


def main() -> None:
    summary = build_database()
    print(
        f"Imported {summary.games} games: {summary.species} species, {summary.moves} moves, "
        f"{summary.learnset_entries} learnset entries -> {DB_PATH} ({summary.size_bytes / 1e6:.1f} MB)"
    )


if __name__ == "__main__":
    main()
