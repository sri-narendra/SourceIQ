"""Minimal CloudWatch Logs handler, active only when AWS creds are set."""
import logging

from config.settings import settings

_LOG_GROUP = "sourceiq"
_LOG_STREAM = "sourceiq-backend"


class CloudWatchHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        import boto3

        self._client = boto3.client(
            "logs",
            region_name=settings.aws_region or None,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self._token = None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            resp = self._client.put_log_events(
                logGroupName=_LOG_GROUP,
                logStreamName=_LOG_STREAM,
                logEvents=[
                    {"timestamp": int(record.created * 1000), "message": self.format(record)}
                ],
                **({"sequenceToken": self._token} if self._token else {}),
            )
            self._token = resp.get("nextSequenceToken")
        except self._client.exceptions.ResourceNotFoundException:
            self._ensure_stream()
        except Exception:
            self.handleError(record)

    def _ensure_stream(self) -> None:
        try:
            self._client.create_log_group(logGroupName=_LOG_GROUP)
        except Exception:
            pass
        try:
            self._client.create_log_stream(logGroupName=_LOG_GROUP, logStreamName=_LOG_STREAM)
        except Exception:
            pass


def install() -> None:
    if not settings.aws_access_key_id:
        return
    handler = CloudWatchHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)
