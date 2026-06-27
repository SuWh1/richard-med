"""Canonical major Kazakhstan cities — the source-neutral spine for multi-city data.

Each clinic source maps a canonical city to its own identifiers (KDL uses a `slug` for
prices and a numeric `city_id` for branches). Center coords drive the map's default view.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str  # display name (ru)
    kdl_slug: str  # KDL prices API (analysis-data?city_slug=)
    kdl_city_id: int  # KDL branches API (procedure-cabinet?city_id=)
    lat: float  # map center
    lng: float


CITIES: tuple[City, ...] = (
    City("Астана", "astana", 98, 51.1605, 71.4704),
    City("Алматы", "almaty", 136, 43.2389, 76.8897),
    City("Шымкент", "shymkent", 21, 42.3417, 69.5901),
    City("Караганда", "karaganda", 15, 49.8047, 73.1094),
    City("Актобе", "aktobe", 99, 50.2839, 57.1670),
    City("Тараз", "taraz", 53, 42.9000, 71.3667),
    City("Павлодар", "pavlodar", 77, 52.2870, 76.9674),
    City("Усть-Каменогорск", "ust-kamenogorsk", 38, 49.9486, 82.6275),
    City("Атырау", "atyrau", 40, 47.0945, 51.9238),
    City("Костанай", "kostanay", 118, 53.2198, 63.6354),
    City("Кызылорда", "kyzylorda", 46, 44.8479, 65.4823),
    City("Актау", "aktau", 83, 43.6410, 51.1980),
    City("Петропавловск", "petropavlovsk", 149, 54.8753, 69.1628),
    City("Кокшетау", "kokshetau", 35, 53.2833, 69.3833),
    City("Туркестан", "turkestan", 126, 43.3017, 68.2696),
    City("Темиртау", "temirtau", 79, 50.0547, 72.9644),
    City("Экибастуз", "ekibastuz", 142, 51.7298, 75.3266),
)

CITY_BY_NAME: dict[str, City] = {c.name: c for c in CITIES}
CITY_NAMES: list[str] = [c.name for c in CITIES]


def kdl_slug(name: str) -> str | None:
    city = CITY_BY_NAME.get(name)
    return city.kdl_slug if city else None


def kdl_city_id(name: str) -> int | None:
    city = CITY_BY_NAME.get(name)
    return city.kdl_city_id if city else None
