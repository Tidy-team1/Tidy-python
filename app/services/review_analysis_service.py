import os
import tempfile
from app.core.logger import logger
from app.utils.s3_utils import download_from_s3
from app.utils.s3_key_builder import slide_image_key
from app.services.review_rules import run_analysis_rules
from app.utils.s3_utils import load_slide_images


def analyze_review(space_id: int, presentation_id: int, options: list[str]):
    with tempfile.TemporaryDirectory() as tmpdir:

        # 1) 슬라이드 이미지 다운로드
        imgs = load_slide_images(space_id, presentation_id, tmpdir)

        # 2) 옵션 기반 분석 실행
        analysis_result = run_analysis_rules(imgs, options)

        return analysis_result
