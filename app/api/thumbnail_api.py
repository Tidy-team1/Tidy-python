from fastapi import APIRouter, UploadFile, HTTPException
from app.services.thumbnail.extract import generate_thumbnails
from app.core.logger import logger

router = APIRouter()

@router.post("/thumbnail")
async def extract_thumbnail(file: UploadFile):
    try:
        logger.info(f"Thumbnail request received: {file.filename}")
        result = await generate_thumbnails(file)
        return {"thumbnails": result}
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
