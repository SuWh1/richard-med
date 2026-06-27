from fastapi import APIRouter

from app.api.v1.endpoints import admin, search, services

api_router = APIRouter()
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
