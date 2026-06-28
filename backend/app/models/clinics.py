from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    website_url: Mapped[str | None] = mapped_column(String(512))
    source_name: Mapped[str] = mapped_column(String(64), index=True)

    branches: Mapped[list["ClinicBranch"]] = relationship(
        back_populates="clinic", cascade="all, delete-orphan"
    )


class ClinicBranch(Base):
    __tablename__ = "clinic_branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True
    )
    city: Mapped[str] = mapped_column(String(64), index=True)
    address: Mapped[str | None] = mapped_column(String(512))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(64))
    working_hours: Mapped[str | None] = mapped_column(String(256))
    twogis_firm_id: Mapped[str | None] = mapped_column(String(32), index=True)
    rating: Mapped[float | None] = mapped_column(Float)
    reviews_count: Mapped[int | None] = mapped_column(Integer)
    rating_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    clinic: Mapped["Clinic"] = relationship(back_populates="branches")
    reviews: Mapped[list["ClinicReview"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan"
    )


class ClinicReview(Base):
    __tablename__ = "clinic_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("clinic_branches.id", ondelete="CASCADE"), index=True
    )
    author: Mapped[str | None] = mapped_column(String(256))
    rating: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(Text)
    official_answer: Mapped[str | None] = mapped_column(Text)
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(32), default="2gis")
    external_id: Mapped[str | None] = mapped_column(String(64), index=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    branch: Mapped["ClinicBranch"] = relationship(back_populates="reviews")
