# Requirements

Status: agreed baseline (2026-11-10). IDs are stable so code, tests and commits can refer to them.

## Goal

Build a "perfect" team for an **in-game playthrough**: a team that covers every imaginable
opponent, not only the league of a specific game.

## Terms

| Term | Meaning |
|---|---|
| **Generation** | A region and its mechanics: Gen 1 Kanto, Gen 2 Johto, Gen 3 Hoenn, ... |
| **Game** | One single version, e.g. Red, Blue, Yellow. The user always picks a **game**, never a generation. |
| **Version group** | Games that share learnsets and TMs (Red + Blue, Gold + Silver, FireRed + LeafGreen). Data and calculators are shared inside a group; only availability differs. |
| **Ruleset** | The mechanics of one generation (stat formula, type chart, physical/special rule). Each game uses the ruleset of its generation. |

## Scope

- **R1 Games.** First release: Red, Blue, Yellow (Gen 1); Gold, Silver, Crystal (Gen 2); FireRed, LeafGreen (Gen 3).
  Ruby/Sapphire/Emerald are out of scope for now.
  Adding further games must not require changes to the GUI or calculators.
- **R2 Level.** All calculations use one level, default **50**, set in `config.toml`. Adjustable in the GUI later.
- **R3 Simplifications.** IVs/DVs, EVs/stat experience, natures, abilities and held items are ignored for now.
  The design must allow adding them later without refactoring (e.g. Koffing's Levitate makes it immune to Ground).

## Team builder

- **R4 Game selection.** The user selects a game first; everything below uses that game's data and ruleset.
- **R5 Pokémon selection.** The user picks up to 6 Pokémon for a team from the **whole Pokédex** of the selected game:
  all species that exist in it (Gen 1: 151, Gen 2: 251, FireRed/LeafGreen: 386).
- **R5a Availability marker.** Each Pokémon is marked if it is obtainable in the selected game
  **without external help**.
  - Available: wild encounters, fixed encounters, gifts, in-game trades with NPCs, evolution by level-up,
    stone or friendship, breeding (Gen 2+).
  - Not available: trading with another cartridge (so also trade evolutions), event Pokémon (e.g. Mew).
  - Version exclusives are marked per game (e.g. Ekans available in Red, not in Blue).
- **R6 Move list.** For a selected Pokémon, show all moves it can learn in the selected game, grouped in this order:
  1. Level-up (with the level)
  2. TM/HM
  3. Tutor
  4. Egg

  A move in several groups is shown in each, with a note (e.g. Blastoise: Skull Bash by level-up *and* TM).
- **R7 Evolution hints.** For each move, show if **only** a previous or later evolution can learn it,
  or if they **also** can (with method and level).
- **R8 Move selection.** The user picks up to 4 moves per Pokémon.
- **R9 Move details.** Show type, accuracy and **attack power**.
- **R10 Attack power.** The outgoing number of *my* Pokémon, independent of the opponent:
  move base power, my Pokémon's attacking stat at the set level, STAB multiplier, and the
  generation's physical/special rule. The exact formula is defined and documented together with the calculator.

## Coverage (later)

- **R11 Offensive coverage.** For each Pokémon and the whole team: which defending types the chosen damaging moves
  hit super-effective, neutral, not very effective or not at all. STAB moves are marked.
- **R12 Defensive coverage.** For each Pokémon and the whole team: the multiplier each attacking type has
  against it (×0 to ×4), **type chart only**.
- **R13 Reporting.** The GUI shows the final team with the coverage results (R11, R12).

## Non-functional

- **N1 Data source.** Data comes from a freely downloadable source (planned: PokeAPI CSVs, to be verified first).
- **N2 Correctness per generation.** Stats, types, moves and the type chart must match the selected game,
  not today's values (e.g. Gen 1 single Special stat, Gen 1 type chart, Gen 1-3 physical/special by type).
- **N3 Testability.** Calculators are pure functions with tests against published reference values.
- **N4 GUI.** Streamlit, runs locally in the browser.

## Open questions

- **Data risk for R5a.** Checked: PokeAPI has gifts, gift eggs, static encounters and NPC trades for all 8 games.
  Crystal seems to lack some wild Pokémon (e.g. Mareep); to be confirmed with a second source when the importer is built.
