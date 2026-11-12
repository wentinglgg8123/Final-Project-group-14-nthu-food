"""Optional Google Places Text Search; only a user-confirmed result is applied."""
from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .distance import valid_coordinates
from .models import ValidationError
from .presentation import map_url


@dataclass(frozen=True)
class PlaceCandidate:
    name: str
    address: str
    latitude: float
    longitude: float
    place_id: str


def configured_places_key(config=None):
    if config is not None and not isinstance(config, Mapping):
        return ''
    value = (config or {}).get('api_key') or os.environ.get('GOOGLE_PLACES_API_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY', '')
    return value.strip() if isinstance(value, str) else ''


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the API-key header to a different destination.


def find_places(restaurant, key, *, transport=None):
    if not key:
        raise ValidationError('Google Maps 自動查詢尚未設定，請直接貼上店家座標。')
    query = parse_qs(urlsplit(map_url(restaurant)).query)['query'][0]
    request = Request('https://places.googleapis.com/v1/places:searchText',
                      data=json.dumps({'textQuery': query, 'languageCode': 'zh-TW', 'regionCode': 'TW', 'pageSize': 5}).encode(),
                      headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': key,
                               'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location'},
                      method='POST')
    send = transport or build_opener(NoRedirect()).open
    try:
        with send(request, timeout=12) as response:
            raw = response.read(256_001)
        if len(raw) > 256_000:
            raise ValueError('response limit')
        payload = json.loads(raw)
        rows = payload.get('places', [])
        if not isinstance(rows, list):
            raise ValueError('invalid response')
        result = []
        for row in rows[:5]:
            location = row.get('location', {})
            latitude, longitude = location.get('latitude'), location.get('longitude')
            name = row.get('displayName', {}).get('text', '')
            if not isinstance(name, str) or not name or not valid_coordinates(latitude, longitude):
                continue
            address, place_id = row.get('formattedAddress', ''), row.get('id', '')
            if not isinstance(address, str) or not isinstance(place_id, str):
                continue
            result.append(PlaceCandidate(name[:200], address[:500], latitude, longitude, place_id[:255]))
        return result
    except HTTPError as error:
        if error.code in (401, 403):
            raise ValidationError('Google Maps 查詢未獲授權，請管理員確認 Places API、金鑰限制與帳務設定。') from None
        if error.code == 429:
            raise ValidationError('Google Maps 查詢額度已用完，請稍後再試或手動貼入座標。') from None
        raise ValidationError('Google Maps 暫時無法查詢，請稍後再試或手動貼入座標。') from None
    except (URLError, OSError, ValueError, TypeError, AttributeError):
        raise ValidationError('Google Maps 暫時無法查詢，請稍後再試或手動貼入座標。') from None
