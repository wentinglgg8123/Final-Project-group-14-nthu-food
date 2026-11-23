"""Render browser-local favorites and the opt-in favorites filter."""

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
_FILTER_KEY = "favorite_draw_filter"


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


def favorite_draw_ids() -> frozenset[str] | None:
    ids = st.session_state.get(_FILTER_KEY, {}).get("ids")
    if ids is None:
        return None
    if not isinstance(ids, list):
        return frozenset()
    return frozenset(value for value in ids if isinstance(value, str))


def reset_favorite_draw_filter() -> None:
    if _FILTER_KEY in st.session_state:
        st.session_state[_FILTER_KEY]["ids"] = None


def render_favorite_draw_filter() -> None:
    ids = favorite_draw_ids()
    _favorites(
        key=_FILTER_KEY,
        data={"drawFilter": True, "ids": sorted(ids) if ids is not None else None},
        default={"ids": None},
        on_ids_change=lambda: None,
    )
