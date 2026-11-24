"""Render the restaurant roulette and animate the server's selection."""

from functools import lru_cache
from hashlib import sha256
from html import escape
from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component

from .models import Restaurant


_WHEEL_SCRIPT = Path(__file__).resolve().parents[1] / "static" / "wheel.js"


@lru_cache(maxsize=8)
def _wheel_component(script: str):
    # A new asset version must have its own component ID in an already-running app.
    version = sha256(script.encode("utf-8")).hexdigest()[:16]
    return component(
        f"restaurant_roulette_{version}",
        html='<div class="restaurant-wheel" aria-hidden="true">'
             '<span class="wheel-pointer"></span><div class="wheel-viewport">'
             '<div class="wheel-face"><div class="wheel-rotor"></div></div></div></div>'
             '<span class="wheel-status" role="status" aria-atomic="true"></span>',
        js=script,
        isolate_styles=False,
    )


def render_wheel(
    pool: list[Restaurant], winner: Restaurant | None, spin: int | None, previous_id: str | None,
) -> None:
    indexes = {restaurant.id: index for index, restaurant in enumerate(pool)}
    names = [restaurant.name for restaurant in pool]
    _wheel_component(_WHEEL_SCRIPT.read_text(encoding="utf-8"))(
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
