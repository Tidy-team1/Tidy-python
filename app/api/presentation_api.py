from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images
from app.core.logger import logger

router = APIRouter()

class ThumbnailRequest(BaseModel):
    pptPath: str
    outputDir: str

@router.post("/presentations/{presentation_id}/thumbnails")
async def convert_ppt(
    presentation_id: int,
    req: ThumbnailRequest
):
    try:
        logger.info(f"Thumbnail conversion request: id={presentation_id}, pptPath={req.pptPath}")

        if not os.path.exists(req.pptPath):
            raise HTTPException(status_code=400, detail=f"PPT file not found: {req.pptPath}")

        # 1. PPT → PDF
        pdf_path = convert_ppt_to_pdf(req.pptPath, req.outputDir)

        # 2. PDF → 이미지
        images = convert_pdf_to_images(pdf_path, req.outputDir, str(presentation_id))

        logger.info(f"Conversion complete: {len(images)} pages")
        return {"thumbnailPaths": images}

    except Exception as e:
        logger.error(f"Thumbnail conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
