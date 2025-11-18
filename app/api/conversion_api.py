from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.thumbnail.extract import generate_thumbnails

router = APIRouter(tags=["conversion"])


@router.post("/convert-ppt")
async def convert_ppt(file: UploadFile = File(...)):
    """
    PPT/PPTX 파일을 업로드 받아 이미지로 변환한다.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일 이름이 필요합니다.")

    try:
        images = await generate_thumbnails(file)
        return {"pages": images, "count": len(images)}
    finally:
        file.file.close()

