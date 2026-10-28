"""Native Python/Streamlit application. Run: streamlit run streamlit_app.py."""
from datetime import datetime
import random

import streamlit as st

from foodguide.data import AREAS, PRICE_LEVELS, coin_text, cuisine_types, load_restaurants, parse_favorites
from foodguide.recommend import Diner, Weights, recommend, taiwan_now
from foodguide.views import hero, load_styles, maps_button, restaurant_body, show_details

st.set_page_config(page_title='清食指南｜清大餐廳選擇器', page_icon='🍚', layout='wide')
restaurants = load_restaurants()
valid_ids = {restaurant['id'] for restaurant in restaurants}


def initialize():
    defaults = {
        'diners': [1], 'next_diner': 2,
        'favorites': parse_favorites(st.query_params.get('favorites', ''), valid_ids),
        'view': '探索美食', 'search': '', 'area': '全部', 'occasion': '不限',
        'strict': True, 'open_only': False,
        'weight_price': 35, 'weight_cuisine': 45, 'weight_area': 20,
        'meal_date': taiwan_now().date(), 'meal_time': taiwan_now().time().replace(second=0, microsecond=0, tzinfo=None),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_diner():
    if len(st.session_state.diners) < 8:
        st.session_state.diners.append(st.session_state.next_diner)
        st.session_state.next_diner += 1


def remove_diner(diner_id):
    if len(st.session_state.diners) > 1:
        st.session_state.diners.remove(diner_id)
        for field in ('name', 'budget', 'cuisine', 'area'):
            st.session_state.pop(f'diner_{diner_id}_{field}', None)


def reset_filters():
    """Reset filters before widgets render; keep the visitor's favorites."""
    for key in list(st.session_state):
        if key.startswith('diner_') or key not in ('favorites',):
            del st.session_state[key]
    initialize()


def toggle_favorite(restaurant_id):
    favorites = set(st.session_state.favorites)
    if restaurant_id in favorites:
        favorites.remove(restaurant_id)
    else:
        favorites.add(restaurant_id)
    st.session_state.favorites = favorites
    # Bookmarkable browser URL preserves favorites on reload without a database.
    if favorites:
        st.query_params['favorites'] = ','.join(map(str, sorted(favorites)))
    elif 'favorites' in st.query_params:
        del st.query_params['favorites']


def preferences():
    diners = []
    with st.sidebar:
        st.markdown('## ☷ 你們想吃什麼？')
        st.caption('告訴我們偏好，讓每個人都吃得開心。')
        st.button('重設條件', key='reset', on_click=reset_filters, width='stretch')
        st.markdown(f'### 用餐夥伴 · {len(st.session_state.diners)} 人')
        for index, diner_id in enumerate(st.session_state.diners, 1):
            prefix = f'diner_{diner_id}_'
            with st.container(border=True):
                name = st.text_input('用餐者姓名', value=f'用餐者 {index}', key=prefix + 'name', max_chars=20)
                budget = st.selectbox('預算上限', PRICE_LEVELS, index=3, format_func=coin_text, key=prefix + 'budget')
                cuisine = st.selectbox('想吃的料理', ['不限', *cuisine_types(restaurants)], key=prefix + 'cuisine')
                area = st.selectbox('偏好區域', AREAS, key=prefix + 'area')
                if len(st.session_state.diners) > 1:
                    st.button('移除這位夥伴', key=prefix + 'remove', on_click=remove_diner, args=(diner_id,))
                diners.append(Diner(name, budget, cuisine, area))
        st.button('＋ 新增用餐夥伴', key='add_diner', on_click=add_diner, disabled=len(diners) >= 8, width='stretch')
        st.divider()
        st.markdown('### 推薦在意什麼？')
        st.slider('預算優先', 0, 100, key='weight_price')
        st.slider('口味優先', 0, 100, key='weight_cuisine')
        st.slider('區域偏好', 0, 100, key='weight_area')
        st.checkbox('符合每個人的預算', key='strict')
        st.caption('條件即時套用。區域只代表店家所在地；實際距離與路線請點 Google Maps 查看。')
    return diners


def filters():
    st.radio('主選單', ('探索美食', '我的收藏', '餐廳資料庫'), key='view', horizontal=True, label_visibility='collapsed')
    if st.session_state.view == '我的收藏':
        st.subheader('想再吃一次的口袋名單 ♡')
        st.caption('收藏會保留在目前網址，加入瀏覽器書籤即可下次繼續使用。')
    elif st.session_state.view == '餐廳資料庫':
        st.subheader('清大周邊餐廳資料庫 ⌖')
        st.caption('此頁顯示全部餐廳，不套用預算、搜尋或其他推薦篩選。')
        return
    else:
        st.subheader('為你們選好的美味 ✦')
        st.caption('不用再問「要吃什麼」，從這裡開始吧。')
    left, right = st.columns([1, 1.5])
    with left:
        st.selectbox('餐廳區域', ('全部', '小吃部', '清夜'), key='area')
    with right:
        st.text_input('搜尋餐廳、想吃的料理', placeholder='找餐廳、想吃的料理…', key='search')
    first, second, third = st.columns(3)
    with first:
        st.date_input('用餐日期（台灣）', key='meal_date')
    with second:
        st.time_input('用餐時間（台灣）', key='meal_time')
    with third:
        st.selectbox('用餐情境', ('不限', '一人食', '約會', '聚餐', '快速吃', '慢慢吃'), key='occasion')
    st.checkbox('只看指定時間營業', key='open_only')


def render_cards(results):
    if not results:
        st.info('沒有符合條件的餐廳。請放寬預算、搜尋或營業時間條件；也可以先收藏喜歡的店家。')
        st.button('重設篩選條件', on_click=reset_filters)
        return
    for start in range(0, len(results), 3):
        for column, restaurant in zip(st.columns(3), results[start:start + 3]):
            with column, st.container(border=True):
                restaurant_body(restaurant, top=start == 0 and restaurant == results[0] and st.session_state.view == '探索美食')
                saved = restaurant['id'] in st.session_state.favorites
                st.button('♥ 已收藏' if saved else '♡ 加入收藏', key=f"favorite_{restaurant['id']}",
                          on_click=toggle_favorite, args=(restaurant['id'],), width='stretch')
                if st.button('查看餐廳資訊 ↗', key=f"detail_{restaurant['id']}", width='stretch'):
                    show_details(restaurant)
                maps_button(restaurant, f"map_{restaurant['id']}")


initialize()
load_styles()
hero()
diners = preferences()
filters()
at = datetime.combine(st.session_state.meal_date, st.session_state.meal_time)
weights = Weights(st.session_state.weight_price, st.session_state.weight_cuisine, st.session_state.weight_area)
if st.session_state.view == '餐廳資料庫':
    results = recommend(restaurants, diners, weights, at=at, strict=False)
else:
    results = recommend(restaurants, diners, weights, at=at, search=st.session_state.search,
                        area=st.session_state.area, occasion=st.session_state.occasion,
                        strict=st.session_state.strict, open_only=st.session_state.open_only)
    if st.session_state.view == '我的收藏':
        results = [restaurant for restaurant in results if restaurant['id'] in st.session_state.favorites]

summary, random_column = st.columns([3, 1])
with summary:
    st.caption(f'找到 {len(results)} 間餐廳 ／ 資料庫共 {len(restaurants)} 間 · 依推薦分數排序')
with random_column:
    if st.button('⚄ 隨機幫我選', key='random', disabled=not results, width='stretch'):
        show_details(random.choice(results))
if weights.price + weights.cuisine + weights.area == 0:
    st.caption('所有權重皆為 0，目前使用三項等權平均。')
render_cards(results)
st.info('⌖ 每間店的 Google Maps 連結會帶入店名與清大／清夜區域；可在地圖內查看位置及規劃路線。')
st.caption('金幣代表附件原始價格級距，並非新台幣金額。營業時間來自附件；實際營業狀態請以店家公告為準。')
st.html('<footer>✳ 清食指南 <span>清大學餐及周邊餐廳選擇器 · 好好吃飯，也是一件重要的事。</span></footer>')
