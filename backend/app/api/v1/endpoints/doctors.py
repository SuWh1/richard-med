from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.doctors import DoctorProfile, DoctorReviewPage
from app.services import doctors

router = APIRouter()


@router.get("/{doctor_id}", response_model=DoctorProfile)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)) -> DoctorProfile:
    profile = doctors.doctor_profile(db, doctor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return profile


@router.get("/{doctor_id}/reviews", response_model=DoctorReviewPage)
def get_doctor_reviews(
    doctor_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> DoctorReviewPage:
    return doctors.doctor_reviews(db, doctor_id, limit=limit, offset=offset)
