import json

import boto3

from config.settings import settings


def _client():
    return boto3.client(
        "sqs",
        region_name=settings.aws_region or None,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def publish_document_job(document_id, job_type: str, s3_key: str):
    """Queue a document-processing job for a background worker."""
    if not settings.sqs_queue_url:
        return  # Local dev without SQS: no-op.
    body = json.dumps({"document_id": str(document_id), "job_type": job_type, "s3_key": s3_key})
    _client().send_message(QueueUrl=settings.sqs_queue_url, MessageBody=body)


def receive_document_jobs(max_messages: int = 10):
    if not settings.sqs_queue_url:
        return []
    resp = _client().receive_message(
        QueueUrl=settings.sqs_queue_url, MaxNumberOfMessages=max_messages, WaitTimeSeconds=1
    )
    return resp.get("Messages", [])


def delete_message(receipt_handle: str):
    if not settings.sqs_queue_url:
        return
    _client().delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle)