from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorDetail, DoctorReview
from app.schemas.doctors import (
    DoctorDetailItem,
    DoctorProfile,
    DoctorReviewOut,
    DoctorReviewPage,
)
from app.services import search


def doctor_profile(session: Session, doctor_id: int) -> DoctorProfile | None:
    doctor = session.get(Doctor, doctor_id)
    if doctor is None:
        return None

    details = session.scalars(
        select(DoctorDetail)
        .where(DoctorDetail.doctor_id == doctor_id)
        .order_by(DoctorDetail.detail_type_id, DoctorDetail.year.desc())
    ).all()

    return DoctorProfile(
        id=doctor.id,
        doq_id=doctor.doq_id,
        slug=doctor.slug,
        name=doctor.name,
        avatar_url=doctor.avatar_url,
        experience_years=doctor.experience_years,
        rating=round(doctor.rating, 1) if doctor.rating is not None else None,
        review_count=doctor.review_count,
        gender=doctor.gender,
        languages=doctor.languages,
        photos=doctor.photos,
        details=[DoctorDetailItem.model_validate(d) for d in details],
        prices=search.prices_for_doctor(session, doctor_id),
    )


def doctor_reviews(
    session: Session, doctor_id: int, *, limit: int = 20, offset: int = 0
) -> DoctorReviewPage:
    total = session.scalar(
        select(func.count())
        .select_from(DoctorReview)
        .where(DoctorReview.doctor_id == doctor_id)
    )
    rows = session.scalars(
        select(DoctorReview)
        .where(DoctorReview.doctor_id == doctor_id)
        .order_by(DoctorReview.created_at.desc().nullslast(), DoctorReview.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return DoctorReviewPage(
        total=total or 0,
        items=[DoctorReviewOut.model_validate(r) for r in rows],
    )
