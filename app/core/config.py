import os
from dotenv import load_dotenv

# PY_ENV에 따라 환경파일 로드
ENV = os.getenv("PY_ENV", "local")

if ENV == "dev":
    load_dotenv(".env.dev")
else:
    load_dotenv(".env.local")


class Settings:
    # 현재 환경
    PY_ENV = ENV

    # 항상 S3 사용
    STORAGE_MODE = "s3"

    # S3 필수 설정
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")

    # boto3는 ~/.aws/credentials 자동 사용 → 별도 설정 필요 없음
    # AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    # AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    # 로컬 모드에서만 쓰던 경로는 제거 가능
    # LOCAL_BUCKET_PATH = None
    # LOCAL_TEMP_PATH = None


settings = Settings()
