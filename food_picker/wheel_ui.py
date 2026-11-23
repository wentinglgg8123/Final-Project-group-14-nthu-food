"""Render the wheel and pass the server's selection to the animation."""

from html import escape
from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component

from .models import Restaurant


_wheel = component(
    "restaurant_roulette",
    html='<div class="restaurant-wheel" aria-hidden="true">'
         '<span class="wheel-pointer"></span><div class="wheel-viewport">'
         '<div class="wheel-face"><div class="wheel-rotor"></div></div></div></div>'
         '<span class="wheel-status" role="status" aria-atomic="true"></span>',
    js=(Path(__file__).resolve().parents[1] / "static" / "wheel.js").read_text(encoding="utf-8"),
    isolate_styles=False,
)


def render_wheel(
    pool: list[Restaurant], winner: Restaurant | None, spin: int | None, previous_id: str | None,
) -> None:
    indexes = {restaurant.id: index for index, restaurant in enumerate(pool)}
    names = [restaurant.name for restaurant in pool]
    _wheel(
        data={
            "names": names,
            "winner": indexes[winner.id] if winner is not None else 0,
            "start": indexes.get(previous_id, 0),
            "spin": spin,
        },
        key=f"wheel_spin_{spin}" if spin is not None else "wheel_preview",
    )


def render_wheel_entries(pool: list[Restaurant]) -> None:
    entries = "".join(f"<li>{escape(restaurant.name)}</li>" for restaurant in pool)
    st.html(
        f'<details class="wheel-entries"><summary>盤面名單（{len(pool)} 間）</summary>'
        f'<ol>{entries}</ol></details>'
    )
