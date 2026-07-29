from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.about import router as about_router

router = APIRouter()

@router.get("/")
def root():
    return {
        "message": "Welcome to VTU AI Study Portal 🚀"
    }

router.include_router(health_router)
router.include_router(about_router)