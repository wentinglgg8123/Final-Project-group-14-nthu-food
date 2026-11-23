"""Render browser-local favorites without reading or writing them on the server."""

from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component

from .models import Restaurant
from .presentation import area_label, map_url


_favorites = component(
    "restaurant_favorites",
    html='<div class="restaurant-favorites"></div>',
    js=(Path(__file__).resolve().parents[1] / "static" / "favorites.js").read_text(encoding="utf-8"),
    isolate_styles=False,
)


def render_favorite_button(restaurant: Restaurant, *, context: str) -> None:
    _favorites(
        key=f"favorite_{context}_{restaurant.id}",
        data={
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "location": area_label(restaurant),
                "url": map_url(restaurant),
            },
        },
    )


def render_favorites() -> None:
    with st.expander("我的最愛"):
        _favorites(key="favorites_list")
