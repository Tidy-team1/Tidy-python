from pptx import Presentation
from pprint import pprint

from app.services.storage_service import download_presentation
from app.models.analysis_dto import ReviewAnalysisResult

from app.services.analysis.analyzers.font_consistency import FontConsistencyAnalyzer
from app.services.analysis.analyzers.spelling_grammar import SpellingGrammarAnalyzer
from app.services.analysis.analyzers.shape_image_alignment import ShapeImageAlignmentAnalyzer

ANALYZER_MAP = {
    "font_consistency": FontConsistencyAnalyzer,
    "spelling_grammar": SpellingGrammarAnalyzer,
    "shape_image_alignment": ShapeImageAlignmentAnalyzer,
}


def analyze_review(space_id: int, presentation_id: int, options: list[str]) -> ReviewAnalysisResult:

    # 1) S3에서 PPTX 다운로드 → 로컬 임시 파일 경로 반환
    ppt_path = download_presentation(space_id, presentation_id)

    # 2) python-pptx로 프리젠테이션 객체 로드
    prs = Presentation(ppt_path)

    # 3) 옵션별 Analyzer 실행
    final_results = []

    for opt in options:
        analyzer_cls = ANALYZER_MAP.get(opt)
        if not analyzer_cls:
            continue

        analyzer = analyzer_cls()
        slide_results = analyzer.analyze(prs)  # prs 그대로 넘김

        final_results.extend(slide_results)
        
    result = ReviewAnalysisResult(results=final_results)

    # ⭐⭐ JSON 반환 전에 출력 ⭐⭐
    print("\n===== ANALYSIS RESULT (dict) =====")
    pprint(result.model_dump()) 
    print("=================================\n")

    return result
