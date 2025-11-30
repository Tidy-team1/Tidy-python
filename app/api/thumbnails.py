from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import tempfile
from app.core.logger import logger
from app.core.config import settings
from app.services.storage_service import get_s3_client
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images
from app.utils.s3_key_builder import original_ppt_key

from pptx import Presentation
from app.utils.ppt_utils import emu_to_px

router = APIRouter()
class ThumbnailRequest(BaseModel):
    spaceId: int
    presentationId: int

@router.post("/presentations/{presentation_id}/thumbnails")
async def convert_ppt(
    presentation_id: int,
    req: ThumbnailRequest
):
    try:
        space_id = req.spaceId
        pres_id = req.presentationId

        original_key = original_ppt_key(space_id, pres_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            ppt_local = os.path.join(tmpdir, "original.pptx")

            s3 = get_s3_client()
            s3.download_file(settings.AWS_S3_BUCKET_NAME, original_key, ppt_local)

            # 🎯 슬라이드 크기 추출
            prs = Presentation(ppt_local)
            slide_width_px = emu_to_px(prs.slide_width)
            slide_height_px = emu_to_px(prs.slide_height)

            slide_sizes = [
                {
                    "index": idx,
                    "width": slide_width_px,
                    "height": slide_height_px
                }
                for idx, _ in enumerate(prs.slides, start=0)
            ]

            # 1) PPT → PDF
            pdf_path = convert_ppt_to_pdf(ppt_local, tmpdir)

            # 2) PDF → 이미지 변환 & 업로드
            thumbnail_keys = convert_pdf_to_images(pdf_path, space_id, pres_id)

            return {
                "thumbnailKeys": thumbnail_keys,
                "slides": slide_sizes
            }

    except Exception as e:
        logger.error(f"Thumbnail conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
