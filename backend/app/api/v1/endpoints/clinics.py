from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clinics import ClinicDetail, ClinicServiceRow, ReviewRow
from app.services import clinics

router = APIRouter()


@router.get("/{clinic_id}", response_model=ClinicDetail)
def get_clinic(clinic_id: int, db: Session = Depends(get_db)) -> ClinicDetail:
    detail = clinics.clinic_detail(db, clinic_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return detail


@router.get("/{clinic_id}/services", response_model=list[ClinicServiceRow])
def get_clinic_services(
    clinic_id: int,
    include_stale: bool = False,
    db: Session = Depends(get_db),
) -> list[ClinicServiceRow]:
    if clinics.clinic_detail(db, clinic_id) is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinics.clinic_services(db, clinic_id, include_stale=include_stale)


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
