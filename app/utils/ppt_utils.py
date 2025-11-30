from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor

EMU_PER_INCH = 914400     # PowerPoint의 고정 단위
PX_PER_INCH = 96          # PowerPoint DPI (기본 96dpi)

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

def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )

# -------------------------- 
# 단위 변환 UTIL
# --------------------------
def emu_to_px(emu: int | float) -> float:
    """
    Convert EMU (English Metric Unit) to pixels(px).
    PowerPoint 기준: 1 inch = 914400 EMU, 1 inch = 96px
    """
    return (emu / EMU_PER_INCH) * PX_PER_INCH


def px_to_emu(px: int | float) -> int:
    """
    Convert pixels(px) back to EMU.
    EMU 값은 정수여야 하므로 round() 처리.
    """
    return int(round((px / PX_PER_INCH) * EMU_PER_INCH))


def slide_size_emu_to_px(width_emu: int, height_emu: int) -> tuple[float, float]:
    """
    Convert a slide's EMU-based width/height into px tuple.
    """
    return emu_to_px(width_emu), emu_to_px(height_emu)


def bbox_emu_to_px(bbox: dict) -> dict:
    """
    bbox dict 내부의 EMU 값들을 px 단위로 변환해서 반환.
    bbox = { "left": emu, "top": emu, "width": emu, "height": emu }
    """
    return {
        "left": emu_to_px(bbox.get("left", 0)),
        "top": emu_to_px(bbox.get("top", 0)),
        "width": emu_to_px(bbox.get("width", 0)),
        "height": emu_to_px(bbox.get("height", 0)),
    }
