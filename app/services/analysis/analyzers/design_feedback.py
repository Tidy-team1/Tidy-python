# app/services/analysis/analyzers/design_feedback.py

from typing import List, Dict, Any
from pptx import Presentation

from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import SlideIssueResult, IssueResult, IssueElement
from app.utils.llm_client import LLMClient
from app.utils.prompts import DESIGN_FEEDBACK_SYSTEM_PROMPT, build_design_feedback_prompt

class DesignFeedbackAnalyzer(BaseAnalyzer):
    """
    슬라이드별 종합 디자인 조언(자연어)을 생성하는 분석기
    """
    analyzer_type = "design_feedback"

    def __init__(self):
        # API Key는 LLMClient 내부 또는 환경변수에서 처리
        self.llm = LLMClient(model="gpt-4o")

    def analyze(self, prs: Presentation) -> List[SlideIssueResult]:
        """
        단독 실행 시에는 동작하지 않거나, orchestrator에서 parsed_data를 주입받아야 함.
        구조상 orchestrator가 analyze_with_context를 호출하도록 유도.
        """
        return []

    def analyze_with_context(self, slides_data: List[Dict[str, Any]], existing_issues: Dict[int, List[IssueResult]]) -> List[SlideIssueResult]:
        """
        Args:
            slides_data: 파싱된 슬라이드 정보
            existing_issues: 이미 발견된 이슈들 (이를 참고해서 피드백 작성)
        """
        # LLM에게 보낼 데이터 구성 (기존 이슈 포함)
        llm_input = []
        for s_data in slides_data:
            slide_idx = s_data["slide_index"]
            ctx = s_data.copy()
            # 기존 이슈 요약
            ctx["known_issues"] = [
                f"{issue.type}: {issue.message}" 
                for issue in existing_issues.get(slide_idx, [])
            ]
            llm_input.append(ctx)

        try:
            # LLM 호출
            response = self.llm.run(
                llm_payload=llm_input,
                system_prompt=DESIGN_FEEDBACK_SYSTEM_PROMPT
            )
            
            return self._parse_response(response)
            
        except Exception as e:
            print(f"[WARN] Design feedback failed: {e}")
            return []

    def _parse_response(self, response: Dict[str, Any]) -> List[SlideIssueResult]:
        results = []
        feedbacks = response.get("design_feedbacks", [])
        
        for item in feedbacks:
            slide_idx = item.get("slide")
            text = item.get("feedback")
            
            if slide_idx is not None and text:
                # "design_feedback" 타입의 이슈로 포장해서 반환
                issue = IssueResult(
                    type="design_feedback",
                    message=text,  # 여기에 긴 줄글 피드백이 들어감
                    element=IssueElement(), # 특정 요소가 아닌 슬라이드 전체에 대한 피드백
                    details={}
                )
                results.append(SlideIssueResult(slide=slide_idx, issues=[issue]))
                
        return results