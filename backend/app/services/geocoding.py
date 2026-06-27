"""Offline geocoding of clinic addresses via the Yandex Geocoder API.

Never called from the user request path (Rule 1) — only the parser pipeline and the
backfill script use this. Results are cached on `clinic_branches.lat/lng`.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class GeocoderError(Exception):
    """Geocoding failed in a way the caller should notice (bad key, bad request)."""


class GeocoderRateLimited(GeocoderError):
    """The API returned 429 — back off and retry later."""


@dataclass(frozen=True)
class GeocodeResult:
    lat: float
    lng: float
    formatted: str | None
    precision: str | None


class _JsonClient(Protocol):
    def get_json(self, url: str, params: dict | None = None) -> dict: ...


def parse_geocode_response(payload: dict) -> GeocodeResult | None:
    """Pull the first toponym out of a Yandex response.

    Yandex encodes `Point.pos` as "longitude latitude" (lon first) — the opposite of
    the lat/lng order the rest of the app uses, so the split order matters here.
    """
    members = (
        payload.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )
    if not members:
        return None

    geo_object = members[0]["GeoObject"]
    lng_str, lat_str = geo_object["Point"]["pos"].split()
    meta = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {})
    return GeocodeResult(
        lat=float(lat_str),
        lng=float(lng_str),
        formatted=meta.get("text"),
        precision=meta.get("precision"),
    )


class YandexGeocoder:
    """Forward-geocodes an address string to coordinates."""

    def __init__(self, api_key: str, url: str, client: _JsonClient):
        self._api_key = api_key
        self._url = url
        self._client = client

    def geocode(self, query: str) -> GeocodeResult | None:
        params = {
            "apikey": self._api_key,
            "geocode": query,
            "format": "json",
            "lang": "ru_RU",
        }
        try:
            payload = self._client.get_json(self._url, params=params)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                raise GeocoderRateLimited("Yandex geocoder rate limited") from exc
            raise GeocoderError(f"Yandex geocoder HTTP {status}") from exc
        return parse_geocode_response(payload)


def geocode_branch(branch, geocoder: YandexGeocoder) -> bool:
    """Fill a branch's lat/lng if missing. Returns True if it was updated.

    Skips (cache hit) when coordinates already exist, and when there is no address to
    geocode — so re-running the backfill is cheap and idempotent.
    """
    if branch.lat is not None and branch.lng is not None:
        return False
    if not branch.address:
        return False

    query = f"{branch.city}, {branch.address}" if branch.city else branch.address
    result = geocoder.geocode(query)
    if result is None:
        logger.warning("no geocode result for %r", query)
        return False

    branch.lat = result.lat
    branch.lng = result.lng
    return True
