"""Radius controls and a local, to-scale view of the matching points."""

from html import escape
from math import atan2, cos, radians, sin

import streamlit as st

from .distance import UserLocation, straight_line_meters
from .models import Restaurant


RADIUS_PRESETS = {
    "不限距離": None, "100 公尺": 100, "300 公尺": 300, "500 公尺": 500,
    "1 公里": 1000, "3 公里": 3000, "5 公里": 5000, "自訂距離": None,
}


def selected_radius() -> int | None:
    choice = st.session_state.get("radius_choice", "不限距離")
    if choice == "自訂距離":
        return st.session_state.get("custom_radius")
    return RADIUS_PRESETS[choice]


def render_radius_menu(origin: UserLocation | None) -> None:
    radius = selected_radius() if origin else None
    label = f"距離 · {radius:,} 公尺" if radius is not None else "距離"
    with st.popover(label, icon=":material/radar:", width="stretch", key="radius_menu"):
        if origin is None:
            st.caption("請先在「找離我近的餐廳」取得你的位置。")
        choice = st.selectbox("搜尋半徑", RADIUS_PRESETS, key="radius_choice", disabled=origin is None)
        if choice == "自訂距離":
            st.number_input(
                "自訂半徑（公尺）", min_value=1, value=None, step=1,
                placeholder="輸入公尺數", key="custom_radius", disabled=origin is None,
            )
        st.caption("只保留半徑內且有座標的店家，距離以直線計算。")


def render_radius_preview(origin: UserLocation, radius: int, restaurants: list[Restaurant]) -> None:
    markers = []
    origin_latitude = radians(origin.latitude)
    for restaurant in restaurants:
        meters = straight_line_meters(origin, restaurant)
        if meters is None:
            continue
        latitude = radians(restaurant.latitude)
        delta_longitude = radians(restaurant.longitude - origin.longitude)
        bearing = atan2(
            sin(delta_longitude) * cos(latitude),
            cos(origin_latitude) * sin(latitude)
            - sin(origin_latitude) * cos(latitude) * cos(delta_longitude),
        )
        offset = 50 * meters / radius
        x, y = 50 + offset * sin(bearing), 50 - offset * cos(bearing)
        markers.append(
            f'<span class="radius-marker" title="{escape(restaurant.name, quote=True)}" '
            f'style="left:{x:.4f}%;top:{y:.4f}%"></span>'
        )
    with st.expander("查看半徑範圍"):
        st.html(
            f'<div class="radius-diagram" role="img" aria-label="以你為圓心，半徑 {radius:,} 公尺，'
            f'有 {len(markers)} 間符合條件的餐廳">'
            '<span class="radius-north" aria-hidden="true">北</span>'
            '<span class="radius-line"></span>'
            + "".join(markers) + '<span class="radius-origin" title="你的位置"></span></div>'
        )
        st.caption(f"半徑 {radius:,} 公尺 · 中心為你的位置 · 圓內標出 {len(markers)} 間符合條件的店家")
