"""Exercise copied features through the published streamlit_app.py entry point."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from food_picker.catalog import parse_rows
from food_picker.defaults import load_default_catalog
from foodguide.data import load_restaurants

ENTRY = Path(__file__).resolve().parents[1] / 'streamlit_app.py'


def explorer():
    page = AppTest.from_file(str(ENTRY), default_timeout=20).run()
    page.radio(key='workflow').set_value('搜尋與抽選').run()
    assert not page.exception
    return page


def rendered(page):
    return '\n'.join(item.value for item in page.get('html'))


def test_copied_features_keep_name_and_original_fourteen_restaurants():
    page = explorer()
    assert '清食指南' in rendered(page)
    assert '食刻決定' not in rendered(page)
    assert len(page.session_state['picker'].restaurants) == 14
    source = load_default_catalog().restaurants
    original = load_restaurants()
    assert [(r.name, r.location, r.price_level) for r in source] == [(r['name'], r['location'], r['price']) for r in original]


def test_fuzzy_search_and_clear_preserve_advanced_filters():
    page = explorer()
    page.pills(key='location_choices').set_value(['清夜']).run()
    page.text_input(key='query_choice').set_value('麥當牢').run()
    assert '麥當勞' in rendered(page)
    assert '讀音或字詞相近' in ' '.join(c.value for c in page.caption)
    assert page.button(key='pick_meal').disabled
    page.button(key='clear_search_query').click().run()
    assert page.pills(key='location_choices').value == ['清夜']
    assert not page.button(key='pick_meal').disabled


def test_pagination_select_all_and_clear():
    page = explorer()
    assert len(page.dataframe[0].value) == 14
    assert len(page.session_state['picker'].restaurants) == 14
    page.button(key='catalog_next').click().run()
    assert page.session_state['catalog_page'] == 1
    page.button(key='catalog_next').click().run()
    assert page.session_state['catalog_page'] == 2
    assert page.button(key='catalog_next').disabled
    page.button(key='select_all_location_choices').click().run()
    assert set(page.pills(key='location_choices').value) == {'小吃部', '清夜'}
    page.button(key='clear_all_filters').click().run()
    assert page.pills(key='location_choices').value == []
    assert not page.exception


def test_random_pick_avoids_previous_and_retains_history():
    page = explorer()
    page.button(key='pick_meal').click().run()
    first = page.session_state['picker'].selected
    page.button(key='pick_meal').click().run()
    state = page.session_state['picker']
    assert first.id != state.selected.id
    assert len(state.history) == 2
    assert '最近推薦' in rendered(page)


def test_import_reset_and_mode_switch_keep_group_inputs():
    page = AppTest.from_file(str(ENTRY), default_timeout=20).run()
    page.text_input(key='diner_1_name').set_value('小清').run()
    page.selectbox(key='diner_1_budget').select(1.5).run()
    page.radio(key='workflow').set_value('搜尋與抽選').run()
    page.pills(key='location_choices').set_value(['小吃部']).run()
    custom = parse_rows([['Restaurant', 'Location', 'Gener', 'Price'], ['匯入測試店', '小吃部', '早餐', 1.5]])
    page.session_state['picker'].import_catalog(custom, '自訂.xlsx')
    page.run()
    assert '匯入測試店' in rendered(page)
    page.radio(key='workflow').set_value('多人推薦').run()
    assert page.text_input(key='diner_1_name').value == '小清'
    assert page.selectbox(key='diner_1_budget').value == 1.5
    page.button(key='reset').click().run()
    page.radio(key='workflow').set_value('搜尋與抽選').run()
    assert page.pills(key='location_choices').value == ['小吃部']
    assert page.session_state['picker'].filename == '自訂.xlsx'
    next(b for b in page.button if b.label == '恢復內建名單').click().run()
    assert len(page.session_state['picker'].restaurants) == 14
    assert not page.exception


def test_reviews_show_honest_setup_notice_without_credentials():
    page = explorer()
    assert any('評論尚未啟用' in message.value for message in page.info)
    assert any('review_rating_' in widget.key for widget in page.slider)
    assert all(button.disabled for button in page.button if button.key and button.key.startswith('review_submit_'))
