from urllib.parse import urlparse

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
    except ClientError:
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

    _ensure_download_cors()


def _ensure_download_cors() -> None:
    """Allow browsers to GET presigned video URLs after an API redirect."""
    try:
        get_s3_client().put_bucket_cors(
            Bucket=settings.s3_bucket,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedOrigins": ["*"],
                        "AllowedMethods": ["GET", "HEAD"],
                        "AllowedHeaders": ["*"],
                        "ExposeHeaders": [
                            "Content-Length",
                            "Content-Type",
                            "Content-Disposition",
                        ],
                        "MaxAgeSeconds": 3600,
                    }
                ]
            },
        )
    except ClientError:
        pass


def _host_is_private(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host or host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return True
    if host.startswith("192.168.") or host.startswith("10."):
        return True
    if host.startswith("172."):
        try:
            second = int(host.split(".")[1])
            if 16 <= second <= 31:
                return True
        except (IndexError, ValueError):
            return False
    return False


def s3_downloads_are_public() -> bool:
    """True when phones can fetch a presigned URL without going through the API."""
    public = (settings.s3_public_endpoint_url or "").strip()
    if public:
        return not _host_is_private(public)
    endpoint = (settings.s3_endpoint_url or "").strip()
    if not endpoint:
        return True
    return not _host_is_private(endpoint)


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


def generate_download_url(
    key: str,
    expires_in: int = 3600,
    filename: str | None = None,
) -> str:
    client = get_s3_client()
    params: dict = {"Bucket": settings.s3_bucket, "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    url = client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
    )
    public = settings.s3_public_endpoint_url
    endpoint = settings.s3_endpoint_url
    if public and endpoint:
        url = url.replace(endpoint.rstrip("/"), public.rstrip("/"))
    return url
