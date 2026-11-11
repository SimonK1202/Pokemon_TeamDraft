"""Streamlit entry point. Run with: streamlit run src/teamdraft/gui/app.py

Streamlit re-runs this whole script top to bottom on every user interaction.
"""

import streamlit as st

from teamdraft.config import load_settings
from teamdraft.gui.data_model_section import render_data_model
from teamdraft.reporting.data_model import build_data_model_view

st.set_page_config(page_title="Pokémon Team Draft")

settings = load_settings()

st.title("Pokémon Team Draft")
st.write(f"Calculation level: **{settings.level}** (set in `config.toml`)")
st.info("Game, Pokémon and move selection will follow. Below: the data the drafter will work with.")

render_data_model(build_data_model_view())
