from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models import Clinic, ClinicBranch, ClinicReview, CompareInsightCache
from app.services import compare_insight as ci
from app.services.compare_insight import ClinicReviewData


def _clear_insight_cache(service_id: int, clinic_ids: list[int]) -> None:
    """Endpoint tests hit the real DB, where the cache persists — clear the key first."""
    session = SessionLocal()
    try:
        session.query(CompareInsightCache).filter(
            CompareInsightCache.cache_key == ci.cache_key(service_id, clinic_ids)
        ).delete()
        session.commit()
    finally:
        session.close()


def _clinic_with_reviews(session, name, *, rating, reviews):
    clinic = Clinic(name=name, source_name="t-insight")
    session.add(clinic)
    session.flush()
    branch = ClinicBranch(
        clinic_id=clinic.id,
        city="Алматы",
        address="ул. Тест",
        lat=43.2,
        lng=76.9,
        rating=rating,
        reviews_count=len(reviews) * 10,
    )
    session.add(branch)
    session.flush()
    for i, text in enumerate(reviews):
        session.add(
            ClinicReview(
                branch_id=branch.id,
                author="Гость",
                rating=5,
                text=text,
                review_date=datetime.now(UTC) - timedelta(days=i),
                source="2gis",
            )
        )
    session.flush()
    return clinic


class FakeLlm:
    def __init__(self, payload: str):
        self.payload = payload
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.payload


def test_should_build_prompt_with_names_ratings_and_reviews():
    clinics = [
        ClinicReviewData(1, "Клиника А", 4.8, 120, ["вежливый персонал", "чисто"]),
        ClinicReviewData(2, "Клиника Б", 4.1, 30, []),
    ]
    prompt = ci.build_prompt("ОАК", clinics)
    assert "ОАК" in prompt
    assert "Клиника А" in prompt and "Клиника Б" in prompt
    assert "4.8" in prompt
    assert "вежливый персонал" in prompt
    assert "Отзывов нет" in prompt


def test_should_parse_insight_mapping_summaries_and_best():
    clinics = [
        ClinicReviewData(11, "А", 4.8, 100, []),
        ClinicReviewData(22, "Б", 4.0, 20, []),
    ]
    raw = '{"summaries": ["хвалят врачей", "жалобы на очереди"], "best_index": 0, "verdict": "Берите А"}'

    insight = ci.parse_insight(raw, clinics, "ОАК")

    assert insight is not None
    assert insight.available is True
    assert insight.clinics[0].clinic_id == 11
    assert insight.clinics[0].summary == "хвалят врачей"
    assert insight.best_clinic_id == 11
    assert insight.verdict == "Берите А"


def test_should_reject_insight_with_mismatched_summary_count():
    clinics = [ClinicReviewData(1, "А", 4.0, 1, [])]
    assert ci.parse_insight('{"summaries": ["a", "b"]}', clinics, "ОАК") is None


def test_should_reject_malformed_insight_json():
    clinics = [ClinicReviewData(1, "А", 4.0, 1, [])]
    assert ci.parse_insight("not json", clinics, "ОАК") is None


def test_should_return_unavailable_when_no_llm(db_session):
    clinic = _clinic_with_reviews(db_session, "Без ИИ", rating=4.5, reviews=["ок"])
    result = ci.compare_insight(db_session, 101, "ОАК", [clinic.id], llm=None)
    assert result.available is False


def test_should_produce_insight_from_db_reviews(db_session):
    a = _clinic_with_reviews(db_session, "Клиника А", rating=4.9, reviews=["отличные врачи"])
    b = _clinic_with_reviews(db_session, "Клиника Б", rating=3.8, reviews=["долго ждать"])
    fake = FakeLlm(
        '{"summaries": ["хвалят врачей", "жалобы на ожидание"], '
        '"best_index": 0, "verdict": "Лучше А"}'
    )

    result = ci.compare_insight(db_session, 102, "Прием терапевта", [a.id, b.id], llm=fake)

    assert result.available is True
    assert [c.clinic_id for c in result.clinics] == [a.id, b.id]
    assert result.clinics[0].summary == "хвалят врачей"
    assert result.best_clinic_id == a.id
    # The actual review texts were handed to the model.
    assert "отличные врачи" in fake.last_prompt
    assert "долго ждать" in fake.last_prompt


def test_should_return_ai_insight_endpoint(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    search = client.get(
        "/api/v1/search", params={"q": "Прием терапевта", "city": "Алматы"}
    ).json()
    service_id = search["resolved_service"]["id"]
    clinic_ids = [c["clinic_id"] for c in search["cards"][:2]]
    assert len(clinic_ids) == 2
    _clear_insight_cache(service_id, clinic_ids)

    fake = FakeLlm(
        '{"summaries": ["хвалят персонал", "жалобы на ожидание"], '
        '"best_index": 0, "verdict": "Берите первую"}'
    )
    monkeypatch.setattr(ci, "get_insighter", lambda: fake)

    resp = client.get(
        "/api/v1/search/compare/insight",
        params={"service_id": service_id, "clinic_ids": ",".join(map(str, clinic_ids))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert len(body["clinics"]) == 2
    assert body["verdict"] == "Берите первую"
    assert body["best_clinic_id"] == clinic_ids[0]


def test_should_report_unavailable_when_no_key(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    search = client.get(
        "/api/v1/search", params={"q": "Прием терапевта", "city": "Алматы"}
    ).json()
    service_id = search["resolved_service"]["id"]
    clinic_ids = [c["clinic_id"] for c in search["cards"][:2]]
    _clear_insight_cache(service_id, clinic_ids)

    monkeypatch.setattr(ci, "get_insighter", lambda: None)

    resp = client.get(
        "/api/v1/search/compare/insight",
        params={"service_id": service_id, "clinic_ids": ",".join(map(str, clinic_ids))},
    )

    assert resp.status_code == 200
    assert resp.json()["available"] is False


def test_should_raise_insight_unavailable_when_llm_fails(db_session):
    import pytest

    clinic = _clinic_with_reviews(db_session, "Есть данные", rating=4.5, reviews=["ок"])
    with pytest.raises(ci.InsightUnavailable):
        ci.compare_insight(db_session, 103, "ОАК", [clinic.id], llm=FakeLlm("это не json"))


def test_should_cache_insight_and_reuse_without_llm(db_session):
    a = _clinic_with_reviews(db_session, "Кэш А", rating=4.9, reviews=["отлично"])
    fake = FakeLlm('{"summaries": ["хорошая клиника"], "best_index": 0, "verdict": "Берите"}')

    first = ci.compare_insight(db_session, 555, "ОАК", [a.id], llm=fake)
    assert first.available is True

    # Second call with NO llm: a cache hit must still return the stored answer,
    # not the "no_ai" fallback — proving the result was persisted and reused.
    second = ci.compare_insight(db_session, 555, "ОАК", [a.id], llm=None)
    assert second.available is True
    assert second.verdict == "Берите"
    assert second.clinics[0].summary == "хорошая клиника"


def test_should_key_cache_by_service_and_clinic_set():
    assert ci.cache_key(7, [3, 1, 2]) == ci.cache_key(7, [1, 2, 3])
    assert ci.cache_key(7, [1, 2]) != ci.cache_key(8, [1, 2])
