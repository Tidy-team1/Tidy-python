from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images
from app.core.logger import logger
from app.core.config import settings

router = APIRouter()

@router.post("/presentations/{presentation_id}/thumbnails")
async def convert_ppt(
    presentation_id: int,
    file: UploadFile = File(...),
):
    try:
        logger.info(f"Thumbnail conversion request received: presentation_id={presentation_id}, filename={file.filename}")
        
        # 1. temp에 파일 저장
        input_path = os.path.join(settings.temp_dir, file.filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 2. PPT → PDF
        pdf_path = convert_ppt_to_pdf(input_path, str(settings.temp_dir))

        # 3. PDF → 이미지
        images = convert_pdf_to_images(pdf_path, str(settings.output_dir), str(presentation_id))

        logger.info(f"Thumbnail conversion completed: {len(images)} pages generated")
        return {"pages": images}
    except Exception as e:
        logger.error(f"Thumbnail conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

