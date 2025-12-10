# app/services/analysis/analyzers/aesthetic_score.py
from typing import List
from PIL import Image
from pathlib import Path
import torch

from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.utils.slide_renderer import find_slide_image

class ClipAestheticAnalyzer(BaseAnalyzer):
    analyzer_type = "clip_aesthetic"

    def __init__(self, model, slide_image_folder: Path = None):
        """
        :param model: CLIPClassifier 인스턴스 (내부에 .preprocess 포함)
        :param slide_image_folder: 슬라이드 이미지가 저장된 디렉토리 경로
        """
        self.model = model
        self.slide_image_folder = slide_image_folder

    def analyze(self, prs) -> List[SlideIssueResult]:
        results: List[SlideIssueResult] = []

        if not self.model or not self.slide_image_folder:
            return []

        for slide_idx, slide in enumerate(prs.slides):
            image_path = find_slide_image(self.slide_image_folder, slide_idx)
            if not image_path:
                continue

            try:
                # CLIP은 RGB 이미지를 기대합니다.
                slide_image = Image.open(image_path).convert("RGB")
            except Exception:
                continue
            
            # 점수 계산
            scores = self.compute_clip_scores(self.model, slide_image)
            
            # 점수 추출 (없으면 0.0)
            aesthetic = scores.get("visuals", 0.0)
            consistency = scores.get("consistency", 0.0)
            readability_clip = scores.get("layout", 0.0) # layout 점수를 readability 보조지표로 활용 가능
            
            # 이슈 생성은 하지 않음 (점수만 전달)
            slide_issues: List[IssueResult] = []

            results.append(
                SlideIssueResult(
                    slide=slide_idx, 
                    issues=slide_issues,
                    aesthetic_score=aesthetic,
                    consistency_score=consistency,
                    readability_score=None  # ReadabilityAnalyzer가 채움
                )
            )

        return results
    
    def compute_clip_scores(self, model, slide_image):
        """
        CLIP 모델을 사용하여 이미지의 점수를 계산
        중요: 학습 때와 동일한 전처리(preprocess)를 사용해야 함
        """
        
        # 1. Preprocess 가져오기
        # MockModel(테스트용)인지 실제 CLIPClassifier인지 확인
        if hasattr(model, "preprocess"):
            # 실제 모델: 내장된 preprocess 사용 (비율 유지, CenterCrop 등 자동 처리)
            preprocess = model.preprocess
        else:
            # Mock 모델 또는 preprocess가 없는 경우: 가짜 점수 반환 (테스트용)
            return {
                "layout": 0.5, "text_amount": 0.5, "color_contrast": 0.5,
                "visuals": 0.5, "consistency": 0.5
            }

        # 2. 이미지 전처리 및 차원 추가 (3, 224, 224) -> (1, 3, 224, 224)
        device = next(model.parameters()).device if hasattr(model, 'parameters') else 'cpu'
        
        try:
            image_input = preprocess(slide_image).unsqueeze(0).to(device)
        except Exception as e:
            print(f"[ERROR] CLIP Preprocess failed: {e}")
            return {}

        # 3. 추론
        with torch.no_grad():
            logits = model(image_input) # (1, 5)
            
            # 텐서를 파이썬 float으로 변환
            # 순서는 학습 코드의 output_dim 순서와 일치해야 함
            # (layout, text_amount, color_contrast, visuals, consistency)
            preds = logits[0].cpu().numpy().tolist()
            
            scores = {
                "layout": preds[0],
                "text_amount": preds[1],
                "color_contrast": preds[2],
                "visuals": preds[3],
                "consistency": preds[4]
            }
            
        return scores