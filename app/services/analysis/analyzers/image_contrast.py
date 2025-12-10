# app/services/analysis/analyzers/image_contrast.py
import cv2
import numpy as np
from typing import List
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE # 필수 Import

from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.utils.ppt_utils import emu_to_px

class ImageContrastAnalyzer(BaseAnalyzer):
    analyzer_type = "image_contrast"

    def __init__(self, low_contrast_thresh=40, low_alpha_thresh=180):
        self.low_contrast_thresh = low_contrast_thresh
        self.low_alpha_thresh = low_alpha_thresh

    def analyze(self, prs: Presentation) -> List[SlideIssueResult]:
        results: List[SlideIssueResult] = []

        for slide_idx, slide in enumerate(prs.slides):
            slide_issues: List[IssueResult] = []
            
            # [수정] slide.shapes를 순회하며 PICTURE 타입만 골라냄
            for i, shape in enumerate(slide.shapes):
                
                # 1. 이미지가 아니면 스킵
                if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    continue
                
                # 2. 이미지 데이터 추출 (메모리상에서 바로 처리)
                if not hasattr(shape, "image"):
                    continue
                
                try:
                    image_blob = shape.image.blob
                    # 바이너리 -> numpy array -> OpenCV 이미지로 변환
                    nparr = np.frombuffer(image_blob, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                except Exception as e:
                    print(f"[WARN] 이미지 디코딩 실패 (Slide {slide_idx}, Shape {shape.shape_id}): {e}")
                    continue

                # 3. 분석 수행
                analysis = self._analyze_cv2_image(
                    img,
                    low_contrast_thresh=self.low_contrast_thresh,
                    low_alpha_thresh=self.low_alpha_thresh
                )

                # 4. 이슈 리포팅
                if analysis["low_contrast"] or analysis["low_alpha"]:
                    issue_msgs = []
                    if analysis["low_contrast"]:
                        issue_msgs.append(f"대비 낮음({analysis['contrast_score']:.1f})")
                    if analysis["low_alpha"]:
                        issue_msgs.append(f"투명도 문제({analysis['alpha_score']:.1f})")
                    
                    message = "이미지 시인성 문제: " + ", ".join(issue_msgs)

                    slide_issues.append(
                        IssueResult(
                            type=self.analyzer_type,
                            message=message,
                            element=IssueElement(
                                shapeId=shape.shape_id,
                                elementIndex=i,
                                bboxLeft=emu_to_px(shape.left),
                                bboxTop=emu_to_px(shape.top),
                                bboxWidth=emu_to_px(shape.width),
                                bboxHeight=emu_to_px(shape.height),
                                text=None,
                                elementType="image",
                            ),
                            details=analysis
                        )
                    )

            if slide_issues:
                results.append(SlideIssueResult(slide=slide_idx, issues=slide_issues))

        return results
    
    def _analyze_cv2_image(self, img, low_contrast_thresh, low_alpha_thresh):
        """
        OpenCV 이미지 객체를 받아 대비/투명도 분석
        """
        if img is None:
            return {
                "status": "error", "contrast_score": 0, "alpha_score": 0,
                "low_contrast": False, "low_alpha": False
            }

        # ------------------------
        # 1) 알파 채널 평가 (투명도)
        # ------------------------
        alpha_score = 255.0 # 기본값 (불투명)
        low_alpha = False

        # 채널이 4개면(BGRA) 알파 채널이 존재함
        if len(img.shape) == 3 and img.shape[2] == 4:
            alpha_channel = img[:, :, 3]
            # 평균 알파값 계산 (0: 투명 ~ 255: 불투명)
            alpha_score = float(np.mean(alpha_channel))
            
            # 기준치보다 낮으면(너무 투명하면) 이슈
            if alpha_score < low_alpha_thresh:
                low_alpha = True

        # ------------------------
        # 2) 대비(명암) 평가
        # ------------------------
        # BGR -> Gray 변환
        if len(img.shape) == 3:
            # Alpha 채널이 있으면 제거하고 변환
            if img.shape[2] == 4:
                gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img # 이미 흑백

        # 표준편차(Standard Deviation)가 곧 대비(Contrast) 점수
        contrast_score = float(np.std(gray))
        low_contrast = contrast_score < low_contrast_thresh

        return {
            "status": "ok",
            "contrast_score": round(contrast_score, 2),
            "alpha_score": round(alpha_score, 2),
            "low_contrast": low_contrast,
            "low_alpha": low_alpha,
        }