"""Central aggregator for all v1 API endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, root

api_router = APIRouter()

api_router.include_router(root.router, tags=["Root"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
