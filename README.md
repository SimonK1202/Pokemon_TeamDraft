# Pokémon Team Draft

A tool to draft a "perfect" team for an in-game playthrough. Pick a game, choose Pokémon and their moves,
and see attack power plus offensive and defensive type coverage for each Pokémon and the whole team.

First games: Red, Blue, Yellow, Gold, Silver, Crystal, FireRed, LeafGreen. More can be added later.

- What the tool must do: [REQUIREMENTS.md](REQUIREMENTS.md)
- How it is built: [ARCHITECTURE.md](ARCHITECTURE.md)

## Status

**Current:** the data of all 8 games is imported and checked against the original games. In the app you pick a game and see its Pokédex (types, base stats, how to obtain each Pokémon) and the data model behind it.

**Planned next (order may change):**
- Detailed check of the Gen 2-3 data against the original games (Gen 1 is fully checked)
- Stat and attack-power calculators
- GUI: select Pokémon and moves (team of 6 plus 2 option slots, 4 moves plus 1 option move)
- Team and coverage calculators
- Team report in the GUI

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Raw data

The game data comes from the [PokeAPI CSV files](https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv).
They are not part of the repository. Download every file listed in `data/pokeapi_source.toml` into
`data/raw/pokeapi/`, ideally from the commit pinned there. The app shows which required files are missing.

Then build the game data (about 4 s), or use the "Import raw data" button in the app:

```powershell
python -m teamdraft.data.importer
```

Where PokeAPI differs from the original games, `data/corrections.toml` holds a small correction with its reason
and source.

### Verifying the data

Compares the imported data with the original games (the [pret](https://github.com/pret) disassemblies, at pinned
commits) and lists every difference. Needs internet access on the first run; files are cached in `data/reference/`.

```powershell
python tools/verify_against_games.py
```

Exit code 0 means: only known, documented differences.

## Run

```powershell
streamlit run src/teamdraft/gui/app.py
```

Run it from the project root so the settings in `.streamlit/config.toml` apply. The browser is **not** opened
automatically: open http://localhost:8501 yourself in the browser of your choice. The app is only reachable
from this computer.

## Configuration

`config.toml` in the project root:

| Key | Default | Meaning |
|---|---|---|
| `team.level` | 50 | Level used for all calculations (1-100) |

## Tests

```powershell
python -m pytest
```
