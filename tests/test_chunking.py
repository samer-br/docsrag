from app.chunking import split_markdown

DOC = """# Title

Intro paragraph about the system.

## Section A

First point about A. It has some detail.

Second point about A with more detail that continues for a while.

## Section B

Only content for B here.
"""


def test_chunks_carry_their_heading():
    chunks = split_markdown(DOC, source="doc.md", chunk_size=200, overlap=20)
    headings = {c.heading for c in chunks}
    assert "Section A" in headings
    assert "Section B" in headings
    assert all(c.source == "doc.md" for c in chunks)


def test_respects_chunk_size_roughly():
    chunks = split_markdown(DOC, source="doc.md", chunk_size=120, overlap=20)
    # Allow overlap slack, but no chunk should be wildly over the target.
    assert all(len(c.text) <= 120 + 80 for c in chunks)
    assert len(chunks) >= 2


def test_text_with_no_headings_still_chunks():
    chunks = split_markdown("Just one paragraph.", source="x.md", chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].heading == ""
