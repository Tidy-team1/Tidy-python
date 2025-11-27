from pptx import Presentation
from app.services.storage_service import download_presentation
from app.utils.ppt_utils import extract_slide_json


def parse_ppt(space_id: int, pres_id: int):
    """
    1) S3 → PPTX 다운로드
    2) python-pptx 로드
    3) 슬라이드/요소 파싱
    """

    ppt_path = download_presentation(space_id, pres_id)   # /tmp/tmpxxxx.pptx

    prs = Presentation(ppt_path)

    slides_json = []
    for slide_index, slide in enumerate(prs.slides):
        slide_json = extract_slide_json(slide_index, slide)
        slides_json.append(slide_json)

    result = {
        "slideCount": len(slides_json),
        "slides": slides_json
    }

    return result
