from sqlalchemy import select

from app.models import Service, ServiceAlias, ServiceCategory, UnmatchedService
from app.services.catalog_grow import (
    _map_category,
    _source_default_category,
    grow_catalog,
)
from app.services.llm_verify import TransientVerifyError


def test_should_default_known_lab_source_to_laboratory():
    assert _source_default_category("kdl_olymp") == ServiceCategory.laboratory
    assert _source_default_category("doq") == ServiceCategory.doctor_visit


def test_should_default_unknown_source_to_other():
    assert _source_default_category(None) == ServiceCategory.other
    assert _source_default_category("mystery_source") == ServiceCategory.other


def test_should_use_source_fallback_for_keywordless_lab_section():
    # "Бор в волосах" matches no keyword; from a lab source it's still a lab test.
    assert (
        _map_category("Исследования в Германии", "Бор B в волосах",
                      fallback=ServiceCategory.laboratory)
        == ServiceCategory.laboratory
    )
    # Same text from an unknown source stays quarantined.
    assert (
        _map_category("Исследования в Германии", "Бор B в волосах",
                      fallback=ServiceCategory.other)
        == ServiceCategory.other
    )


def _clear_queue(session):
    session.query(UnmatchedService).delete()
    session.flush()


class _FakeVerifier:
    def __init__(self, verdict: bool | None):
        self._verdict = verdict

    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        return self._verdict


class _RateLimitedVerifier:
    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        raise TransientVerifyError("429")


class _SpyVerifier:
    """Records calls so a test can assert the AI was (or wasn't) consulted."""

    def __init__(self, verdict: bool | None = True):
        self._verdict = verdict
        self.calls: list[tuple[str, str]] = []

    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        self.calls.append((raw_name, candidate_name))
        return self._verdict


def _lab_candidate(session) -> Service:
    return session.scalars(
        select(Service).where(Service.category == ServiceCategory.laboratory)
    ).first()


def test_should_add_a_new_catalog_entry_when_nothing_is_similar(db_session):
    _clear_queue(db_session)
    db_session.add(
        UnmatchedService(raw_name="Уникальный анализ источника XYZ", confidence=0.0)
    )
    db_session.flush()

    result = grow_catalog(db_session)

    assert result["added"] == 1
    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Уникальный анализ источника XYZ")
    ).first()
    assert svc is not None
    assert svc.service_key.startswith("auto-")
    assert svc.category == ServiceCategory.laboratory


def test_should_be_idempotent_on_rerun(db_session):
    _clear_queue(db_session)
    db_session.add(UnmatchedService(raw_name="Повторный тест", confidence=0.0))
    db_session.flush()

    grow_catalog(db_session)
    again = grow_catalog(db_session)

    assert again["added"] == 0  # already added, nothing pending
    count = db_session.scalars(
        select(Service).where(Service.name_ru == "Повторный тест")
    ).all()
    assert len(count) == 1  # no duplicate service


def test_should_alias_to_candidate_when_ai_confirms(db_session):
    _clear_queue(db_session)
    candidate = _lab_candidate(db_session)
    db_session.add(
        UnmatchedService(
            raw_name="Похожий анализ на существующую услугу",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session, verifier=_FakeVerifier(True))

    assert result["aliased"] == 1
    alias = db_session.scalars(
        select(ServiceAlias).where(ServiceAlias.alias == "Похожий анализ на существующую услугу")
    ).first()
    assert alias is not None and alias.service_id == candidate.id


def test_should_add_new_entry_when_ai_says_different(db_session):
    _clear_queue(db_session)
    candidate = _lab_candidate(db_session)
    db_session.add(
        UnmatchedService(
            raw_name="Похожий анализ но другой тест",
            suggested_service_id=candidate.id,
            confidence=0.9,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session, verifier=_FakeVerifier(False))

    assert result["added"] == 1
    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Похожий анализ но другой тест")
    ).first()
    assert svc is not None and svc.service_key.startswith("auto-")


def test_should_leave_gray_zone_pending_without_a_verifier(db_session):
    _clear_queue(db_session)
    candidate = _lab_candidate(db_session)
    db_session.add(
        UnmatchedService(
            raw_name="Серый анализ зона без AI",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session)  # no verifier

    assert result["skipped"] == 1
    assert result["added"] == 0


def test_should_quarantine_unclassifiable_entry_as_other(db_session):
    # No medical keyword anywhere → must land in `other`, not silently in laboratory.
    _clear_queue(db_session)
    db_session.add(UnmatchedService(raw_name="Подарочный сертификат на сумму", confidence=0.0))
    db_session.flush()

    grow_catalog(db_session)

    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Подарочный сертификат на сумму")
    ).first()
    assert svc is not None and svc.category == ServiceCategory.other


def test_should_classify_lab_names_as_laboratory_not_other(db_session):
    # Positive lab inference must keep real analytes out of the quarantine bucket.
    _clear_queue(db_session)
    db_session.add(UnmatchedService(raw_name="Анализ крови на магний", confidence=0.0))
    db_session.flush()

    grow_catalog(db_session)

    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Анализ крови на магний")
    ).first()
    assert svc is not None and svc.category == ServiceCategory.laboratory


def test_should_keep_gray_zone_pending_when_verifier_is_rate_limited(db_session):
    # A 429 must not file the row as "deferred" — it should stay pending for the next run.
    _clear_queue(db_session)
    candidate = _lab_candidate(db_session)
    db_session.add(
        UnmatchedService(
            raw_name="Анализ лимит запросов исчерпан",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session, verifier=_RateLimitedVerifier())

    assert result["deferred"] == 0 and result["aliased"] == 0 and result["added"] == 0
    row = db_session.scalars(
        select(UnmatchedService).where(
            UnmatchedService.raw_name == "Анализ лимит запросов исчерпан"
        )
    ).first()
    assert row.status == "pending"


def test_should_resolve_category_mismatch_without_calling_ai(db_session):
    # A lab raw name suggested against a diagnostic candidate is a token-overlap false
    # positive (e.g. an antibody test ~> an MRI). The prefilter makes a new entry for free.
    _clear_queue(db_session)
    diagnostic = db_session.scalars(
        select(Service).where(Service.category == ServiceCategory.diagnostic)
    ).first()
    db_session.add(
        UnmatchedService(
            raw_name="Антитела к коре надпочечников",
            suggested_service_id=diagnostic.id,
            confidence=0.86,
        )
    )
    db_session.flush()
    spy = _SpyVerifier()

    result = grow_catalog(db_session, verifier=spy)

    assert spy.calls == []  # AI never consulted — category mismatch resolved it
    assert result["added"] == 1
    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Антитела к коре надпочечников")
    ).first()
    assert svc is not None and svc.category == ServiceCategory.laboratory


def test_should_send_same_category_gray_zone_to_ai(db_session):
    # Same category → genuine look-alike → the AI must arbitrate.
    _clear_queue(db_session)
    candidate = _lab_candidate(db_session)
    db_session.add(
        UnmatchedService(
            raw_name="Похожий анализ крови вариант",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()
    spy = _SpyVerifier(verdict=True)

    grow_catalog(db_session, verifier=spy)

    assert len(spy.calls) == 1
