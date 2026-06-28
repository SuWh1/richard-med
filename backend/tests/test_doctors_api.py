from datetime import UTC, datetime

from app.models import Doctor, DoctorDetail, DoctorReview
from app.services import doctors


def _seed_doctor(db) -> Doctor:
    doc = Doctor(
        doq_id=999,
        name="Тестов Тест",
        avatar_url="https://img/a.webp",
        experience_years=7,
        rating=9.55,
        review_count=3,
        gender="Мужчина",
        photos=["https://img/1.webp"],
    )
    db.add(doc)
    db.flush()
    db.add_all(
        [
            DoctorDetail(doctor_id=doc.id, detail_type="Образование", detail_type_id=1, info="ВУЗ", year="2018"),
            DoctorDetail(doctor_id=doc.id, detail_type="Курсы", detail_type_id=2, info="Курс", year="2022"),
        ]
    )
    db.add_all(
        [
            DoctorReview(doctor_id=doc.id, doq_feedback_id=1, score=10, text_ru="Отлично",
                         service_name="Прием", created_at=datetime(2026, 6, 1, tzinfo=UTC)),
            DoctorReview(doctor_id=doc.id, doq_feedback_id=2, score=8, text_ru="Средне",
                         service_name="Прием", created_at=datetime(2026, 6, 10, tzinfo=UTC)),
        ]
    )
    db.flush()
    return doc


def test_should_return_doctor_profile_with_details(db_session):
    doc = _seed_doctor(db_session)
    profile = doctors.doctor_profile(db_session, doc.id)
    assert profile is not None
    assert profile.name == "Тестов Тест"
    assert profile.rating == 9.6  # rounded
    assert {d.detail_type for d in profile.details} == {"Образование", "Курсы"}
    assert profile.prices == []  # no prices linked in this test


def test_should_return_none_for_unknown_doctor(db_session):
    assert doctors.doctor_profile(db_session, 123456) is None


def test_should_paginate_doctor_reviews_newest_first(db_session):
    doc = _seed_doctor(db_session)
    page = doctors.doctor_reviews(db_session, doc.id, limit=1, offset=0)
    assert page.total == 2
    assert len(page.items) == 1
    assert page.items[0].text_ru == "Средне"  # 2026-06-10 newest first
