from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    clinics,
    doctors,
    search,
    services,
    sources,
)
from app.core.auth import require_admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(clinics.router, prefix="/clinics", tags=["clinics"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
# Admin endpoints (Source Health, Run Parser) require an authenticated admin session.
api_router.include_router(
    admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)
