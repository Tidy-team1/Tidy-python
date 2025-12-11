# app/services/modify/rules/spelling_grammar.py

from app.core.logger import logger


def apply_spelling_grammar(slide, item, details):
    """
    paragraph 단위로 텍스트 적용 (줄 구조 유지)
    run 스타일 유지
    """

    shape_id = item.shapeId
    if shape_id is None:
        logger.warning("[spelling_grammar] shapeId is None → skip")
        return

    corrected_text = details.get("corrected")
    if not corrected_text:
        logger.warning(f"[spelling_grammar] No corrected text for shapeId={shape_id}")
        return

    updated = False

    # 줄 단위로 분리
    corrected_lines = corrected_text.split("\n")

    for shape in slide.shapes:
        if getattr(shape, "shape_id", None) != shape_id:
            continue
        if not shape.has_text_frame:
            continue

        text_frame = shape.text_frame
        paragraphs = text_frame.paragraphs

        # 기존 paragraph보다 corrected 줄이 더 많으면 → 마지막 paragraph 복제
        while len(paragraphs) < len(corrected_lines):
            paragraphs[-1]._p.addnext(paragraphs[-1]._p)  # paragraph clone
            paragraphs = text_frame.paragraphs

        # 줄 단위로 paragraph에 적용
        for idx, line in enumerate(corrected_lines):
            p = paragraphs[idx]

            if len(p.runs) == 0:
                run = p.add_run()
            else:
                run = p.runs[0]

            # 첫 run에 텍스트 전체 적용
            run.text = line

            # 나머지 run은 스타일 유지하고 내용만 제거
            for r in p.runs[1:]:
                r.text = ""

        # 줄 수가 줄어든 경우 → 남은 paragraph는 비우기
        for j in range(len(corrected_lines), len(paragraphs)):
            p = paragraphs[j]
            for r in p.runs:
                r.text = ""

        updated = True

        logger.info(f"[spelling_grammar] Updated paragraphs for shapeId={shape_id}")

    if not updated:
        logger.warning(f"[spelling_grammar] No shape updated for shapeId={shape_id}")
