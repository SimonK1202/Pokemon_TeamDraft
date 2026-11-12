"""Streamlit entry point. Run with: streamlit run src/teamdraft/gui/app.py

Streamlit re-runs this whole script top to bottom on every user interaction.
"""

import streamlit as st

from teamdraft.config import load_settings
from teamdraft.gui.data_model_section import render_data_model
from teamdraft.gui.game_data_section import render_game_data, select_game
from teamdraft.gui.team_draft_section import render_team_draft
from teamdraft.reporting.data_model import build_data_model_view
from teamdraft.reporting.team_draft import build_draft_view, is_draft_supported

st.set_page_config(page_title="Pokémon Team Draft", layout="wide")

settings = load_settings()

st.title("Pokémon Team Draft")
st.write(f"Calculation level: **{settings.level}** (set in `config.toml`)")

# The picker sits above the tabs because every tab works on the selected game (R4).
selection = select_game()

draft_tab, game_tab, model_tab = st.tabs(["Team draft", "Game data", "Data model"])
with draft_tab:
    if selection is None:
        st.info("Import the game data first.")
    elif not is_draft_supported(selection.data.game):
        st.info("The team draft is available for Red, Blue and Yellow so far. Pick one of them above.")
    else:
        game = selection.data.game
        render_team_draft(build_draft_view(game, selection.data.ruleset, settings.level))
with game_tab:
    if selection is not None:
        render_game_data(selection)
with model_tab:
    render_data_model(build_data_model_view())
