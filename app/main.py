from fastapi import FastAPI
from app.core.logger import setup_logger
from app.api.thumbnails import router as thumbnails_router
from app.api.ananlysis import router as analysis_router
from app.api.parsing import router as parsing_router

setup_logger()

app = FastAPI()

# API 라우터 등록
app.include_router(thumbnails_router)
app.include_router(analysis_router)
app.include_router(parsing_router)