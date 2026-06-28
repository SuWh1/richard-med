from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Clinic, ClinicServicePrice
from app.scrapers.registry import available_sources
from app.services.admin import _age_days, _freshness

# Public-facing metadata per source: (display_name, kind, description, website).
SOURCE_META: dict[str, tuple[str, str, str, str]] = {
    "kdl_olymp": (
        "KDL Olymp",
        "Лаборатория",
        "Крупнейшая сеть лабораторий — анализы по всем городам Казахстана.",
        "https://kdlolymp.kz",
    ),
    "invitro": (
        "Invitro",
        "Лаборатория",
        "Сеть независимых медицинских лабораторий.",
        "https://invitro.kz",
    ),
    "doq": (
        "DOQ",
        "Врачи и клиники",
        "Приёмы врачей и медицинские центры.",
        "https://doq.kz",
    ),
    "helix": (
        "Helix",
        "Лаборатория",
        "Лабораторная диагностика.",
        "https://helix.kz",
    ),
}


@dataclass(frozen=True)
class SourceStat:
    name: str
    display_name: str
    kind: str
    description: str
    website: str
    clinics: int
    prices: int
    cities: int
    last_parsed_at: datetime | None
    freshness: str | None


def sources_overview(session: Session) -> list[SourceStat]:
    now = datetime.now(UTC)
    out: list[SourceStat] = []

    for name in available_sources():
        clinics = session.scalar(
            select(func.count(Clinic.id)).where(Clinic.source_name == name)
        )
        if not clinics:
            continue

        prices, cities, last_parsed = session.execute(
            select(
                func.count(ClinicServicePrice.id),
                func.count(func.distinct(ClinicServicePrice.city)),
                func.max(ClinicServicePrice.parsed_at),
            )
            .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
            .where(
                Clinic.source_name == name,
                ClinicServicePrice.is_active.is_(True),
            )
        ).one()
        if not prices:
            continue

        display_name, kind, description, website = SOURCE_META.get(
            name, (name, "Источник", "", "")
        )
        freshness = _freshness(_age_days(last_parsed, now)) if last_parsed else None
        out.append(
            SourceStat(
                name=name,
                display_name=display_name,
                kind=kind,
                description=description,
                website=website,
                clinics=int(clinics),
                prices=int(prices),
                cities=int(cities),
                last_parsed_at=last_parsed,
                freshness=freshness,
            )
        )

    out.sort(key=lambda s: s.prices, reverse=True)
    return out
