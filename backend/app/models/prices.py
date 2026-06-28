from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.catalog import Service
    from app.models.clinics import Clinic, ClinicBranch
    from app.models.doctors import Doctor


class RawDocument(Base):
    __tablename__ = "raw_documents"
    __table_args__ = (
        UniqueConstraint("source_url", "content_hash", name="uq_raw_doc_url_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(64))
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_html: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    items: Mapped[list["RawPriceItem"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class RawPriceItem(Base):
    __tablename__ = "raw_price_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_document_id: Mapped[int] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True
    )
    clinic_raw: Mapped[str | None] = mapped_column(String(256))
    service_name_raw: Mapped[str] = mapped_column(String(512))
    price_raw: Mapped[str | None] = mapped_column(String(64))
    duration_raw: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    document: Mapped["RawDocument"] = relationship(back_populates="items")


class ClinicServicePrice(Base):
    __tablename__ = "clinic_service_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True
    )
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("clinic_branches.id", ondelete="SET NULL")
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), index=True
    )
    raw_price_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_price_items.id", ondelete="SET NULL")
    )
    doctor_id: Mapped[int | None] = mapped_column(
        ForeignKey("doctors.id", ondelete="SET NULL"), index=True
    )
    # Non-null: the active-price key is (clinic, service, city); a NULL city breaks the
    # upsert's dedup (SQL `city = NULL` is never true) and escapes city-scoped staling.
    city: Mapped[str] = mapped_column(String(64), index=True)
    price_kzt: Mapped[int] = mapped_column(Integer)
    duration_min: Mapped[int | None] = mapped_column(Integer)
    duration_max: Mapped[int | None] = mapped_column(Integer)
    service_name_raw: Mapped[str | None] = mapped_column(String(512))
    source_category: Mapped[str | None] = mapped_column(String(128), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    match_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    match_method: Mapped[str | None] = mapped_column(String(32))
    source_url: Mapped[str] = mapped_column(String(512))
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    clinic: Mapped["Clinic"] = relationship()
    branch: Mapped["ClinicBranch | None"] = relationship()
    service: Mapped["Service"] = relationship()
    doctor: Mapped["Doctor | None"] = relationship()


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(256), index=True)
    old_price: Mapped[int | None] = mapped_column(Integer)
    new_price: Mapped[int | None] = mapped_column(Integer)
    percent_change: Mapped[float | None] = mapped_column(Float)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
