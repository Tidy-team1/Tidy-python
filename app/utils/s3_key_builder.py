# app/utils/s3_key_builder.py

BASE = "spaces"


def base_path(space_id: int, presentation_id: int) -> str:
    """
    기본 경로: spaces/{spaceId}/presentations/{presentationId}
    """
    return f"{BASE}/{space_id}/presentations/{presentation_id}"


# =========================
# Versioned PPTX
# =========================

def pptx_key_for_version(space_id: int, presentation_id: int, version: int) -> str:
    """
    버전별 PPTX 파일
    예) spaces/{spaceId}/presentations/{presentationId}/v{version}/ppt/presentation.pptx
    """
    return f"{base_path(space_id, presentation_id)}/v{version}/ppt/presentation.pptx"


# =========================
# Versioned Slides (이미지)
# =========================

def slide_image_key_for_version(
    space_id: int,
    presentation_id: int,
    version: int,
    slide_idx: int,
) -> str:
    """
    버전별 슬라이드 이미지
    예) .../v{version}/slides/{slide_idx}.png
    """
    return f"{base_path(space_id, presentation_id)}/v{version}/slides/{slide_idx}.png"


# =========================
# 원본 PPT (v0 alias)
# =========================

def original_ppt_key(space_id: int, presentation_id: int) -> str:
    """
    업로드된 원본 PPTX는 v0 으로 간주한다.
    기존 original/ 경로 대신 이 함수를 사용한다.
    """
    return pptx_key_for_version(space_id, presentation_id, 0)


# =========================
# (레거시) 버전 없는 slide 이미지 키
# =========================

def slide_image_key(space_id: int, presentation_id: int, slide_idx: int) -> str:
    """
    과거 코드 호환을 위한 래퍼.
    버전 개념이 없던 시절의 slide 이미지 경로를 사용하던 코드가
    있더라도 v0 기준으로 동작하도록 매핑한다.
    (가능하면 slide_image_key_for_version(...) 으로 교체할 것)
    """
    return slide_image_key_for_version(space_id, presentation_id, 0, slide_idx)


# =========================
# Analysis Files (AI 결과물)
# =========================

def analysis_key(space_id: int, presentation_id: int, filename: str) -> str:
    """
    분석 결과 파일 (JSON 등)
    예: layout.json, text.json, style.json ...
    version과는 독립적으로 관리한다고 가정.
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
