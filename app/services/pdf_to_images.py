import os
import uuid
import fitz  # PyMuPDF

def convert_pdf_to_images(pdf_path: str, output_dir: str) -> list:
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    paths = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=150)  # 150~200 DPI면 썸네일 충분
        filename = f"{uuid.uuid4()}_page_{page_index+1}.png"
        filepath = os.path.join(output_dir, filename)
        pix.save(filepath)
        paths.append(filepath)

    doc.close()
    return paths
