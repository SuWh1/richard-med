from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import httpx
import pytest

from app.services.geocoding import (
    GeocoderError,
    GeocodeResult,
    GeocoderRateLimited,
    YandexGeocoder,
    geocode_branch,
    parse_geocode_response,
)


def _payload(pos: str, *, text: str = "Казахстан, Астана", precision: str = "exact") -> dict:
    return {
        "response": {
            "GeoObjectCollection": {
                "metaDataProperty": {"GeocoderResponseMetaData": {"found": "1"}},
                "featureMember": [
                    {
                        "GeoObject": {
                            "metaDataProperty": {
                                "GeocoderMetaData": {"precision": precision, "text": text}
                            },
                            "Point": {"pos": pos},
                        }
                    }
                ],
            }
        }
    }


_EMPTY_PAYLOAD = {
    "response": {
        "GeoObjectCollection": {
            "metaDataProperty": {"GeocoderResponseMetaData": {"found": "0"}},
            "featureMember": [],
        }
    }
}


class _FakeClient:
    """Stand-in for PoliteClient.get_json that records calls or raises."""

    def __init__(self, payload: dict | None = None, error: Exception | None = None):
        self._payload = payload
        self._error = error
        self.calls: list[tuple[str, dict | None]] = []

    def get_json(self, url: str, params: dict | None = None) -> dict:
        self.calls.append((url, params))
        if self._error is not None:
            raise self._error
        return self._payload


def _http_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://geocode-maps.yandex.ru/v1")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"{status}", request=request, response=response)


def test_should_parse_pos_as_longitude_then_latitude():
    result = parse_geocode_response(_payload("71.430411 51.128207"))
    assert result is not None
    assert result.lng == pytest.approx(71.430411)
    assert result.lat == pytest.approx(51.128207)
    assert result.precision == "exact"


def test_should_return_none_when_no_geo_objects_found():
    assert parse_geocode_response(_EMPTY_PAYLOAD) is None


def test_should_geocode_query_passing_apikey_format_and_lang():
    client = _FakeClient(payload=_payload("76.945465 43.238949"))
    geocoder = YandexGeocoder("test-key", "https://geocode-maps.yandex.ru/v1", client)

    result = geocoder.geocode("Алматы, проспект Абая 1")

    assert result is not None
    assert (result.lat, result.lng) == pytest.approx((43.238949, 76.945465))
    _url, params = client.calls[0]
    assert params["apikey"] == "test-key"
    assert params["geocode"] == "Алматы, проспект Абая 1"
    assert params["format"] == "json"
    assert params["lang"] == "ru_RU"


def test_should_raise_geocoder_error_on_invalid_apikey():
    client = _FakeClient(error=_http_error(403))
    geocoder = YandexGeocoder("bad", "https://geocode-maps.yandex.ru/v1", client)
    with pytest.raises(GeocoderError):
        geocoder.geocode("Астана")


def test_should_raise_rate_limited_on_429():
    client = _FakeClient(error=_http_error(429))
    geocoder = YandexGeocoder("k", "https://geocode-maps.yandex.ru/v1", client)
    with pytest.raises(GeocoderRateLimited):
        geocoder.geocode("Астана")


def test_should_skip_branch_that_already_has_coordinates():
    client = _FakeClient(payload=_payload("71.0 51.0"))
    geocoder = YandexGeocoder("k", "u", client)
    branch = SimpleNamespace(city="Астана", address="Тұран 43", lat=51.1, lng=71.4)

    updated = geocode_branch(branch, geocoder)

    assert updated is False
    assert client.calls == []  # cache hit — never calls the API


def test_should_set_coordinates_on_branch_without_coords():
    client = _FakeClient(payload=_payload("71.430411 51.128207"))
    geocoder = YandexGeocoder("k", "u", client)
    branch = SimpleNamespace(city="Астана", address="Тұран 43", lat=None, lng=None)

    updated = geocode_branch(branch, geocoder)

    assert updated is True
    assert branch.lat == pytest.approx(51.128207)
    assert branch.lng == pytest.approx(71.430411)


def test_should_not_geocode_branch_without_address():
    client = _FakeClient(payload=_payload("71.0 51.0"))
    geocoder = YandexGeocoder("k", "u", client)
    branch = SimpleNamespace(city="Астана", address=None, lat=None, lng=None)

    assert geocode_branch(branch, geocoder) is False
    assert client.calls == []


def test_geocode_result_is_immutable():
    result = GeocodeResult(lat=51.1, lng=71.4, formatted="x", precision="exact")
    with pytest.raises(FrozenInstanceError):
        result.lat = 0.0  # type: ignore[misc]
