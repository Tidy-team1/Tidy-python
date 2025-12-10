import json
import boto3
import os
from botocore.exceptions import ClientError
from app.core.logger import logger

s3 = boto3.client("s3")
BUCKET = os.getenv("AWS_S3_BUCKET_NAME")

def download_from_s3(s3_key: str, dst_path: str):
    """
    S3의 특정 키 파일을 로컬 경로로 다운로드
    """
    try:
        s3.download_file(BUCKET, s3_key, dst_path)
        logger.info(f"[S3] Downloaded: s3://{BUCKET}/{s3_key} → {dst_path}")
        return dst_path
    except ClientError as e:
        logger.error(f"[S3] Download failed: {s3_key}  ({e})")
        raise

def upload_to_s3(src_path: str, s3_key: str):
    """
    로컬 파일을 S3의 지정된 Key에 업로드
    """
    try:
        s3.upload_file(src_path, BUCKET, s3_key)
        logger.info(f"[S3] Uploaded: {src_path} → s3://{BUCKET}/{s3_key}")
        return f"s3://{BUCKET}/{s3_key}"
    except ClientError as e:
        logger.error(f"[S3] Upload failed: {src_path}  ({e})")
        raise

def upload_json_to_s3(data: dict | list, s3_key: str):
    """
    JSON 데이터를 S3 특정 위치에 업로드
    """
    try:
        json_bytes = json.dumps(data).encode("utf-8")
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=json_bytes, ContentType="application/json")
        logger.info(f"[S3] JSON uploaded: s3://{BUCKET}/{s3_key}")
        return f"s3://{BUCKET}/{s3_key}"
    except ClientError as e:
        logger.error(f"[S3] JSON upload failed: {e}")
        raise

def read_s3_json(s3_key: str):
    """
    S3에 저장된 JSON 파일 읽기
    """
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
        data = json.loads(obj["Body"].read())
        logger.info(f"[S3] JSON loaded: s3://{BUCKET}/{s3_key}")
        return data
    except ClientError as e:
        logger.error(f"[S3] Read failed: {s3_key} ({e})")
        raise

def list_s3_files(prefix: str) -> list[str]:
    """
    특정 prefix 아래의 모든 S3키 리스트 얻기
    """
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        if "Contents" not in resp:
            return []

        keys = [item["Key"] for item in resp["Contents"]]
        logger.info(f"[S3] Files under {prefix}: {len(keys)} found")
        return keys

    except ClientError as e:
        logger.error(f"[S3] List failed: {prefix} ({e})")
        raise


# ======================
# 슬라이드 이미지 가져오기(버전 적용된 버전)
# ======================
def load_slide_images(space_id: int, presentation_id: int, version: int, tmpdir: str) -> list[str]:
    """
    S3에 저장된 슬라이드 이미지 (0.png, 1.png, ...)를 다운로드하여
    로컬 tmpdir 경로 리스트로 반환.
    """
    from app.utils.s3_key_builder import base_path

    # 1) Prefix 생성
    prefix = f"{base_path(space_id, presentation_id)}/v{version}/slides/"

    # 2) S3 파일 목록 불러오기
    slide_keys = list_s3_files(prefix)

    if not slide_keys:
        raise RuntimeError(
            f"No slide images found in S3: s3://{BUCKET}/{prefix}"
        )

    # 3) 파일명 숫자 기준 정렬
    #    Key 예: .../slides/0.png → 숫자만 추출하여 정렬
    def extract_number(key: str) -> int:
        filename = key.split("/")[-1]     # "0.png"
        num = filename.split(".")[0]      # "0"
        return int(num)

    slide_keys = sorted(slide_keys, key=extract_number)

    # 4) 다운로드
    local_paths = []
    os.makedirs(tmpdir, exist_ok=True)

    for key in slide_keys:
        filename = key.split("/")[-1]
        local_path = os.path.join(tmpdir, filename)
        download_from_s3(key, local_path)
        local_paths.append(local_path)

    logger.info(f"[S3] Loaded {len(local_paths)} slide images for analysis")
    return local_paths
