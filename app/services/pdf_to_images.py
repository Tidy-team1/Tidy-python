import os
import shutil
import fitz  # PyMuPDF

def convert_pdf_to_images(pdf_path: str, output_dir: str, presentation_id: str) -> list:
    os.makedirs(output_dir, exist_ok=True)
    presentation_dir = os.path.join(output_dir, presentation_id)
    if os.path.exists(presentation_dir):
        shutil.rmtree(presentation_dir)
    os.makedirs(presentation_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    paths = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=150)  # 150~200 DPI면 썸네일 충분
        filename = f"{page_index}.png"
        filepath = os.path.join(presentation_dir, filename)
        pix.save(filepath)
        paths.append(filepath)

    doc.close()
    return paths
