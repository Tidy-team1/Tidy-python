from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor

EMU_PER_INCH = 914400
DPI = 96   # 이미지 렌더링 기준 px


# --------------------------
# COLOR UTIL
# --------------------------

def rgb_to_hex(rgb: RGBColor | None):
    if rgb is None:
        return None
    try:
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
    except:
        return None


# --------------------------
# BBOX (EMU → PX 변환 정식)
# --------------------------

def extract_bbox(shape):
    return {
        "leftPos": shape.left / EMU_PER_INCH * DPI,
        "topPos": shape.top / EMU_PER_INCH * DPI,
        "width": shape.width / EMU_PER_INCH * DPI,
        "height": shape.height / EMU_PER_INCH * DPI,
    }


# --------------------------
# SLIDE PARSING
# --------------------------

def extract_slide_json(slide_idx, slide):
    elements = []

    for element_idx, shape in enumerate(slide.shapes):
        try:
            element_json = parse_element(element_idx, shape)
            if element_json:
                elements.append(element_json)
        except Exception as e:
            # 기본 placeholder element
            elements.append({
                "elementIndex": element_idx,
                "shapeId": None,
                "type": "unknown",
                "leftPos": 0,
                "topPos": 0,
                "width": 0,
                "height": 0,
                "zIndex": element_idx,
                "rotation": 0,
                "detail": {"error": str(e)}
            })

    return {
        "index": slide_idx,
        "elements": elements
    }


# --------------------------
# ELEMENT DISPATCHER
# --------------------------

def parse_element(element_idx, shape):
    shape_id = int(shape.shape_id) if hasattr(shape, "shape_id") else None

    # TEXT
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        return parse_text_element(element_idx, shape, shape_id)

    # IMAGE
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return parse_image_element(element_idx, shape, shape_id)

    # DEFAULT SHAPE
    return parse_shape_element(element_idx, shape, shape_id)


# --------------------------
# TEXT ELEMENT
# --------------------------

def parse_text_element(idx, shape, shape_id):
    paragraphs = []
    try:
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
    except:
        paragraphs = []

    bbox = extract_bbox(shape)

    return {
        "elementIndex": idx,
        "shapeId": shape_id,
        "type": "text",
        **bbox,
        "zIndex": idx,
        "rotation": shape.rotation,
        "detail": {
            "paragraphs": paragraphs
        }
    }


# --------------------------
# IMAGE ELEMENT
# --------------------------

def parse_image_element(idx, shape, shape_id):
    bbox = extract_bbox(shape)

    try:
        image = shape.image
        detail = {
            "contentType": image.content_type,
            "filename": image.filename,
            "widthPx": image.width,
            "heightPx": image.height
        }
    except:
        detail = {
            "error": "image metadata unavailable"
        }

    return {
        "elementIndex": idx,
        "shapeId": shape_id,
        "type": "image",
        **bbox,
        "zIndex": idx,
        "rotation": shape.rotation,
        "detail": detail
    }


# --------------------------
# SHAPE ELEMENT (도형)
# --------------------------

def parse_shape_element(idx, shape, shape_id):
    bbox = extract_bbox(shape)

    fill_color = None
    try:
        if shape.fill and shape.fill.type and shape.fill.fore_color:
            fill_color = rgb_to_hex(shape.fill.fore_color.rgb)
    except:
        pass

    line_color = None
    try:
        if shape.line and shape.line.color:
            line_color = rgb_to_hex(shape.line.color.rgb)
    except:
        pass

    return {
        "elementIndex": idx,
        "shapeId": shape_id,
        "type": "shape",
        **bbox,
        "zIndex": idx,
        "rotation": shape.rotation,
        "detail": {
            "fillColor": fill_color,
            "lineColor": line_color
        }
    }