from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clinics import ClinicDetail, ClinicServiceRow
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
