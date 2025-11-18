# app/services/ppt_to_pdf.py
import subprocess
import os
import uuid

from app.services.font_loader import prepare_fonts_for_ppt


def convert_ppt_to_pdf(ppt_path: str, output_dir: str) -> str:
    """
    PPT/PPTX 파일을 PDF로 변환.
    - 변환 전에 PPT에 임베디드된 폰트를 시스템에 등록한다.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1) 폰트 준비
    prepare_fonts_for_ppt(ppt_path)

    # 2) LibreOffice 변환
    command = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        ppt_path,
    ]

    subprocess.run(command, check=True)

    # 3) outdir 내에서 PDF 찾기 (LibreOffice는 원래 파일명을 기반으로 생성)
    pdf_candidates = [
        f for f in os.listdir(output_dir) if f.lower().endswith(".pdf")
    ]
    if not pdf_candidates:
        raise FileNotFoundError("PDF 변환 실패: output_dir에 PDF가 생성되지 않았습니다.")

    # 가장 최근 파일 하나 고르거나, 파일명이 원본과 매칭되는 걸 골라도 됨
    pdf_candidates.sort(key=lambda name: os.path.getmtime(os.path.join(output_dir, name)), reverse=True)
    pdf_path = os.path.join(output_dir, pdf_candidates[0])
    return pdf_path
