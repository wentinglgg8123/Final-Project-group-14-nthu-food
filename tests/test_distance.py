"""Measured coordinate math and explicit Google Maps point parsing."""
from dataclasses import replace
import math

import pytest

from food_picker.defaults import load_default_catalog
from food_picker.distance import UserLocation, straight_line_meters, nearest_first, distance_text, parse_google_coordinates
from food_picker.models import ValidationError
from food_picker.session import PickerSession
from food_picker.excel import export_restaurants, parse_excel


def record(lat=None, lon=None, name='test'):
    return replace(load_default_catalog().restaurants[0], latitude=lat, longitude=lon, name=name)


def test_equator_quarter_earth_and_same_point():
    origin = UserLocation(0, 0)
    assert straight_line_meters(origin, record(0, 0)) == 0
    assert straight_line_meters(origin, record(0, 1)) == pytest.approx(111195.08, abs=0.1)
    assert straight_line_meters(origin, record(90, 0)) == pytest.approx(math.pi * 6371008.8 / 2)
    assert straight_line_meters(UserLocation(0, 179.9), record(0, -179.9)) == pytest.approx(22239.02, abs=0.1)


@pytest.mark.parametrize('lat,lon', [(None, 120), (True, 0), (0, math.nan), (91, 0), (0, 181), ('24', 120), (math.inf, 0)])
def test_invalid_device_and_restaurant_points_are_not_used(lat, lon):
    with pytest.raises(ValidationError):
        UserLocation(lat, lon)
    assert straight_line_meters(UserLocation(0, 0), record(lat, lon)) is None


def test_nearest_sort_is_stable_and_unknowns_remain_visible():
    far, close, missing, tied = record(0, 2, 'far'), record(0, 1, 'near'), record(name='unknown'), record(0, 1, 'tie')
    original = [far, missing, close, tied]
    assert [r.name for r in nearest_first(original, UserLocation(0, 0))] == ['near', 'tie', 'far', 'unknown']
    assert original == [far, missing, close, tied]
    assert nearest_first(original, None) == original
    assert '尚無座標' in distance_text(missing, UserLocation(0, 0))
    assert '公尺' in distance_text(record(0, 0.001), UserLocation(0, 0))
    assert '公里' in distance_text(far, UserLocation(0, 0))


@pytest.mark.parametrize('text,expected', [
    ('24.8, 120.97', (24.8, 120.97)),
    ('-33.8，151.2', (-33.8, 151.2)),
    ('https://www.google.com/maps/place/Store/@1,2,15z/data=!4m2!3d24.8!4d120.97', (24.8, 120.97)),
    ('https://maps.google.com/?q=24.8%2C120.97', (24.8, 120.97)),
    ('https://www.google.com/maps/search/?api=1&query=24.8,120.97', (24.8, 120.97)),
])
def test_google_point_coordinates(text, expected):
    assert parse_google_coordinates(text) == expected


@pytest.mark.parametrize('text', [
    '91,120', '0,nan', '0,inf', '店家名稱',
    'https://www.google.com/maps/place/name/@24.8,120.97,15z',
    'https://maps.app.goo.gl/short', 'https://evil.test/maps/!3d24.8!4d120.97',
    'https://www.google.com/maps/data=!3d24!4d120!3d25!4d121',
    'https://www.google.com/search?q=24.8,120.97',
])
def test_viewports_ambiguous_short_and_non_maps_urls_are_not_store_points(text):
    with pytest.raises(ValidationError):
        parse_google_coordinates(text)


def test_updating_coordinates_keeps_reviews_identity_selection_history_and_exports():
    session = PickerSession()
    original = session.restaurants[0]
    session.selected = original
    session.history = [original]
    session.user_location = UserLocation(24.8, 120.97, 20)
    session.set_coordinates(original.id, 24.801, 120.971)
    updated = session.restaurants[0]
    assert updated.id == original.id
    assert updated.latitude == 24.801 and updated.longitude == 120.971
    assert session.selected == updated and session.history == [updated]
    restored = parse_excel(export_restaurants(session.restaurants), 'coordinates.xlsx').restaurants
    assert restored[0].latitude == updated.latitude and restored[0].id == original.id
    session.reset()
    assert session.user_location == UserLocation(24.8, 120.97, 20)
    with pytest.raises(ValidationError):
        session.set_coordinates('missing-store', 24.8, 120.97)


def test_exported_ids_are_validated_and_an_invalid_id_does_not_hide_a_valid_duplicate():
    from food_picker.catalog import parse_rows
    result=parse_rows([
        ['Restaurant','Location','Genre','Price','RestaurantID'],
        ['測試店','小吃部','早餐',1,'bad id!'],
        ['測試店','小吃部','早餐',1,'valid_id'],
        ['另一間店','清夜','早餐',1,'valid_id'],
    ])
    assert [r.id for r in result.restaurants]==['valid_id']
    assert len(result.warnings)==2
