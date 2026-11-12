"""Team draft screen: placeholders for team, option slots and coverage. Display only; content comes from reporting.

Two layouts are offered side by side until one is chosen.
"""

import streamlit as st

from teamdraft.reporting.team_draft import CoverageArea, DraftView, PokemonSlot

LAYOUTS = ("Cards", "Rows")
EMPTY = "–"
PICTURE_HEIGHT = 96


def render_team_draft(view: DraftView) -> None:
    st.header(f"Team draft – {view.game_name}")
    st.caption(f"Level {view.level}, IV {view.iv} for all stats. Everything below is a placeholder for now.")
    layout = st.radio("Layout", LAYOUTS, horizontal=True)
    if layout == "Cards":
        _render_cards(view)
    else:
        _render_rows(view)


def _render_cards(view: DraftView) -> None:
    st.subheader("Team")
    _render_card_grid(view, view.team_slots)
    st.subheader("Option slots")
    st.caption("Bench Pokémon that can easily be swapped in. Not part of team coverage.")
    _render_card_grid(view, view.option_slots)

    offensive, defensive = st.columns(2)
    with offensive:
        _render_coverage("Offensive coverage", view.offensive)
    with defensive:
        _render_coverage("Defensive coverage", view.defensive)


def _render_card_grid(view: DraftView, slots: tuple[PokemonSlot, ...], per_row: int = 3) -> None:
    for start in range(0, len(slots), per_row):
        for column, slot in zip(st.columns(per_row), slots[start : start + per_row]):
            with column, st.container(border=True):
                st.markdown(f"**{slot.label}** · Pokémon {EMPTY}")
                _render_picture()
                st.markdown(_stats_table(view))
                st.markdown(_details_line(view))
                st.markdown(_moves_list(view))


def _render_rows(view: DraftView) -> None:
    team, coverage = st.columns([3, 1])
    with team:
        st.subheader("Team")
        for slot in view.team_slots:
            _render_row(view, slot)
        st.subheader("Option slots")
        st.caption("Not part of team coverage.")
        for slot in view.option_slots:
            _render_row(view, slot)
    with coverage:
        _render_coverage("Offensive coverage", view.offensive)
        _render_coverage("Defensive coverage", view.defensive)


def _render_row(view: DraftView, slot: PokemonSlot) -> None:
    with st.container(border=True):
        picture, stats, moves = st.columns([1, 3, 3])
        with picture:
            st.markdown(f"**{slot.label}**")
            _render_picture()
        with stats:
            st.markdown(f"Pokémon {EMPTY}")
            st.markdown(_stats_table(view))
            st.markdown(_details_line(view))
        with moves:
            st.markdown(_moves_list(view))


def _render_picture() -> None:
    with st.container(height=PICTURE_HEIGHT, border=True):
        st.caption("Picture")


def _stats_table(view: DraftView) -> str:
    header = "| " + " | ".join(view.stat_labels) + " |"
    divider = "|" + "---|" * len(view.stat_labels)
    values = "| " + " | ".join(EMPTY for _ in view.stat_labels) + " |"
    return "\n".join((header, divider, values))


def _details_line(view: DraftView) -> str:
    parts = [
        f"{detail.label}: {EMPTY}" if detail.available else f"{detail.label}: *not in Gen {view.generation}*"
        for detail in view.details
    ]
    return " · ".join(parts)


def _moves_list(view: DraftView) -> str:
    # Option moves in italics, so they read as "not counted".
    return "\n".join(
        f"- *{move.label}: {EMPTY}*" if move.is_option else f"- {move.label}: {EMPTY}" for move in view.moves
    )


def _render_coverage(title: str, areas: tuple[CoverageArea, ...]) -> None:
    st.subheader(title)
    for area in areas:
        with st.container(border=True):
            st.markdown(f"**{area.label}**")
            st.caption(area.description)
