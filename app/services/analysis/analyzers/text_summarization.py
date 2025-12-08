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
                
                results.append(
                    SlideIssueResult(
                        slide=slide_idx,
                        issues=[
                            IssueResult(
                                type=self.analyzer_type,
                                message="한 슬라이드에 텍스트가 너무 많으므로 요약 정리 필요",
                                element=IssueElement(text=full_text),
                                details={
                                    "current": full_text,
                                    "recommend": recommended
                                }
                            )
                        ]
                    )
                )
        
        return results