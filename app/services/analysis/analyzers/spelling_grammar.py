from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.services.analysis.base_analyzer import BaseAnalyzer

class SpellingGrammarAnalyzer(BaseAnalyzer):
    analyzer_type = "spelling_grammar"

    def analyze(self, prs):
        """
        실제 분석 대신 Mock 결과 반환
        """

        slide0_issues = [
            IssueResult(
                type=self.analyzer_type,
                message="맞춤법 오류가 있습니다.",
                element=IssueElement(
                    shapeId=101,
                    elementIndex=0,
                    bboxLeft=100,
                    bboxTop=200,
                    bboxWidth=300,
                    bboxHeight=60,
                    text="안녕하세요 저는 개발자 입니닼ㅋㅋ",
                    elementType="text"
                ),
                details={
                    "wrong": "입니닼",
                    "suggestion": "입니다"
                }
            )
        ]

        slide1_issues = [
            IssueResult(
                type=self.analyzer_type,
                message="조사 사용이 잘못되었습니다.",
                element=IssueElement(
                    shapeId=102,
                    elementIndex=3,
                    bboxLeft=150,
                    bboxTop=180,
                    bboxWidth=350,
                    bboxHeight=70,
                    text="내가 너를 좋아해",
                    elementType="text"
                ),
                details={
                    "wrongPart": "내가 너를",
                    "suggestion": "내가 너를(문맥에 따라 다름)"
                }
            )
        ]

        return [
            SlideIssueResult(slide=0, issues=slide0_issues),
            SlideIssueResult(slide=1, issues=slide1_issues)
        ]
