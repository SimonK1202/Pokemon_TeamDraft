"""Streamlit entry point. Run with: streamlit run src/teamdraft/gui/app.py

Streamlit re-runs this whole script top to bottom on every user interaction.
"""

import streamlit as st

from teamdraft.config import load_settings
from teamdraft.gui.data_model_section import render_data_model
from teamdraft.gui.game_data_section import render_game_data
from teamdraft.reporting.data_model import build_data_model_view

st.set_page_config(page_title="Pokémon Team Draft", layout="wide")

settings = load_settings()

st.title("Pokémon Team Draft")
st.write(f"Calculation level: **{settings.level}** (set in `config.toml`)")
st.info("Team and move selection will follow. For now: the data of each game and the data model behind it.")

game_tab, model_tab = st.tabs(["Game data", "Data model"])
with game_tab:
    render_game_data()
with model_tab:
    render_data_model(build_data_model_view())
