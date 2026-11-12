"""Google Places contract tests use only an injected fake HTTP transport."""
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from food_picker.defaults import load_default_catalog
from food_picker.models import ValidationError
from food_picker.places import find_places, configured_places_key


def test_fixed_api_destination_field_mask_and_validated_candidates():
    def send(request, timeout):
        assert request.full_url == 'https://places.googleapis.com/v1/places:searchText'
        assert request.method == 'POST' and timeout == 12
        assert '包子商行' in json.loads(request.data)['textQuery']
        assert 'location' in request.get_header('X-goog-fieldmask')
        return BytesIO(json.dumps({'places': [
            {'id':'test-id','displayName':{'text':'測試分店'},'formattedAddress':'測試地址','location':{'latitude':24.8,'longitude':120.97}},
            {'displayName':{'text':'缺少位置'}},
            {'displayName':{'text':'無效座標'},'location':{'latitude':999,'longitude':1}},
        ]}).encode())
    candidates = find_places(load_default_catalog().restaurants[0], 'test-only-key', transport=send)
    assert len(candidates) == 1 and candidates[0].latitude == 24.8
    assert candidates[0].name == '測試分店'


@pytest.mark.parametrize('status',[403,429,500])
def test_service_errors_do_not_expose_provider_body_or_key(status):
    def send(request, timeout):
        raise HTTPError(request.full_url, status, 'private service error', {}, BytesIO(b'private-body'))
    with pytest.raises(ValidationError) as error:
        find_places(load_default_catalog().restaurants[0], 'private-key', transport=send)
    assert not any(text in str(error.value) for text in ('private-body','private-key','private service error'))


def test_key_configuration_priority_and_no_request_without_key(monkeypatch):
    monkeypatch.delenv('GOOGLE_PLACES_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_MAPS_API_KEY', raising=False)
    assert configured_places_key() == ''
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY','env-test-key')
    assert configured_places_key() == 'env-test-key'
    assert configured_places_key({'api_key':'server-test-key'}) == 'server-test-key'
    with pytest.raises(ValidationError):
        find_places(load_default_catalog().restaurants[0], '', transport=lambda *a, **k: pytest.fail('must not send'))
