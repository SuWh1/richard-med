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


def test_should_not_inflate_match_on_a_shared_generic_token(db_session):
    """A short catalog name must not auto-match a longer raw name just because they
    share one generic word — the classic 'Витамин D matches every Витамин X' bug."""
    vit_d = Service(
        service_key="svc_vit_d",
        name_ru="Витамин D",
        category=ServiceCategory.laboratory,
    )
    db_session.add(vit_d)
    db_session.flush()
    m = ServiceMatcher(db_session)

    result = m.match("Витамин B6 (пиридоксин) (хроматография)")

    assert result.service_id is None
    assert result.method == "none"
    assert result.confidence < 0.75


def test_should_semantic_match_when_fuzzy_fails(db_session):
    svc = Service(
        service_key="svc_sem",
        name_ru="Гонадотропин зюмбель",
        category=ServiceCategory.laboratory,
        embedding=[0.1] * 384,
    )
    db_session.add(svc)
    db_session.flush()
    # Fake embedder returns the same vector → cosine similarity 1.0 with svc.
    matcher = ServiceMatcher(db_session, embedder=lambda _text: [0.1] * 384)

    result = matcher.match("qpwoeiruty zxcvbnm asdfghjkl")

    assert result.method == "semantic"
    assert result.service_id == svc.id
    assert result.confidence >= 0.88


def test_should_skip_semantic_without_an_embedder(db_session):
    svc = Service(
        service_key="svc_sem2",
        name_ru="Кортикотропин зюмбель",
        category=ServiceCategory.laboratory,
        embedding=[0.1] * 384,
    )
    db_session.add(svc)
    db_session.flush()
    matcher = ServiceMatcher(db_session)  # no embedder → semantic disabled

    result = matcher.match("qpwoeiruty zxcvbnm asdfghjkl")

    assert result.method == "none"
