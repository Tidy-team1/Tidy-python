# app/services/analysis/analyzers/color_contrast.py
import colorsys
from pptx import Presentation
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.ppt_parser import parse_presentation
from app.utils.color_utils import hex_to_rgb, contrast_ratio  

class ColorContrastAnalyzer(BaseAnalyzer):
    analyzer_type = "color_contrast"

    def __init__(self):
        self.min_contrast_large = 3.0
        self.min_contrast_normal = 4.5

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        parsed = parse_presentation(prs)
        results = []
        
        for slide_data in parsed["slides"]:
            slide_idx = slide_data["slide_index"]
            slide_issues = []
            
            bg_hex = slide_data.get("background_color", "#FFFFFF")
            bg_rgb = hex_to_rgb(bg_hex)
            # 팔레트 정보 가져오기
            palette = slide_data.get("palette_hex", [])
            
            for el in slide_data["elements"]:
                if el["type"] != "text":
                    continue
                
                text_color = el.get("textColor")
                if not text_color:
                    continue
                
                try:
                    fg_rgb = hex_to_rgb(text_color)
                except:
                    continue
                
                # 배경색 확인 (도형 채우기 > 슬라이드 배경)
                element_bg = bg_rgb
                if el.get("fillColor"):
                    try:
                        element_bg = hex_to_rgb(el["fillColor"])
                    except:
                        pass
                
                # 대비율 계산
                cr = contrast_ratio(fg_rgb, element_bg)
                
                font_size = el.get("fontSize", 14.0)
                is_bold = el.get("isBold", False)
                is_large = (font_size >= 18) or (font_size >= 14 and is_bold)
                min_cr = self.min_contrast_large if is_large else self.min_contrast_normal
                
                if cr < min_cr:
                    # [수정] 개선된 추천 로직 호출
                    recommended = self._recommend_better_colors(
                        fg_hex=text_color,
                        bg_rgb=element_bg,
                        palette=palette,
                        min_contrast=min_cr
                    )
                    
                    text_type = "제목" if is_large else "본문"
                    
                    slide_issues.append(
                        IssueResult(
                            type=self.analyzer_type,
                            message=f"{text_type} 텍스트 색상({text_color})이 배경과 충분한 대비를 이루지 않습니다. (대비율: {cr:.2f}, 필요: {min_cr})",
                            element=IssueElement(
                                shapeId=el["shape_id"],
                                elementIndex=el["element_index"],
                                bboxLeft=el["left"],
                                bboxTop=el["top"],
                                bboxWidth=el["width"],
                                bboxHeight=el["height"],
                                text=el["text"],
                                elementType="text"
                            ),
                            details={
                                "current": text_color,
                                "contrast": round(cr, 2),
                                "required": min_cr,
                                "recommended": recommended
                            }
                        )
                    )
            
            # 이슈가 없어도 결과 객체는 반환할 수 있으나, 여기선 이슈 있을 때만 issues 채움
            if slide_issues:
                results.append(SlideIssueResult(slide=slide_idx, issues=slide_issues))
        
        return results

    def _recommend_better_colors(self, fg_hex, bg_rgb, palette, min_contrast):
        """
        1. 팔레트 색상 중 대비 만족하는 것 (Hue 차이 적은 순)
        2. 현재 색상의 명도를 조절한 색상 (Tone-on-tone)
        3. 기본 흑/백
        순서로 추천 목록 생성
        """
        recommendations = []
        
        try:
            fg_rgb = hex_to_rgb(fg_hex)
        except:
            return ["#000000", "#FFFFFF"] # Fallback

        # RGB -> HSV 변환
        r, g, b = fg_rgb[0]/255.0, fg_rgb[1]/255.0, fg_rgb[2]/255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        # 1. 팔레트 색상 우선 검색
        valid_palette_colors = []
        for p_hex in palette:
            try:
                p_rgb = hex_to_rgb(p_hex)
                if contrast_ratio(p_rgb, bg_rgb) >= min_contrast:
                    # 원래 색상과 Hue 차이 계산 (유사한 색조 우선)
                    pr, pg, pb = p_rgb[0]/255.0, p_rgb[1]/255.0, p_rgb[2]/255.0
                    ph, _, _ = colorsys.rgb_to_hsv(pr, pg, pb)
                    hue_diff = abs(h - ph)
                    valid_palette_colors.append((hue_diff, p_hex))
            except:
                continue
        
        # Hue 차이 적은 순 정렬 -> 색상 코드만 추출
        valid_palette_colors.sort(key=lambda x: x[0])
        recommendations.extend([c[1] for c in valid_palette_colors])

        # 2. 현재 색상 명도/채도 조절 (Tone-on-tone)
        # 배경이 밝으면 -> 텍스트를 어둡게 (Value 감소)
        # 배경이 어두우면 -> 텍스트를 밝게 (Value 증가)
        bg_lum = (0.299 * bg_rgb[0] + 0.587 * bg_rgb[1] + 0.114 * bg_rgb[2])
        is_bg_light = bg_lum > 128
        
        generated_color = None
        if is_bg_light:
            # 어둡게 만들기 (v를 0.1씩 감소)
            target_v = v
            while target_v > 0:
                target_v = max(0, target_v - 0.1)
                tr, tg, tb = colorsys.hsv_to_rgb(h, s, target_v)
                t_rgb = (int(tr*255), int(tg*255), int(tb*255))
                if contrast_ratio(t_rgb, bg_rgb) >= min_contrast:
                    generated_color = "#{:02X}{:02X}{:02X}".format(*t_rgb)
                    break
        else:
            # 밝게 만들기 (v를 0.1씩 증가)
            target_v = v
            while target_v < 1.0:
                target_v = min(1.0, target_v + 0.1)
                tr, tg, tb = colorsys.hsv_to_rgb(h, s, target_v)
                t_rgb = (int(tr*255), int(tg*255), int(tb*255))
                if contrast_ratio(t_rgb, bg_rgb) >= min_contrast:
                    generated_color = "#{:02X}{:02X}{:02X}".format(*t_rgb)
                    break
        
        if generated_color and generated_color not in recommendations:
            recommendations.append(generated_color)

        # 3. 최후의 수단 (완전 검정 or 완전 흰색)
        fallback = "#000000" if is_bg_light else "#FFFFFF"
        if fallback not in recommendations:
            recommendations.append(fallback)

        return recommendations[:5] # 최대 5개 반환