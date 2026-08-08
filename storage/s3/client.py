import boto3
from pathlib import Path

from config.settings import settings


class S3Client:
    def __init__(self):
        self.bucket = settings.s3_bucket_name
        # ponytail: local-disk fallback when S3 is unconfigured so dev uploads work
        # without AWS. swap path handling if a real storage layer is added.
        self._local_root = (
            Path(__file__).resolve().parent.parent.parent / "storage_local"
        )

    def _remote(self):
        return bool(self.bucket and settings.aws_access_key_id)

    def _local_path(self, key: str) -> Path:
        return self._local_root / key

    def upload_fileobj(self, fileobj, key: str, content_type: str = None):
        if self._remote():
            extra = {"ContentType": content_type} if content_type else {}
            self._client().upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra)
            return key
        target = self._local_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as fh:
            fh.write(fileobj.read())
        fileobj.seek(0)
        return key

    def download(self, key: str) -> bytes:
        if self._remote():
            body = self._client().get_object(Bucket=self.bucket, Key=key)["Body"]
            return body.read()
        with open(self._local_path(key), "rb") as fh:
            return fh.read()

    def delete(self, key: str):
        if self._remote():
            self._client().delete_object(Bucket=self.bucket, Key=key)
            return
        path = self._local_path(key)
        if path.exists():
            path.unlink()

    def generate_url(self, key: str, expires: int = 3600) -> str:
        if self._remote():
            return self._client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires,
            )
        return f"/storage_local/{key}"

    def _client(self):
        return boto3.client(
            "s3",
            region_name=settings.aws_region or None,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )


s3_client = S3Client()