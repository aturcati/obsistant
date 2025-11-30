"""Document ingestion functions for Qdrant vector database."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, TypedDict, cast
from uuid import UUID

import numpy as np
from loguru import logger
from openai import OpenAI
from qdrant_client.http.models.models import PointIdsList
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct
from sentence_transformers import SentenceTransformer

from ..config import Config
from ..core.dates import get_file_creation_date, get_file_modification_date
from ..core.frontmatter import split_frontmatter
from ..core.tags import extract_tags


class IngestStats(TypedDict):
    """Statistics dictionary for document ingestion."""

    files_processed: int
    files_skipped: int
    chunks_created: int
    embeddings_generated: int
    errors: list[str]


# Cache for SentenceTransformer model
_chunking_model: SentenceTransformer | None = None


def _get_chunking_model() -> SentenceTransformer:
    """Get or create the SentenceTransformer model for semantic chunking.

    Returns:
        Cached SentenceTransformer model instance.
    """
    global _chunking_model
    if _chunking_model is None:
        _chunking_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _chunking_model


def collect_markdown_files(vault_path: Path, config: Config) -> list[Path]:
    """Collect markdown files from notes and meetings folders.

    Excludes files in the Weekly Summaries subfolder.

    Args:
        vault_path: Path to the vault root directory.
        config: Configuration object with folder names.

    Returns:
        List of absolute file paths to markdown files.
    """
    files: list[Path] = []

    # Collect from notes folder
    notes_path = vault_path / config.vault.notes
    if notes_path.exists() and notes_path.is_dir():
        for md_file in notes_path.rglob("*.md"):
            files.append(md_file.resolve())

    # Collect from meetings folder, excluding Weekly Summaries
    meetings_path = vault_path / config.vault.meetings
    if meetings_path.exists() and meetings_path.is_dir():
        weekly_summaries_path = meetings_path / "Weekly Summaries"
        for md_file in meetings_path.rglob("*.md"):
            # Skip files in Weekly Summaries folder
            try:
                md_file.resolve().relative_to(weekly_summaries_path.resolve())
                continue
            except ValueError:
                # File is not in Weekly Summaries, include it
                files.append(md_file.resolve())

    return files


def parse_markdown_file(
    file_path: Path, vault_path: Path, config: Config
) -> dict[str, Any]:
    """Parse a markdown file and extract content and metadata.

    Args:
        file_path: Path to the markdown file.
        vault_path: Path to the vault root directory.
        config: Configuration object.

    Returns:
        Dictionary with 'content', 'metadata', and 'file_path' keys.

    Raises:
        OSError: If file cannot be read.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise OSError(f"Failed to read file {file_path}: {e}") from e

    # Split frontmatter and body
    frontmatter, body = split_frontmatter(text)

    # Extract tags from body
    body_tags, _ = extract_tags(body, config)

    # Merge tags from frontmatter and body
    frontmatter_tags = set(frontmatter.get("tags", [])) if frontmatter else set()
    all_tags = frontmatter_tags.union(body_tags)

    # Determine document type
    relative_path = file_path.relative_to(vault_path)
    meetings_prefix = config.vault.meetings + "/"
    if str(relative_path).startswith(meetings_prefix):
        document_type = "meeting"
    else:
        document_type = "note"

    # Build metadata dictionary
    metadata: dict[str, Any] = {
        "file_path": str(relative_path),
        "document_type": document_type,
        "tags": sorted(all_tags) if all_tags else [],
    }

    # Add frontmatter fields
    if frontmatter:
        metadata.update(frontmatter)

    # Add file dates if not in frontmatter
    if "created" not in metadata:
        created_date = get_file_creation_date(file_path)
        if created_date:
            metadata["created"] = created_date

    if "modified" not in metadata:
        modified_date = get_file_modification_date(file_path)
        if modified_date:
            metadata["modified"] = modified_date

    # Add title from frontmatter or filename
    metadata["title"] = metadata.get("title") or file_path.stem

    return {
        "content": body,
        "metadata": metadata,
        "file_path": relative_path,
    }


