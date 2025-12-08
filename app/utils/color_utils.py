# color_utils.py
import colorsys
from typing import List, Optional, Tuple

def hex_to_rgb(hex_color):
    """#RRGGBB → (r, g, b) 0~1."""
    hex_color = hex_color.replace("#", "").strip()
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b)

def rgb_to_hex(rgb):
    r = int(max(0, min(1, rgb[0])) * 255)
    g = int(max(0, min(1, rgb[1])) * 255)
    b = int(max(0, min(1, rgb[2])) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"

def srgb_to_linear(c):
    """sRGB 0~1 → linear 0~1 (WCAG 대비용)"""
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def luminance(rgb):
    """Relative luminance (WCAG 2.0)"""
    r, g, b = rgb
    r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast_ratio(rgb1, rgb2):
    """WCAG contrast ratio"""
    L1 = luminance(rgb1)
    L2 = luminance(rgb2)
    L1, L2 = max(L1, L2), min(L1, L2)
    return (L1 + 0.05) / (L2 + 0.05)

def adjust_brightness(rgb, factor):
    """Hue & saturation 유지, value만 조절"""
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    v = max(0, min(1, v * factor))
    return colorsys.hsv_to_rgb(h, s, v)

def increase_saturation(rgb, amount=0.3):
    """채도를 높여서 더 선명한 색상으로"""
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    s = min(1.0, s + amount)
    return colorsys.hsv_to_rgb(h, s, v)

# ========== 프리셋 고대비 컬러 팔레트 ==========
PRESET_HIGH_CONTRAST_COLORS = {
    # 어두운 계열 (흰색 배경용)
    "dark_neutral": ["#000000", "#1A1A1A", "#2D2D2D", "#404040"],
    "dark_blue": ["#003366", "#1E3A5F", "#2C5F8D", "#004080"],
    "dark_purple": ["#4A148C", "#6A1B9A", "#7B1FA2", "#8E24AA"],
    "dark_green": ["#1B5E20", "#2E7D32", "#388E3C", "#43A047"],
    "dark_red": ["#B71C1C", "#C62828", "#D32F2F", "#E53935"],
    "dark_teal": ["#004D40", "#00695C", "#00796B", "#00897B"],
    
    # 밝은 계열 (어두운 배경용)
    "light_neutral": ["#FFFFFF", "#F5F5F5", "#E0E0E0", "#BDBDBD"],
    "light_blue": ["#E3F2FD", "#BBDEFB", "#90CAF9", "#64B5F6"],
    "light_purple": ["#F3E5F5", "#E1BEE7", "#CE93D8", "#BA68C8"],
    "light_green": ["#E8F5E9", "#C8E6C9", "#A5D6A7", "#81C784"],
    "light_yellow": ["#FFF9C4", "#FFF59D", "#FFF176", "#FFEE58"],
    
    # 비비드 (강렬한 색상)
    "vivid_blue": ["#0D47A1", "#1565C0", "#1976D2", "#1E88E5"],
    "vivid_orange": ["#E65100", "#EF6C00", "#F57C00", "#FB8C00"],
    "vivid_pink": ["#880E4F", "#AD1457", "#C2185B", "#D81B60"],
    "vivid_teal": ["#006064", "#00838F", "#0097A7", "#00ACC1"],
}

def get_preset_colors_for_background(bg_luminance: float) -> List[str]:
    """
    배경 밝기에 따라 적절한 프리셋 색상 반환.
    bg_luminance > 0.5 → 어두운 색
    bg_luminance <= 0.5 → 밝은 색
    """
    if bg_luminance > 0.5:  # 밝은 배경
        return (
            PRESET_HIGH_CONTRAST_COLORS["dark_neutral"] +
            PRESET_HIGH_CONTRAST_COLORS["dark_blue"] +
            PRESET_HIGH_CONTRAST_COLORS["dark_purple"] +
            PRESET_HIGH_CONTRAST_COLORS["dark_green"] +
            PRESET_HIGH_CONTRAST_COLORS["vivid_blue"] +
            PRESET_HIGH_CONTRAST_COLORS["vivid_orange"]
        )
    else:  # 어두운 배경
        return (
            PRESET_HIGH_CONTRAST_COLORS["light_neutral"] +
            PRESET_HIGH_CONTRAST_COLORS["light_blue"] +
            PRESET_HIGH_CONTRAST_COLORS["light_purple"] +
            PRESET_HIGH_CONTRAST_COLORS["light_green"]
        )

def recommend_colors(text_hex, palette_hex_list=None, bg_rgb=(1.0, 1.0, 1.0), min_contrast=4.5):
    """
    텍스트 색상에 대한 고대비 색상 추천.
    
    Args:
        text_hex: 원본 텍스트 색상 (#RRGGBB)
        palette_hex_list: 슬라이드 팔레트 (선택)
        bg_rgb: 배경 RGB (0~1, 기본값=흰색)
        min_contrast: 최소 대비율 (기본 4.5)
    
    Returns:
        추천 색상 리스트 (최대 5개)
    """
    if text_hex is None:
        return ["#000000", "#FFFFFF"]

    try:
        text_rgb = hex_to_rgb(text_hex)
    except:
        return ["#000000", "#FFFFFF"]

    candidates = []
    bg_L = luminance(bg_rgb)

    # ========== 1. 팔레트 우선 (있다면) ==========
    if palette_hex_list:
        for p_hex in palette_hex_list:
            try:
                p_rgb = hex_to_rgb(p_hex)
                cr = contrast_ratio(p_rgb, bg_rgb)
                
                if cr >= min_contrast:
                    candidates.append((p_hex, cr))
                
                # 팔레트 색을 조정
                for factor in [0.3, 0.4, 0.5, 0.6, 1.5, 1.8]:
                    adjusted = adjust_brightness(p_rgb, factor)
                    adj_cr = contrast_ratio(adjusted, bg_rgb)
                    if adj_cr >= min_contrast:
                        candidates.append((rgb_to_hex(adjusted), adj_cr))
            except:
                continue

    # ========== 2. 프리셋 고대비 색상 ==========
    preset_colors = get_preset_colors_for_background(bg_L)
    for preset_hex in preset_colors:
        try:
            preset_rgb = hex_to_rgb(preset_hex)
            cr = contrast_ratio(preset_rgb, bg_rgb)
            if cr >= min_contrast:
                candidates.append((preset_hex, cr))
        except:
            continue

    # ========== 3. 원본 색상 기반 변형 ==========
    # 3-1. 채도 높인 버전
    try:
        saturated = increase_saturation(text_rgb, 0.5)
        for factor in [0.2, 0.3, 0.4, 0.5]:
            adjusted = adjust_brightness(saturated, factor)
            cr = contrast_ratio(adjusted, bg_rgb)
            if cr >= min_contrast:
                candidates.append((rgb_to_hex(adjusted), cr))
    except:
        pass

    # 3-2. 보색 계열
    try:
        h, s, v = colorsys.rgb_to_hsv(*text_rgb)
        comp_h = (h + 0.5) % 1.0
        
        # 채도 높이고 어둡게
        comp_colors = [
            colorsys.hsv_to_rgb(comp_h, min(1.0, s + 0.3), v * 0.3),
            colorsys.hsv_to_rgb(comp_h, min(1.0, s + 0.3), v * 0.4),
            colorsys.hsv_to_rgb((h + 0.33) % 1.0, min(1.0, s + 0.3), v * 0.35),  # 120도
            colorsys.hsv_to_rgb((h - 0.33) % 1.0, min(1.0, s + 0.3), v * 0.35),  # -120도
        ]
        
        for comp_rgb in comp_colors:
            cr = contrast_ratio(comp_rgb, bg_rgb)
            if cr >= min_contrast:
                candidates.append((rgb_to_hex(comp_rgb), cr))
    except:
        pass

    # ========== 4. 중복 제거 및 정렬 ==========
    seen = set()
    unique_candidates = []
    for c_hex, cr in candidates:
        c_upper = c_hex.upper()
        if c_upper not in seen:
            seen.add(c_upper)
            unique_candidates.append((c_hex, cr))
    
    # 대비율 높은 순 정렬
    unique_candidates.sort(key=lambda x: -x[1])
    
    # 상위 5개
    recommended = [c[0] for c in unique_candidates[:5]]

    # 최소 보장
    if not recommended:
        if bg_L > 0.5:
            return ["#000000", "#1A1A1A", "#2D2D2D"]
        else:
            return ["#FFFFFF", "#F5F5F5", "#E0E0E0"]

    return recommended