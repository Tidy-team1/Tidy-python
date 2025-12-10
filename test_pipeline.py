import sys
import os
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from pprint import pprint

# =========================================================================
# 🛑 [중요] 앱이 로드되기 전에 환경 변수와 모듈을 먼저 가짜(Mock)로 설정해야 합니다.
# =========================================================================

# 1. 가짜 환경 변수 주입 (config.py 에러 방지용)
os.environ["AWS_ACCESS_KEY_ID"] = "fake_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "fake_secret"
os.environ["AWS_S3_BUCKET_NAME"] = "fake_bucket"
os.environ["AWS_REGION"] = "ap-northeast-2"
#os.environ["OPENAI_API_KEY"] = "fake_openai_key" # 실제 키는 llm_client나 여기에 넣으세요

# 2. boto3 라이브러리 가짜(Mock) 처리 (설치 안 해도 에러 안 나게 함)
sys.modules["boto3"] = MagicMock()
sys.modules["botocore"] = MagicMock()
sys.modules["botocore.exceptions"] = MagicMock()

# =========================================================================
# 🚀 이제 앱 모듈을 Import 합니다.
# =========================================================================

# 프로젝트 루트 경로 추가 (app 모듈을 찾기 위함)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.analysis.review_analysis_service import analyze_review

# ==========================================
# ⚙️ 테스트 설정 (이 경로만 본인 PC에 맞게 수정!)
# ==========================================

# 1. 테스트할 로컬 PPTX 파일 절대 경로
TEST_PPTX_PATH = r"C:\Users\naeun\capstone_1\Tidy-python\test.pptx"
# TEST_PPTX_PATH = r"C:\Users\naeun\capstone_1\Tidy-python\2W4FR5QCNIDWDPDHSOPQRQFPNBUSU5HJ.pptx"

# 2. 테스트할 분석 옵션들
TEST_OPTIONS = [
    "readability", 
    "color_contrast", 
    # "clip_aesthetic",   
    "image_contrast",
    "llm_feedback",
    "text_summarization",
    "readability",
    "design_feedback"
]

MOCK_SPACE_ID = 1
MOCK_PRESENTATION_ID = 999 

# ==========================================

def run_test():
    print(f"[TEST] Starting pipeline test with file: {TEST_PPTX_PATH}")
    
    if not os.path.exists(TEST_PPTX_PATH):
        print(f"[ERROR] File not found: {TEST_PPTX_PATH}")
        return

    # S3 다운로드를 가로채서 로컬 파일 경로를 반환하도록 설정
    with patch('app.services.analysis.review_analysis_service.download_presentation') as mock_download:
        mock_download.return_value = TEST_PPTX_PATH
        
        try:
            # -------------------------------------------------
            # 🔥 핵심: 오케스트레이터 호출
            # -------------------------------------------------
            result = analyze_review(
                space_id=MOCK_SPACE_ID, 
                presentation_id=MOCK_PRESENTATION_ID, 
                options=TEST_OPTIONS
            )
            
            print("\n" + "="*50)
            print("✅ TEST SUCCESS: Pipeline finished successfully.")
            print("="*50 + "\n")
            
            # -------------------------------------------------
            # 💾 결과 확인 및 JSON 저장 로직
            # -------------------------------------------------
            
            # Pydantic 모델을 Dict로 변환
            try:
                result_dict = result.model_dump() # Pydantic v2
            except AttributeError:
                result_dict = result.dict()       # Pydantic v1
            
            # 1. 콘솔에 출력
            # pprint(result_dict)

            # 2. 파일로 저장 (보기 편하게)
            output_file = "analysis_result.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
                
            print(f"📂 결과가 파일로 저장되었습니다: {os.path.abspath(output_file)}")
            print("   (VS Code에서 이 파일을 열어서 포맷팅된 JSON을 확인하세요)")

        except Exception as e:
            print("\n" + "="*50)
            print(f"❌ TEST FAILED: {e}")
            print("="*50 + "\n")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()