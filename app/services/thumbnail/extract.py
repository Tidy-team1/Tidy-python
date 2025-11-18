import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile

from app.core.config import settings
from app.services.pdf_to_images import convert_pdf_to_images
from app.services.ppt_to_pdf import convert_ppt_to_pdf


async def generate_thumbnails(file: UploadFile) -> List[str]:
    """
    업로드된 PPT/PPTX 파일을 임시 디렉터리에 저장한 뒤
    PDF와 이미지로 변환하여 이미지 경로 리스트를 반환한다.
    """
    suffix = Path(file.filename or "presentation.pptx").suffix or ".pptx"
    temp_name = f"{uuid.uuid4()}{suffix}"
    temp_path = settings.temp_dir / temp_name

    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with temp_path.open("wb") as buffer:
        file.file.seek(0)
        shutil.copyfileobj(file.file, buffer)

    pdf_path = convert_ppt_to_pdf(str(temp_path), str(settings.temp_dir))

    target_dir = settings.output_dir / temp_path.stem
    target_dir.mkdir(parents=True, exist_ok=True)
    images = convert_pdf_to_images(pdf_path, str(target_dir))

    return images

