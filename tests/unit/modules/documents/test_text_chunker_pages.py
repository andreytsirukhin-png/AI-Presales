from app.modules.documents.chunkers.text_chunker import TextChunker


def test_chunk_with_pages_assigns_page_numbers() -> None:
    chunker = TextChunker(chunk_size=40, chunk_overlap=0)
    page_texts = [
        "Page one content about integrations.",
        "Page two content about pricing and support.",
    ]
    full_text = "\n".join(page_texts)

    chunks = chunker.chunk_with_pages(full_text, page_texts)

    assert chunks
    assert any(chunk.page_number == 1 for chunk in chunks)
    assert any(chunk.page_number == 2 for chunk in chunks)
