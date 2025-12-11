# app/services/modify/rules/__init__.py

from .font_consistency import apply_font_consistency
from .shape_image_alignment import apply_align_shapes
from .color_contrast import apply_color_contrast
from .text_summarization import apply_text_summarization
from .image_contrast import apply_image_contrast

_RULE_HANDLERS = {
    "font_consistency": apply_font_consistency,
    "shape_image_alignment": apply_align_shapes,
    "color_contrast": apply_color_contrast,
    "shape_contrast": apply_color_contrast,
    "text_summarization": apply_text_summarization,
    "image_contrast" : apply_image_contrast,
}

def get_rule_handler(rule_type: str):
    return _RULE_HANDLERS.get(rule_type)
