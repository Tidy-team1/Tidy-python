# app/services/modify/service.py

import json
import os
import tempfile

from pptx import Presentation

from app.core.logger import logger
from app.utils.s3_utils import download_from_s3, upload_to_s3
from app.services.storage_service import save_file
from app.utils.s3_key_builder import (
    pptx_key_for_version,
    slide_image_key_for_version,
)
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images

from .rules import get_rule_handler


def process_modify(batch):
    pres_id = batch.presentationId
    space_id = batch.spaceId

    base_v = batch.baseVersion
    target_v = batch.targetVersion

    with tempfile.TemporaryDirectory() as tmpdir:
        base_ppt_path = os.path.join(tmpdir, "base.pptx")
        target_ppt_path = os.path.join(tmpdir, "target.pptx")

        download_from_s3(
            pptx_key_for_version(space_id, pres_id, base_v),
            base_ppt_path
        )

        prs = Presentation(base_ppt_path)

        # 피드백 순차 적용
        for item in batch.items:
            apply_single_feedback(prs, item)

        prs.save(target_ppt_path)

        ppt_key = pptx_key_for_version(space_id, pres_id, target_v)
        upload_to_s3(src_path=target_ppt_path, s3_key=ppt_key)

        pdf_path = convert_ppt_to_pdf(target_ppt_path, tmpdir)
        image_bytes_list = convert_pdf_to_images(pdf_path)
        slide_count = len(image_bytes_list)

        for idx, img_bytes in enumerate(image_bytes_list):
            key = slide_image_key_for_version(space_id, pres_id, target_v, idx)
            save_file(key, img_bytes)

        slide_prefix = f"spaces/{space_id}/presentations/{pres_id}/v{target_v}/slides/"

        return {
            "slideCount": slide_count,
            "pptS3Key": ppt_key,
            "slidePrefix": slide_prefix
        }


def apply_single_feedback(prs, item):
    slide = prs.slides[item.slideIndex]

    details = parse_details(item.detailsJson)

    handler = get_rule_handler(item.type)
    if not handler:
        logger.warning(f"[MODIFY] Unknown feedback type: {item.type}")
        return

    logger.info(
        f"[MODIFY] Apply type='{item.type}', slide={item.slideIndex}, "
        f"shapeId={item.shapeId}, details={details}"
    )

    # 모든 룰이 동일 시그니처 사용
    handler(slide, item, details)


def parse_details(details_raw: str | None):
    details_raw = details_raw or "{}"
    try:
        loaded = json.loads(details_raw)
        if isinstance(loaded, str):
            return json.loads(loaded)
        return loaded
    except Exception:
        logger.error(f"[MODIFY] Failed to parse detailsJson: {details_raw}")
        return {}
