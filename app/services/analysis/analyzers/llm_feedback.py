# app/services/analysis/analyzers/llm_feedback.py

from typing import List, Dict, Any
from pptx import Presentation

from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.llm_client import LLMClient
from app.utils.prompts import LLM_FEEDBACK_SYSTEM_PROMPT

class LLMFeedbackAnalyzer(BaseAnalyzer):
    analyzer_type = "llm_feedback"

    def __init__(self):
        self.llm = LLMClient(model="gpt-4o")

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        return []

    def analyze_with_context(self, slides_data: list, existing_issues: dict) -> list[SlideIssueResult]:
        llm_input_data = []
        for slide_data in slides_data:
            slide_idx = slide_data["slide_index"]
            ctx = slide_data.copy()
            ctx["existing_issues"] = [
                {"type": i.type, "message": i.message, "details": i.details}
                for i in existing_issues.get(slide_idx, [])
            ]
            llm_input_data.append(ctx)

        try:
            llm_response = self.llm.run(
                llm_payload=llm_input_data,
                system_prompt=LLM_FEEDBACK_SYSTEM_PROMPT
            )
            return self._parse_llm_response(llm_response, slides_data)
        
        except Exception as e:
            print(f"[WARN] LLM feedback failed: {e}")
            return []

    def _parse_llm_response(self, llm_raw, slides_data_list) -> list[SlideIssueResult]:
        results = []
        slides_lookup = {s["slide_index"]: s for s in slides_data_list}

        try:
            target_list = []
            if isinstance(llm_raw, list):
                target_list = llm_raw
            elif isinstance(llm_raw, dict):
                target_list = llm_raw.get("slides") or llm_raw.get("results") or []

            for item in target_list:
                if not isinstance(item, dict): continue
                
                slide_idx = item.get("slide")
                if slide_idx is None: continue

                original_slide = slides_lookup.get(slide_idx, {})
                # [수정] shape_id를 문자열과 정수 모두 매칭 가능하도록 처리
                original_elements = {}
                for el in original_slide.get("elements", []):
                    original_elements[el["shape_id"]] = el          # int key
                    original_elements[str(el["shape_id"])] = el     # str key

                parsed_issues = []
                for issue_data in item.get("issues", []):
                    if not isinstance(issue_data, dict): continue
                    
                    raw_elem = issue_data.get("element", {})
                    shape_id = raw_elem.get("shapeId")
                    
                    final_element = IssueElement()
                    
                    # [수정] Hydration: shapeId로 원본 데이터 찾기
                    if shape_id is not None and shape_id in original_elements:
                        orig = original_elements[shape_id]
                        final_element = IssueElement(
                            shapeId=orig["shape_id"],
                            elementIndex=orig["element_index"],
                            bboxLeft=orig["left"],
                            bboxTop=orig["top"],
                            bboxWidth=orig["width"],
                            bboxHeight=orig["height"],
                            text=raw_elem.get("text") or orig["text"],
                            elementType=orig["type"]
                        )
                    else:
                        # 매칭 실패 시 LLM 값이라도 넣음
                        final_element = IssueElement(**raw_elem) if raw_elem else IssueElement()

                    issue = IssueResult(
                        type=issue_data.get("type", "llm_feedback"),
                        message=issue_data.get("message", ""),
                        element=final_element,
                        details=issue_data.get("details", {})
                    )
                    parsed_issues.append(issue)
                
                if parsed_issues:
                    results.append(SlideIssueResult(slide=slide_idx, issues=parsed_issues))
                    
        except Exception as e:
            print(f"[WARN] Parsing LLM response failed: {e}")
        
        return results