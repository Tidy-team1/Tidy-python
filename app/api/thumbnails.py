from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import tempfile
import boto3
from app.core.logger import logger
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images
from app.utils.s3_key_builder import original_ppt_key

router = APIRouter()
s3 = boto3.client("s3")

BUCKET = os.getenv("AWS_S3_BUCKET_NAME")


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

        logger.info(f"[Thumbnail Request] space={space_id}, pres={pres_id}")

        original_key = original_ppt_key(space_id, pres_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            ppt_local = os.path.join(tmpdir, "original.pptx")
            s3.download_file(BUCKET, original_key, ppt_local)

            # 1) PPT → PDF
            pdf_path = convert_ppt_to_pdf(ppt_local, tmpdir)

            # 2) PDF → 이미지 변환 & 이미지 → S3 저장까지 convert_pdf_to_images에서 수행됨
            thumbnail_keys = convert_pdf_to_images(pdf_path, space_id, pres_id)

            # 3) FastAPI에서 추가 업로드 없음
            return {"thumbnailKeys": thumbnail_keys}

    except Exception as e:
        logger.error(f"Thumbnail conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
