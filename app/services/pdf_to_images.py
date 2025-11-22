import fitz
from app.services.storage_service import save_file
from app.utils.s3_key_builder import slide_image_key

def convert_pdf_to_images(pdf_path: str, space_id: int, presentation_id: int) -> list:
    doc = fitz.open(pdf_path)
    results = []

    for idx in range(len(doc)):
        page = doc.load_page(idx)
        pix = page.get_pixmap(dpi=150)

        img_bytes = pix.tobytes("png")

        # S3 key 생성
        key = slide_image_key(space_id, presentation_id, idx + 1)

        # 저장 (하지만 반환은 URL이 아니라 key)
        save_file(key, img_bytes)

        # ✔ key만 append한다
        results.append(key)

    doc.close()
    return results
