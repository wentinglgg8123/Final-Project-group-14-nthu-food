"""Native Streamlit views with small, escaped decorative HTML fragments."""
from html import escape
from pathlib import Path

import streamlit as st

from foodguide.data import maps_url


def coins_html(price):
    """Draw full coins and a clipped half coin (1.5 is never rounded to 2)."""
    coin = '<span class="coin-face" aria-hidden="true">＄</span>'
    full = ''.join(f'<span class="coin">{coin}</span>' for _ in range(int(price)))
    half = f'<span class="coin half">{coin}</span>' if price % 1 else ''
    return f'<span class="coins" role="img" aria-label="{price:g} 個金幣" title="{price:g} 個金幣">{full}{half}</span>'


def dish(restaurant):
    kinds = restaurant['types']
    if '飲料' in kinds or '超商' in kinds:
        return '🥤', 'drink'
    if '甜點' in kinds:
        return '🍮', 'dessert'
    if '早餐' in kinds:
        return '🥪', 'breakfast'
    if '義大利麵' in kinds or '麵食' in kinds:
        return '🍜', 'noodles'
    if '火鍋' in kinds:
        return '🍲', 'rice'
    if '牛排' in kinds:
        return '🥩', 'breakfast'
    return '🍱', 'rice'


def load_styles():
    css = (Path(__file__).resolve().parents[1] / 'assets' / 'style.css').read_text(encoding='utf-8')
    st.html(f'<style>{css}</style>')


def hero():
    st.html('''<header class="brand"><span class="brand-mark">食</span><div>清食指南<small>NTHU FOOD GUIDE</small></div><span class="campus">⌖ 新竹・清華大學</span></header>
    <section class="hero"><div><div class="eyebrow">✦ 好好吃飯，也是一件重要的事</div><h1>今天，吃點<span>什麼？</span></h1><p>從學餐到清夜，把選擇困難交給我們。<br>找到符合每個人口味的那一餐。</p><div class="hero-meta"><b>14</b> 間精選餐廳 <i>／</i> <b>2</b> 大美食區域 <i>／</i> 為你們一起挑選</div></div><div class="hero-art" aria-hidden="true"><span class="hero-orbit"></span><span class="hero-food">🍱</span><span class="hero-note">♥ 一起吃，更好吃</span></div></section>''')


def restaurant_body(restaurant, *, top=False):
    icon, color = dish(restaurant)
    badge = '<span class="top-pick">✦ 本次首選</span>' if top else ''
    st.html(f'''<div class="food-art {color}">{badge}<span class="food-icon" aria-hidden="true">{icon}</span><span class="area-badge">⌖ {escape(restaurant['location'])}</span></div>
    <div class="card-heading"><h3>{escape(restaurant['name'])}</h3><div class="score">{restaurant['score']}<small>推薦分數</small></div></div>
    <p class="cuisine">{escape(' · '.join(restaurant['types']))}</p>
    <div class="price-line">{coins_html(restaurant['price'])}<span>原始價格級距</span></div>
    <div class="hours {restaurant['status']}">● {escape(restaurant['status_label'])}<small>{escape(restaurant['hours'] or '時間待確認')}</small></div>
    <div class="reason">✧ {'<br>'.join(escape(reason) for reason in restaurant['reasons'])}</div>''')


def maps_button(restaurant, key):
    st.link_button('⌖ Google Maps 店家位置 ↗', maps_url(restaurant), key=key, width='stretch')


@st.dialog('餐廳詳細資訊', width='medium')
def show_details(restaurant):
    st.subheader(restaurant['name'])
    st.caption(' · '.join(restaurant['types']))
    st.html(coins_html(restaurant['price']))
    st.write('**所在區域：**', restaurant['location'])
    st.write('**一般營業時間：**', restaurant['hours'] or '清單未提供，請向店家確認')
    st.write('**特殊營業資訊：**', restaurant['specialHours'] or '清單未提供特殊時段')
    st.write('**適合情境：**', '、'.join(restaurant['occasions']))
    st.write('**推薦理由**')
    for reason in restaurant['reasons']:
        st.write(f'• {reason}')
    maps_button(restaurant, 'detail-map')
    st.caption('Google Maps 會以店名與清大／清夜區域開啟查詢；連鎖店請確認分店。路線、距離與即時營業狀態請以地圖及店家公告為準。')
