"""Compares the imported game data with the original games (pret disassemblies on GitHub).

Run from the project root after the import:  python tools/verify_against_games.py

Downloads the reference files once into data/reference/ (not committed), from the commits pinned below,
so the check is reproducible. Prints every difference; exit code 1 if a difference is not in ACCEPTED.
Fixes for real differences belong in data/corrections.toml, not here.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

from teamdraft.data.paths import DB_PATH, PROJECT_ROOT
from teamdraft.data.repository import load_game_data
from teamdraft.domain.availability import Acquisition
from teamdraft.domain.mechanics import Stat
from teamdraft.domain.move import LearnMethod

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
COMMITS = {  # pinned 2026-11-12
    "pokered": "130ac3fa5493fb29a8005e8439fd31b4826e46af",
    "pokecrystal": "3c813b0b4d82b39bf62185aceffb76fd6026c70b",
    "pokefirered": "ce6406d8c2eaf46d543c8a2606de0c3cb1951982",
}
# Differences that are not errors in our data, with the reason.
ACCEPTED = {
    "red move struggle: pp 10 vs 1": "Struggle cannot be learned or chosen",
    "crystal move sonic-boom: power 20 vs None": "fixed damage; the game stores it as power",
    "crystal move dragon-rage: power 40 vs None": "fixed damage; the game stores it as power",
    "crystal move rain-dance: accuracy 90 vs None": "status move; accuracy is not used by the drafter",
    "crystal move sunny-day: accuracy 90 vs None": "status move; accuracy is not used by the drafter",
    "firered move spit-up: power 100 vs None": "variable power; the game stores a placeholder",
}
TYPE_NAMES = {"psychic_type": "psychic", "curse_type": "unknown", "mystery": "unknown"}
EFFECTS = {"SUPER_EFFECTIVE": 2.0, "NOT_VERY_EFFECTIVE": 0.5, "NO_EFFECT": 0.0}


def fetch(repo: str, path: str) -> str:
    target = REFERENCE_DIR / f"{repo}-{COMMITS[repo][:7]}" / path
    if not target.exists():
        url = f"https://raw.githubusercontent.com/pret/{repo}/{COMMITS[repo]}/{path}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_download(url))
    return target.read_text(encoding="utf-8")


def list_dir(repo: str, path: str) -> list[str]:
    url = f"https://api.github.com/repos/pret/{repo}/contents/{path}?ref={COMMITS[repo]}"
    return sorted(entry["name"] for entry in json.loads(_download(url)) if entry["name"].endswith(".asm"))


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "teamdraft-verify"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def key(name: str) -> str:
    """Normalise names across sources: 'NIDORAN_F', 'nidoran-f' -> 'nidoranf'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def type_name(name: str) -> str:
    name = name.lower().removeprefix("type_")
    return TYPE_NAMES.get(name, name)


class Report:
    def __init__(self):
        self.unexpected = 0

    def section(self, title: str, compared: int, differences: list[str]) -> None:
        print(f"== {title}: {compared} compared, {len(differences)} differences")
        for difference in differences:
            reason = ACCEPTED.get(difference)
            if reason is None:
                self.unexpected += 1
            print(f"   {'accepted' if reason else 'CHECK   '}  {difference}" + (f"  ({reason})" if reason else ""))


def compare_moves(report: Report, game: str, reference: dict[int, tuple[str, int, int, int]], db: Path) -> None:
    moves = load_game_data(game, db).moves
    differences = []
    for move_id, (type_, power, accuracy, pp) in reference.items():
        move = moves[move_id]
        prefix = f"{game} move {move.identifier}"
        if type_name(type_) != move.type:
            differences.append(f"{prefix}: type {type_name(type_)} vs {move.type}")
        if power > 1 and power != move.power:  # 0/1 = status or special-cased damage in the games
            differences.append(f"{prefix}: power {power} vs {move.power}")
        if accuracy not in (0, move.accuracy if move.accuracy is not None else 100):
            differences.append(f"{prefix}: accuracy {accuracy} vs {move.accuracy}")
        if pp != move.pp:
            differences.append(f"{prefix}: pp {pp} vs {move.pp}")
    report.section(f"{game}: moves", len(reference), differences)


def compare_type_chart(report: Report, game: str, text: str, db: Path) -> None:
    text = text.split("FORESIGHT")[0]  # Gen 2: entries after the Foresight marker are Ghost immunities again
    reference = {(type_name(a), type_name(d)): EFFECTS[e] for a, d, e in re.findall(
        r"db\s+(\w+),\s*(\w+),\s*(SUPER_EFFECTIVE|NOT_VERY_EFFECTIVE|NO_EFFECT)", text)}
    chart = load_game_data(game, db).ruleset.type_chart
    imported = dict(chart.factors)
    differences = [f"{game} type chart {a} -> {d}: {reference.get((a, d), 1.0)} vs {imported.get((a, d), 1.0)}"
                   for a, d in sorted(reference.keys() | imported.keys())
                   if reference.get((a, d), 1.0) != imported.get((a, d), 1.0)]
    report.section(f"{game}: type chart", len(reference), differences)


