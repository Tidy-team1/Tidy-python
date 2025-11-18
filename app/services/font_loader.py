# app/services/font_loader.py
import os
import uuid
import zipfile
import subprocess
from typing import List

FONT_DIR = os.path.expanduser("/usr/share/fonts/truetype/ppt-embedded")
os.makedirs(FONT_DIR, exist_ok=True)


def extract_embedded_fonts_from_ppt(ppt_path: str) -> List[str]:
    """
    PPTX 파일 안에서 임베디드된 폰트 파일(ppt/fonts/*.ttf|otf)을 추출해서
    컨테이너 내 폰트 디렉토리에 저장.
    """
    os.makedirs(FONT_DIR, exist_ok=True)
    extracted_paths: List[str] = []

    # pptx는 zip 구조
    with zipfile.ZipFile(ppt_path, "r") as zf:
        for name in zf.namelist():
            # embedded font 파트는 보통 ppt/fonts/ 아래에 위치
            if not name.lower().startswith("ppt/fonts/"):
                continue
            if not (name.lower().endswith(".ttf") or name.lower().endswith(".otf")):
                continue

            data = zf.read(name)
            out_name = f"{uuid.uuid4()}_{os.path.basename(name)}"
            out_path = os.path.join(FONT_DIR, out_name)
            with open(out_path, "wb") as f:
                f.write(data)
            extracted_paths.append(out_path)

    return extracted_paths


def refresh_font_cache():
    """
    fontconfig 캐시 갱신.
    폰트가 추가되었을 때 LibreOffice가 인식하도록 fc-cache 실행.
    """
    try:
        subprocess.run(["fc-cache", "-f", "-v"], check=False)
    except Exception as e:
        # 폰트 캐시 실패해도 전체 파이프라인이 터지진 않게만 함
        print(f"[font_loader] fc-cache 실행 중 오류: {e}")


def prepare_fonts_for_ppt(ppt_path: str) -> None:
    """
    PPT 변환 전에 호출할 함수.
    1) PPTX에서 embedded fonts 추출
    2) 추출된 폰트가 있다면 fc-cache로 등록
    """
    print(f"[font_loader] 폰트 준비 시작: {ppt_path}")
    embedded = extract_embedded_fonts_from_ppt(ppt_path)
    if embedded:
        print(f"[font_loader] 임베디드 폰트 {len(embedded)}개 추출 완료")
        refresh_font_cache()
    else:
        print("[font_loader] 임베디드 폰트 없음 (PPT 파일에 폰트 파일이 포함돼 있지 않음)")
