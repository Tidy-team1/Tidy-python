import os
from dotenv import load_dotenv

# PY_ENV에 따라 환경파일 로드
ENV = os.getenv("PY_ENV", "local")

if ENV == "dev":
    load_dotenv(".env.dev")
else:
    load_dotenv(".env.local")

# 환경변수가 없어도 동작하도록 docker-compose의 environment에서도 읽을 수 있도록 함
# .env 파일이 없어도 docker-compose의 environment에서 설정한 값 사용 가능


class Settings:
    # 현재 환경
    PY_ENV = ENV

    # 항상 S3 사용
    STORAGE_MODE = "s3"

    # S3 필수 설정 (환경변수 또는 docker-compose의 environment에서 읽음)
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")

    # boto3는 ~/.aws/credentials 자동 사용 → 별도 설정 필요 없음
    # AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    # AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    # 로컬 모드에서만 쓰던 경로는 제거 가능
    # LOCAL_BUCKET_PATH = None
    # LOCAL_TEMP_PATH = None


settings = Settings()

# Settings 인스턴스 생성 후 검증
if not settings.AWS_S3_BUCKET_NAME:
    raise ValueError("AWS_S3_BUCKET_NAME 환경변수가 설정되지 않았습니다.")
if not settings.AWS_REGION:
    raise ValueError("AWS_REGION 환경변수가 설정되지 않았습니다.")
