# app/services/modify/rules/text_summarization.py

from app.core.logger import logger


def copy_font_style(src_run, dst_run):
    """src_run의 스타일을 dst_run에 복사"""
    s = src_run.font
    d = dst_run.font

    d.name = s.name
    d.size = s.size
    d.bold = s.bold
    d.italic = s.italic
    d.underline = s.underline

    # 색상 복사
    try:
        if s.color and s.color.rgb:
            d.color.rgb = s.color.rgb
    except:
        pass


def copy_paragraph_style(src_p, dst_p):
    """단순 paragraph 스타일만 복사 (alignment, spacing)"""
    dst_p.alignment = src_p.alignment

    if src_p.line_spacing is not None:
        dst_p.line_spacing = src_p.line_spacing

    if src_p.space_before is not None:
        dst_p.space_before = src_p.space_before

    if src_p.space_after is not None:
        dst_p.space_after = src_p.space_after


def apply_text_summarization(slide, item, details):
    """
    요약 텍스트를 단순 bullet 리스트로 재구성한다.
    - 계층 구조(level)는 신경 쓰지 않는다
    - 모든 줄은 bullet + level 0
    - 스타일만 템플릿 paragraph/run에서 복사
    """

    shape_id = item.shapeId
    if shape_id is None:
        logger.warning("[text_summarization] shapeId is None → skip")
        return

    recommend_list = details.get("recommend")
    if not recommend_list:
        logger.warning(f"[text_summarization] No recommend for shapeId={shape_id}")
        return

    updated = False

    for shape in slide.shapes:
        if getattr(shape, "shape_id", None) != shape_id:
            continue
        if not shape.has_text_frame:
            continue

        tf = shape.text_frame

        # 템플릿 paragraph/run
        template_p = tf.paragraphs[0]
        template_run = template_p.runs[0] if template_p.runs else template_p.add_run()

        # ----------------------------------------
        # 1) 기존 paragraph 내용 전부 지움 (스타일만 남음)
        # ----------------------------------------
        tf.clear()

        # ----------------------------------------
        # 2) 첫 줄: recommend[0]
        # ----------------------------------------
        first_p = tf.paragraphs[0]
        run = first_p.add_run()
        run.text = recommend_list[0]

        # 스타일 복사
        copy_paragraph_style(template_p, first_p)
        copy_font_style(template_run, run)
        first_p.level = 0

        # ----------------------------------------
        # 3) 나머지 줄들 bullet로 추가
        # ----------------------------------------
        for line in recommend_list[1:]:
            p = tf.add_paragraph()
            r = p.add_run()
            r.text = line
            copy_paragraph_style(template_p, p)
            copy_font_style(template_run, r)
            p.level = 0

        updated = True
        logger.info(f"[text_summarization] shapeId={shape_id} → bullet summarized")

    if not updated:
        logger.warning(f"[text_summarization] No shape updated for shapeId={shape_id}")
