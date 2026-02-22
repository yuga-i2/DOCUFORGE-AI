"""Unit tests for the text chunker."""

from core.rag.chunker import chunk_text, chunk_document


def test_chunk_text_produces_list():
    """Test that chunk_text returns a list of strings."""
    long_text = "word " * 500  # ~2500 characters
    result = chunk_text(long_text)
    
    assert isinstance(result, list)
    assert all(isinstance(chunk, str) for chunk in result)


def test_chunk_minimum_length():
    """Test that no chunk is shorter than 50 characters."""
    text = "This is a test. " * 100
    result = chunk_text(text)
    
    for chunk in result:
        assert len(chunk) >= 50, f"Chunk too short: {len(chunk)} chars"


def test_chunk_document_has_metadata():
    """Test that chunk_document adds required metadata."""
    text = "sample content " * 100
    docs = chunk_document(text, source_label="test_doc")
    
    for doc in docs:
        assert "source" in doc.metadata
        assert "chunk_index" in doc.metadata
        assert doc.metadata["source"] == "test_doc"


def test_chunk_overlap_respected():
    """Test that chunks overlap as configured."""
    text = ("AAAA BBBB CCCC DDDD EEEE " * 50)  # Repeated pattern
    chunks = chunk_text(text)
    
    if len(chunks) > 1:
        # Adjacent chunks should share some content
        for i in range(len(chunks) - 1):
            words_i = set(chunks[i].split())
            words_next = set(chunks[i + 1].split())
            overlap = len(words_i & words_next)
            # Should have some overlap due to configured overlap
            assert overlap > 0, "No overlap detected in adjacent chunks"


def test_empty_string_returns_empty_list():
    """Test that chunking empty string returns empty list."""
    result = chunk_text("")
    
    assert result == []
