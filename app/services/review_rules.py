from app.core.logger import logger

from app.core.logger import logger

def run_analysis_rules(images: list[str], options: list[str]):
    """
    선택된 옵션들만 실행하는 메인 룰 엔진
    """
    results = []

    for idx, img_path in enumerate(images):
        issues = []

        if "spelling_grammar" in options:
            issues.extend(check_spelling_grammar(img_path))

        if "font_consistency" in options:
            issues.extend(check_font_consistency(img_path))

        if "shape_image_alignment" in options:
            issues.extend(check_shape_image_alignment(img_path))

        if "layout_alignment" in options:
            issues.extend(check_layout_alignment(img_path))

        if "theme" in options:
            issues.extend(check_theme(img_path))

        if "readability" in options:
            issues.extend(check_readability(img_path))

        if "color_contrast" in options:
            issues.extend(check_color_contrast(img_path))

        if "design_feedback" in options:
            issues.extend(check_design_feedback(img_path))

        results.append({
            "slide": idx,
            "issues": issues,
        })

    return {
        "slideCount": len(images),
        "results": results
    }

def check_spelling_grammar(img_path: str):
    """
    맞춤법/오타 점검 (OCR → LanguageTool 등 연동 예상)
    """
    # TODO: OCR + grammar check
    return []

def check_font_consistency(img_path: str):
    """
    폰트 크기/스타일 일관성 점검
    """
    return []

def check_shape_image_alignment(img_path: str):
    """
    도형/이미지 정렬 체크
    """
    return []

def check_layout_alignment(img_path: str):
    """
    전체 레이아웃 정렬, 대칭성 체크
    """
    return []

def check_theme(img_path: str):
    """
    PPT 테마 분석 (색상 팔레트, 스타일 통일성)
    """
    return []

def check_readability(img_path: str):
    """
    텍스트 가독성 분석
    """
    return []

def check_color_contrast(img_path: str):
    """
    색상 대비 검사(WCAG 대비 기준 등)
    """
    return []

def check_design_feedback(img_path: str):
    """
    종합적인 디자인 피드백 (AI 기반 확장 예정)
    """
    return []
