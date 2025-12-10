# app/services/analysis/utils/text_summarizer.py
import json
from .llm_client import LLMClient
from .prompts import build_summary_prompt


class TextSummarizer:
    """슬라이드 텍스트 요약 전용 유틸리티"""
    
    def __init__(self, model: str = "gpt-4.1"):
        self.llm = LLMClient(model=model)

    def summarize(self, text: str) -> dict | None:
        """
        긴 텍스트를 bullet point로 요약
        
        Returns:
            {
                "summary_bullets": ["요약 1", "요약 2", ...]
            }
        """
        if not text:
            return None

        lines = text.strip().splitlines()
        if len(lines) < 5 and len(text) < 50:
            return None  # 충분히 짧음

        prompt = build_summary_prompt(text)

        try:
            output = self.llm.run(
                llm_payload={"text": text},
                system_prompt=prompt
            )

            # ```json 제거
            if isinstance(output, str):
                if "```json" in output:
                    output = output.split("```json")[1].split("```")[0]
                elif "```" in output:
                    output = output.split("```")[1].split("```")[0]
                output = json.loads(output)

            return output

        except Exception as e:
            print(f"[WARN] Text summarization failed: {e}")
            return None