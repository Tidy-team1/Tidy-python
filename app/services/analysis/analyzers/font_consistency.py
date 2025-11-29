from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult


class FontConsistencyAnalyzer(BaseAnalyzer):
    analyzer_type = "font_consistency"

    def analyze(self, prs):
        results: list[SlideIssueResult] = []

        for slide_index, slide in enumerate(prs.slides):
            issues: list[IssueResult] = []

            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue

                # 텍스트 요소만 검토
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        font_size = run.font.size.pt if run.font.size else None

                        if font_size and font_size != 14:
                            issues.append(
                                IssueResult(
                                    type=self.analyzer_type,
                                    message="폰트 크기가 일관되지 않습니다.",
                                    element=IssueElement(
                                        shapeId=id(shape),
                                        elementIndex=0,  # 필요하면 shape 인덱싱 생성 가능
                                        bboxLeft=shape.left,
                                        bboxTop=shape.top,
                                        bboxWidth=shape.width,
                                        bboxHeight=shape.height,
                                        text=run.text,
                                        elementType="text"
                                    ),
                                    details={
                                        "currentSize": font_size,
                                        "recommendedSize": 14
                                    }
                                )
                            )

            if issues:
                results.append(
                    SlideIssueResult(slide=slide_index, issues=issues)
                )

        return results
