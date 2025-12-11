# app/services/analysis/analyzers/spelling_grammar.py
from typing import List, Dict, Any
from pptx import Presentation

from app.services.analysis.base_analyzer import BaseAnalyzer
from app.models.analysis_dto import IssueElement, IssueResult, SlideIssueResult
from app.utils.llm_client import LLMClient
from app.utils.prompts import SPELLING_GRAMMAR_SYSTEM_PROMPT


class SpellingGrammarAnalyzer(BaseAnalyzer):
    analyzer_type = "spelling_grammar"

    def __init__(self):
        self.llm = LLMClient(model="gpt-4o")

    def analyze(self, prs: Presentation) -> list[SlideIssueResult]:
        """
        이 Analyzer는 기본 analyze()는 사용하지 않고
        analyze_with_context() 방식만 사용.
        """
        return []

    def analyze_with_context(self, slides_data: list, existing_issues: dict) -> list[SlideIssueResult]:
        """
        slides_data + 기존 issues 기반 맞춤법/오타 교정.
        """
        llm_input_data = []
        for slide_data in slides_data:
            slide_index = slide_data["slide_index"]

            ctx = slide_data.copy()
            ctx["existing_issues"] = [
                {"type": i.type, "message": i.message, "details": i.details}
                for i in existing_issues.get(slide_index, [])
            ]
            llm_input_data.append(ctx)

        try:
            llm_response = self.llm.run(
                llm_payload=llm_input_data,
                system_prompt=SPELLING_GRAMMAR_SYSTEM_PROMPT
            )

            # 🔥 디버깅 로그 출력
            print("\n======= [SpellingGrammarAnalyzer LLM RAW RESPONSE] =======")
            print(llm_response)
            print("==========================================================\n")

            return self._parse_llm_response(llm_response, slides_data)

        except Exception as e:
            print(f"[WARN] Spelling/Grammar LLM failed: {e}")
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

            for slide_item in target_list:
                if not isinstance(slide_item, dict):
                    continue

                slide_idx = slide_item.get("slide")
                if slide_idx is None:
                    continue

                original_slide = slides_lookup.get(slide_idx, {})
                
                # shape_id → original element lookup dict
                original_elements = {}
                for el in original_slide.get("elements", []):
                    original_elements[el["shape_id"]] = el
                    original_elements[str(el["shape_id"])] = el

                parsed_issues = []
                for issue_data in slide_item.get("issues", []):
                    if not isinstance(issue_data, dict):
                        continue

                    raw_elem = issue_data.get("element", {}) or {}
                    shape_id = raw_elem.get("shapeId")

                    # 기본값
                    final_element = IssueElement()

                    # hydration: shapeId 기반 원본 element 매핑
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
                        final_element = IssueElement(**raw_elem) if raw_elem else IssueElement()

                    parsed_issues.append(
                        IssueResult(
                            type=issue_data.get("type", "spelling_grammar"),
                            message=issue_data.get("message", ""),
                            element=final_element,
                            details=issue_data.get("details", {})
                        )
                    )

                if parsed_issues:
                    results.append(
                        SlideIssueResult(slide=slide_idx, issues=parsed_issues)
                    )

        except Exception as e:
            print(f"[WARN] Parsing spelling/grammar LLM response failed: {e}")

        return results
