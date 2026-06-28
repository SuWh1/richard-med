from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clinics import (
    ClinicDetail,
    ClinicListPage,
    ClinicServicesPage,
    ReviewRow,
)
from app.services import clinics

router = APIRouter()


@router.get("", response_model=ClinicListPage)
def list_clinics(
    q: str | None = Query(None, description="Filter by clinic name substring"),
    city: str | None = Query(None),
    source: str | None = Query(None),
    sort: str = Query("name", pattern="name|rating|services"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ClinicListPage:
    return clinics.list_clinics(
        db, q=q, city=city, source=source, sort=sort, limit=limit, offset=offset
    )


@router.get("/{clinic_id}", response_model=ClinicDetail)
def get_clinic(clinic_id: int, db: Session = Depends(get_db)) -> ClinicDetail:
    detail = clinics.clinic_detail(db, clinic_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return detail


@router.get("/{clinic_id}/services", response_model=ClinicServicesPage)
def get_clinic_services(
    clinic_id: int,
    q: str | None = Query(None, description="Filter by service name substring"),
    category: str | None = Query(None),
    include_stale: bool = False,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ClinicServicesPage:
    if clinics.clinic_detail(db, clinic_id) is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinics.clinic_services_page(
        db,
        clinic_id,
        q=q,
        category=category,
        include_stale=include_stale,
        limit=limit,
        offset=offset,
    )


@router.get("/{clinic_id}/reviews", response_model=list[ReviewRow])
def get_clinic_reviews(
    clinic_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[ReviewRow]:
    if clinics.clinic_detail(db, clinic_id) is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinics.clinic_reviews(db, clinic_id, limit=limit, offset=offset)
