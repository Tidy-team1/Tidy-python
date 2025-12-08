# image_contrast_analyzer.py
import cv2
import numpy as np
from typing import List
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.utils.ppt_utils import emu_to_px

class ImageContrastAnalyzer(BaseAnalyzer):
    analyzer_type = "image_contrast"

    def __init__(self, low_contrast_thresh=40, low_alpha_thresh=180):
        self.low_contrast_thresh = low_contrast_thresh
        self.low_alpha_thresh = low_alpha_thresh

    def analyze(self, prs) -> List[SlideIssueResult]:
        results: List[SlideIssueResult] = []

        for slide_idx, slide in enumerate(prs.slides):
            # TODO: slide 내 이미지 경로 가져오기
            # 여기서는 slide.images 리스트를 가정
            slide_issues: List[IssueResult] = []
            for idx, img_obj in enumerate(getattr(slide, "images", [])):
                img_path = getattr(img_obj, "path", None)
                if not img_path:
                    continue

                analysis = self.analyze_image_contrast(
                    img_path,
                    low_contrast_thresh=self.low_contrast_thresh,
                    low_alpha_thresh=self.low_alpha_thresh
                )

                if analysis["low_contrast"] or analysis["low_alpha"]:
                    slide_issues.append(
                        IssueResult(
                            type=self.analyzer_type,
                            message=f"이미지 대비/투명도 문제가 있습니다",
                            element=IssueElement(
                                shapeId=None,
                                elementIndex=idx,
                                bboxLeft=getattr(img_obj, "left", None),
                                bboxTop=getattr(img_obj, "top", None),
                                bboxWidth=getattr(img_obj, "width", None),
                                bboxHeight=getattr(img_obj, "height", None),
                                text=None,
                                elementType="image",
                            ),
                            details=analysis
                        )
                    )

            if slide_issues:
                results.append(SlideIssueResult(slide=slide_idx, issues=slide_issues))

        return results
    

    def analyze_image_contrast(image_path, 
                           low_contrast_thresh=40,   # 대비 기준
                           low_alpha_thresh=180):    # 투명도 기준 (255 중)
        """
        이미지 대비 및 투명도(알파) 분석
        """
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if img is None:
            return {
                "status": "error",
                "message": "이미지 로드 실패",
                "contrast_score": None,
                "alpha_score": None,
                "low_contrast": False,
                "low_alpha": False,
            }

        h, w = img.shape[:2]

        # ------------------------
        # 1) 알파 채널 평가
        # ------------------------
        alpha_score = None
        low_alpha = False

        if img.shape[2] == 4:
            alpha_channel = img[:, :, 3]
            alpha_score = float(np.mean(alpha_channel))
            if alpha_score < low_alpha_thresh:
                low_alpha = True

        # ------------------------
        # 2) 대비(명암) 평가
        # ------------------------
        gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
        contrast_score = float(np.std(gray))

        low_contrast = contrast_score < low_contrast_thresh

        return {
            "status": "ok",
            "contrast_score": contrast_score,
            "alpha_score": alpha_score,
            "low_contrast": low_contrast,
            "low_alpha": low_alpha,
        }

