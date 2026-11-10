# Architecture

## Flow

```
raw CSV files ──► Importer (ETL) ──► local database
                                          │
                                  Repository (loads one game)
                                          │
Domain:   Game ─► Ruleset │ Species │ Move │ LearnsetEntry │ PokemonBuild │ Team
                                          │
Calculators (pure functions, receive a Ruleset):
          stats │ attack power │ offensive coverage │ defensive coverage
                                          │
Reporting (tables and matrices ready for display)
                                          │
GUI (Streamlit: display and input only)
```

Dependencies point **downwards only**: the GUI may use everything, calculators never import the GUI,
and nothing outside `data/` knows the file format.

## Packages (`src/teamdraft/`)

| Package | Responsibility | State |
|---|---|---|
| `config.py` | Reads `config.toml` (e.g. level) | Done |
| `data/` | Importer for raw data, repository that loads one game | Planned |
| `domain/` | Game, Ruleset, Species, Move, LearnsetEntry, PokemonBuild, Team | Planned |
| `calculators/` | Stats, attack power, coverage | Planned |
| `reporting/` | View models for the GUI | Planned |
| `gui/` | Streamlit app | Empty page only |

## Key decisions

1. **Game, not generation, is the user's entry point.** A `Game` is a single version (Red, Blue, ...).
   It belongs to a **version group** (Red + Blue) that holds the shared learnsets and TMs, and the group refers
   to its generation's `Ruleset`. Only availability is stored per game, so data and calculators are reused
   within a group while version exclusives are still marked correctly.
2. **Ruleset is the extension point for mechanics.** One per generation: stat formula, type chart,
   physical/special rule (by type in Gen 1-3, by move from Gen 4), special stat (single in Gen 1, split from Gen 2).
   New generation = new ruleset + data; GUI and calculators stay unchanged.
3. **Simplifications are parameters, not omissions.** IVs and EVs exist as parameters with default 0.
   Abilities, natures and items get optional slots in the domain model so they can be added later.
4. **Calculators are pure functions.** Input: domain objects and a ruleset. Output: plain values.
   No I/O, no GUI. This keeps them easy to test against reference values.
5. **Storage is hidden behind the repository.** Planned: download PokeAPI CSVs into `data/raw/` (not committed),
   import a filtered extract into SQLite (standard library, no extra dependency). Final decision after the data source has been verified.
6. **Paths are resolved relative to the package**, never the current working directory.

## Data folders

| Folder | Content | Committed |
|---|---|---|
| `data/raw/` | Downloaded source files | No |
| `data/legacy/` | Hand-written JSON libraries from the first prototype; compared during data-source verification, then removed | Yes (temporary) |

## Risks

- **Historical accuracy of the data source (N2).** PokeAPI may hold only current values for some stats, moves
  or type chart entries. This is checked before any code builds on it.
