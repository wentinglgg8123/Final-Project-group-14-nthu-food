"""Consent-based browser location and explicit Google Maps restaurant coordinates."""
from pathlib import Path

import streamlit as st
import streamlit.components.v2 as components

from .distance import UserLocation, valid_coordinates, parse_google_coordinates
from .models import ValidationError
from .places import configured_places_key, find_places
from .presentation import map_url

ASSETS = Path(__file__).resolve().parents[1] / 'static'
_control = components.component(
    'browser_location',
    html='<div class="controls"><button data-locate type="button">⌖ 取得我的位置</button><button data-clear type="button" hidden>清除位置</button><span data-status role="status" aria-live="polite"></span></div>',
    css='\n.controls{display:flex;gap:10px;align-items:center;\nflex-wrap:wrap;font:14px sans-serif;color:#5e6d62}button{border:1px solid #b8cdbd;background:#eef2ed;color:#27624e;border-radius:7px;padding:10px 14px;cursor:pointer}button:focus-visible{outline:3px solid #27624e}button:disabled{opacity:.6;cursor:wait}[hidden]{display:none!important}',
    js=(ASSETS / 'geolocation.js').read_text(),
)
ERRORS = {
    'denied': '未取得定位權限。請在網址列的位置權限設定允許此網站，再按一次取得位置。',
    'timeout': '定位逾時，請到訊號較好的位置再試一次。',
    'insecure': '瀏覽器定位需要 HTTPS 網站或本機 localhost。',
    'unsupported': '這個瀏覽器不支援定位，請換用支援定位的瀏覽器。',
    'unavailable': '裝置目前無法提供位置，請確認定位服務已開啟。',
}


def handle_location_event(state, event):
    """Validate frontend input; never accept arbitrary component coordinates."""
    if not isinstance(event, dict):
        return
    kind = event.get('kind')
    if kind == 'clear':
        state.user_location = None
        st.session_state['distance_order'] = '原始順序'
        st.session_state.pop('location_error', None)
    elif kind == 'position':
        origin = UserLocation(event.get('latitude'), event.get('longitude'), event.get('accuracy'))
        if state.user_location is None:
            st.session_state['distance_order'] = '距離由近到遠'
        state.user_location = origin
        st.session_state.pop('location_error', None)
    elif kind == 'error':
        st.session_state['location_error'] = ERRORS.get(event.get('code'), ERRORS['unavailable'])


def close_coordinate_dialog():
    st.session_state['coordinates_dialog_open'] = False


@st.dialog('Google Maps 餐廳座標', width='medium', on_dismiss=close_coordinate_dialog)
def coordinate_dialog(state):
    records = {r.id: r for r in state.restaurants}
    if st.session_state.get('coordinate_restaurant') not in records:
        st.session_state.pop('coordinate_restaurant', None)
    chosen = st.selectbox('要設定位置的餐廳', list(records), format_func=lambda key: records[key].name,
                          key='coordinate_restaurant')
    restaurant = records[chosen]
    st.caption(f"目前選擇：{restaurant.name}")
    st.markdown(f'[到 Google Maps 確認這間店的位置]({map_url(restaurant)})')
    st.caption('確認店家分店後，對地圖中的店家圖釘按右鍵，複製最上方的「緯度, 經度」。也接受含店家座標的完整 Google Maps 網址；相機中心 @ 座標與短分享網址不會被當成店家位置。')
    if valid_coordinates(restaurant.latitude, restaurant.longitude):
        st.caption(f'目前店家座標：{restaurant.latitude}, {restaurant.longitude}')
    current = f'{restaurant.latitude}, {restaurant.longitude}' if valid_coordinates(restaurant.latitude, restaurant.longitude) else ''
    with st.form(f'coordinate_manual_{chosen}'):
        value = st.text_input('Google Maps 座標或完整店家網址', value=current, key=f'coordinate_value_{chosen}')
        if st.form_submit_button('套用座標', key='apply_coordinates', type='primary'):
            try:
                latitude, longitude = parse_google_coordinates(value)
                state.set_coordinates(chosen, latitude, longitude)
            except ValidationError as error:
                st.error(str(error))
            else:
                close_coordinate_dialog()
                st.rerun()
    st.divider()
    try:
        config = st.secrets.get('google_maps', {})
    except FileNotFoundError:
        config = {}
    api_key = configured_places_key(config)
    if not api_key:
        st.caption('Google Maps 自動查詢尚未啟用；目前可直接貼入 Google Maps 座標。')
    if st.button('從 Google Maps 查詢店家', key='lookup_places', disabled=not api_key):
        try:
            with st.spinner('正在查詢 Google Maps 店家…'):
                st.session_state[f'places_{chosen}'] = find_places(restaurant, api_key)
                st.session_state.pop(f'place_candidate_{chosen}', None)
        except ValidationError as error:
            st.error(str(error))
    candidates = st.session_state.get(f'places_{chosen}', [])
    if candidates:
        st.caption('資料來源：Google Maps。請核對名稱、地址與分店，確認後才套用。')
        index = st.selectbox('Google Maps 查詢結果', range(len(candidates)),
                             format_func=lambda i: f'{candidates[i].name} — {candidates[i].address}',
                             key=f'place_candidate_{chosen}')
        if st.button('使用這間店的座標', key='apply_place'):
            candidate = candidates[index]
            state.set_coordinates(chosen, candidate.latitude, candidate.longitude)
            close_coordinate_dialog()
            st.rerun()
    elif f'places_{chosen}' in st.session_state:
        st.info('Google Maps 沒有回傳可用座標，請確認店名或手動貼入位置。')
    st.caption('套用的店家座標只保存在目前工作階段。可從餐廳名單的「匯出篩選名單」下載含座標的 Excel，下次再匯入。')


def render_location(state):
    with st.expander('⌖ 找離我近的餐廳', expanded=False):
        st.caption('按鈕會要求瀏覽器定位。位置傳至本站計算直線距離，只在目前工作階段使用，不寫入評論資料庫或網址。')
        result = _control(key='location_control', data={'active': state.user_location is not None},
                          on_event_change=lambda: None)
        event = result.event
        if isinstance(event, dict) and event.get('nonce') and event['nonce'] != st.session_state.get('last_location_event'):
            st.session_state['last_location_event'] = event['nonce']
            try:
                handle_location_event(state, event)
            except ValidationError as error:
                st.session_state['location_error'] = str(error)
            st.rerun()
        if message := st.session_state.get('location_error'):
            st.warning(message + (' 仍使用先前取得的位置，可按清除位置移除。' if state.user_location else ''))
        if state.user_location:
            accuracy = state.user_location.accuracy
            st.success('已取得你的位置；' + (f'裝置回報精度約 ±{round(accuracy)} 公尺。' if accuracy is not None else '裝置未提供精度。'))
            st.selectbox('餐廳排序', ('原始順序', '距離由近到遠'), key='distance_order')
            st.caption('距離是兩點間的直線距離，不是道路長度、步行時間或即時路線。沒有座標的店家排在最後。')
        known = sum(valid_coordinates(r.latitude, r.longitude) for r in state.restaurants)
        st.caption(f'目前 {known}/{len(state.restaurants)} 間餐廳可計算距離。')
        if known < len(state.restaurants):
            st.info('名單中有店家尚未填入 Google Maps 座標；補上後才能比較遠近。')
        if st.button('設定餐廳位置', key='edit_coordinates'):
            st.session_state['coordinates_dialog_open'] = True
        if st.session_state.get('coordinates_dialog_open'):
            coordinate_dialog(state)
