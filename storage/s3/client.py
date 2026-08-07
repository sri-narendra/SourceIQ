import boto3

from config.settings import settings


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.aws_region or None,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self.bucket = settings.s3_bucket_name

    def upload_fileobj(self, fileobj, key: str, content_type: str = None):
        extra = {"ContentType": content_type} if content_type else {}
        self.client.upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra)
        return key

    def download(self, key: str) -> bytes:
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
        return body.read()

    def delete(self, key: str):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def generate_url(self, key: str, expires: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires,
        )


s3_client = S3Client()