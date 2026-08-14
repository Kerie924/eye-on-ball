import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


def get_s3_client():
    kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "region_name": settings.s3_region,
        "config": Config(signature_version="s3v4"),
    }
    # Empty/None = real Amazon S3; set for MinIO or custom endpoints.
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client(**kwargs)


def ensure_bucket_exists() -> None:
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
        return
    except ClientError:
        pass

    params: dict = {"Bucket": settings.s3_bucket}
    # AWS requires LocationConstraint outside us-east-1; MinIO ignores it safely in most setups.
    if settings.s3_region and settings.s3_region != "us-east-1":
        params["CreateBucketConfiguration"] = {"LocationConstraint": settings.s3_region}
    try:
        client.create_bucket(**params)
    except ClientError as exc:
        # Bucket may already exist or be owned by us after a race.
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise


def upload_file(file_obj, key: str, content_type: str = "video/mp4") -> None:
    client = get_s3_client()
    client.upload_fileobj(
        file_obj,
        settings.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def delete_file(key: str) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)


def generate_download_url(key: str, expires_in: int = 3600) -> str:
    client = get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )
    public = settings.s3_public_endpoint_url
    endpoint = settings.s3_endpoint_url
    if public and endpoint:
        url = url.replace(endpoint.rstrip("/"), public.rstrip("/"))
    return url
