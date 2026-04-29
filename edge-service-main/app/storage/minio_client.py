import time
from pathlib import Path

import boto3
from botocore.config import Config

from app.config import Settings


class MinioClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            use_ssl=settings.minio_secure,
            config=Config(proxies={}),
        )

    def upload_file(
        self,
        local_path: Path,
        object_key: str,
        bucket: str | None = None,
        content_type: str = "video/mp4",
    ) -> None:
        attempts = 0
        target_bucket = bucket or self.settings.minio_bucket
        while True:
            attempts += 1
            try:
                self.client.upload_file(
                    str(local_path),
                    target_bucket,
                    object_key,
                    ExtraArgs={"ContentType": content_type},
                )
                return
            except Exception:
                if attempts >= self.settings.max_retry_attempts:
                    raise
                time.sleep(self.settings.retry_base_sec * attempts)
