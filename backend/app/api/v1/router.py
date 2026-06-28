from fastapi import APIRouter, Depends

from app.api.v1.endpoints import admin, analytics, clinics, search, services
from app.core.auth import require_admin

api_router = APIRouter()
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(clinics.router, prefix="/clinics", tags=["clinics"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
# Admin endpoints (Source Health, Run Parser) require a valid Better Auth admin session.
api_router.include_router(
    admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)
