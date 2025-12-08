# app/services/analysis/analyzers/readability.py
from pptx import Presentation
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.ppt_parser import parse_presentation


class ReadabilityAnalyzer(BaseAnalyzer):
    analyzer_type = "readability"

    def __init__(self):
        self.max_text_chars = 150
        self.max_text_density = 0.4

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        parsed = parse_presentation(prs)
        results = []
        
        slide_area = prs.slide_width * prs.slide_height
        
        for slide_data in parsed["slides"]:
            slide_idx = slide_data["slide_index"]
            slide_issues = []
            
            all_text = "\n".join(
                el["text"] for el in slide_data["elements"]
                if el["type"] == "text" and el["text"]
            )
            char_count = len(all_text)
            
            # [수정] 점수 계산 로직 (간단한 예시: 300자 넘으면 0점, 적을수록 1.0에 가까움)
            # score = 1.0 - (현재글자수 / (권장글자수 * 2))  (최소 0)
            # 권장 150자일 때, 150자면 0.5점, 0자면 1.0점, 300자면 0.0점
            base_score = 1.0 - (char_count / (self.max_text_chars * 2))
            readability_score = max(0.0, min(1.0, base_score))

            # 이슈 생성 로직 (기존과 동일)
            if char_count > self.max_text_chars:
                slide_issues.append(
                    IssueResult(
                        type="too_much_text",
                        message=f"슬라이드에 텍스트가 과다합니다 ({char_count}자)",
                        element=IssueElement(),
                        details={"current": char_count, "recommended": self.max_text_chars}
                    )
                )
            
            # 2) 텍스트 밀도
            text_area = sum(
                (el["width"] * el["height"])
                for el in slide_data["elements"]
                if el["type"] == "text"
            )
            
            density = text_area / slide_area if slide_area > 0 else 0
            
            if density > self.max_text_density:
                slide_issues.append(
                    IssueResult(
                        type="high_text_density",
                        message="텍스트가 슬라이드의 대부분을 차지합니다",
                        element=IssueElement(),
                        details={
                            "current": round(density, 3),
                            "recommended": self.max_text_density
                        }
                    )
                )
            
            results.append(
                SlideIssueResult(
                    slide=slide_idx, 
                    issues=slide_issues,
                    readability_score=readability_score # 점수 할당
                )
            )
        
        return results