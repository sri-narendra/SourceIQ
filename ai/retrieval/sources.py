def format_sources(chunks) -> list[dict]:
    result = []
    for c in chunks:
        result.append(
            {
                "document_id": str(c.document.id) if c.document else None,
                "document": c.document.original_name if c.document else "unknown",
                "page": c.page_number,
                "score": getattr(c, "_score", 0.0),
                "content": c.content,
            }
        )
    return result