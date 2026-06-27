import os
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Service, ServiceAlias, ServiceCategory
from app.services.normalization import ServiceMatcher

_DEFAULT_BLUEPRINT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "MedServicePrice_Winning_Blueprint.xlsx"
)
BLUEPRINT_PATH = Path(os.getenv("BLUEPRINT_PATH", _DEFAULT_BLUEPRINT))
CATALOG_SHEET = "Services_Clean"

# Canonical catalog name -> synonyms, from blueprint sheet 07_Normalization. The
# canonical is matched to a real service via the waterfall; ОАК has no single
# canonical row, so we anchor it to a concrete variant.
SYNONYM_GROUPS: list[tuple[str, list[str]]] = [
    ("ОАК 5 классов", ["ОАК", "CBC", "клинический анализ крови", "общий анализ крови"]),
    ("Общий анализ мочи", ["ОАМ", "анализ мочи общий", "моча общий анализ"]),
    ("Глюкоза (кровь)", ["сахар крови", "glucose", "глюкоза в крови", "глюкоза"]),
    ("ТТГ тиреотропный гормон", ["ТТГ", "тиреотропный гормон", "TSH"]),
    ("Витамин D", ["25-OH витамин D", "vitamin D", "кальциферол"]),
    ("Ферритин", ["ferritin", "железо запас"]),
    ("УЗИ брюшной полости", ["УЗИ ОБП", "УЗИ живота", "ultrasound abdomen"]),
    ("ЭКГ", ["электрокардиограмма", "ECG"]),
    ("Прием терапевта", ["терапевт", "консультация терапевта"]),
    ("Прием педиатра", ["педиатр", "консультация педиатра"]),
    ("Прием гинеколога", ["акушер-гинеколог", "гинеколог", "консультация гинеколога"]),
    ("Прием невропатолога", ["невролог", "невропатолог", "консультация невролога"]),
    ("Прием кардиолога", ["кардиолог", "консультация кардиолога"]),
    ("Прием эндокринолога", ["эндокринолог", "консультация эндокринолога"]),
    ("Прием уролога", ["уролог", "консультация уролога"]),
    ("Прием дерматолога", ["дерматолог", "дерматовенеролог", "консультация дерматолога"]),
    ("Прием окулиста", ["офтальмолог", "окулист", "консультация офтальмолога"]),
]


@dataclass
class ImportStats:
    services_inserted: int = 0
    services_updated: int = 0
    aliases_seeded: int = 0
    groups_unresolved: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.groups_unresolved is None:
            self.groups_unresolved = []


def read_services_clean(path: Path = BLUEPRINT_PATH) -> list[dict]:
    """Read the Services_Clean sheet into a list of row dicts (header auto-located)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[CATALOG_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header_idx = next(i for i, r in enumerate(rows) if r and r[0] == "service_key")
    header = rows[header_idx]
    out = []
    for raw in rows[header_idx + 1 :]:
        if not raw or not raw[0]:
            continue
        out.append(dict(zip(header, raw, strict=False)))
    return out


def import_catalog(session: Session, path: Path = BLUEPRINT_PATH) -> ImportStats:
    """Upsert services from Services_Clean (idempotent by service_key), then seed aliases."""
    stats = ImportStats()
    existing = {s.service_key: s for s in session.execute(select(Service)).scalars()}

    for row in read_services_clean(path):
        key = str(row["service_key"]).strip()
        name = (row["name_ru"] or "").strip()
        if not name:
            continue
        category = ServiceCategory(row["category"])
        specialty = (row.get("specialty") or None) and str(row["specialty"]).strip()
        code = (row.get("tarificatr_code") or None) and str(row["tarificatr_code"]).strip()

        service = existing.get(key)
        if service is None:
            session.add(
                Service(
                    service_key=key,
                    name_ru=name,
                    category=category,
                    specialty=specialty,
                    tarificatr_code=code,
                )
            )
            stats.services_inserted += 1
        else:
            service.name_ru = name
            service.category = category
            service.specialty = specialty
            service.tarificatr_code = code
            stats.services_updated += 1

    session.flush()
    stats.aliases_seeded, stats.groups_unresolved = seed_aliases(session, path)
    return stats


def seed_aliases(session: Session, path: Path = BLUEPRINT_PATH) -> tuple[int, list[str]]:
    """Seed service_aliases from the synonym groups + per-row suggested_alias_seed.

    Idempotent: removes prior seed aliases before re-inserting.
    """
    session.execute(
        delete(ServiceAlias).where(ServiceAlias.source.in_(["seed", "catalog_seed"]))
    )
    session.flush()

    matcher = ServiceMatcher(session)
    seeded = 0
    unresolved: list[str] = []
    seen: set[tuple[int, str]] = set()

    def add_alias(service_id: int, alias: str, source: str, confidence: float) -> None:
        nonlocal seeded
        cleaned = alias.strip()
        if not cleaned:
            return
        dedup_key = (service_id, cleaned.lower())
        if dedup_key in seen:
            return
        seen.add(dedup_key)
        session.add(
            ServiceAlias(
                service_id=service_id,
                alias=cleaned,
                source=source,
                confidence=confidence,
            )
        )
        seeded += 1

    for canonical, synonyms in SYNONYM_GROUPS:
        result = matcher.match(canonical)
        if result.service_id is None:
            unresolved.append(canonical)
            continue
        for syn in synonyms:
            add_alias(result.service_id, syn, "seed", 0.95)

    key_to_id = {
        s.service_key: s.id for s in session.execute(select(Service)).scalars()
    }
    for row in read_services_clean(path):
        seed = row.get("suggested_alias_seed")
        if not seed:
            continue
        sid = key_to_id.get(str(row["service_key"]).strip())
        if sid is None:
            continue
        for syn in str(seed).split(";"):
            add_alias(sid, syn, "catalog_seed", 0.9)

    session.flush()
    return seeded, unresolved
