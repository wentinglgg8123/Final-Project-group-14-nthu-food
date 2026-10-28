"""Restaurant data, input validation and Google Maps destinations."""
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'restaurants.json'
PRICE_LEVELS = (1.0, 1.5, 2.0, 2.5)
AREAS = ('不限', '小吃部', '清夜')


def load_restaurants(path=DATA_PATH):
    """Load the supplied spreadsheet records without assuming prices or routes."""
    records = json.loads(Path(path).read_text(encoding='utf-8'))
    ids = set()
    for restaurant in records:
        if restaurant['id'] in ids:
            raise ValueError('餐廳編號不可重複')
        ids.add(restaurant['id'])
        if restaurant['price'] not in PRICE_LEVELS:
            raise ValueError('不支援的價格級距')
        if restaurant['location'] not in AREAS[1:]:
            raise ValueError('不支援的餐廳區域')
        if not restaurant['name'] or not restaurant['types']:
            raise ValueError('餐廳名稱與料理類型不得留白')
        if restaurant.get('mapsUrl') and not is_google_maps_url(restaurant['mapsUrl']):
            raise ValueError('店家地圖網址必須是 Google Maps 網址')
    return records


def is_google_maps_url(url):
    """Accept optional merchant share links, not arbitrary external destinations."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        return False
    host = parsed.hostname
    if host in ('maps.app.goo.gl', 'maps.google.com'):
        return True
    return host in ('www.google.com', 'google.com') and parsed.path.startswith('/maps')


def maps_url(restaurant):
    """Use a verified share link if supplied; otherwise search the named branch.

    A name-based Google Maps query does not claim a verified Place ID or compute
    distance. Adding campus/area context disambiguates generic chain names.
    """
    direct = restaurant.get('mapsUrl')
    if direct and is_google_maps_url(direct):
        return direct
    area = '國立清華大學 小吃部' if restaurant['location'] == '小吃部' else '清大夜市'
    query = f"新竹市 {area} {restaurant['name']}"
    return 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': query})


def cuisine_types(restaurants):
    return sorted({kind for restaurant in restaurants for kind in restaurant['types']})


def coin_text(price):
    """Plain-text alternative for select widgets; cards render actual half coins."""
    full = '🪙' * int(price)
    return full + (' + ½🪙' if price % 1 else '')


def parse_favorites(value, valid_ids):
    """Ignore invalid/stale IDs from a bookmark without crashing the app."""
    return {int(part) for part in str(value).split(',') if part.isdigit() and int(part) in valid_ids}
