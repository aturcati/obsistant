"""Tests for Qdrant client management functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from obsistant.qdrant.client import ensure_collection, get_qdrant_client


class TestGetQdrantClient:
    """Test get_qdrant_client function."""

    @patch("obsistant.qdrant.client.is_qdrant_running")
    @patch("obsistant.qdrant.client.QdrantClient")
    def test_get_client_success(
        self,
        mock_qdrant_client_class: MagicMock,
        mock_is_running: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful client initialization."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_is_running.return_value = True
        mock_client = MagicMock()
        mock_client.get_collections.return_value = []
        mock_qdrant_client_class.return_value = mock_client

        client = get_qdrant_client(vault_path)

        assert client == mock_client
        mock_is_running.assert_called_once_with(vault_path)
        mock_qdrant_client_class.assert_called_once_with(url="http://localhost:6333")
        mock_client.get_collections.assert_called_once()

    @patch("obsistant.qdrant.client.is_qdrant_running")
    @patch("obsistant.qdrant.client.QdrantClient")
    def test_get_client_custom_url(
        self,
        mock_qdrant_client_class: MagicMock,
        mock_is_running: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test client initialization with custom URL."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_is_running.return_value = True
        mock_client = MagicMock()
        mock_client.get_collections.return_value = []
        mock_qdrant_client_class.return_value = mock_client

        client = get_qdrant_client(vault_path, url="http://localhost:8080")

        assert client == mock_client
        mock_qdrant_client_class.assert_called_once_with(url="http://localhost:8080")

    @patch("obsistant.qdrant.client.is_qdrant_running")
    def test_get_client_server_not_running(
        self, mock_is_running: MagicMock, tmp_path: Path
    ) -> None:
        """Test that client initialization raises error when server is not running."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_is_running.return_value = False

        with pytest.raises(RuntimeError, match="Qdrant server is not running"):
            get_qdrant_client(vault_path)

    @patch("obsistant.qdrant.client.is_qdrant_running")
    @patch("obsistant.qdrant.client.QdrantClient")
    def test_get_client_connection_failure(
        self,
        mock_qdrant_client_class: MagicMock,
        mock_is_running: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that client initialization raises error on connection failure."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_is_running.return_value = True
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection failed")
        mock_qdrant_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to connect to Qdrant server"):
            get_qdrant_client(vault_path)


class TestEnsureCollection:
    """Test ensure_collection function."""

    def test_ensure_collection_creates_new(self) -> None:
        """Test that ensure_collection creates a new collection when it doesn't exist."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        ensure_collection(mock_client, "test-collection", vector_size=3072)

        mock_client.collection_exists.assert_called_once_with("test-collection")
        mock_client.create_collection.assert_called_once()
        call_args = mock_client.create_collection.call_args
        assert call_args[1]["collection_name"] == "test-collection"
        assert call_args[1]["vectors_config"].size == 3072
        mock_client.delete_collection.assert_not_called()

    def test_ensure_collection_skips_existing(self) -> None:
        """Test that ensure_collection skips creation when collection already exists."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True

        ensure_collection(mock_client, "test-collection", vector_size=3072)

        mock_client.collection_exists.assert_called_once_with("test-collection")
        mock_client.create_collection.assert_not_called()
        mock_client.delete_collection.assert_not_called()

    def test_ensure_collection_recreates_when_requested(self) -> None:
        """Test that ensure_collection recreates collection when recreate=True."""
        mock_client = MagicMock()
        # First call (check before delete) returns True, after delete it should return False
        mock_client.collection_exists.side_effect = [True, False]

        ensure_collection(
            mock_client, "test-collection", vector_size=3072, recreate=True
        )

        assert mock_client.collection_exists.call_count == 2
        mock_client.delete_collection.assert_called_once_with("test-collection")
        mock_client.create_collection.assert_called_once()

    def test_ensure_collection_recreate_skips_delete_when_not_exists(self) -> None:
        """Test that ensure_collection skips delete when recreate=True but collection doesn't exist."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        ensure_collection(
            mock_client, "test-collection", vector_size=3072, recreate=True
        )

        mock_client.delete_collection.assert_not_called()
        mock_client.create_collection.assert_called_once()

    def test_ensure_collection_custom_vector_size(self) -> None:
        """Test that ensure_collection uses custom vector size."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        ensure_collection(mock_client, "test-collection", vector_size=1536)

        call_args = mock_client.create_collection.call_args
        assert call_args[1]["vectors_config"].size == 1536

    def test_ensure_collection_delete_error(self) -> None:
        """Test that ensure_collection raises error when delete fails."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_client.delete_collection.side_effect = Exception("Delete failed")

        with pytest.raises(RuntimeError, match="Failed to delete existing collection"):
            ensure_collection(mock_client, "test-collection", recreate=True)

    def test_ensure_collection_create_error(self) -> None:
        """Test that ensure_collection raises error when create fails."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False
        mock_client.create_collection.side_effect = Exception("Create failed")

        with pytest.raises(RuntimeError, match="Failed to create collection"):
            ensure_collection(mock_client, "test-collection")
