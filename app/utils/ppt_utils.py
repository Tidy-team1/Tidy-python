from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor

# --------------------------
# 유틸 함수
# --------------------------

def rgb_to_hex(rgb: RGBColor | None):
    if rgb is None:
        return None
    try:
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
    except:
        return None


# --------------------------
# 슬라이드 파싱
# --------------------------

def extract_slide_json(slide_idx, slide):
    elements = []

    for element_idx, shape in enumerate(slide.shapes):
        element_json = parse_element(element_idx, shape)
        if element_json:
            elements.append(element_json)

    return {
        "index": slide_idx,
        "elements": elements
    }


# --------------------------
# 요소 파싱
# --------------------------
def parse_element(element_idx, shape):
    try:
        # TEXT 요소
        if shape.has_text_frame:
            return parse_text_element(element_idx, shape)

        # IMAGE 요소
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            return parse_image_element(element_idx, shape)

        # default SHAPE
        return parse_shape_element(element_idx, shape)

    except Exception as e:
        # 어떤 shape에서도 오류가 나면 기본적인 placeholder element를 리턴
        return {
            "elementIndex": element_idx,
            "type": "unknown",
            "leftPos": 0,
            "topPos": 0,
            "width": 0,
            "height": 0,
            "zIndex": int(element_idx),
            "rotation": 0,
            "detail": {
                "error": str(e)
            }
        }

# --------------------------
# 공통: 위치 정보(BBOX)
# --------------------------

def extract_bbox(shape):
    return {
        "leftPos": float(shape.left.cm * 37.795),
        "topPos": float(shape.top.cm * 37.795),
        "width": float(shape.width.cm * 37.795),
        "height": float(shape.height.cm * 37.795),
    }


# --------------------------
# TEXT ELEMENT
# --------------------------

def parse_text_element(idx, shape):
    # 텍스트 내용
    paragraphs = []
    for p in shape.text_frame.paragraphs:
        runs = []
        for r in p.runs:
            runs.append({
                "text": r.text,
                "bold": r.font.bold,
                "italic": r.font.italic,
                "fontSize": r.font.size.pt if r.font.size else None,
                "fontName": r.font.name,
                "color": rgb_to_hex(r.font.color.rgb if r.font.color else None)
            })

        paragraphs.append({
            "alignment": str(p.alignment),
            "runs": runs
        })

    bbox = extract_bbox(shape)

    return {
        "elementIndex": idx,
        "type": "text",
        **bbox,
        "zIndex": int(idx),
        "rotation": shape.rotation,
        "detail": {
            "paragraphs": paragraphs
        }
    }


# --------------------------
# IMAGE ELEMENT
# --------------------------

def parse_image_element(idx, shape):
    bbox = extract_bbox(shape)
    image = shape.image

    return {
        "elementIndex": idx,
        "type": "image",
        **bbox,
        "zIndex": int(idx),
        "rotation": shape.rotation,
        "detail": {
            "contentType": image.content_type,
            "filename": image.filename,
            "widthPx": image.width,
            "heightPx": image.height
        }
    }


# --------------------------
# SHAPE ELEMENT
# --------------------------

def parse_shape_element(idx, shape):
    bbox = extract_bbox(shape)

    # fill
    fill = None
    try:
        if shape.fill.type:
            fill = rgb_to_hex(shape.fill.fore_color.rgb)
    except:
        pass

    # line
    line_color = None
    try:
        if shape.line:
            line_color = rgb_to_hex(shape.line.color.rgb)
    except:
        pass

    return {
        "elementIndex": idx,
        "type": "shape",
        **bbox,
        "zIndex": int(idx),
        "rotation": shape.rotation,
        "detail": {
            "fillColor": fill,
            "lineColor": line_color
        }
    }
