"""Shows the data model the drafter will work with. Display only; content comes from reporting."""

import streamlit as st

from teamdraft.reporting.data_model import DataModelView, to_dot


def render_data_model(view: DataModelView) -> None:
    st.header("Data model")
    _render_raw_data_status(view)

    st.caption("Blue: loaded per game from the raw data. Yellow: drafted by the user. Arrows: field that refers to it.")
    st.graphviz_chart(to_dot(view))

    for group in dict.fromkeys(entity.group for entity in view.entities):
        st.subheader(group)
        for entity in (e for e in view.entities if e.group == group):
            with st.expander(f"**{entity.name}** – {entity.summary}"):
                st.table({"Field": [f.name for f in entity.fields], "Type": [f.type for f in entity.fields]})
                if entity.sources:
                    st.caption("Raw files: " + ", ".join(f"`{name}`" for name in entity.sources))

    st.subheader("Value lists")
    for value_list in view.value_lists:
        st.markdown(f"**{value_list.name}:** " + ", ".join(f"`{value}`" for value in value_list.values))


def _render_raw_data_status(view: DataModelView) -> None:
    raw = view.raw_data
    source = f"[PokeAPI]({raw.repository}) commit `{raw.commit[:7]}`"
    if raw.missing:
        st.warning(
            f"Raw data from {source}: {len(raw.missing)} of {raw.required} required files missing in "
            f"`data/raw/pokeapi/`: " + ", ".join(f"`{name}`" for name in raw.missing)
        )
    else:
        st.success(f"Raw data from {source}: all {raw.required} required files present in `data/raw/pokeapi/`.")
