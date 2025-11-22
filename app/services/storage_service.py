# app/services/storage_service.py
import boto3
from app.core.config import settings


### ======================
### S3 CLIENT (IAM Role or Local credentials)
### ======================

def get_s3_client():
    """
    dev 환경 → IAM ROLE 자동 인증
    local 환경 → ~/.aws/credentials 사용
    """
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
