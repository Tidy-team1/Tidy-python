# app/utils/s3_key_builder.py

BASE = "spaces"

def base_path(space_id: int, presentation_id: int) -> str:
    """
    기본 경로: spaces/{spaceId}/presentations/{presentationId}
    """
    return f"{BASE}/{space_id}/presentations/{presentation_id}"


# =========================
# Original PPTX
# =========================

def original_ppt_key(space_id: int, presentation_id: int) -> str:
    """
    원본 PPTX 파일 (업로드된 파일 그대로)
    """
    return f"{base_path(space_id, presentation_id)}/original/presentation.pptx"


# =========================
# Slides (이미지)
# =========================

def slide_image_key(space_id: int, presentation_id: int, slide_no: int) -> str:
    """
    슬라이드 이미지: slide_1.png, slide_2.png ...
    """
    return f"{base_path(space_id, presentation_id)}/slides/slide_{slide_no}.png"


# =========================
# Thumbnails
# =========================

def thumbnail_key(space_id: int, presentation_id: int, slide_no: int) -> str:
    """
    썸네일 이미지: thumb_1.png, thumb_2.png ...
    """
    return f"{base_path(space_id, presentation_id)}/thumbnails/thumb_{slide_no}.png"


# =========================
# Analysis Files (AI 결과물)
# =========================

def analysis_key(space_id: int, presentation_id: int, filename: str) -> str:
    """
    분석 결과 파일 (JSON 등)
    예: layout.json, text.json, style.json ...
    """
    return f"{base_path(space_id, presentation_id)}/analysis/{filename}"


# =========================
# Metadata
# =========================

def metadata_key(space_id: int, presentation_id: int) -> str:
    """
    프레젠테이션 전체 정보 메타데이터
    예: 총 슬라이드 수, 제목, 폰트 리스트 등
    """
    return f"{base_path(space_id, presentation_id)}/metadata.json"
