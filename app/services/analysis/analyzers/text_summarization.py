# app/services/analysis/analyzers/text_summarization.py
from pptx import Presentation
from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.ppt_parser import parse_presentation
from app.utils.text_summarizer import TextSummarizer


class TextSummarizationAnalyzer(BaseAnalyzer):
    analyzer_type = "text_summarization"

    def __init__(self):
        self.summarizer = TextSummarizer(model="gpt-4.1")
        self.min_lines = 5
        self.min_chars = 50

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        parsed = parse_presentation(prs)
        results = []
        
        for slide_data in parsed["slides"]:
            slide_idx = slide_data["slide_index"]
            text_elements = [el for el in slide_data["elements"] if el["type"] == "text" and el["text"]]
            full_text = "\n".join(
                el["text"] for el in slide_data["elements"]
                if el["type"] == "text" and el["text"]
            )
            
            lines = full_text.strip().splitlines()
            
            if len(lines) >= self.min_lines or len(full_text) >= self.min_chars:
                # 요약 호출
                summary_result = self.summarizer.summarize(full_text)
                
                if summary_result and "summary_bullets" in summary_result:
                    recommended = summary_result["summary_bullets"]
                else:
                    recommended = ["자동 요약 불가, 수동 요약 필요"]

                main_element = None
                if text_elements:
                    # 텍스트 길이 순으로 정렬하여 가장 긴 요소를 대표로 설정
                    main_element = sorted(text_elements, key=lambda x: len(x["text"]), reverse=True)[0]

                if main_element:
                    issue_elem = IssueElement(
                        shapeId=main_element["shape_id"],
                        elementIndex=main_element["element_index"],
                        bboxLeft=main_element["left"],
                        bboxTop=main_element["top"],
                        bboxWidth=main_element["width"],
                        bboxHeight=main_element["height"],
                        text=full_text, # 텍스트는 전체 텍스트
                        elementType="text_summary"
                    )
                else:
                    # 텍스트 요소가 없는데 텍스트가 추출된 경우
                    issue_elem = IssueElement(text=full_text)
                
                results.append(
                    SlideIssueResult(
                        slide=slide_idx,
                        issues=[
                            IssueResult(
                                type=self.analyzer_type,
                                message="한 슬라이드에 텍스트가 너무 많으므로 요약 정리 필요",
                                element=issue_elem,
                                # element=IssueElement(text=full_text),
                                details={
                                    "current": full_text,
                                    "recommend": recommended
                                }
                            )
                        ]
                    )
                )
        
        return results