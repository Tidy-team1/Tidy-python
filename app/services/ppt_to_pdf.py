# app/services/ppt_to_pdf.py
import subprocess
import os
import uuid

from app.services.font_loader import prepare_fonts_for_ppt


def convert_ppt_to_pdf(ppt_path: str, temp_dir: str) -> str:
    """
    PPT → PDF 변환
    PDF는 로컬 temp에만 저장하고 슬라이드 변환 후 삭제
    """
    os.makedirs(temp_dir, exist_ok=True)

    # 폰트 준비
    prepare_fonts_for_ppt(ppt_path)

    # 변환
    command = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", temp_dir,
        ppt_path,
    ]

    subprocess.run(command, check=True)

    # PDF 찾기
    pdf_files = [f for f in os.listdir(temp_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise FileNotFoundError("PDF 변환 실패")

    pdf_files.sort(key=lambda name: os.path.getmtime(os.path.join(temp_dir, name)), reverse=True)
    pdf_path = os.path.join(temp_dir, pdf_files[0])

    return pdf_path
