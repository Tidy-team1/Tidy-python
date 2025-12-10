# app/services/analysis/analyzers/color_contrast.py
import colorsys
from typing import List, Dict, Any
from pptx import Presentation
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.ppt_parser import parse_presentation
from app.utils.color_utils import hex_to_rgb, contrast_ratio  

class ColorContrastAnalyzer(BaseAnalyzer):
    analyzer_type = "color_contrast"

    def __init__(self):
        self.min_contrast_large = 3.0   # 큰 텍스트
        self.min_contrast_normal = 4.5  # 일반 텍스트
        self.min_contrast_shape = 3.0   # 도형 자체 (WCAG Non-text Contrast)

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        parsed = parse_presentation(prs)
        results = []
        
        for slide_data in parsed["slides"]:
            slide_idx = slide_data["slide_index"]
            slide_issues = []
            
            slide_bg_hex = slide_data.get("background_color", "#FFFFFF")
            slide_bg_rgb = hex_to_rgb(slide_bg_hex)
            palette = slide_data.get("palette_hex", [])
            elements = slide_data["elements"]

            for i, el in enumerate(elements):
                # =========================================================
                # Case 1: 텍스트 요소 (텍스트 박스 또는 텍스트가 있는 도형)
                # =========================================================
                if el["type"] == "text":
                    text_color = el.get("textColor")
                    if not text_color: continue
                    
                    try:
                        fg_rgb = hex_to_rgb(text_color)
                    except: continue
                    
                    # 1-1. 텍스트 자체의 배경색 찾기 (채우기 색상 or 뒤에 있는 요소)
                    text_bg_rgb = None
                    has_own_fill = False
                    
                    if el.get("fillColor"):
                        try:
                            text_bg_rgb = hex_to_rgb(el["fillColor"])
                            has_own_fill = True
                        except: pass
                    
                    if text_bg_rgb is None:
                        text_bg_rgb = self._find_visual_background(el, elements, slide_bg_rgb, current_index=i)

                    # 1-2. [Text Check] 텍스트 vs 텍스트 배경 대비 검사
                    cr = contrast_ratio(fg_rgb, text_bg_rgb)
                    
                    font_size = el.get("fontSize", 14.0)
                    is_bold = el.get("isBold", False)
                    is_large = (font_size >= 18) or (font_size >= 14 and is_bold)
                    min_cr_text = self.min_contrast_large if is_large else self.min_contrast_normal
                    
                    if cr < min_cr_text:
                        recommended = self._recommend_better_colors(
                            fg_hex=text_color, bg_rgb=text_bg_rgb, palette=palette, min_contrast=min_cr_text
                        )
                        text_type = "제목" if is_large else "본문"
                        slide_issues.append(
                            IssueResult(
                                type=self.analyzer_type,
                                message=f"{text_type} 텍스트 색상({text_color})이 배경과 잘 구분되지 않습니다. (대비율: {cr:.2f})",
                                element=self._create_element(el, "text"),
                                details={
                                    "current": text_color, "contrast": round(cr, 2),
                                    "required": min_cr_text, "recommended": recommended
                                }
                            )
                        )

                    # 1-3. [Shape Check] 텍스트가 있는 '도형 자체'의 대비 검사 (추가된 로직)
                    # 도형에 채우기 색이 있다면, 그 도형 색이 슬라이드 배경과 구분되는지 확인해야 함
                    if has_own_fill:
                        container_bg_rgb = self._find_visual_background(el, elements, slide_bg_rgb, current_index=i)
                        shape_cr = contrast_ratio(text_bg_rgb, container_bg_rgb) # text_bg_rgb가 곧 도형 색상
                        
                        if shape_cr < self.min_contrast_shape:
                            shape_color = el["fillColor"]
                            rec_shape = self._recommend_better_colors(
                                fg_hex=shape_color, bg_rgb=container_bg_rgb, palette=palette, min_contrast=self.min_contrast_shape
                            )
                            slide_issues.append(
                                IssueResult(
                                    type="shape_contrast",
                                    message=f"텍스트 상자(도형) 색상({shape_color})이 배경과 잘 구분되지 않습니다. (대비율: {shape_cr:.2f})",
                                    element=self._create_element(el, "shape"), # 타입은 shape로 표시
                                    details={
                                        "current": shape_color, "contrast": round(shape_cr, 2),
                                        "required": self.min_contrast_shape, "recommended": rec_shape
                                    }
                                )
                            )

                # =========================================================
                # Case 2: 텍스트 없는 순수 도형
                # =========================================================
                elif el["type"] == "shape":
                    shape_color = el.get("fillColor")
                    if not shape_color: continue

                    try:
                        fg_rgb = hex_to_rgb(shape_color)
                    except: continue

                    bg_rgb = self._find_visual_background(el, elements, slide_bg_rgb, current_index=i)
                    cr = contrast_ratio(fg_rgb, bg_rgb)

                    if cr < self.min_contrast_shape:
                        recommended = self._recommend_better_colors(
                            fg_hex=shape_color, bg_rgb=bg_rgb, palette=palette, min_contrast=self.min_contrast_shape
                        )
                        slide_issues.append(
                            IssueResult(
                                type="color_contrast",
                                message=f"도형 색상({shape_color})이 배경과 잘 구분되지 않습니다. (대비율: {cr:.2f})",
                                element=self._create_element(el, "shape"),
                                details={
                                    "current": shape_color, "contrast": round(cr, 2),
                                    "required": self.min_contrast_shape, "recommended": recommended
                                }
                            )
                        )

            if slide_issues:
                results.append(SlideIssueResult(slide=slide_idx, issues=slide_issues))
        
        return results

    def _create_element(self, el_data, el_type):
        """IssueElement 생성 헬퍼"""
        return IssueElement(
            shapeId=el_data["shape_id"],
            elementIndex=el_data["element_index"],
            bboxLeft=el_data["left"],
            bboxTop=el_data["top"],
            bboxWidth=el_data["width"],
            bboxHeight=el_data["height"],
            text=el_data.get("text"),
            elementType=el_type
        )

    def _find_visual_background(self, target_el, all_elements, slide_bg_rgb, current_index):
        """타겟 요소 뒤에 겹쳐있는 가장 상위 요소의 색상 찾기"""
        tx, ty = target_el["left"], target_el["top"]
        tw, th = target_el["width"], target_el["height"]
        margin = 2 # 마진 축소
        
        center_x = tx + tw / 2
        center_y = ty + th / 2

        # 역순 탐색
        for i in range(current_index - 1, -1, -1):
            other = all_elements[i]
            if not other.get("fillColor"): continue
                
            ox, oy = other["left"], other["top"]
            ow, oh = other["width"], other["height"]
            
            if None in [tx, ty, tw, th, ox, oy, ow, oh]: continue

            # 중심점 포함 여부로 단순화
            if (ox - margin <= center_x <= ox + ow + margin) and \
               (oy - margin <= center_y <= oy + oh + margin):
                try:
                    return hex_to_rgb(other["fillColor"])
                except: pass
        
        return slide_bg_rgb

    def _recommend_better_colors(self, fg_hex, bg_rgb, palette, min_contrast):
        # (기존 로직 동일 - 생략 없이 사용)
        recommendations = []
        try: fg_rgb = hex_to_rgb(fg_hex)
        except: return ["#000000", "#FFFFFF"]

        r, g, b = fg_rgb[0]/255.0, fg_rgb[1]/255.0, fg_rgb[2]/255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        valid_palette = []
        for p_hex in palette:
            try:
                p_rgb = hex_to_rgb(p_hex)
                if contrast_ratio(p_rgb, bg_rgb) >= min_contrast:
                    pr, pg, pb = p_rgb[0]/255.0, p_rgb[1]/255.0, p_rgb[2]/255.0
                    ph, _, _ = colorsys.rgb_to_hsv(pr, pg, pb)
                    valid_palette.append((abs(h - ph), p_hex))
            except: continue
        
        valid_palette.sort(key=lambda x: x[0])
        recommendations.extend([c[1] for c in valid_palette])

        bg_lum = (0.299 * bg_rgb[0] + 0.587 * bg_rgb[1] + 0.114 * bg_rgb[2])
        is_bg_light = bg_lum > 128
        
        generated = None
        target_v = v
        for _ in range(10):
            if is_bg_light: target_v = max(0, target_v - 0.1)
            else: target_v = min(1.0, target_v + 0.1)
            
            tr, tg, tb = colorsys.hsv_to_rgb(h, s, target_v)
            t_rgb = (int(tr*255), int(tg*255), int(tb*255))
            if contrast_ratio(t_rgb, bg_rgb) >= min_contrast:
                generated = "#{:02X}{:02X}{:02X}".format(*t_rgb)
                break
        
        if generated and generated not in recommendations:
            recommendations.append(generated)
        
        fallback = "#000000" if is_bg_light else "#FFFFFF"
        if fallback not in recommendations: recommendations.append(fallback)
        
        return recommendations[:5]