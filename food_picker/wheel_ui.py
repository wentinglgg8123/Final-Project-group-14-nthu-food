"""Render the restaurant pool and animate the pointer to the server's selection."""

from html import escape

import streamlit as st

from .models import Restaurant


COLORS = ("#eaf3e6", "#f8e6c7", "#f2d9ce", "#d9e9f4", "#daeade")


def render_wheel(pool: list[Restaurant], winner: Restaurant | None, spin: int | None) -> None:
    step = 360 / len(pool)
    stops = []
    labels = []
    entries = []
    winner_index = 0
    for index, restaurant in enumerate(pool):
        name = escape(restaurant.name)
        color = COLORS[index % len(COLORS)]
        if index == len(pool) - 1 and index and color == COLORS[0]:
            color = COLORS[1]
        stops.append(f"{color} {index * step:.5f}deg {(index + 1) * step:.5f}deg")
        if len(pool) <= 60:
            label = name if len(pool) <= 20 else str(index + 1)
            labels.append(
                f'<span class="wheel-spoke" style="--spoke-angle:{index * step:.5f}deg">'
                f'<span class="wheel-label">{label}</span></span>'
            )
        entries.append(f"<li>{name}</li>")
        if winner is not None and restaurant.id == winner.id:
            winner_index = index

    angle = -winner_index * step + (1440 if spin is not None else 0)
    gradient = f"conic-gradient(from {-step / 2:.5f}deg,{','.join(stops)})"
    spinning = " wheel-spinning" if spin is not None else ""
    with st.container(key=f"wheel_spin_{spin}" if spin is not None else "wheel_preview"):
        st.html(
            f'<div class="restaurant-wheel" aria-hidden="true">'
            '<span class="wheel-pointer"></span>'
            f'<div class="wheel-rotor{spinning}" style="--wheel-angle:{angle:.5f}deg;background:{gradient}">'
            f'{"".join(labels)}<span class="wheel-hub"></span></div></div>'
        )
    st.html(
        f'<details class="wheel-entries"><summary>盤面名單（{len(pool)} 間）</summary>'
        f'<ol>{"".join(entries)}</ol></details>'
    )
