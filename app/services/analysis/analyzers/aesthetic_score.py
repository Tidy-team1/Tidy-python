# app/services/analysis/analyzers/aesthetic_score.py
from typing import List
from PIL import Image
from pathlib import Path
import torch
import torchvision.transforms as T

from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.utils.slide_renderer import find_slide_image  # 유틸리티 import

class ClipAestheticAnalyzer(BaseAnalyzer):
    analyzer_type = "clip_aesthetic"

    def __init__(self, model, slide_image_folder: Path = None):
        """
        :param model: 로드된 CLIP 모델 (또는 점수 계산 모델)
        :param slide_image_folder: 슬라이드 이미지가 저장된 디렉토리 경로
        """
        self.model = model
        self.slide_image_folder = slide_image_folder

    def analyze(self, prs) -> List[SlideIssueResult]:
        results: List[SlideIssueResult] = []

        # 모델이나 이미지 폴더가 없으면 분석 불가
        if not self.model:
            print("[WARN] ClipAestheticAnalyzer: Model is not loaded.")
            return []
        
        if not self.slide_image_folder:
            print("[WARN] ClipAestheticAnalyzer: Slide image folder is not provided.")
            return []

        for slide_idx, slide in enumerate(prs.slides):
            image_path = find_slide_image(self.slide_image_folder, slide_idx)
            if not image_path: continue

            try:
                slide_image = Image.open(image_path).convert("RGB")
            except Exception: continue

            scores = self.compute_clip_scores(self.model, slide_image)
            
            # [수정] 점수 추출
            aesthetic = scores.get("visuals", 0.0)
            consistency = scores.get("consistency", 0.0)
            
            slide_issues: List[IssueResult] = []

            # [수정] SlideIssueResult에 점수 필드 채워서 반환 (이슈가 없어도 반환)
            results.append(
                SlideIssueResult(
                    slide=slide_idx, 
                    issues=slide_issues,
                    aesthetic_score=aesthetic,     # 점수 할당
                    consistency_score=consistency  # 점수 할당
                )
            )

        return results
    
    def compute_clip_scores(self, model, slide_image):
        """CLIP 모델을 사용하여 이미지의 점수를 계산"""
        # 전처리
        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(
                mean=[0.48145466, 0.4578275, 0.40821073],
                std=[0.26862954, 0.26130258, 0.27577711]
            )
        ])
        
        # model.device가 있는지 확인하거나, 기본적으로 cpu/cuda 설정 필요
        device = next(model.parameters()).device if hasattr(model, 'parameters') else 'cpu'
        x = transform(slide_image).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model(x)
            # 모델 출력 구조에 맞춰 수정 필요. 여기서는 예시로 5개 항목 가정
            scores = {
                "layout": float(logits[0, 0]),
                "text_amount": float(logits[0, 1]),
                "color_contrast": float(logits[0, 2]),
                "visuals": float(logits[0, 3]),
                "consistency": float(logits[0, 4])
            }
        return scores