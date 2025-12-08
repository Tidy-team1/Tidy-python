# app/services/analysis/utils/ppt_parser.py
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from pptx import Presentation
from pptx.enum.dml import MSO_FILL, MSO_COLOR_TYPE
from pptx.dml.color import RGBColor

from app.utils.ppt_utils import emu_to_px

# =========================================================
# 🔹 Internal Utils (Migrated from parsing.py)
# =========================================================

def _rgb_to_hex(rgb: Tuple[int, int, int]) -> Optional[str]:
    """RGB 튜플을 Hex 문자열로 변환"""
    if not rgb:
        return None
    try:
        return "#{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])
    except Exception:
        return None

def _normalize_hex(s: str) -> Optional[str]:
    """색상 문자열 정규화"""
    if not s:
        return None
    s = str(s).strip()
    if s.startswith('#') and len(s) == 7:
        return s.upper()
    if len(s) == 6:
        return '#' + s.upper()
    return None

def _load_theme_colors(pptx_path: Path) -> Dict[str, Tuple[int, int, int]]:
    """
    PPTX 파일 내부의 theme1.xml을 파싱하여 테마 색상(accent1, dk1 등) 매핑 정보를 추출합니다.
    """
    if not pptx_path:
        return {}
        
    theme_map = {}
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            # theme1.xml 찾기
            theme_files = [f for f in z.namelist() if f.startswith("ppt/theme/theme")]
            if not theme_files:
                return {}

            with z.open(theme_files[0]) as theme_xml:
                tree = ET.parse(theme_xml)
                root = tree.getroot()
                # 네임스페이스 처리
                ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                
                # clrScheme 내부 순회
                theme_elems = root.findall(".//a:themeElements/a:clrScheme/*", ns)
                for elem in theme_elems:
                    # 태그 이름 (dk1, lt1, accent1, ...)
                    name = elem.tag.split("}")[-1].lower()
                    
                    # srgbClr (Hex 값) 찾기
                    srgb = elem.find(".//a:srgbClr", ns)
                    if srgb is not None and "val" in srgb.attrib:
                        hex_code = srgb.attrib["val"]
                        if len(hex_code) == 6:
                            r = int(hex_code[0:2], 16)
                            g = int(hex_code[2:4], 16)
                            b = int(hex_code[4:6], 16)
                            theme_map[name] = (r, g, b)
                            
                    # sysClr (시스템 컬러) 예외 처리 (흰색/검은색 등)
                    sys_clr = elem.find(".//a:sysClr", ns)
                    if sys_clr is not None and "lastClr" in sys_clr.attrib:
                         hex_code = sys_clr.attrib["lastClr"]
                         if len(hex_code) == 6:
                            r = int(hex_code[0:2], 16)
                            g = int(hex_code[2:4], 16)
                            b = int(hex_code[4:6], 16)
                            theme_map[name] = (r, g, b)

    except Exception as e:
        print(f"[WARN] Failed to load theme_colors: {e}")
    
    return theme_map

def _get_safe_color(color_obj, theme_map: Dict) -> Optional[str]:
    """
    ColorFormat 객체에서 색상을 안전하게 추출 (RGB 우선 -> 테마 색상 매핑)
    """
    if not color_obj:
        return None
    
    try:
        # 1. RGB 직접 정의된 경우
        if color_obj.type == MSO_COLOR_TYPE.RGB:
            return _rgb_to_hex(color_obj.rgb)
        
        # 2. 테마 색상인 경우 (ACCENT_1 등)
        if color_obj.type == MSO_COLOR_TYPE.THEME:
            if color_obj.theme_color:
                # python-pptx의 theme_color enum을 문자열 키로 변환 (예: MSO_THEME_COLOR.ACCENT_1 -> 'accent1')
                # 여기서는 단순화를 위해 문자열 변환 시도
                theme_key = str(color_obj.theme_color).split('.')[-1].lower()
                # 매핑 테이블에서 조회
                rgb_tuple = theme_map.get(theme_key)
                if rgb_tuple:
                    return _rgb_to_hex(rgb_tuple)
    except Exception:
        pass
        
    return None

