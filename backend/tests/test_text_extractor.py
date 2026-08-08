from ai.chunking.text_extractor import extract_pages, extract_text


def test_text_extraction_single_page():
    pages = extract_pages("notes.txt", b"hello world")
    assert pages == [("hello world", None)]
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_pdf_extracts_per_page():
    import io

    import pymupdf
    from pypdf import PdfReader

    buf = io.BytesIO()
    doc = pymupdf.open()
    for text in ("first page text", "second page text"):
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(buf)

    reader = PdfReader(io.BytesIO(buf.getvalue()))
    pages = extract_pages("doc.pdf", buf.getvalue())
    assert isinstance(pages, list)
    assert [p for _, p in pages] == [1, 2]
    assert "first page text" in pages[0][0]
    assert "second page text" in pages[1][0]
    assert len(pages) == len(reader.pages)


def test_unsupported_type_raises():
    import pytest
    from ai.chunking.text_extractor import UnknownTypeError

    with pytest.raises(UnknownTypeError):
        extract_pages("thing.xyz", b"data")
