from app.core.logger import logger

def run_analysis_rules(images: list[str], options: list[str]):
    """
    선택된 옵션들만 실행하는 메인 룰 엔진
    """
    results = []

    for idx, img_path in enumerate(images):
        issues = []
        logger.info(f"[RULE ENGINE] Running checks for slide {idx}, path={img_path}")

        if "spelling_grammar" in options:
            issues.extend(check_spelling_grammar(img_path, idx))

        if "font_consistency" in options:
            issues.extend(check_font_consistency(img_path, idx))

        if "shape_image_alignment" in options:
            issues.extend(check_shape_image_alignment(img_path, idx))

        if "layout_alignment" in options:
            issues.extend(check_layout_alignment(img_path, idx))

        if "theme" in options:
            issues.extend(check_theme(img_path, idx))

        if "readability" in options:
            issues.extend(check_readability(img_path, idx))

        if "color_contrast" in options:
            issues.extend(check_color_contrast(img_path, idx))

        if "design_feedback" in options:
            issues.extend(check_design_feedback(img_path, idx))

        results.append({
            "slide": idx,
            "issues": issues,
        })

    return {
        "slideCount": len(images),
        "results": results
    }


# ---------------------------
# MOCKUP ISSUE GENERATORS
# ---------------------------

def check_spelling_grammar(img_path: str, idx: int):
    return [{
        "type": "spelling_grammar",
        "message": f"[MOCK] Slide {idx}: 맞춤법/오타 검사 실행됨",
        "debug": img_path
    }]

def check_font_consistency(img_path: str, idx: int):
    return [{
        "type": "font_consistency",
        "message": f"[MOCK] Slide {idx}: 폰트 일관성 검사 실행됨",
        "debug": img_path
    }]

def check_shape_image_alignment(img_path: str, idx: int):
    return [{
        "type": "shape_image_alignment",
        "message": f"[MOCK] Slide {idx}: 도형/이미지 정렬 검사 실행됨",
        "debug": img_path
    }]

def check_layout_alignment(img_path: str, idx: int):
    return [{
        "type": "layout_alignment",
        "message": f"[MOCK] Slide {idx}: 레이아웃 정렬 검사 실행됨",
        "debug": img_path
    }]

def check_theme(img_path: str, idx: int):
    return [{
        "type": "theme",
        "message": f"[MOCK] Slide {idx}: 테마 분석 실행됨",
        "debug": img_path
    }]

def check_readability(img_path: str, idx: int):
    return [{
        "type": "readability",
        "message": f"[MOCK] Slide {idx}: 가독성 분석 실행됨",
        "debug": img_path
    }]

def check_color_contrast(img_path: str, idx: int):
    return [{
        "type": "color_contrast",
        "message": f"[MOCK] Slide {idx}: 색상 대비 분석 실행됨",
        "debug": img_path
    }]

def check_design_feedback(img_path: str, idx: int):
    return [{
        "type": "design_feedback",
        "message": f"[MOCK] Slide {idx}: AI 디자인 피드백 실행됨",
        "debug": img_path
    }]
