import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ServiceCategory(str, enum.Enum):
    laboratory = "лаборатория"
    doctor_visit = "приём врача"
    diagnostic = "диагностика"
    procedure = "процедура"
    # Internal quarantine for auto-grown rows the pipeline can't confidently classify.
    # Hidden from default user search; surfaced in the admin catalog for review.
    other = "прочее"


def _category_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(512), index=True)
    category: Mapped[ServiceCategory] = mapped_column(
        Enum(ServiceCategory, values_callable=_category_values, name="service_category")
    )
    specialty: Mapped[str | None] = mapped_column(String(256))
    tarificatr_code: Mapped[str | None] = mapped_column(String(64))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    aliases: Mapped[list["ServiceAlias"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )


class ServiceAlias(Base):
    __tablename__ = "service_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), index=True
    )
    alias: Mapped[str] = mapped_column(String(512), index=True)
    source: Mapped[str] = mapped_column(String(64), default="seed")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    notes: Mapped[str | None] = mapped_column(Text)

    service: Mapped["Service"] = relationship(back_populates="aliases")
