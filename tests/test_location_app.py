from pathlib import Path

from streamlit.testing.v1 import AppTest

from food_picker.distance import UserLocation

ENTRY = Path(__file__).resolve().parents[1] / 'streamlit_app.py'


def test_coordinate_editor_and_nearest_sort_and_current_session_only():
    page = AppTest.from_file(str(ENTRY), default_timeout=20).run()
    assert not page.exception
    page.button(key='edit_coordinates').click().run()
    original_id = page.session_state['picker'].restaurants[0].id
    page.text_input(key=f'coordinate_value_{original_id}').set_value('24.8,120.97')
    page.button(key='apply_coordinates').click().run()
    assert not page.exception
    assert page.session_state['picker'].restaurants[0].latitude == 24.8
    state = page.session_state['picker']
    state.set_coordinates(state.restaurants[1].id, 24.801, 120.97)
    state.user_location = UserLocation(24.801, 120.97, 10)
    page.session_state['distance_order'] = '距離由近到遠'
    page.run()
    assert not page.exception
    assert page.dataframe[0].value.iloc[0]['餐廳名稱'] == state.restaurants[1].name
    assert page.dataframe[0].value.iloc[0]['直線距離（公尺）'] == 0
    another = AppTest.from_file(str(ENTRY), default_timeout=20).run()
    assert another.session_state['picker'].user_location is None
    assert another.session_state['picker'].restaurants[0].latitude is None


def test_google_places_does_not_apply_an_unconfirmed_candidate(monkeypatch):
    from food_picker import location_ui
    from food_picker.places import PlaceCandidate
    monkeypatch.setattr(location_ui, 'configured_places_key', lambda config: 'test-only-key')
    queries=[]
    def lookup(restaurant, key):
        queries.append(restaurant.id)
        return [PlaceCandidate('測試 A 分店','測試地址 A',24.8,120.97,'a'),
                PlaceCandidate('測試 B 分店','測試地址 B',24.9,120.98,'b')]
    monkeypatch.setattr(location_ui, 'find_places', lookup)
    page=AppTest.from_file(str(ENTRY), default_timeout=20).run()
    page.button(key='edit_coordinates').click().run()
    original_id=page.session_state['picker'].restaurants[0].id
    page.button(key='lookup_places').click().run()
    assert queries==[original_id]
    assert page.session_state['picker'].restaurants[0].latitude is None
    page.selectbox(key=f'place_candidate_{original_id}').select(1).run()
    page.button(key='apply_place').click().run()
    assert not page.exception
    updated=page.session_state['picker'].restaurants[0]
    assert updated.id==original_id and updated.latitude==24.9 and updated.longitude==120.98
