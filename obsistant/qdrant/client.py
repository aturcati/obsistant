"""Qdrant client management functions."""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from .server import is_qdrant_running


def get_qdrant_client(
    vault_path: Path, url: str = "http://localhost:6333"
) -> QdrantClient:
    """Get a Qdrant client connected to the local Qdrant instance.

    Args:
        vault_path: Path to the vault root directory.
        url: Qdrant server URL. Defaults to http://localhost:6333.

    Returns:
        Configured QdrantClient instance.

    Raises:
        RuntimeError: If Qdrant server is not running or connection fails.
    """
    # Check if server is running
    if not is_qdrant_running(vault_path):
        raise RuntimeError(
            "Qdrant server is not running. Please start it first with: "
            f"obsistant qdrant start {vault_path}"
        )

    try:
        client = QdrantClient(url=url)
        # Test connection by getting collections list
        client.get_collections()
        return client
    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to Qdrant server at {url}. "
            "Please ensure the server is running."
        ) from e


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = 3072,
    recreate: bool = False,
) -> None:
    """Ensure a Qdrant collection exists with the specified configuration.

    Args:
        client: Qdrant client instance.
        collection_name: Name of the collection.
        vector_size: Size of the embedding vectors. Defaults to 3072 (OpenAI text-embedding-3-large).
        recreate: If True, delete existing collection before creating.

    Raises:
        RuntimeError: If collection creation fails.
    """
    if recreate and client.collection_exists(collection_name):
        try:
            client.delete_collection(collection_name)
        except Exception as e:
            raise RuntimeError(
                f"Failed to delete existing collection '{collection_name}': {e}"
            ) from e

    if not client.collection_exists(collection_name):
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create collection '{collection_name}': {e}"
            ) from e
