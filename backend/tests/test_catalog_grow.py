from sqlalchemy import select

from app.models import Service, ServiceAlias, ServiceCategory, UnmatchedService
from app.services.catalog_grow import grow_catalog


def _clear_queue(session):
    session.query(UnmatchedService).delete()
    session.flush()


class _FakeVerifier:
    def __init__(self, verdict: bool | None):
        self._verdict = verdict

    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        return self._verdict


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
    candidate = db_session.scalars(select(Service)).first()
    db_session.add(
        UnmatchedService(
            raw_name="Похоже на существующую услугу",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session, verifier=_FakeVerifier(True))

    assert result["aliased"] == 1
    alias = db_session.scalars(
        select(ServiceAlias).where(ServiceAlias.alias == "Похоже на существующую услугу")
    ).first()
    assert alias is not None and alias.service_id == candidate.id


def test_should_add_new_entry_when_ai_says_different(db_session):
    _clear_queue(db_session)
    candidate = db_session.scalars(select(Service)).first()
    db_session.add(
        UnmatchedService(
            raw_name="Выглядит похоже но другой тест",
            suggested_service_id=candidate.id,
            confidence=0.9,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session, verifier=_FakeVerifier(False))

    assert result["added"] == 1
    svc = db_session.scalars(
        select(Service).where(Service.name_ru == "Выглядит похоже но другой тест")
    ).first()
    assert svc is not None and svc.service_key.startswith("auto-")


def test_should_leave_gray_zone_pending_without_a_verifier(db_session):
    _clear_queue(db_session)
    candidate = db_session.scalars(select(Service)).first()
    db_session.add(
        UnmatchedService(
            raw_name="Серая зона без AI",
            suggested_service_id=candidate.id,
            confidence=0.86,
        )
    )
    db_session.flush()

    result = grow_catalog(db_session)  # no verifier

    assert result["skipped"] == 1
    assert result["added"] == 0
