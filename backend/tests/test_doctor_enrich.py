import httpx

from app.models import Doctor, DoctorDetail, DoctorReview
from app.services.doctor_enrich import enrich_doctors

_DETAIL = {
    "gender_display": "Мужчина",
    "languages": ["kk", "ru"],
    "photo_versions": {"gallery_photos": ["https://img/1.webp", "https://img/2.webp"]},
    "details": [
        {"info": "Карагандинский ГМУ. Радиология.", "detail_type": "Образование", "detail_type_id": 1, "year": "2020"},
        {"info": "  ", "detail_type": "Образование", "detail_type_id": 1, "year": ""},
        {"info": "ЭМИРМЕД", "detail_type": "Опыт работы", "detail_type_id": 3, "year": "2025-"},
    ],
}
_FEEDBACKS = {
    "count": 2,
    "next": None,
    "results": [
        {"id": 1, "score": 10, "text": "Жақсы", "text_translated": "Хорошо",
         "service_name": "Флюорография", "client_name": "Берик", "is_anonymous": None,
         "waiting_time": 5, "clinic_reply": "", "source": "audio",
         "created_at": "2026-06-14T10:00:00+05:00"},
        {"id": 2, "score": 8, "text": "", "text_translated": "Средне",
         "service_name": "Прием", "client_name": "Аня", "is_anonymous": True,
         "waiting_time": None, "clinic_reply": "Спасибо", "source": "web",
         "created_at": None},
    ],
}


class _FakeResp:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """Serves the detail endpoint and the feedbacks endpoint by URL shape."""

    def __init__(self, fail_doq_ids: set[int] | None = None):
        self._fail = fail_doq_ids or set()

    def get_json(self, url: str) -> dict:
        if "/feedbacks/" in url:
            doq = int(url.split("doctor=")[1].split("&")[0])
            if doq in self._fail:
                raise httpx.ConnectError("boom")
            return _FEEDBACKS
        doq = int(url.split("/doctors/")[1].split("/")[0])
        if doq in self._fail:
            raise httpx.ConnectError("boom")
        return _DETAIL

    def close(self) -> None:
        pass


def test_should_enrich_doctor_with_details_photos_and_reviews(db_session):
    doctor = Doctor(doq_id=10870, name="Сабиров")
    db_session.add(doctor)
    db_session.flush()

    result = enrich_doctors(db_session, client=_FakeClient())

    assert result.doctors_enriched == 1
    assert result.errors == 0
    db_session.refresh(doctor)
    assert doctor.enriched_at is not None
    assert doctor.photos == ["https://img/1.webp", "https://img/2.webp"]
    assert doctor.gender == "Мужчина"
    # Blank-info detail row is skipped.
    details = db_session.query(DoctorDetail).filter_by(doctor_id=doctor.id).all()
    assert len(details) == 2
    reviews = db_session.query(DoctorReview).filter_by(doctor_id=doctor.id).all()
    assert {r.text_ru for r in reviews} == {"Хорошо", "Средне"}
    anon = next(r for r in reviews if r.score == 8)
    assert anon.client_name is None  # is_anonymous → name dropped


def test_should_only_enrich_doctors_missing_enrichment_by_default(db_session):
    from datetime import UTC, datetime

    done = Doctor(doq_id=1, name="A", enriched_at=datetime.now(UTC))
    todo = Doctor(doq_id=2, name="B")
    db_session.add_all([done, todo])
    db_session.flush()

    result = enrich_doctors(db_session, client=_FakeClient())

    assert result.doctors_enriched == 1  # only the un-enriched one


def test_should_isolate_a_failing_doctor_and_continue(db_session):
    a = Doctor(doq_id=10, name="A")
    b = Doctor(doq_id=20, name="B")
    db_session.add_all([a, b])
    db_session.flush()

    result = enrich_doctors(db_session, client=_FakeClient(fail_doq_ids={10}))

    assert result.errors == 1
    assert result.doctors_enriched == 1
    db_session.refresh(b)
    assert b.enriched_at is not None
