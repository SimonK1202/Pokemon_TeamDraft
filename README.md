# Pokémon Team Draft

A tool to draft a "perfect" team for an in-game playthrough. Pick a game, choose Pokémon and their moves,
and see attack power plus offensive and defensive type coverage for each Pokémon and the whole team.

First games: Red, Blue, Yellow, Gold, Silver, Crystal, FireRed, LeafGreen. More can be added later.

- What the tool must do: [REQUIREMENTS.md](REQUIREMENTS.md)
- How it is built: [ARCHITECTURE.md](ARCHITECTURE.md)

## Status

**Current:** project structure, configuration and an empty Streamlit app. No game data loaded yet.

**Planned next (order may change):**
- Verify the data source (PokeAPI) for Gen 1-3
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

## Run

```powershell
streamlit run src/teamdraft/gui/app.py
```

The app opens in the browser at http://localhost:8501.

## Configuration

`config.toml` in the project root:

| Key | Default | Meaning |
|---|---|---|
| `team.level` | 50 | Level used for all calculations (1-100) |

## Tests

```powershell
python -m pytest
```