def parse_pdf_file(file_path: Path, vault_path: Path) -> dict[str, Any]:
    """Parse a PDF file and extract text content.

    Args:
        file_path: Path to the PDF file.
        vault_path: Path to the vault root directory.

    Returns:
        Dictionary with 'content', 'metadata', and 'file_path' keys.

    Raises:
        ImportError: If pdfplumber is not installed.
        OSError: If file cannot be read.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF processing. "
            "Install it with: uv pip install pdfplumber"
        ) from None

    try:
        text_chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text.strip())

        content = "\n\n".join(text_chunks)

        # Build metadata
        relative_path = file_path.relative_to(vault_path)
        modified_date = get_file_modification_date(file_path)

        metadata: dict[str, Any] = {
            "file_path": str(relative_path),
            "document_type": "pdf",
            "title": file_path.stem,
        }

        if modified_date:
            metadata["modified"] = modified_date

        return {
            "content": content,
            "metadata": metadata,
            "file_path": relative_path,
        }
    except Exception as e:
        raise OSError(f"Failed to parse PDF file {file_path}: {e}") from e


def semantic_chunk(text: str, similarity_threshold: float = 0.5) -> list[str]:
    """Chunk text semantically using sentence similarity.

    Args:
        text: Text to chunk.
        similarity_threshold: Minimum similarity between sentences to keep in same chunk.

    Returns:
        List of text chunks.
    """
    if not text.strip():
        return []

    model = _get_chunking_model()

    # Split into sentences (simple approach: split by period + space)
    sentences = [s.strip() + "." for s in text.split(". ") if s.strip()]
    if not sentences:
        return [text] if text.strip() else []

    # Encode sentences
    try:
        embeddings = model.encode(sentences, show_progress_bar=False)
    except Exception as e:
        logger.warning(f"Failed to encode sentences for chunking: {e}")
        # Fallback: return text as single chunk
        return [text] if text.strip() else []

    # Group sentences by similarity
    chunks = []
    current_chunk = [sentences[0]]

    for i in range(1, len(sentences)):
        # Calculate cosine similarity
        similarity = np.dot(embeddings[i - 1], embeddings[i]) / (
            np.linalg.norm(embeddings[i - 1]) * np.linalg.norm(embeddings[i])
        )

        if similarity < similarity_threshold:
            chunk_text = " ".join(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text)
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    # Add final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        if chunk_text.strip():
            chunks.append(chunk_text)

    return chunks if chunks else [text] if text.strip() else []


def generate_embedding(text: str, client: OpenAI, max_retries: int = 3) -> list[float]:
    """Generate embedding for text using OpenAI API.

    Args:
        text: Text to embed.
        client: OpenAI client instance.
        max_retries: Maximum number of retry attempts.

    Returns:
        Embedding vector (3072 dimensions for text-embedding-3-large).

    Raises:
        RuntimeError: If embedding generation fails after retries.
    """
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-large",
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    f"Embedding generation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    f"Failed to generate embedding after {max_retries} attempts: {e}"
                ) from e

    raise RuntimeError("Failed to generate embedding")  # Should never reach here


def build_payload(
    chunk: str, file_metadata: dict[str, Any], chunk_index: int
) -> dict[str, Any]:
    """Build payload dictionary for Qdrant point.

    Args:
        chunk: Text chunk content.
        file_metadata: Metadata dictionary from parsed file.
        chunk_index: Index of chunk within document.

    Returns:
        Payload dictionary for Qdrant.
    """
    payload = {
        "text": chunk,
        "chunk_index": chunk_index,
    }

    # Copy all metadata fields
    payload.update(file_metadata)

    return payload


def _file_needs_ingestion(
    qdrant_client: Any,
    collection_name: str,
    file_path: str,
    current_modified: str | None,
) -> tuple[bool, list[str]]:
    """Check if a file needs to be ingested or re-ingested.

    Args:
        qdrant_client: Qdrant client instance.
        collection_name: Name of the collection.
        file_path: Relative file path to check.
        current_modified: Current file modification date.

    Returns:
        Tuple of (needs_ingestion: bool, existing_point_ids: list[str]).
        If file doesn't exist in collection, returns (True, []).
        If file exists and hasn't changed, returns (False, [point_ids]).
        If file exists but has changed, returns (True, [point_ids]) to delete old chunks.
    """

    try:
        # Query for existing points with this file_path
        results = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="file_path",
                        match=MatchValue(value=file_path),
                    )
                ]
            ),
            limit=1000,  # Should be enough for most documents
            with_payload=True,
            with_vectors=False,
        )

        points, _ = results

        if not points:
            # File not in collection, needs ingestion
            return True, []

        # Check modification date from first point (all should have same modified date)
        if points:
            stored_modified = points[0].payload.get("modified")
            if stored_modified == current_modified and current_modified:
                # File exists and hasn't changed, skip ingestion
                return False, [str(p.id) for p in points]

        # File exists but has changed, needs re-ingestion
        return True, [str(p.id) for p in points]

    except Exception as e:
        # If query fails, assume file needs ingestion
        logger.warning(
            f"Failed to check existing ingestion status for {file_path}: {e}"
        )
        return True, []


def ingest_documents(
    vault_path: Path,
    config: Config,
    collection_name: str,
    include_pdfs: bool,
    recreate_collection: bool,
    dry_run: bool,
    logger_instance: Any,
) -> IngestStats:
    """Ingest documents from vault into Qdrant vector database.

    Args:
        vault_path: Path to the vault root directory.
        config: Configuration object.
        collection_name: Name of the Qdrant collection.
        include_pdfs: Whether to include PDF files.
        recreate_collection: Whether to recreate the collection.
        dry_run: If True, don't actually ingest documents.
        logger_instance: Logger instance for logging.

    Returns:
        IngestStats dictionary with statistics: files_processed, chunks_created, embeddings_generated, errors.

    Raises:
        RuntimeError: If OpenAI API key is missing or Qdrant connection fails.
    """
    from .client import ensure_collection, get_qdrant_client

    stats: IngestStats = {
        "files_processed": 0,
        "files_skipped": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "errors": [],
    }

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in .obsistant/.env file or environment."
        )

    # Initialize OpenAI client
    openai_client = OpenAI(api_key=api_key)

    # Get Qdrant client
    try:
        qdrant_client = get_qdrant_client(vault_path)
    except RuntimeError as e:
        raise RuntimeError(
            f"Cannot connect to Qdrant server: {e}. "
            "Please start it with: obsistant qdrant start <vault_path>"
        ) from e

    # Ensure collection exists
    if not dry_run:
        ensure_collection(qdrant_client, collection_name, recreate=recreate_collection)
        logger_instance.info(f"Using collection '{collection_name}'")

    # Collect markdown files
    md_files = collect_markdown_files(vault_path, config)
    logger_instance.info(f"Found {len(md_files)} markdown files")

    # Collect PDF files if enabled
    pdf_files: list[Path] = []
    if include_pdfs:
        notes_path = vault_path / config.vault.notes
        meetings_path = vault_path / config.vault.meetings
        for folder_path in [notes_path, meetings_path]:
            if folder_path.exists():
                pdf_files.extend(folder_path.rglob("*.pdf"))
        logger_instance.info(f"Found {len(pdf_files)} PDF files")

    # Process markdown files
    for file_path in md_files:
        try:
            parsed = parse_markdown_file(file_path, vault_path, config)
            chunks = semantic_chunk(parsed["content"])

            if not chunks:
                logger_instance.debug(
                    f"Skipping {file_path}: no content after chunking"
                )
                continue

            # Check if file needs ingestion
            file_path_str = str(parsed["file_path"])
            current_modified = parsed["metadata"].get("modified")

            if not dry_run:
                needs_ingestion, existing_point_ids = _file_needs_ingestion(
                    qdrant_client, collection_name, file_path_str, current_modified
                )

                if not needs_ingestion:
                    logger_instance.debug(
                        f"Skipping {file_path}: already ingested and unchanged"
                    )
                    stats["files_skipped"] += 1
                    continue

                # Delete old chunks if file was modified
                if existing_point_ids:
                    logger_instance.debug(
                        f"File {file_path} has changed, deleting {len(existing_point_ids)} old chunks"
                    )
                    try:
                        # Cast to satisfy type checker - list[str] is compatible with list[int | str | UUID]
                        point_ids: list[int | str | UUID] = cast(
                            list[int | str | UUID], existing_point_ids
                        )
                        qdrant_client.delete(
                            collection_name=collection_name,
                            points_selector=PointIdsList(points=point_ids),
                        )
                    except Exception as e:
                        logger_instance.warning(
                            f"Failed to delete old chunks for {file_path}: {e}"
                        )

            logger_instance.debug(
                f"Processing {file_path}: {len(chunks)} chunks, "
                f"tags: {parsed['metadata'].get('tags', [])}"
            )

            if dry_run:
                stats["files_processed"] += 1
                stats["chunks_created"] += len(chunks)
                continue

            # Generate embeddings and upsert
            points = []
            for idx, chunk in enumerate(chunks):
                try:
                    embedding = generate_embedding(chunk, openai_client)
                    payload = build_payload(chunk, parsed["metadata"], idx)
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=embedding,
                            payload=payload,
                        )
                    )
                    stats["embeddings_generated"] += 1
                except Exception as e:
                    error_msg = f"Failed to process chunk {idx} of {file_path}: {e}"
                    logger_instance.error(error_msg)
                    stats["errors"].append(error_msg)

            if points:
                qdrant_client.upsert(collection_name=collection_name, points=points)
                stats["files_processed"] += 1
                stats["chunks_created"] += len(points)

        except Exception as e:
            error_msg = f"Failed to process {file_path}: {e}"
            logger_instance.error(error_msg)
            stats["errors"].append(error_msg)

    # Process PDF files if enabled
    if include_pdfs:
        for file_path in pdf_files:
            try:
                parsed = parse_pdf_file(file_path, vault_path)
                chunks = semantic_chunk(parsed["content"])

                if not chunks:
                    logger_instance.debug(
                        f"Skipping {file_path}: no content after chunking"
                    )
                    continue

                # Check if file needs ingestion
                file_path_str = str(parsed["file_path"])
                current_modified = parsed["metadata"].get("modified")

                if not dry_run:
                    needs_ingestion, existing_point_ids = _file_needs_ingestion(
                        qdrant_client, collection_name, file_path_str, current_modified
                    )

                    if not needs_ingestion:
                        logger_instance.debug(
                            f"Skipping {file_path}: already ingested and unchanged"
                        )
                        stats["files_skipped"] += 1
                        continue

                    # Delete old chunks if file was modified
                    if existing_point_ids:
                        logger_instance.debug(
                            f"File {file_path} has changed, deleting {len(existing_point_ids)} old chunks"
                        )
                        try:
                            # Cast to satisfy type checker - list[str] is compatible with list[int | str | UUID]
                            point_ids: list[int | str | UUID] = cast(
                                list[int | str | UUID], existing_point_ids
                            )
                            qdrant_client.delete(
                                collection_name=collection_name,
                                points_selector=PointIdsList(points=point_ids),
                            )
                        except Exception as e:
                            logger_instance.warning(
                                f"Failed to delete old chunks for {file_path}: {e}"
                            )

                logger_instance.debug(f"Processing {file_path}: {len(chunks)} chunks")

                if dry_run:
                    stats["files_processed"] += 1
                    stats["chunks_created"] += len(chunks)
                    continue

                # Generate embeddings and upsert
                points = []
                for idx, chunk in enumerate(chunks):
                    try:
                        embedding = generate_embedding(chunk, openai_client)
                        payload = build_payload(chunk, parsed["metadata"], idx)
                        points.append(
                            PointStruct(
                                id=str(uuid.uuid4()),
                                vector=embedding,
                                payload=payload,
                            )
                        )
                        stats["embeddings_generated"] += 1
                    except Exception as e:
                        error_msg = f"Failed to process chunk {idx} of {file_path}: {e}"
                        logger_instance.error(error_msg)
                        stats["errors"].append(error_msg)

                if points:
                    qdrant_client.upsert(collection_name=collection_name, points=points)
                    stats["files_processed"] += 1
                    stats["chunks_created"] += len(points)

            except Exception as e:
                error_msg = f"Failed to process {file_path}: {e}"
                logger_instance.error(error_msg)
                stats["errors"].append(error_msg)

    return stats
