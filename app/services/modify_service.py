# app/services/modify_service.py

import json
import os
import tempfile

from pptx import Presentation
from pptx.util import Pt

from app.core.config import settings
from app.core.logger import logger
from app.utils.s3_utils import download_from_s3, upload_to_s3
from app.services.storage_service import save_file
from app.utils.s3_key_builder import (
    pptx_key_for_version,
    slide_image_key_for_version,
)
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images

from pptx.enum.text import MSO_AUTO_SIZE, MSO_VERTICAL_ANCHOR
from pptx.util import Pt


def process_modify(batch):
    """
    전체 수정 작업 메인 엔트리:
    - baseVersion PPTX 불러오기
    - payload.items의 피드백을 차례대로 적용
    - targetVersion PPTX / 이미지 생성 및 업로드
    - 최종 ModifyResult(dict) 반환
    """
    pres_id = batch.presentationId
    space_id = batch.spaceId

    base_v = batch.baseVersion
    target_v = batch.targetVersion

    with tempfile.TemporaryDirectory() as tmpdir:
        base_ppt_path = os.path.join(tmpdir, "base.pptx")
        target_ppt_path = os.path.join(tmpdir, "target.pptx")

        # 1) baseVersion PPT 다운로드
        download_from_s3(
            pptx_key_for_version(space_id, pres_id, base_v),
            base_ppt_path
        )

        prs = Presentation(base_ppt_path)

        # 2) payload.items 반복 → 슬라이드별 수정
        for item in batch.items:
            apply_single_feedback(prs, item)

        # 3) targetVersion PPT 저장
        prs.save(target_ppt_path)

        # 4) target PPT S3 Key
        ppt_key = pptx_key_for_version(space_id, pres_id, target_v)

        # 5) PPT 업로드
        upload_to_s3(
            src_path=target_ppt_path,
            s3_key=ppt_key,
        )

        # 6) PPT → PDF
        pdf_path = convert_ppt_to_pdf(target_ppt_path, tmpdir)

        # 7) PDF → 이미지 바이트 리스트
        image_bytes_list = convert_pdf_to_images(pdf_path)
        slide_count = len(image_bytes_list)

        # 8) 이미지 업로드
        for idx, img_bytes in enumerate(image_bytes_list):
            key = slide_image_key_for_version(space_id, pres_id, target_v, idx)
            save_file(key, img_bytes)

        # 9) slidePrefix
        slide_prefix = f"spaces/{space_id}/presentations/{pres_id}/v{target_v}/slides/"

        # 10) 결과 반환(JSON으로 직렬화됨)
        return {
            "slideCount": slide_count,
            "pptS3Key": ppt_key,
            "slidePrefix": slide_prefix
        }


def apply_single_feedback(prs, item):
    slide = prs.slides[item.slideIndex]

    # ----- detailsJson 파싱 -----
    details_raw = item.detailsJson or "{}"
    details = None

    try:
        # 1차 loads (escape 제거)
        loaded = json.loads(details_raw)

        # loaded가 문자열이면 → 2차 loads 필요
        if isinstance(loaded, str):
            details = json.loads(loaded)
        else:
            details = loaded

    except Exception:
        details = {}
        logger.error(f"[MODIFY] Failed to parse detailsJson: {details_raw}")

    logger.info(
        f"[MODIFY] Apply type='{item.type}', slide={item.slideIndex}, shapeId={item.shapeId}, details={details}"
    )

    # ----- 타입 라우팅 -----
    if item.type == "font_consistency":
        apply_font_consistency(slide, item, details)

    elif item.type == "align_center":
        apply_align_center(slide, item)

    elif item.type == "spelling_grammar":
        apply_text_replacement(slide, item, details)

    else:
        logger.warning(f"[MODIFY] Unknown feedback type: {item.type}")


# -----------------------------
# 각 규칙 apply 함수
# -----------------------------
from pptx.util import Pt

def apply_font_consistency(slide, item, details):
    """
    글자 크기만 recommendedSize 로 변경.
    텍스트박스 크기/위치 조정 없음.
    """

    if item.shapeId is None:
        logger.warning("[font_consistency] shapeId is None → skip")
        return

    current_size = details.get("currentSize")
    recommended = details.get("recommendedSize")

    if not current_size or not recommended:
        logger.warning(
            f"[font_consistency] currentSize/recommendedSize missing for shapeId={item.shapeId}"
        )
        return

    updated = False

    for shape in slide.shapes:
        if getattr(shape, "shape_id", None) != item.shapeId:
            continue
        if not shape.has_text_frame:
            continue

        tf = shape.text_frame

        # ---------------------------
        # ONLY change font size
        # ---------------------------
        for paragraph in tf.paragraphs:
            for run in paragraph.runs:
                if run.font:
                    run.font.size = Pt(recommended)

        logger.info(
            f"[font_consistency] shapeId={item.shapeId} "
            f"font {current_size} → {recommended}"
        )

        updated = True

    if not updated:
        logger.warning(f"[font_consistency] No shape updated for shapeId={item.shapeId}")


def apply_align_center(slide, item):
    if item.shapeId is None:
        return

    for shape in slide.shapes:
        if getattr(shape, "shape_id", None) == item.shapeId:
            shape.left = int(item.bboxLeft)
            shape.top = int(item.bboxTop)


def apply_text_replacement(slide, item):
    """
    detailsJson 예시:
    {"before": "helo", "after": "hello"}
    """
    if item.shapeId is None:
        return

    before = item.details.get("before")
    after = item.details.get("after")

    if not before or after is None:
        return

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if getattr(shape, "shape_id", None) != item.shapeId:
            continue

        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                if run.text:
                    run.text = run.text.replace(before, after)
