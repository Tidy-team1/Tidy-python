# app/services/modify/rules/spelling_grammar.py

from app.core.logger import logger


def apply_spelling_grammar(slide, item, details):
    """
    - 기존 paragraph/run 구조 유지
    - run.font 스타일 보존
    - 텍스트만 corrected 값으로 교체
    """

    shape_id = item.shapeId
    if shape_id is None:
        logger.warning("[spelling_grammar] shapeId is None → skip")
        return

    corrected_text = details.get("corrected")
    if not corrected_text:
        logger.warning(f"[spelling_grammar] No corrected text for shapeId={shape_id}")
        return

    # corrected text를 문자의 리스트로 변환
    chars = list(corrected_text)
    char_len = len(chars)

    updated = False

    # shape 탐색
    for shape in slide.shapes:
        if getattr(shape, "shape_id", None) != shape_id:
            continue

        if not shape.has_text_frame:
            logger.warning(f"[spelling_grammar] shapeId={shape_id} has no text_frame")
            continue

        text_frame = shape.text_frame

        # paragraph/run 순회하면서 텍스트를 순차적으로 채움
        remaining = chars[:]  # 남은 문자들

        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:

                if not remaining:
                    # 이미 모든 텍스트를 소진한 경우 → 기존 스타일 유지, text만 비우기
                    run.text = ""
                    continue

                # 현재 run에 들어갈 텍스트 길이는 기존 run 길이 그대로 유지하는 방식
                # run.text의 기존 길이를 기준으로 분배
                original_len = len(run.text)

                if original_len <= 0:
                    # 글자가 없던 run -> 최소 1자라도 넣고 끝
                    run.text = remaining.pop(0)
                    continue

                # 기존 길이만큼 텍스트 채우기
                new_text = ""
                for _ in range(original_len):
                    if not remaining:
                        break
                    new_text += remaining.pop(0)

                run.text = new_text

        # 만약 남은 텍스트가 있다면 → 마지막 run에 몰아넣기
        if remaining:
            last_para = text_frame.paragraphs[-1]
            last_run = last_para.runs[-1]
            last_run.text += "".join(remaining)

        updated = True

        logger.info(
            f"[spelling_grammar] shapeId={shape_id} text updated with style preserved"
        )

    if not updated:
        logger.warning(f"[spelling_grammar] No shape updated for shapeId={shape_id}")
