# Architecture

## Flow

```
raw CSV files ──► Importer (ETL) ──► local database
                                          │
                                  Repository (loads one game)
                                          │
Domain:   GameData: Game │ Ruleset │ Species │ Move │ LearnsetEntry │ Availability;  Team │ PokemonBuild
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
| `data/` | Source manifest, importer (raw CSV → SQLite), repository that loads one game | Done |
| `domain/` | Data model, see below | Done (no logic beyond validation yet) |
| `calculators/` | Stats, attack power, coverage | Planned |
| `reporting/` | View models for the GUI (game overview and data model so far) | Partly done |
| `gui/` | Streamlit app | Game picker with game data overview, data model |

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
5. **Raw data stays raw; an importer builds one SQLite file for all games in scope.** The PokeAPI CSVs are downloaded
   by hand into `data/raw/pokeapi/` (not committed). `data/pokeapi_source.toml` lists the needed files, what they feed
   and the pinned PokeAPI commit. The importer filters them to the games in scope and resolves all historical values
   (`*_past` files, `move_changelog`) once, then applies `data/corrections.toml`. SQLite is in the standard library.
   Every table is keyed by game (rulesets by generation), even where version groups share data: this costs some
   duplicate rows but keeps the lookups trivial and handles per-game forms (Deoxys).
   Measured: import of all 8 games about 4 s, file about 3.4 MB, loading one game 20-70 ms (the GUI caches it).
   Storage stays hidden behind the repository, which returns one `GameData` object.
   The app can run the import itself (button) when the file is missing.
6. **Paths are resolved relative to the package**, never the current working directory.
7. **The GUI library is replaceable.** Only `gui/` may import a GUI library (Streamlit today; Tkinter or others
   possible later). Everything the GUI shows comes from `reporting/` as plain Python data. A test
   (`tests/test_architecture.py`) fails if any other package imports a GUI library.
8. **Streamlit runs quiet and local** (`.streamlit/config.toml`): no browser auto-open, no e-mail prompt,
   no usage statistics, bound to `localhost` only, terminal shows errors only.

## Data model (`domain/`)

All classes are frozen dataclasses. The GUI shows this model live (diagram, fields, raw files), generated from the code.

| Class | Meaning |
|---|---|
| `GameData` | Everything for one game, values already resolved to that game; returned by the repository |
| `Game`, `VersionGroup` | The game the user picks and the group that shares learnsets and TMs |
| `Ruleset`, `TypeChart` | Mechanics of one generation: stats, type chart, physical/special rule |
| `Species`, `Evolution` | Pokédex entry with types and base stats of that generation; how it evolves |
| `Move`, `LearnsetEntry` | Move values of that version group; how a species learns it (level-up, TM/HM, tutor, egg) |
| `Availability` | How a species can be obtained in one game (R5a); empty = not obtainable |
| `Team`, `PokemonBuild` | What the user drafts: up to 6 builds with up to 4 moves, with slots for IVs, EVs, ability, item, nature. Planned (R5, R8): 2 option slots and 1 option move, both left out of coverage |

Types are plain identifiers (`"fire"`), species and moves are referenced by their PokeAPI id.

## Data folders

| Folder | Content | Committed |
|---|---|---|
| `data/pokeapi_source.toml` | Manifest: needed raw files, their purpose, pinned PokeAPI commit | Yes |
| `data/raw/pokeapi/` | Downloaded PokeAPI CSV files | No |
| `data/corrections.toml` | Hand-made corrections where PokeAPI differs from the games, each with a reason | Yes |
| `data/teamdraft.sqlite` | Built by the importer: `python -m teamdraft.data.importer` | No |
| `data/legacy/` | Hand-written JSON libraries from the first prototype; compared during data-source verification, then removed | Yes (temporary) |

## Risks

- **Historical accuracy of the data source (N2).** Checked against the game disassemblies (pret/pokered,
  pokecrystal, pokefirered): Gen 1 base stats, types, type chart and learnsets match exactly; all moves of Gen 1-3
  and the Gen 2 type chart match except a few values fixed in `data/corrections.toml`. Not yet cross-checked:
  Gen 2-3 base stats and learnsets.
- **Availability is a model (R5a).** Breeding is simplified (legendary/mythical cannot breed, egg groups are not
  checked). Encounter data of Crystal was checked against the disassembly and is correct.
- **Deoxys** has one form per game: FireRed Attack, LeafGreen Defense. The importer maps this in `FORM_BY_GAME`;
  PokeAPI has the FireRed/LeafGreen learnsets only for these two forms.
- **Status moves of type `unknown`** (Curse in Gen 2-4) are not in the type chart. Coverage calculators must skip
  status moves.
