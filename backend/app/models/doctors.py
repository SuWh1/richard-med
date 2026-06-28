from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Doctor(Base):
    """A DOQ doctor, deduped by DOQ's own id. Enriched from three API layers: the city
    sweep (base fields), the detail endpoint (`details`/photos), and feedbacks."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    doq_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String(256))
    name: Mapped[str] = mapped_column(String(256), index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    experience_years: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(32))
    languages: Mapped[list | None] = mapped_column(JSON)
    photos: Mapped[list | None] = mapped_column(JSON)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    details: Mapped[list["DoctorDetail"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["DoctorReview"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )


class DoctorDetail(Base):
    """One row of the doctor's "О враче" block: Образование / Курсы / Опыт работы /
    Проводимые процедуры / Общая информация, with an optional year."""

    __tablename__ = "doctor_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), index=True
    )
    detail_type: Mapped[str] = mapped_column(String(64))
    detail_type_id: Mapped[int | None] = mapped_column(Integer)
    info: Mapped[str] = mapped_column(Text)
    year: Mapped[str | None] = mapped_column(String(64))

    doctor: Mapped["Doctor"] = relationship(back_populates="details")


class DoctorReview(Base):
    """A patient review for a doctor (DOQ feedbacks). `text_ru` is DOQ's own translation
    of a Kazakh original; we keep both."""

    __tablename__ = "doctor_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), index=True
    )
    doq_feedback_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    score: Mapped[float | None] = mapped_column(Float)
    text: Mapped[str | None] = mapped_column(Text)
    text_ru: Mapped[str | None] = mapped_column(Text)
    service_name: Mapped[str | None] = mapped_column(String(256))
    client_name: Mapped[str | None] = mapped_column(String(256))
    waiting_time: Mapped[int | None] = mapped_column(Integer)
    clinic_reply: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    doctor: Mapped["Doctor"] = relationship(back_populates="reviews")
