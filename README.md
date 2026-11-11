# Pokémon Team Draft

A tool to draft a "perfect" team for an in-game playthrough. Pick a game, choose Pokémon and their moves,
and see attack power plus offensive and defensive type coverage for each Pokémon and the whole team.

First games: Red, Blue, Yellow, Gold, Silver, Crystal, FireRed, LeafGreen. More can be added later.

- What the tool must do: [REQUIREMENTS.md](REQUIREMENTS.md)
- How it is built: [ARCHITECTURE.md](ARCHITECTURE.md)

## Status

**Current:** data model for games, rulesets, species, moves, learnsets, availability and teams. The app shows this data model and whether the raw data files are present. No game data loaded yet.

**Planned next (order may change):**
- Importer, database, repository
- Domain model, rulesets, stat and attack-power calculators
- GUI: select game, Pokémon and moves
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
