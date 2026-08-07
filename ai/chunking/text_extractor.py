import io


class UnknownTypeError(Exception):
    pass


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "txt":
        return data.decode("utf-8", errors="ignore")
    if ext == "pdf":
        return _pdf(data)
    if ext == "docx":
        return _docx(data)
    raise UnknownTypeError(f"Unsupported file type: {ext}")


def _pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _docx(data: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)