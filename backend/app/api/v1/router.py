from fastapi import APIRouter

from app.api.v1.endpoints import admin, analytics, search, services

api_router = APIRouter()
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
