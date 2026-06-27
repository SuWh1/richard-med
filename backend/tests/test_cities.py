from app.core.cities import CITIES, CITY_NAMES, kdl_city_id, kdl_slug


def test_should_include_the_major_kz_cities():
    names = {c.name for c in CITIES}
    assert {"Астана", "Алматы", "Шымкент", "Караганда", "Актобе"} <= names
    assert len(CITIES) >= 15


def test_should_map_a_city_to_its_kdl_slug_and_id():
    assert kdl_slug("Астана") == "astana"
    assert kdl_city_id("Астана") == 98
    assert kdl_slug("Алматы") == "almaty"
    assert kdl_city_id("Алматы") == 136


def test_should_return_none_for_an_unknown_city():
    assert kdl_slug("Атлантида") is None
    assert kdl_city_id("Атлантида") is None


def test_every_city_has_valid_center_coordinates():
    for city in CITIES:
        assert -90 <= city.lat <= 90
        assert -180 <= city.lng <= 180
        assert city.name in CITY_NAMES
