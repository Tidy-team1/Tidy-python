# app/services/pdf_to_images.py

import fitz
from typing import List


def convert_pdf_to_images(pdf_path: str, dpi: int = 150) -> List[bytes]:
    """
    PDF 파일을 슬라이드 순서대로 PNG 이미지 바이트 리스트로 변환한다.
    - S3 업로드는 여기서 하지 않는다.
    - 호출자가 version 정보에 맞게 S3 저장을 담당한다.
    """
    doc = fitz.open(pdf_path)
    images: List[bytes] = []

    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)
    finally:
        doc.close()

    return images
