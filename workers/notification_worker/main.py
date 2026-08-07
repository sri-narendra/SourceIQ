"""Notification worker: marks the document complete / sends async notices.

ponytail: placeholder for email/webhook delivery; no real channel yet.
"""


def notify_document_complete(document_id: str):
    print(f"[notification] document {document_id} completed")


if __name__ == "__main__":
    import sys

    doc_id = sys.argv[1] if len(sys.argv) > 1 else "?"
    notify_document_complete(doc_id)