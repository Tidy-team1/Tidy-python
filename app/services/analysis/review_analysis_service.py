# app/services/analysis/review_analysis_service.py

import sys
import torch
from pathlib import Path
from collections import defaultdict
from pptx import Presentation
import clip

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
from app.utils.s3_utils import load_slide_images


# =========================================================
# 🔹 Global Config & Model Caching
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]   # Tidy-python 폴더
CLIP_MODULE_PATH = PROJECT_ROOT / "tidyclip"
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
        from tidyclip.training import CLIPClassifier
    except ImportError as e:
        print(f"[ERROR] Failed to import CLIPClassifier: {e}")
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔥 Loading Model on Device: {device}")

    try:
        # training.py 수정본(내부 clip.load) 사용
        model = CLIPClassifier(output_dim=5, device=device).to(device)
    except Exception as e:
        print(f"[ERROR] Model initialization failed: {e}")
        return None

    # 3. 가중치(.pth) 로드 확인
    if not CLIP_WEIGHTS_PATH.exists():
        print(f"[CRITICAL] Weights file missing at: {CLIP_WEIGHTS_PATH}")
        print("-> 모델이 초기화되지 않은 상태로 실행되어 0.5 근처의 랜덤값이 나올 수 있습니다.")
        return None # 가중치 없으면 아예 None 리턴해서 분석 스킵 유도

    try:
        state_dict = torch.load(CLIP_WEIGHTS_PATH, map_location=device)
        # [수정] strict=True로 변경하여 구조 불일치 시 에러 발생시킴 (그래야 0.5점 문제를 잡음)
        model.load_state_dict(state_dict, strict=True) 
        model.eval()
        _CACHED_CLIP_MODEL = model
        print("[INFO] ✅ Custom CLIP Classifier weights loaded successfully.")
        return model
    except Exception as e:
        print(f"[ERROR] Failed to load weights: {e}")
        # 로드 실패 시 None 반환하여 0.5점 출력 방지
        return None
    
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
def analyze_review(space_id: int, presentation_id: int, version: int, options: list[str]) -> ReviewAnalysisResult:
    # 🔍 선택된 옵션 로그 출력
    print("====================================================")
    print(f"[OPTIONS] Selected: {', '.join(options) if options else '(none)'}")
    print("====================================================")

    # 1. 파일 준비 (요청받은 version 기반)
    ppt_path = download_presentation(space_id, presentation_id, version)
    if not ppt_path or not Path(ppt_path).exists():
        raise FileNotFoundError(f"Presentation file not found: {ppt_path}")

    prs = Presentation(ppt_path)

    # 2. 이미지 추출 (요청받은 version 기반)
    temp_root = Path("temp")
    slide_image_dir = temp_root / str(presentation_id) / f"v{version}" / "full_slides"
    slide_image_dir.mkdir(parents=True, exist_ok=True)

    try:
        slide_image_paths = load_slide_images(
            space_id=space_id,
            presentation_id=presentation_id,
            version=version,
            tmpdir=str(slide_image_dir)
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load slide images from S3: {e}")

    # 3. [점수 강제 계산] 옵션 여부와 상관없이 실행
    # 키 이름을 DTO와 동일하게 'xxx_score'로 통일합니다.
    slide_scores = defaultdict(lambda: {
        "readability_score": None, 
        "aesthetic_score": None, 
        "consistency_score": None
    })

    # 3-1. Readability Score
    try:
        r_analyzer = ReadabilityAnalyzer()
        r_results = r_analyzer.analyze(prs)
        for res in r_results:
            slide_scores[res.slide]["readability_score"] = res.readability_score
    except Exception as e:
        print(f"[WARN] Readability scoring failed: {e}")

    # 3-2. CLIP Aesthetic/Consistency Score
    clip_model = _get_clip_model()
    if clip_model:
        try:
            c_analyzer = ClipAestheticAnalyzer(model=clip_model, slide_image_folder=slide_image_dir)
            c_results = c_analyzer.analyze(prs)
            for res in c_results:
                # [중요] 키 이름 일치시킴
                slide_scores[res.slide]["aesthetic_score"] = res.aesthetic_score
                slide_scores[res.slide]["consistency_score"] = res.consistency_score
        except Exception as e:
            print(f"[WARN] CLIP scoring failed: {e}")

    # 4. [이슈 분석] 선택된 옵션 실행
    all_results: list[SlideIssueResult] = []
    
    for opt in options:
        # LLM 관련은 후처리에서 실행
        if opt in ["llm_feedback", "design_feedback"]: continue
        
        analyzer_cls = ANALYZER_MAP.get(opt)
        if not analyzer_cls: continue

        try:
            # CLIP 분석기는 점수만 계산하고 이슈는 안 낼 거라면 여기서 스킵해도 됨
            # 하지만 혹시 나중에 이슈도 낼 수 있으니 실행은 하되, aesthetic_score.py에서 이슈 리스트를 빈배열로 주면 됨
            if opt == "clip_aesthetic":
                if not clip_model: continue
                analyzer = analyzer_cls(model=clip_model, slide_image_folder=slide_image_dir)
            else:
                analyzer = analyzer_cls()

            slide_results = analyzer.analyze(prs)
            all_results.extend(slide_results)
            
        except Exception as e:
            print(f"[ERROR] Analyzer '{opt}' failed: {e}")

    # 5. LLM 후처리 (옵션인 경우)
    issues_by_slide = defaultdict(list)
    for res in all_results:
        issues_by_slide[res.slide].extend(res.issues)
    
    parsed_data = None
    if "llm_feedback" in options or "design_feedback" in options:
        parsed_data = parse_presentation(prs, ppt_path)

    # 5-1. LLM Contextual Issues
    if "llm_feedback" in options:
        print("[INFO] Running LLM Feedback...")
        try:
            llm = LLMFeedbackAnalyzer()
            llm_res = llm.analyze_with_context(parsed_data["slides"], issues_by_slide)
            all_results.extend(llm_res)
            # 신규 이슈 업데이트 (Design Feedback이 참고할 수 있도록)
            for res in llm_res:
                issues_by_slide[res.slide].extend(res.issues)
        except Exception as e:
            print(f"[ERROR] LLM Feedback failed: {e}")

    # 5-2. Design Feedback (Natural Language)
    if "design_feedback" in options:
        print("[INFO] Running Design Feedback...")
        try:
            design = DesignFeedbackAnalyzer()
            design_res = design.analyze_with_context(parsed_data["slides"], issues_by_slide)
            all_results.extend(design_res)
        except Exception as e:
            print(f"[ERROR] Design Feedback failed: {e}")

    # 6. 최종 병합
    final_merged = _merge_results_by_slide(all_results, slide_scores)
    
    result = ReviewAnalysisResult(results=final_merged)
    return result


def _merge_results_by_slide(all_results: list[SlideIssueResult], slide_scores: dict) -> list[SlideIssueResult]:
    """
    이슈 병합 및 중복 제거
    """
    merged_map = defaultdict(lambda: {
        "issues": [],
        "readability_score": None, 
        "aesthetic_score": None, 
        "consistency_score": None
    })

    # 1. 강제 점수 주입
    for slide_idx, scores in slide_scores.items():
        merged_map[slide_idx]["readability_score"] = scores["readability_score"]
        merged_map[slide_idx]["aesthetic_score"] = scores["aesthetic_score"]
        merged_map[slide_idx]["consistency_score"] = scores["consistency_score"]
    
    # 2. 이슈 수집 (LLM 피드백 포함)
    for res in all_results:
        # 점수 덮어쓰기
        if res.readability_score is not None: merged_map[res.slide]["readability_score"] = res.readability_score
        if res.aesthetic_score is not None: merged_map[res.slide]["aesthetic_score"] = res.aesthetic_score
        if res.consistency_score is not None: merged_map[res.slide]["consistency_score"] = res.consistency_score
        
        merged_map[res.slide]["issues"].extend(res.issues)
    
    final_list = []
    
    for slide_idx in sorted(merged_map.keys()):
        data = merged_map[slide_idx]
        raw_issues = data["issues"]
        unique_issues = []
        
        # [중복 제거 키 관리]
        seen_keys = set()
        
        # 우선순위를 위해 정렬할 수도 있으나, 여기서는 순서대로 처리하되 키를 분리
        for issue in raw_issues:
            shape_id = issue.element.shapeId if issue.element else None
            
            # 1. 텍스트 요약
            if issue.type == "text_summarization":
                key = ("text_summarization", "slide")
            
            # 2. 디자인 피드백
            elif issue.type == "design_feedback":
                key = ("design_feedback", "slide")

            # 3. 색상 대비 (Rule-based)
            elif issue.type == "color_contrast":
                key = ("color_contrast", shape_id)

            # 4. LLM 색상 제안 (Contextual) - [중요] Rule-based와 키를 다르게 해서 공존시킴
            elif issue.type == "color_contextual_suggestion":
                key = ("color_contextual_suggestion", shape_id) # Rule-based와 별개로 취급

            # 5. 기타
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
