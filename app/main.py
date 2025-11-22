from fastapi import FastAPI
from app.core.logger import setup_logger
from app.api.presentation_api import router as presentation_router
from app.api.thumbnails import router as thumbnails_router

setup_logger()

app = FastAPI()

# API 라우터 등록
app.include_router(thumbnails_router)
