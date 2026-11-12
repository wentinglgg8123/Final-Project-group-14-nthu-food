"""Validated geographic points and straight-line distances, never route estimates."""
from dataclasses import dataclass
import math
import re
from urllib.parse import parse_qs, unquote, urlsplit

from .models import Restaurant, ValidationError


def valid_coordinates(latitude, longitude):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
               for v in (latitude, longitude)) and -90 <= latitude <= 90 and -180 <= longitude <= 180


@dataclass(frozen=True)
class UserLocation:
    latitude: float
    longitude: float
    accuracy: float | None = None

    def __post_init__(self):
        if not valid_coordinates(self.latitude, self.longitude):
            raise ValidationError('定位座標無效，請重新取得位置。')
        if self.accuracy is not None and (
            isinstance(self.accuracy, bool) or not isinstance(self.accuracy, (int, float))
            or not math.isfinite(self.accuracy) or self.accuracy < 0
        ):
            raise ValidationError('定位精度資料無效，請重新取得位置。')


def straight_line_meters(origin: UserLocation, restaurant: Restaurant):
    if not valid_coordinates(restaurant.latitude, restaurant.longitude):
        return None
    lat1, lat2 = math.radians(origin.latitude), math.radians(restaurant.latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(restaurant.longitude - origin.longitude)
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 2 * 6_371_008.8 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def distance_text(restaurant, origin):
    if origin is None:
        return '尚未取得你的位置'
    meters = straight_line_meters(origin, restaurant)
    if meters is None:
        return '店家尚無座標，無法計算距離'
    if meters < 1000:
        return f'直線距離約 {round(meters)} 公尺'
    return f'直線距離約 {meters / 1000:.2f} 公里'


def nearest_first(restaurants, origin):
    """Unknown points sort last, ties preserve the input order. Do not mutate data."""
    if origin is None:
        return list(restaurants)
    def key(restaurant):
        meters = straight_line_meters(origin, restaurant)
        return math.inf if meters is None else meters
    return sorted(restaurants, key=key)


def parse_google_coordinates(value):
    """Accept explicit coordinate pairs or a Google Maps place point, not viewport @.

    Google Maps /@lat,lng is often only the camera center, not the business. Place
    URLs with !3d...!4d... identify the destination. Short links require opening
    Maps first; this parser never fetches an untrusted URL or follows redirects.
    """
    if not isinstance(value, str):
        raise ValidationError('請貼上 Google Maps 店家座標或完整網址。')
    value = value.strip()
    if len(value) > 8192:
        raise ValidationError('地圖網址過長，請直接貼上緯度與經度。')
    pair = value
    if '://' in value:
        try:
            parsed = urlsplit(value)
        except ValueError:
            raise ValidationError('Google Maps 網址格式無效。') from None
        hosts = {'google.com', 'www.google.com', 'maps.google.com', 'google.com.tw', 'www.google.com.tw'}
        if parsed.scheme != 'https' or parsed.hostname not in hosts or parsed.username or parsed.password:
            raise ValidationError('請貼 Google Maps 完整店家網址，或直接貼「緯度, 經度」。短連結請先在地圖開啟。')
        if parsed.hostname != 'maps.google.com' and not parsed.path.startswith('/maps'):
            raise ValidationError('這不是 Google Maps 店家網址。')
        decoded = unquote(value)
        points = re.findall(r'!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)', decoded)
        if points:
            # Several distinct points may describe a route; don't silently pick one.
            if len(set(points)) != 1:
                raise ValidationError('網址包含多個地點，請直接貼這間店的緯度與經度。')
            pair = ','.join(points[0])
        else:
            query = parse_qs(parsed.query)
            pair = next((query[k][0] for k in ('query', 'q', 'destination') if query.get(k)), '')
            if not pair:
                raise ValidationError('網址未提供可確認的店家座標；請在店家圖釘按右鍵複製緯度、經度。')
    if not re.fullmatch(r'\s*-?\d+(?:\.\d+)?\s*[,，]\s*-?\d+(?:\.\d+)?\s*', pair):
        raise ValidationError('請填「緯度, 經度」，或包含店家座標的 Google Maps 完整網址。')
    latitude, longitude = map(float, re.split('[,，]', pair))
    if not valid_coordinates(latitude, longitude):
        raise ValidationError('緯度須在 -90～90、經度須在 -180～180。')
    return latitude, longitude
