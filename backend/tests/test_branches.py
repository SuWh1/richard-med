from sqlalchemy import func, select

from app.models import Clinic, ClinicBranch
from app.scrapers.base import BranchHit
from app.services.branches import sync_branches


def _hits() -> list[BranchHit]:
    return [
        BranchHit("ext1", "Пункт 1", "Астана", "Адрес 1", 51.1, 71.4, "+7700", "Пн-Пт 08-16"),
        BranchHit("ext2", "Пункт 2", "Астана", "Адрес 2", 51.2, 71.5, None, None),
    ]


def test_should_sync_branches_and_create_the_clinic(db_session):
    added = sync_branches(db_session, "test_src", "Test Brand", _hits())
    assert added == 2

    clinic = db_session.scalars(
        select(Clinic).where(Clinic.source_name == "test_src", Clinic.name == "Test Brand")
    ).first()
    assert clinic is not None
    count = db_session.scalar(
        select(func.count()).select_from(ClinicBranch).where(ClinicBranch.clinic_id == clinic.id)
    )
    assert count == 2


def test_should_be_idempotent_and_update_coords_on_rerun(db_session):
    sync_branches(db_session, "test_src", "Test Brand", _hits())
    moved = [
        BranchHit("ext1", "Пункт 1", "Астана", "Адрес 1", 51.9, 71.9, "+7700", "Пн-Пт 08-16"),
        BranchHit("ext2", "Пункт 2", "Астана", "Адрес 2", 51.2, 71.5, None, None),
    ]
    added = sync_branches(db_session, "test_src", "Test Brand", moved)

    assert added == 0  # no new rows on rerun
    branch = db_session.scalars(
        select(ClinicBranch).where(ClinicBranch.address == "Адрес 1")
    ).first()
    assert branch.lat == 51.9  # coords refreshed in place
