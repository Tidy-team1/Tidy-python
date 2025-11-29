from app.models.analysis_dto import SlideIssueResult

class BaseAnalyzer:
    """
    모든 분석기 공통 구조 정의
    """

    analyzer_type: str = "base"

    def analyze(self, prs) -> list[SlideIssueResult]:
        """
        분석 결과를 SlideIssueResult 리스트로 반환해야 함
        """
        raise NotImplementedError("Analyzer must implement analyze()")
