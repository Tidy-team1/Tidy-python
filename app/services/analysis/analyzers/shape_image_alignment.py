from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer

class ShapeImageAlignmentAnalyzer(BaseAnalyzer):
    analyzer_type = "shape_image_alignment"

    def analyze(self, prs):
        """
        실제 분석 대신 Mock 결과 반환
        """

        slide0_issues = [
            IssueResult(
                type=self.analyzer_type,
                message="이미지와 텍스트 상자가 정렬되어 있지 않습니다.",
                element=IssueElement(
                    shapeId=201,
                    elementIndex=1,
                    bboxLeft=80,
                    bboxTop=120,
                    bboxWidth=200,
                    bboxHeight=200,
                    text=None,
                    elementType="image"
                ),
                details={
                    "alignment": "left",
                    "recommendedAlignment": "center"
                }
            )
        ]

        slide1_issues = [
            IssueResult(
                type=self.analyzer_type,
                message="두 요소의 간격이 너무 좁습니다.",
                element=IssueElement(
                    shapeId=202,
                    elementIndex=4,
                    bboxLeft=300,
                    bboxTop=220,
                    bboxWidth=350,
                    bboxHeight=120,
                    text="Some text",
                    elementType="text"
                ),
                details={
                    "gap": 6,
                    "minRecommendedGap": 20
                }
            )
        ]

        return [
            SlideIssueResult(slide=0, issues=slide0_issues),
            SlideIssueResult(slide=1, issues=slide1_issues)
        ]
