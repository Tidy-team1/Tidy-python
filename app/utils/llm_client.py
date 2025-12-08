# app/utils/llm_client.py
import os
import json
from typing import Dict, Any, Optional, Union
from openai import OpenAI

class LLMClient:
    """
    OpenAI GPT Wrapper with strict JSON output.
    """

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        # 1순위: 생성자 인자로 들어온 key
        # 2순위: 환경변수 OPENAI_API_KEY
        # 3순위: 하드코딩된 Key (테스트용)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def run(self, llm_payload: Union[Dict, list], system_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
             return {"error": "API Key is missing"}

        try:
            # Payload가 딕셔너리나 리스트면 JSON 문자열로 변환
            if isinstance(llm_payload, (dict, list)):
                user_content = json.dumps(llm_payload, ensure_ascii=False)
            else:
                user_content = str(llm_payload)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            raw = response.choices[0].message.content
            
            if not raw:
                return {"error": "Empty response from LLM"}

            return json.loads(raw)

        except json.JSONDecodeError:
            return {
                "error": "JSON decoding failed", 
                "raw_output": raw if 'raw' in locals() else "No output"
            }
        except Exception as e:
            print(f"[ERROR] LLM run failed: {e}")
            return {"error": str(e)}