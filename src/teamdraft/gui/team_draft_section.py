"""Team draft screen: one row per Pokémon, coverage next to what it belongs to. Display only; content comes from reporting."""

import streamlit as st

from teamdraft.reporting.team_draft import CoverageArea, DraftView, PokemonSlot

EMPTY = "–"
PICTURE_HEIGHT = 96


def render_team_draft(view: DraftView) -> None:
    st.header(f"Team draft – {view.game_name}")
    st.caption(f"Level {view.level}, IV {view.iv} for all stats. Everything below is a placeholder for now.")

    st.subheader("Team")
    for slot in view.team_slots:
        _render_row(view, slot)
    st.subheader("Option slots")
    st.caption("Bench Pokémon that can easily be swapped in. Not part of team coverage.")
    for slot in view.option_slots:
        _render_row(view, slot)

    st.subheader("Team coverage")
    for column, area in zip(st.columns(len(view.team_coverage)), view.team_coverage):
        with column:
            _render_coverage_box(area)


def _render_row(view: DraftView, slot: PokemonSlot) -> None:
    with st.container(border=True):
        picture, build, moves, coverage = st.columns([1, 2, 4, 2])
        with picture:
            st.markdown(f"**{slot.label}**")
            with st.container(height=PICTURE_HEIGHT, border=True):
                st.caption("Picture")
        with build:
            st.markdown(f"Pokémon {EMPTY}")
            st.markdown(_stats_table(view))
            st.markdown(_details_list(view))
        with moves:
            st.markdown(_moves_table(view))
        with coverage:
            for area in view.pokemon_coverage:
                _render_coverage_box(area)


def _stats_table(view: DraftView) -> str:
    header = "| " + " | ".join(view.stat_labels) + " |"
    divider = "|" + "---|" * len(view.stat_labels)
    values = "| " + " | ".join(EMPTY for _ in view.stat_labels) + " |"
    return "\n".join((header, divider, values))


def _details_list(view: DraftView) -> str:
    return "\n".join(
        f"- **{detail.label}:** {EMPTY}" if detail.available else f"- **{detail.label}:** *not in Gen {view.generation}*"
        for detail in view.details
    )


def _moves_table(view: DraftView) -> str:
    # Each move gets its own offensive coverage cell; option moves in italics, so they read as "not counted".
    lines = [f"| Move | {view.move_coverage.label} coverage |", "|---|---|"]
    for move in view.moves:
        label = f"*{move.label}*" if move.is_option else move.label
        lines.append(f"| {label}: {EMPTY} | {EMPTY} |")
    return "\n".join(lines)


def _render_coverage_box(area: CoverageArea) -> None:
    with st.container(border=True):
        st.markdown(f"**{area.label} coverage**")
        st.caption(area.description)
        st.markdown(EMPTY)
