# app/services/storage_service.py
import boto3
import os
import tempfile
from app.core.config import settings
from app.utils.s3_utils import download_from_s3
from app.utils.s3_key_builder import original_ppt_key


### ======================
### S3 CLIENT (IAM Role or Local credentials)
### ======================

def get_s3_client():
    """
    dev 환경 → IAM ROLE 자동 인증 (환경변수 또는 EC2/ECS 메타데이터)
    local 환경 → 환경변수 또는 ~/.aws/credentials 사용
    """
    # 환경변수로 자격 증명이 제공되면 사용
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key_id and aws_secret_access_key:
        # 환경변수로 자격 증명 제공
        return boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    else:
        # 환경변수가 없으면 boto3의 기본 자격 증명 체인 사용
        # (IAM Role, ~/.aws/credentials, 환경변수 순서로 자동 탐색)
        return boto3.client("s3", region_name=settings.AWS_REGION)


### ======================
### S3 SAVE (항상 S3 사용)
### ======================

def save_file_s3(s3_key: str, data: bytes) -> str:
    s3 = get_s3_client()

    s3.put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=data
    )

    # S3 public URL (필요 시 presigned URL 사용 가능)
    return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


### ======================
### MAIN ENTRY (무조건 S3)
### ======================

def save_file(key: str, data: bytes) -> str:
    """
    항상 S3에 저장
    """
    return save_file_s3(key, data)


### ======================
### DELETE entire presentation folder in S3
### ======================

def delete_presentation_folder(space_id: int, presentation_id: int):
    """
    S3에서 프레젠테이션 전체 폴더 삭제 (로컬에서도 S3 삭제)
    """
    s3 = get_s3_client()
    prefix = f"spaces/{space_id}/presentations/{presentation_id}/"

    # List all objects under prefix
    response = s3.list_objects_v2(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Prefix=prefix
    )

    if "Contents" not in response:
        return

    delete_keys = [{"Key": obj["Key"]} for obj in response["Contents"]]

    s3.delete_objects(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Delete={"Objects": delete_keys}
    )

    print(f"[storage_service] Deleted presentation folder: {prefix}")


def download_presentation(space_id: int, presentation_id: int) -> str:
    """
    S3에서 pptx 파일을 로컬 임시 파일로 다운로드하여 로컬 경로 반환한다.
    예: /tmp/tmpabcd1234.pptx
    """

    # 1) S3 key 생성
    s3_key = original_ppt_key(space_id, presentation_id)
    # 예: "spaces/{spaceId}/presentations/{presId}/file.pptx"

    # 2) 로컬 temp 파일 생성
    _, tmp_path = tempfile.mkstemp(suffix=".pptx")

    # 3) 다운로드 실행
    download_from_s3(s3_key, tmp_path)

    return tmp_path