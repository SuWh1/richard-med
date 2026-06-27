from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParseRun(Base):
    __tablename__ = "parse_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    city: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="success")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_saved: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text)


class UnmatchedService(Base):
    __tablename__ = "unmatched_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_price_items.id", ondelete="SET NULL")
    )
    raw_name: Mapped[str] = mapped_column(String(512))
    suggested_service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL")
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
