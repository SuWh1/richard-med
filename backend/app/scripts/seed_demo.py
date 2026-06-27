import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    ParseRun,
    RawDocument,
    RawPriceItem,
    UnmatchedService,
)
from app.services.normalization import ServiceMatcher

SOURCES = ["kdl_olymp", "doq", "invitro"]

def _branch(city, address, lat, lng, phone, hours):
    return {
        "city": city,
        "address": address,
        "lat": lat,
        "lng": lng,
        "phone": phone,
        "working_hours": hours,
    }


CLINICS = [
    {
        "source": "kdl_olymp",
        "name": "KDL Olymp",
        "website_url": "https://kdlolymp.kz",
        "branches": [
            _branch("Астана", "пр. Кабанбай батыра, 53", 51.1282, 71.4307,
                    "+7 717 233 44 55", "Пн-Сб 07:00-17:00"),
            _branch("Алматы", "ул. Розыбакиева, 37", 43.2200, 76.8900,
                    "+7 727 233 44 55", "Пн-Сб 07:00-16:00"),
        ],
    },
    {
        "source": "doq",
        "name": "DOQ Clinic",
        "website_url": "https://doq.kz",
        "branches": [
            _branch("Астана", "ул. Сыганак, 18", 51.1490, 71.4250,
                    "+7 717 255 66 77", "Пн-Пт 08:00-20:00"),
        ],
    },
    {
        "source": "invitro",
        "name": "Invitro",
        "website_url": "https://invitro.kz",
        "branches": [
            _branch("Астана", "пр. Республики, 5", 51.1700, 71.4200,
                    "+7 717 277 88 99", "Ежедневно 08:00-18:00"),
            _branch("Алматы", "ул. Достык, 89", 43.2350, 76.9550,
                    "+7 727 277 88 99", "Ежедневно 08:00-18:00"),
        ],
    },
]

# (source, city, raw clinic service name, price_kzt, age in days). Raw names are matched
# to the catalog through the waterfall — this exercises the real normalization path.
PRICE_ROWS = [
    ("kdl_olymp", "Астана", "Общий анализ крови (ОАК), 5 классов", 1880, 1),
    ("kdl_olymp", "Астана", "Глюкоза (сахар крови)", 950, 1),
    ("kdl_olymp", "Астана", "ТТГ тиреотропный гормон", 2600, 1),
    ("kdl_olymp", "Астана", "Витамин D", 8200, 1),
    ("kdl_olymp", "Астана", "Ферритин", 2900, 1),
    ("kdl_olymp", "Алматы", "Общий анализ крови (ОАК), 5 классов", 2050, 2),
    ("kdl_olymp", "Алматы", "Глюкоза (сахар крови)", 1100, 2),
    ("invitro", "Астана", "Клинический анализ крови (CBC)", 2200, 3),
    ("invitro", "Астана", "Глюкоза крови", 1050, 3),
    ("invitro", "Астана", "УЗИ органов брюшной полости (ОБП)", 9500, 15),
    ("invitro", "Астана", "ЭКГ с расшифровкой", 3200, 3),
    ("invitro", "Алматы", "Клинический анализ крови (CBC)", 2400, 40),
    ("invitro", "Алматы", "УЗИ органов брюшной полости (ОБП)", 8800, 40),
    ("doq", "Астана", "Прием врача-терапевта", 7000, 1),
    ("doq", "Астана", "Консультация педиатра", 6500, 1),
    ("doq", "Астана", "Прием гинеколога", 8000, 2),
    ("doq", "Астана", "Прием терапевта повторный", 5000, 2),
]

# A raw name that intentionally won't match, to populate the unmatched-review queue.
UNMATCHED_ROWS = [("doq", "Астана", "Комплексная программа Check-up Премиум", 95000, 1)]


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _clear(session: Session) -> None:
    src_clinics = select(Clinic.id).where(Clinic.source_name.in_(SOURCES))
    session.execute(
        delete(ClinicServicePrice).where(
            ClinicServicePrice.clinic_id.in_(src_clinics)
        )
    )
    session.execute(delete(UnmatchedService))
    raw_docs = select(RawDocument.id).where(RawDocument.source_name.in_(SOURCES))
    session.execute(
        delete(RawPriceItem).where(RawPriceItem.raw_document_id.in_(raw_docs))
    )
    session.execute(delete(RawDocument).where(RawDocument.source_name.in_(SOURCES)))
    session.execute(delete(Clinic).where(Clinic.source_name.in_(SOURCES)))
    session.execute(delete(ParseRun).where(ParseRun.source_name.in_(SOURCES)))
    session.flush()


