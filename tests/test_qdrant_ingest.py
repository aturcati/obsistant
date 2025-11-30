"""Tests for Qdrant document ingestion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from obsistant.config import Config
from obsistant.qdrant.ingest import (
    build_payload,
    collect_markdown_files,
    parse_markdown_file,
    semantic_chunk,
)


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
    """Create a sample vault structure for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create folder structure
    notes = vault / "20-Notes"
    notes.mkdir()
    meetings = vault / "10-Meetings"
    meetings.mkdir()
    weekly_summaries = meetings / "Weekly Summaries"
    weekly_summaries.mkdir()

    # Create test markdown files
    (notes / "note1.md").write_text("# Note 1\n\nContent here.")
    (notes / "note2.md").write_text("---\ntags:\n  - test\n---\n# Note 2")
    (meetings / "meeting1.md").write_text("# Meeting 1\n\nDiscussion.")
    (weekly_summaries / "summary.md").write_text("# Summary\n\nWeekly summary.")

    return vault


@pytest.fixture
def sample_config() -> Config:
    """Create a sample config for testing."""
    return Config()


def test_collect_markdown_files_excludes_weekly_summaries(
    sample_vault: Path, sample_config: Config
) -> None:
    """Test that Weekly Summaries are excluded from collection."""
    files = collect_markdown_files(sample_vault, sample_config)

    file_paths = [str(f.relative_to(sample_vault)) for f in files]

    assert "20-Notes/note1.md" in file_paths
    assert "20-Notes/note2.md" in file_paths
    assert "10-Meetings/meeting1.md" in file_paths
    assert "10-Meetings/Weekly Summaries/summary.md" not in file_paths


def test_parse_markdown_file_with_frontmatter(
    sample_vault: Path, sample_config: Config
) -> None:
    """Test parsing markdown file with frontmatter."""
    file_path = sample_vault / "20-Notes" / "note2.md"
    result = parse_markdown_file(file_path, sample_vault, sample_config)

    assert "content" in result
    assert "metadata" in result
    assert "file_path" in result
    assert result["metadata"]["tags"] == ["test"]
    assert result["document_type"] == "note"


def test_parse_markdown_file_without_frontmatter(
    sample_vault: Path, sample_config: Config
) -> None:
    """Test parsing markdown file without frontmatter."""
    file_path = sample_vault / "20-Notes" / "note1.md"
    result = parse_markdown_file(file_path, sample_vault, sample_config)

    assert "content" in result
    assert "metadata" in result
    assert result["document_type"] == "note"
    assert "created" in result["metadata"]


def test_semantic_chunk_empty_text() -> None:
    """Test semantic chunking with empty text."""
    chunks = semantic_chunk("")
    assert chunks == []


def test_semantic_chunk_simple_text() -> None:
    """Test semantic chunking with simple text."""
    text = "This is a sentence. This is another sentence. They are related."
    chunks = semantic_chunk(text, similarity_threshold=0.5)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_semantic_chunk_handles_encoding_error() -> None:
    """Test that semantic chunking handles encoding errors gracefully."""
    with patch("obsistant.qdrant.ingest._get_chunking_model") as mock_model:
        mock_model.return_value.encode.side_effect = Exception("Encoding error")
        text = "Test text."
        chunks = semantic_chunk(text)

        # Should fallback to single chunk
        assert len(chunks) == 1
        assert chunks[0] == text


def test_build_payload() -> None:
    """Test payload construction."""
    chunk = "This is a chunk."
    metadata = {
        "file_path": "notes/test.md",
        "document_type": "note",
        "tags": ["test"],
        "title": "Test Note",
    }
    chunk_index = 0

    payload = build_payload(chunk, metadata, chunk_index)

    assert payload["text"] == chunk
    assert payload["chunk_index"] == chunk_index
    assert payload["file_path"] == metadata["file_path"]
    assert payload["document_type"] == metadata["document_type"]
    assert payload["tags"] == metadata["tags"]
    assert payload["title"] == metadata["title"]


def test_parse_pdf_file_requires_pdfplumber(tmp_path: Path) -> None:
    """Test that PDF parsing requires pdfplumber."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"fake pdf content")

    vault_path = tmp_path

    # Mock import error
    with patch(
        "builtins.__import__", side_effect=ImportError("No module named 'pdfplumber'")
    ):
        with pytest.raises(ImportError, match="pdfplumber is required"):
            from obsistant.qdrant.ingest import parse_pdf_file

            parse_pdf_file(pdf_path, vault_path)


@patch("obsistant.qdrant.ingest.OpenAI")
def test_generate_embedding_success(mock_openai_class: MagicMock) -> None:
    """Test successful embedding generation."""
    from obsistant.qdrant.ingest import generate_embedding

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 3072)]
    mock_client.embeddings.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    client = mock_client
    embedding = generate_embedding("test text", client)

    assert len(embedding) == 3072
    assert all(isinstance(x, float) for x in embedding)


@patch("obsistant.qdrant.ingest.OpenAI")
def test_generate_embedding_retry(mock_openai_class: MagicMock) -> None:
    """Test embedding generation with retry on failure."""

    from obsistant.qdrant.ingest import generate_embedding

    mock_client = MagicMock()
    # First call fails, second succeeds
    mock_client.embeddings.create.side_effect = [
        Exception("Rate limit"),
        MagicMock(data=[MagicMock(embedding=[0.1] * 3072)]),
    ]
    mock_openai_class.return_value = mock_client

    with patch("time.sleep"):  # Mock sleep to speed up test
        embedding = generate_embedding("test text", mock_client, max_retries=3)

    assert len(embedding) == 3072
    assert mock_client.embeddings.create.call_count == 2
