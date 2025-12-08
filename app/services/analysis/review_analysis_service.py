# app/services/analysis/review_analysis_service.py

import sys
import torch
from pathlib import Path
from collections import defaultdict
from pptx import Presentation

# DTO & Services
from app.services.storage_service import download_presentation
from app.models.analysis_dto import ReviewAnalysisResult, SlideIssueResult

# Analyzers
from app.services.analysis.analyzers.font_consistency import FontConsistencyAnalyzer
from app.services.analysis.analyzers.spelling_grammar import SpellingGrammarAnalyzer
from app.services.analysis.analyzers.shape_image_alignment import ShapeImageAlignmentAnalyzer
from app.services.analysis.analyzers.color_contrast import ColorContrastAnalyzer
from app.services.analysis.analyzers.readability import ReadabilityAnalyzer
from app.services.analysis.analyzers.image_contrast import ImageContrastAnalyzer
from app.services.analysis.analyzers.text_summarization import TextSummarizationAnalyzer
from app.services.analysis.analyzers.llm_feedback import LLMFeedbackAnalyzer
from app.services.analysis.analyzers.aesthetic_score import ClipAestheticAnalyzer
from app.services.analysis.analyzers.design_feedback import DesignFeedbackAnalyzer

# Utils
from app.utils.ppt_parser import parse_presentation
from app.utils.slide_renderer import export_slide_images


# =========================================================
# 🔹 Global Config & Model Caching
# =========================================================

CLIP_MODULE_PATH = Path(r"C:\Users\naeun\capstone_1\Tidy-python\clip")
CLIP_WEIGHTS_PATH = CLIP_MODULE_PATH / "clip_linear_probe.pth"
_CACHED_CLIP_MODEL = None

def _get_clip_model():
    """CLIPClassifier 모델 로드 (Singleton)"""
    global _CACHED_CLIP_MODEL
    if _CACHED_CLIP_MODEL is not None:
        return _CACHED_CLIP_MODEL

    print(f"[INFO] Loading CLIP model from {CLIP_MODULE_PATH}...")
    if str(CLIP_MODULE_PATH) not in sys.path:
        sys.path.append(str(CLIP_MODULE_PATH))
    
    try:
        from training import CLIPClassifier
    except ImportError as e:
        print(f"[ERROR] Failed to import CLIPClassifier. Check path: {e}")
        raise e

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPClassifier(output_dim=5).to(device)

    if not CLIP_WEIGHTS_PATH.exists():
        print(f"[ERROR] Weights file not found: {CLIP_WEIGHTS_PATH}")
        return None

    try:
        state_dict = torch.load(CLIP_WEIGHTS_PATH, map_location=device)
        model.load_state_dict(state_dict, strict=False)
        model.eval()
        _CACHED_CLIP_MODEL = model
        print("[INFO] CLIP model loaded successfully.")
        return model
    except Exception as e:
        print(f"[ERROR] Failed to load weights: {e}")
        return None


# =========================================================
# 🔹 Analyzer Map
# =========================================================

ANALYZER_MAP = {
    "font_consistency": FontConsistencyAnalyzer,
    "spelling_grammar": SpellingGrammarAnalyzer,
    "shape_image_alignment": ShapeImageAlignmentAnalyzer,
    "color_contrast": ColorContrastAnalyzer,
    "readability": ReadabilityAnalyzer,
    "text_summarization": TextSummarizationAnalyzer,
    "image_contrast": ImageContrastAnalyzer, 
    "clip_aesthetic": ClipAestheticAnalyzer,
    "design_feedback": DesignFeedbackAnalyzer
}


# =========================================================
# 🔹 Main Service Logic
# =========================================================

