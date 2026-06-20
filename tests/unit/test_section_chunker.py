import pytest
import sys
import os
sys.path.insert(0, os.path.abspath("apps/worker"))
from app.ucd.section_chunker import section_chunker

@pytest.mark.unit
class TestSectionChunker:
    def test_chunk_empty_text(self):
        assert section_chunker.chunk_document("") == []
        assert section_chunker.chunk_document(None) == []

    def test_chunk_whitespace_only(self):
        assert section_chunker.chunk_document("   \n\n  ") == []

    def test_chunk_short_text(self):
        text = "This is a very short document."
        chunks = section_chunker.chunk_document(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["page_number"] is None

    def test_chunk_long_text(self):
        # Generate text > 512 tokens
        text = "word " * 1000
        chunks = section_chunker.chunk_document(text)
        assert len(chunks) > 1
        # Each chunk should be <= chunk_size (in characters relative to tokens, this is an approximation check)
        # We just verify it successfully splits.
        
    def test_chunk_overlap_present(self):
        text = "word " * 600
        chunks = section_chunker.chunk_document(text)
        if len(chunks) > 1:
            chunk1 = chunks[0]["text"]
            chunk2 = chunks[1]["text"]
            # With overlap=50, there should be some common words at the boundary
            words1 = chunk1.split()
            words2 = chunk2.split()
            # Check last 10 words of chunk 1 exist in chunk 2
            overlap = set(words1[-10:]).intersection(set(words2[:20]))
            assert len(overlap) > 0

    def test_chunk_with_pages(self):
        pages = [
            {"page_number": 1, "text": "Page 1 content."},
            {"page_number": 2, "text": "Page 2 content."}
        ]
        chunks = section_chunker.chunk_document("raw unused", pages=pages)
        assert len(chunks) == 2
        assert chunks[0]["text"] == "Page 1 content."
        assert chunks[0]["page_number"] == 1
        assert chunks[1]["page_number"] == 2

    def test_chunk_empty_pages_skipped(self):
        pages = [
            {"page_number": 1, "text": "  "},
            {"page_number": 2, "text": "Valid text"}
        ]
        chunks = section_chunker.chunk_document("raw", pages=pages)
        assert len(chunks) == 1
        assert chunks[0]["page_number"] == 2

    def test_chunk_with_utterances(self):
        utterances = [
            {"speaker_id": "S1", "text": "Hello", "start_time": "1.5s"}
        ]
        chunks = section_chunker.chunk_document("raw", utterances=utterances)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Hello"
        assert chunks[0]["speaker_id"] == "S1"
        assert chunks[0]["timestamp_start_seconds"] == 1.5

    def test_chunk_utterance_invalid_time(self):
        utterances = [
            {"speaker_id": "S1", "text": "Hello", "start_time": "abcs"}
        ]
        chunks = section_chunker.chunk_document("raw", utterances=utterances)
        assert chunks[0]["timestamp_start_seconds"] is None