def seed_demo(session: Session) -> dict:
    _clear(session)
    now = datetime.now(UTC)

    clinics: dict[str, Clinic] = {}
    branches: dict[tuple[str, str], ClinicBranch] = {}
    for spec in CLINICS:
        clinic = Clinic(
            name=spec["name"],
            website_url=spec["website_url"],
            source_name=spec["source"],
        )
        session.add(clinic)
        session.flush()
        clinics[spec["source"]] = clinic
        for b in spec["branches"]:
            branch = ClinicBranch(clinic_id=clinic.id, **b)
            session.add(branch)
            session.flush()
            branches[(spec["source"], b["city"])] = branch

    docs: dict[tuple[str, str], RawDocument] = {}

    def get_doc(source: str, city: str) -> RawDocument:
        key = (source, city)
        if key not in docs:
            url = f"{clinics[source].website_url}/pricelist/{city.lower()}"
            html = f"<html><body>price list for {source} {city}</body></html>"
            doc = RawDocument(
                source_name=source,
                source_url=url,
                city=city,
                content_hash=_hash(html + str(now)),
                raw_html=html,
                status_code=200,
                fetched_at=now,
            )
            session.add(doc)
            session.flush()
            docs[key] = doc
        return docs[key]

    matcher = ServiceMatcher(session)
    saved = 0
    unmatched = 0

    for source, city, raw_name, price, age in PRICE_ROWS:
        doc = get_doc(source, city)
        item = RawPriceItem(
            raw_document_id=doc.id,
            clinic_raw=clinics[source].name,
            service_name_raw=raw_name,
            price_raw=str(price),
        )
        session.add(item)
        session.flush()

        result = matcher.match(raw_name)
        if result.service_id is None:
            session.add(
                UnmatchedService(
                    raw_item_id=item.id,
                    raw_name=raw_name,
                    confidence=result.confidence,
                )
            )
            unmatched += 1
            continue

        branch = branches[(source, city)]
        session.add(
            ClinicServicePrice(
                clinic_id=clinics[source].id,
                branch_id=branch.id,
                service_id=result.service_id,
                city=city,
                raw_price_item_id=item.id,
                price_kzt=price,
                service_name_raw=raw_name,
                content_hash=doc.content_hash,
                match_confidence=result.confidence,
                match_method=result.method,
                source_url=doc.source_url,
                parsed_at=now - timedelta(days=age),
                is_active=True,
            )
        )
        saved += 1

    for source, city, raw_name, price, _age in UNMATCHED_ROWS:
        doc = get_doc(source, city)
        item = RawPriceItem(
            raw_document_id=doc.id,
            clinic_raw=clinics[source].name,
            service_name_raw=raw_name,
            price_raw=str(price),
        )
        session.add(item)
        session.flush()
        result = matcher.match(raw_name)
        session.add(
            UnmatchedService(
                raw_item_id=item.id,
                raw_name=raw_name,
                suggested_service_id=result.service_id,
                confidence=result.confidence,
            )
        )
        unmatched += 1

    for source in SOURCES:
        city = "Астана"
        found = sum(1 for r in PRICE_ROWS if r[0] == source)
        session.add(
            ParseRun(
                source_name=source,
                city=city,
                status="success",
                finished_at=now,
                items_found=found,
                items_saved=sum(
                    1
                    for r in PRICE_ROWS
                    if r[0] == source and matcher.match(r[2]).service_id is not None
                ),
            )
        )

    return {"prices_saved": saved, "unmatched": unmatched}


def main() -> None:
    session = SessionLocal()
    try:
        stats = seed_demo(session)
        session.commit()
    finally:
        session.close()
    print(f"prices saved: {stats['prices_saved']}, unmatched queued: {stats['unmatched']}")


if __name__ == "__main__":
    main()
