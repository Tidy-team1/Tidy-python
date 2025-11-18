from fastapi import APIRouter

from app.api.conversion_api import router as conversion_router
from app.api.thumbnail_api import router as thumbnail_router

api_router = APIRouter()

api_router.include_router(conversion_router)
api_router.include_router(thumbnail_router)

