from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/about")
def about():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "team": {
            "founder": settings.FOUNDER,
            "co_founder": settings.CO_FOUNDER
        }
    }