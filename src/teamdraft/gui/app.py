"""Streamlit entry point. Run with: streamlit run src/teamdraft/gui/app.py

Streamlit re-runs this whole script top to bottom on every user interaction.
"""

import streamlit as st

from teamdraft.config import load_settings

st.set_page_config(page_title="Pokémon Team Draft")

settings = load_settings()

st.title("Pokémon Team Draft")
st.write(f"Calculation level: **{settings.level}** (set in `config.toml`)")
st.info("Skeleton only. Game, Pokémon and move selection will follow.")
