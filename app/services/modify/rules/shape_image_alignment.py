# app/services/modify/rules/shape_image_alignment.py

from pptx.enum.shapes import MSO_SHAPE_TYPE
from app.core.logger import logger

def iter_all_shapes(parent):
    for shape in parent.shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for sub in iter_all_shapes(shape):
                yield sub


def apply_align_shapes(slide, item, details):
    shape_positions = details.get("shapes", [])
    if not shape_positions:
        return

    EMU_PER_PX = 9525
    pos_map = {s["shapeId"]: s for s in shape_positions}

    updated = False

    for shape in iter_all_shapes(slide):
        sid = getattr(shape, "shape_id", None)
        if sid not in pos_map:
            continue

        new_left_px = pos_map[sid]["newLeft"]
        new_top_px = pos_map[sid]["newTop"]

        shape.left = int(new_left_px * EMU_PER_PX)
        shape.top = int(new_top_px * EMU_PER_PX)

        updated = True
        logger.info(f"[shape_image_alignment] Updated shapeId={sid}")

    if not updated:
        logger.warning("[shape_image_alignment] No shapes updated")
