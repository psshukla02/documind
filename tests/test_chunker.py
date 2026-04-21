from app.services.chunker import chunk_text


def test_empty_text():
    assert chunk_text("") == []


def test_paragraphs_are_grouped():
    text = "\n\n".join([f"Paragraph {i} with some content." for i in range(5)])
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 1
    assert all(c.text for c in chunks)


def test_oversized_paragraph_is_split():
    text = "A" * 2500
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    # Expect multiple chunks because one paragraph exceeds size
    assert len(chunks) > 1