def gen1(report: Report, db: Path) -> None:
    red = load_game_data("red", db)
    move_names = re.findall(r"^\s*const\s+([A-Z0-9_]+)", fetch("pokered", "constants/move_constants.asm"), re.M)
    move_ids = {name: index for index, name in enumerate(move_names)}  # NO_MOVE = 0
    moves = re.findall(r"^\s*move\s+\w+,\s*\w+,\s*(\d+),\s*(\w+),\s*(\d+),\s*(\d+)",
                       fetch("pokered", "data/moves/moves.asm"), re.M)
    compare_moves(report, "red", {i: (t, int(p), int(a), int(q)) for i, (p, t, a, q) in enumerate(moves, 1)}, db)
    compare_type_chart(report, "red", fetch("pokered", "data/types/type_matchups.asm"), db)

    species = {key(s.identifier): s for s in red.species.values()}
    stat_order = (Stat.HP, Stat.ATTACK, Stat.DEFENSE, Stat.SPEED, Stat.SPECIAL)
    stat_diffs, level_one, machines = [], {}, {}
    for file_name in list_dir("pokered", "data/pokemon/base_stats"):
        text = fetch("pokered", f"data/pokemon/base_stats/{file_name}")
        s = species[key(file_name.removesuffix(".asm"))]
        stats = map(int, re.search(r"db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\n\s*;\s*hp", text).groups())
        for stat, value in zip(stat_order, stats):
            if s.base_stats[stat] != value:
                stat_diffs.append(f"red {s.identifier} {stat}: {value} vs {s.base_stats[stat]}")
        types = tuple(dict.fromkeys(type_name(t) for t in re.search(r"db\s+(\w+),\s*(\w+)\s*;\s*type", text).groups()))
        if types != s.types:
            stat_diffs.append(f"red {s.identifier} types: {types} vs {s.types}")
        first = re.search(r"db\s+([\w, ]+);\s*level 1 learnset", text).group(1)
        level_one[s.id] = {(1, move_ids[m.strip()]) for m in first.split(",") if m.strip() != "NO_MOVE"}
        tmhm = re.search(r"tmhm(.*?); end", text, re.S).group(1)
        machines[s.id] = {move_ids[m] for m in re.findall(r"[A-Z][A-Z0-9_]+", tmhm) if m in move_ids}
    report.section("red: base stats and types", len(machines), stat_diffs)

    learn_diffs = []
    evos_moves = fetch("pokered", "data/pokemon/evos_moves.asm")
    for label, body in re.findall(r"^(\w+)EvosMoves:\n(.*?)(?=^\w+EvosMoves:|\Z)", evos_moves, re.M | re.S):
        s = species.get(key(label))
        if s is None:
            continue  # MissingNo. and other unused slots
        level_up = body.split("\tdb 0", 1)[1] if "\tdb 0" in body else ""
        reference = {(int(lv), move_ids[m]) for lv, m in re.findall(r"db\s+(\d+),\s*([A-Z0-9_]+)", level_up)}
        reference |= level_one[s.id]
        entries = red.learnset(s.id)
        imported = {(e.level, e.move_id) for e in entries if e.method is LearnMethod.LEVEL_UP}
        if reference != imported:
            learn_diffs.append(f"red {s.identifier} level-up: {sorted(reference ^ imported)}")
        imported_machines = {e.move_id for e in entries if e.method is LearnMethod.MACHINE}
        if machines[s.id] != imported_machines:
            learn_diffs.append(f"red {s.identifier} TM/HM: {sorted(machines[s.id] ^ imported_machines)}")
    report.section("red: level-up and TM/HM learnsets", len(machines), learn_diffs)


def gen2(report: Report, db: Path) -> None:
    moves = re.findall(r"^\s*move\s+\w+,\s*\w+,\s*(\d+),\s*(\w+),\s*(\d+),\s*(\d+)",
                       fetch("pokecrystal", "data/moves/moves.asm"), re.M)
    compare_moves(report, "crystal", {i: (t, int(p), int(a), int(q)) for i, (p, t, a, q) in enumerate(moves, 1)}, db)
    compare_type_chart(report, "crystal", fetch("pokecrystal", "data/types/type_matchups.asm"), db)

    # Every species in Crystal's grass and water tables must be marked as wild.
    crystal = load_game_data("crystal", db)
    wild = {key(crystal.species[sid].identifier) for sid, a in crystal.availability.items()
            if Acquisition.WILD in a.methods}
    reference = set()
    for path in ("johto_grass", "johto_water", "kanto_grass", "kanto_water"):
        reference |= {key(m) for m in re.findall(r"^\s*db\s+\d+,\s*([A-Z_0-9]+)\s*$",
                                                 fetch("pokecrystal", f"data/wild/{path}.asm"), re.M)}
    report.section("crystal: wild grass/water species", len(reference),
                   [f"crystal wild {name}: in the game, not imported" for name in sorted(reference - wild)])


def gen3(report: Report, db: Path) -> None:
    blocks = re.findall(r"\[MOVE_\w+\]\s*=\s*\{(.*?)\}", fetch("pokefirered", "src/data/battle_moves.h"), re.S)
    reference = {}
    for move_id, block in enumerate(blocks):
        if move_id == 0:
            continue  # MOVE_NONE
        field = lambda name: re.search(rf"\.{name}\s*=\s*(\w+)", block).group(1)  # noqa: E731
        reference[move_id] = (field("type"), int(field("power")), int(field("accuracy")), int(field("pp")))
    compare_moves(report, "firered", reference, db)


def main(db: Path = DB_PATH) -> int:
    report = Report()
    gen1(report, db)
    gen2(report, db)
    gen3(report, db)
    print(f"\n{report.unexpected} unexpected differences.")
    return 1 if report.unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