def _get_slide_background_color(slide, theme_map: Dict) -> str:
    """
    슬라이드 배경색 추출 (Slide -> Layout -> Master 순서)
    """
    def extract_from_bg(bg):
        if not bg: return None
        fill = bg.fill
        if not fill: return None
        
        try:
            # Solid Fill 인 경우
            if fill.type == MSO_FILL.SOLID:
                return _get_safe_color(fill.fore_color, theme_map)
        except:
            pass
        return None

    # 1. Slide 자체 배경
    color = extract_from_bg(slide.background)
    if color: return color

    # 2. Layout 배경
    if slide.slide_layout:
        color = extract_from_bg(slide.slide_layout.background)
        if color: return color
        
        # 3. Master 배경
        if slide.slide_layout.slide_master:
            color = extract_from_bg(slide.slide_layout.slide_master.background)
            if color: return color

    return "#FFFFFF"  # 기본값


# =========================================================
# 🔹 Main Logic
# =========================================================

def parse_presentation(prs: Presentation, pptx_path: Path = None) -> Dict:
    """
    prs 객체를 분석하여 표준 JSON 구조로 변환
    """
    # 1. 테마 색상 로드 (pptx 파일 경로가 있을 때만 가능)
    theme_map = {}
    if pptx_path and Path(pptx_path).exists():
        theme_map = _load_theme_colors(Path(pptx_path))
    
    slides_data = []
    
    for slide_idx, slide in enumerate(prs.slides):
        # 배경색 추출
        bg_hex = _get_slide_background_color(slide, theme_map) or "#FFFFFF"
        
        elements = []
        palette_colors = set()
        
        # 배경색도 팔레트에 추가 (분석 시 중요)
        palette_colors.add(bg_hex)
        
        for el_idx, shape in enumerate(slide.shapes):
            elem = {
                "shape_id": shape.shape_id,
                "element_index": el_idx,
                "type": None,
                "text": None,
                "left": emu_to_px(shape.left),
                "top": emu_to_px(shape.top),
                "width": emu_to_px(shape.width),
                "height": emu_to_px(shape.height),
                "fontSize": None,
                "isBold": False,
                "textColor": None,
                "fillColor": None,
                "image_path": None
            }
            
            # 1) 텍스트 요소
            if shape.has_text_frame:
                elem["type"] = "text"
                elem["text"] = shape.text.strip()
                
                # 첫 번째 문단의 첫 번째 run을 기준으로 스타일 추출
                if shape.text_frame.paragraphs:
                    first_para = shape.text_frame.paragraphs[0]
                    if first_para.runs:
                        run = first_para.runs[0]
                        
                        # 폰트 크기
                        if run.font.size:
                            elem["fontSize"] = run.font.size.pt
                        
                        # Bold
                        elem["isBold"] = run.font.bold or False
                        
                        # 텍스트 색상
                        try:
                            t_color = _get_safe_color(run.font.color, theme_map)
                            if t_color:
                                elem["textColor"] = t_color
                                palette_colors.add(t_color)
                        except:
                            pass
                
                # 도형 Fill 색상 (텍스트 박스 배경)
                try:
                    if shape.fill.type == MSO_FILL.SOLID:
                        f_color = _get_safe_color(shape.fill.fore_color, theme_map)
                        if f_color:
                            elem["fillColor"] = f_color
                            palette_colors.add(f_color)
                except:
                    pass
            
            # 2) 이미지 요소
            elif shape.shape_type == 13:  # PICTURE
                elem["type"] = "image"
                # 이미지는 별도 추출 과정(slide_renderer)을 통해 생성되므로 경로 패턴만 지정
                # 실제 파일 생성은 orchestrator의 export_slide_images가 담당
                elem["image_path"] = f"extracted_images/slide_{slide_idx+1}_{shape.shape_id}.png"
            
            elements.append(elem)
        
        slides_data.append({
            "slide_index": slide_idx,
            "background_color": bg_hex,
            "palette_hex": list(palette_colors),
            "elements": elements
        })
    
    return {"slides": slides_data}