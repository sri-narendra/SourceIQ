"""SQS consumer helpers.

ponytail: thin wrapper around receive/delete; long-polling + DLQ wiring later.
"""
from queueing import producer


def consume_loop(handler, once: bool = False):
    import time

    while True:
        messages = producer.receive_document_jobs()
        for m in messages:
            handler(m)
            producer.delete_message(m["ReceiptHandle"])
        if once:
            break
        time.sleep(1)