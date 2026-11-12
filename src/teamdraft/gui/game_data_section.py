"""Game picker and an overview of the selected game's data. Display and input only."""

from dataclasses import dataclass

import streamlit as st

from teamdraft.data.importer import build_database
from teamdraft.data.repository import DatabaseError, DatabaseInfo, database_info, list_games, load_game_data
from teamdraft.data.sources import load_manifest
from teamdraft.domain.game_data import GameData
from teamdraft.reporting.game_overview import game_summary, pokedex_rows


@dataclass(frozen=True)
class Selection:
    data: GameData
    info: DatabaseInfo


@st.cache_resource(show_spinner="Loading game data …")
def _load(game_identifier: str, imported_at: str) -> GameData:
    # imported_at is part of the cache key, so a new import is picked up automatically.
    return load_game_data(game_identifier)


def select_game() -> Selection | None:
    """Game picker for the whole app. None if there is no game data yet (import button is shown instead)."""
    try:
        info = database_info()
        games = list_games()
    except DatabaseError as error:
        st.warning(str(error))
        _render_import_button()
        return None
    game = st.selectbox("Game", games, format_func=lambda g: g.name)
    return Selection(_load(game.identifier, info.imported_at), info)


def render_game_data(selection: Selection) -> None:
    data, info = selection.data, selection.info
    summary = game_summary(data)

    columns = st.columns(4)
    columns[0].metric("Generation", summary.generation)
    columns[1].metric("Pokémon obtainable", f"{summary.obtainable} / {summary.species}")
    columns[2].metric("Moves", summary.moves)
    columns[3].metric("Learnset entries", summary.learnset_entries)

    st.dataframe(pokedex_rows(data), hide_index=True)
    st.caption(
        f"Version group `{summary.version_group}`. Obtainable = without trading with another cartridge or events. "
        f"Data imported {info.imported_at} from PokeAPI commit `{info.source_commit[:7]}`."
    )
    with st.expander("Rebuild game data"):
        st.write("Only needed after new raw files were downloaded or `data/corrections.toml` was changed.")
        _render_import_button()


def _render_import_button() -> None:
    missing = load_manifest().missing_files()
    if missing:
        st.error("Cannot import, raw files missing: " + ", ".join(f"`{file.name}`" for file in missing))
        return
    if st.button("Import raw data"):
        with st.spinner("Importing all games …"):
            summary = build_database()
        st.cache_resource.clear()
        st.toast(f"Imported {summary.games} games ({summary.size_bytes / 1e6:.1f} MB).")
        st.rerun()
