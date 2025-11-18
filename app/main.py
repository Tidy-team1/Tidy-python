from fastapi import FastAPI

from app.api.routes import api_router
from app.core.logger import setup_logger


def create_app() -> FastAPI:
    setup_logger()

    application = FastAPI(title="Tidy Python Service")
    application.include_router(api_router)

    @application.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    return application


app = create_app()