def analyze_review(space_id: int, presentation_id: int, options: list[str]) -> ReviewAnalysisResult:
    # 1) PPTX 다운로드
    ppt_path = download_presentation(space_id, presentation_id)
    if not ppt_path or not Path(ppt_path).exists():
        raise FileNotFoundError(f"Presentation file not found: {ppt_path}")
        
    prs = Presentation(ppt_path)
    
    # 1-1) CLIP 이미지 추출
    temp_root = Path("temp")
    slide_image_dir = temp_root / str(presentation_id) / "full_slides"
    
    if "clip_aesthetic" in options:
        try:
            if not slide_image_dir.exists() or not any(slide_image_dir.iterdir()):
                print(f"[INFO] Extracting slide images to {slide_image_dir}")
                export_slide_images(ppt_path, slide_image_dir)
        except Exception as e:
            print(f"[WARN] Slide export failed: {e}")
            options.remove("clip_aesthetic")

    # 2) CLIP 모델 로드
    clip_model = None
    if "clip_aesthetic" in options:
        clip_model = _get_clip_model()
        if not clip_model:
            options.remove("clip_aesthetic")

    # 3) score 계산 실행
    slide_scores = defaultdict(lambda: {
        "readability_score": None, 
        "aesthetic_score": None, 
        "consistency_score": None
    })

    # Readability score
    try:
        r_analyzer = ReadabilityAnalyzer()
        r_results = r_analyzer.analyze(prs)
        for res in r_results:
            slide_scores[res.slide]["readability_score"] = res.readability_score
    except Exception as e:
        print(f"[WARN] Readability scoring failed: {e}")

    # CLIP Aestehtic/Consistency score
    clip_model = _get_clip_model()
    if clip_model:
        try:
            c_analyzer = ClipAestheticAnalyzer(model=clip_model, slide_image_folder=slide_image_dir)
            c_results = c_analyzer.analyze(prs)
            for res in c_results:
                slide_scores[res.slide]["aesthetic_score"] = res.aesthetic_score
                slide_scores[res.slide]["consistency_score"] = res.consistency_score
        except Exception as e:
            print(f"[WARN] CLIP scoring failed: {e}")

    # 3-1) Option Analyzer 실행
    all_results: list[SlideIssueResult] = []
    
    for opt in options:
        if opt in ["llm_feedback", "design_feedback"] : continue
        
        analyzer_cls = ANALYZER_MAP.get(opt)
        if not analyzer_cls: continue

        try:
            if opt == "clip_aesthetic":
                # analyzer = analyzer_cls(model=clip_model, slide_image_folder=slide_image_dir)
                continue 
            else:
                analyzer = analyzer_cls()

            slide_results = analyzer.analyze(prs)
            all_results.extend(slide_results)
            
        except Exception as e:
            print(f"[ERROR] Analyzer '{opt}' failed: {e}")

    # 4) LLM 통합 피드백
    issues_by_slide = defaultdict(list)
    for res in all_results:
        issues_by_slide[res.slide].extend(res.issues)
    
    # 파싱은 한 번만
    parsed_data = None
    if "llm_feedback" in options or "design_feedback" in options:
        parsed_data = parse_presentation(prs, ppt_path)

    # 4-1) LLM Feedback (이슈 생성 & 색상 추천)
    if "llm_feedback" in options:
        print("[INFO] Running LLM Feedback (Contextual Issues)...")
        llm_analyzer = LLMFeedbackAnalyzer()
        try:
            llm_results = llm_analyzer.analyze_with_context(
                slides_data=parsed_data["slides"],
                existing_issues=issues_by_slide
            )
            all_results.extend(llm_results)
            # 새로 생긴 이슈도 갱신 (Design Feedback이 참고할 수 있도록)
            for res in llm_results:
                issues_by_slide[res.slide].extend(res.issues)
        except Exception as e:
            print(f"[ERROR] LLM Feedback failed: {e}")

    # 4-2) Design Feedback (자연어 조언)
    if "design_feedback" in options:
        print("[INFO] Running Design Feedback (Natural Language)...")
        design_analyzer = DesignFeedbackAnalyzer()
        try:
            design_results = design_analyzer.analyze_with_context(
                slides_data=parsed_data["slides"],
                existing_issues=issues_by_slide
            )
            all_results.extend(design_results)
        except Exception as e:
            print(f"[ERROR] Design Feedback failed: {e}")

    # 5) 최종 병합
    final_merged = _merge_results_by_slide(all_results, slide_scores)
    result = ReviewAnalysisResult(results=final_merged)
    
    print("\n===== ANALYSIS RESULT =====")
    print(f"Total Slides: {len(final_merged)}")
    print("===========================\n")
    return result


def _merge_results_by_slide(all_results: list[SlideIssueResult], slide_scores: dict) -> list[SlideIssueResult]:
    """
    [개선된 병합 로직]
    1. 점수(Readability, Aesthetic 등)는 Analyzer가 계산한 값을 그대로 유지 (덮어쓰기)
    2. 이슈(IssueResult)는 중복 제거 수행
       - Text Summarization: 슬라이드당 1개만 허용
       - Color Contrast: Shape ID 기준으로 1개만 허용 (Rule-based 우선)
       - 기타: 동일한 Type과 Shape ID면 중복 제거
    """
    merged_map = defaultdict(lambda: {
        "issues": [],
        "readability_score": None,
        "aesthetic_score": None,
        "consistency_score": None
    })

    for slide_idx, scores in slide_scores.items():
        merged_map[slide_idx]["readability_score"] = scores["readability_score"]
        merged_map[slide_idx]["aesthetic_score"] = scores["aesthetic_score"]
        merged_map[slide_idx]["consistency_score"] = scores["consistency_score"]
    
    for res in all_results:
        # 점수 병합 (None이 아닌 경우 갱신)
        if res.readability_score is not None:
            merged_map[res.slide]["readability_score"] = res.readability_score
        if res.aesthetic_score is not None:
            merged_map[res.slide]["aesthetic_score"] = res.aesthetic_score
        if res.consistency_score is not None:
            merged_map[res.slide]["consistency_score"] = res.consistency_score
            
        # 이슈는 일단 다 모음
        merged_map[res.slide]["issues"].extend(res.issues)
    
    final_list = []
    
    for slide_idx in sorted(merged_map.keys()):
        data = merged_map[slide_idx]
        raw_issues = data["issues"]
        unique_issues = []
        
        # 중복 체크를 위한 키 집합
        # Key format: (General_Type, Shape_ID)
        seen_keys = set()
        
        for issue in raw_issues:
            shape_id = issue.element.shapeId if issue.element else None
            
            # 1. 텍스트 요약: 슬라이드당 1개
            if "text_summarization" in issue.type:
                key = ("text_summarization", "slide_level")
            
            # 2. 디자인 피드백: 슬라이드당 1개
            elif issue.type == "design_feedback":
                key = ("design_feedback", "slide_level")

            # 3. 색상 대비 (Rule-based): Shape ID 기준
            elif issue.type == "color_contrast":
                key = ("color_contrast", shape_id)

            # 4. LLM 색상 제안 (Contextual): Shape ID 기준이지만 Type을 분리
            # 이렇게 해야 Rule-based 경고도 뜨고, LLM 조언도 같이 뜸 (중복 아님)
            elif issue.type == "color_contextual_suggestion":
                key = ("color_contextual_suggestion", shape_id)
            
            # 5. 기타: Type + Shape ID
            else:
                key = (issue.type, shape_id)
            
            if key not in seen_keys:
                seen_keys.add(key)
                unique_issues.append(issue)

        final_list.append(SlideIssueResult(
            slide=slide_idx,
            issues=unique_issues,
            readability_score=data["readability_score"],
            aesthetic_score=data["aesthetic_score"],
            consistency_score=data["consistency_score"]
        ))
        
    return final_list