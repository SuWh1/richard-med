from sqlalchemy import Float, ForeignKey, String
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

    clinic: Mapped["Clinic"] = relationship(back_populates="branches")
