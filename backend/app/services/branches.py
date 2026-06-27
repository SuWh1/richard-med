from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Clinic, ClinicBranch
from app.scrapers.base import BranchHit


def sync_branches(
    session: Session, source_name: str, brand_name: str, hits: list[BranchHit]
) -> int:
    """Upsert a clinic's points into clinic_branches. Returns how many were newly added.

    Idempotent — deduped by (clinic, city, address); existing rows have coords/contacts
    refreshed in place so re-running the import never duplicates a point.
    """
    clinic = session.scalars(
        select(Clinic).where(Clinic.source_name == source_name, Clinic.name == brand_name)
    ).first()
    if clinic is None:
        clinic = Clinic(name=brand_name, source_name=source_name)
        session.add(clinic)
        session.flush()

    added = 0
    for hit in hits:
        existing = session.scalars(
            select(ClinicBranch).where(
                ClinicBranch.clinic_id == clinic.id,
                ClinicBranch.city == hit.city,
                ClinicBranch.address == hit.address,
            )
        ).first()
        if existing is not None:
            existing.lat = hit.lat
            existing.lng = hit.lng
            existing.phone = hit.phone
            existing.working_hours = hit.working_hours
            continue
        session.add(
            ClinicBranch(
                clinic_id=clinic.id,
                city=hit.city,
                address=hit.address,
                lat=hit.lat,
                lng=hit.lng,
                phone=hit.phone,
                working_hours=hit.working_hours,
            )
        )
        added += 1
    return added
