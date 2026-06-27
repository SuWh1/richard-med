import pytest

from app.models import Service, ServiceAlias, ServiceCategory
from app.services.normalization import ServiceMatcher, canonical_clean


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Общий   анализ  крови ", "общий анализ крови"),
        ("ОАК, без СОЭ!", "оак без соэ"),
        ("Приём терапевта", "прием терапевта"),
        ("ЭКГ (ECG)", "экг есg"),
    ],
)
def test_should_clean_to_canonical_form(raw, expected):
    assert canonical_clean(raw) == expected


# Unique nonsense names so the assertions don't collide with the real imported catalog.
@pytest.fixture
def matcher(db_session):
    svc_a = Service(
        service_key="svc_test_a",
        name_ru="Квазулин экзактпроба",
        category=ServiceCategory.laboratory,
    )
    svc_b = Service(
        service_key="svc_test_b",
        name_ru="Зюмбель алиасоснова",
        category=ServiceCategory.doctor_visit,
    )
    db_session.add_all([svc_a, svc_b])
    db_session.flush()
    db_session.add(
        ServiceAlias(service_id=svc_b.id, alias="фывапро синонимикс", confidence=0.97)
    )
    db_session.flush()
    return ServiceMatcher(db_session), svc_a.id, svc_b.id


def test_should_exact_match_with_full_confidence(matcher):
    m, a_id, _ = matcher
    result = m.match("квазулин экзактпроба")
    assert result.service_id == a_id
    assert result.method == "exact"
    assert result.confidence == 1.0


def test_should_alias_match(matcher):
    m, _, b_id = matcher
    result = m.match("Фывапро Синонимикс")
    assert result.service_id == b_id
    assert result.method == "alias"
    assert result.confidence == pytest.approx(0.97)


def test_should_fuzzy_match_above_threshold(matcher):
    m, a_id, _ = matcher
    result = m.match("квазулин экзактпробаа")
    assert result.service_id == a_id
    assert result.method == "fuzzy"
    assert result.confidence >= 0.88


def test_should_return_none_below_threshold(matcher):
    m, _, _ = matcher
    result = m.match("qpwoeiruty zxcvbnm asdfghjkl")
    assert result.service_id is None
    assert result.method == "none"
