"""Tests for Qdrant server management functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from obsistant.qdrant.server import (
    _check_docker_available,
    _check_ports_available,
    _container_exists,
    _get_container_name,
    ensure_qdrant_storage,
    get_qdrant_storage_path,
    is_qdrant_running,
    start_qdrant_server,
    stop_qdrant_server,
)


class TestGetQdrantStoragePath:
    """Test get_qdrant_storage_path function."""

    def test_get_storage_path(self, tmp_path: Path) -> None:
        """Test that storage path is correctly generated."""
        vault_path = tmp_path / "vault"
        storage_path = get_qdrant_storage_path(vault_path)

        assert storage_path == vault_path / ".obsistant" / "qdrant_storage"


class TestEnsureQdrantStorage:
    """Test ensure_qdrant_storage function."""

    def test_ensure_storage_creates_directory(self, tmp_path: Path) -> None:
        """Test that storage directory is created if it doesn't exist."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        storage_path = ensure_qdrant_storage(vault_path)

        assert storage_path.exists()
        assert storage_path.is_dir()
        assert storage_path == vault_path / ".obsistant" / "qdrant_storage"

    def test_ensure_storage_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that parent directories are created if they don't exist."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        storage_path = ensure_qdrant_storage(vault_path)

        assert (vault_path / ".obsistant").exists()
        assert storage_path.exists()

    def test_ensure_storage_idempotent(self, tmp_path: Path) -> None:
        """Test that ensure_storage is idempotent."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        storage_path1 = ensure_qdrant_storage(vault_path)
        storage_path2 = ensure_qdrant_storage(vault_path)

        assert storage_path1 == storage_path2
        assert storage_path1.exists()


class TestGetContainerName:
    """Test _get_container_name function."""

    def test_container_name_format(self, tmp_path: Path) -> None:
        """Test that container name has correct format."""
        vault_path = tmp_path / "vault"
        container_name = _get_container_name(vault_path)

        assert container_name.startswith("obsistant-qdrant-")
        assert len(container_name) == len("obsistant-qdrant-") + 8  # 8 char hash

    def test_container_name_deterministic(self, tmp_path: Path) -> None:
        """Test that container name is deterministic for same path."""
        vault_path = tmp_path / "vault"
        name1 = _get_container_name(vault_path)
        name2 = _get_container_name(vault_path)

        assert name1 == name2

    def test_container_name_unique_for_different_paths(self, tmp_path: Path) -> None:
        """Test that container names are unique for different paths."""
        vault_path1 = tmp_path / "vault1"
        vault_path2 = tmp_path / "vault2"

        name1 = _get_container_name(vault_path1)
        name2 = _get_container_name(vault_path2)

        assert name1 != name2


class TestCheckDockerAvailable:
    """Test _check_docker_available function."""

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_docker_available_success(self, mock_run: MagicMock) -> None:
        """Test that Docker availability check returns True when Docker is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _check_docker_available()

        assert result is True
        mock_run.assert_called_once()

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_docker_available_file_not_found(self, mock_run: MagicMock) -> None:
        """Test that Docker availability check returns False when Docker is not found."""
        mock_run.side_effect = FileNotFoundError()

        result = _check_docker_available()

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_docker_available_timeout(self, mock_run: MagicMock) -> None:
        """Test that Docker availability check returns False on timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("docker", 5)

        result = _check_docker_available()

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_docker_available_subprocess_error(self, mock_run: MagicMock) -> None:
        """Test that Docker availability check returns False on subprocess error."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Subprocess error")

        result = _check_docker_available()

        assert result is False


class TestCheckPortsAvailable:
    """Test _check_ports_available function."""

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_ports_available_success(self, mock_run: MagicMock) -> None:
        """Test that ports are available when not in use."""
        mock_result = MagicMock()
        mock_result.stdout = "0.0.0.0:8080->80/tcp"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _check_ports_available((6333, 6334))

        assert result is True

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_ports_available_http_port_in_use(self, mock_run: MagicMock) -> None:
        """Test that ports check returns False when HTTP port is in use."""
        mock_result = MagicMock()
        mock_result.stdout = "0.0.0.0:6333->6333/tcp"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _check_ports_available((6333, 6334))

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_ports_available_grpc_port_in_use(self, mock_run: MagicMock) -> None:
        """Test that ports check returns False when gRPC port is in use."""
        mock_result = MagicMock()
        mock_result.stdout = "0.0.0.0:6334->6334/tcp"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _check_ports_available((6333, 6334))

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_ports_available_error_returns_true(self, mock_run: MagicMock) -> None:
        """Test that ports check returns True on error (assumes available)."""
        mock_run.side_effect = FileNotFoundError()

        result = _check_ports_available((6333, 6334))

        assert result is True


class TestContainerExists:
    """Test _container_exists function."""

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_container_exists_true(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test that container existence check returns True when container exists."""
        vault_path = tmp_path / "vault"
        container_name = _get_container_name(vault_path)

        mock_result = MagicMock()
        mock_result.stdout = f"{container_name}\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _container_exists(vault_path)

        assert result is True

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_container_exists_false(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test that container existence check returns False when container doesn't exist."""
        vault_path = tmp_path / "vault"

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _container_exists(vault_path)

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_container_exists_error_returns_false(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test that container existence check returns False on error."""
        vault_path = tmp_path / "vault"
        mock_run.side_effect = FileNotFoundError()

        result = _container_exists(vault_path)

        assert result is False


class TestIsQdrantRunning:
    """Test is_qdrant_running function."""

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_is_running_true(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test that is_qdrant_running returns True when container is running."""
        vault_path = tmp_path / "vault"
        container_name = _get_container_name(vault_path)

        mock_result = MagicMock()
        mock_result.stdout = f"{container_name}\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = is_qdrant_running(vault_path)

        assert result is True

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_is_running_false(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test that is_qdrant_running returns False when container is not running."""
        vault_path = tmp_path / "vault"

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = is_qdrant_running(vault_path)

        assert result is False

    @patch("obsistant.qdrant.server.subprocess.run")
    def test_is_running_error_returns_false(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Test that is_qdrant_running returns False on error."""
        vault_path = tmp_path / "vault"
        mock_run.side_effect = FileNotFoundError()

        result = is_qdrant_running(vault_path)

        assert result is False


class TestStartQdrantServer:
    """Test start_qdrant_server function."""

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_start_server_already_running(
        self,
        mock_run: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test starting server when it's already running."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = True

        mock_result = MagicMock()
        mock_result.stdout = "container-id-123\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        container_id = start_qdrant_server(vault_path)

        assert container_id == "container-id-123"
        # Should check if running and get container ID, but not start new container
        assert mock_run.call_count >= 1

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server._container_exists")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_start_server_existing_stopped_container(
        self,
        mock_run: MagicMock,
        mock_container_exists: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test starting server when container exists but is stopped."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = False
        mock_container_exists.return_value = True

        # Mock docker start
        mock_start_result = MagicMock()
        mock_start_result.returncode = 0
        # Mock docker ps to get container ID
        mock_ps_result = MagicMock()
        mock_ps_result.stdout = "container-id-456\n"
        mock_ps_result.returncode = 0
        mock_run.side_effect = [mock_start_result, mock_ps_result]

        container_id = start_qdrant_server(vault_path)

        assert container_id == "container-id-456"
        # Should call docker start
        assert any("start" in str(call) for call in mock_run.call_args_list)

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server._container_exists")
    @patch("obsistant.qdrant.server._check_ports_available")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_start_server_new_container(
        self,
        mock_run: MagicMock,
        mock_ports_available: MagicMock,
        mock_container_exists: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test starting a new container."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = False
        mock_container_exists.return_value = False
        mock_ports_available.return_value = True

        # Mock docker run
        mock_run_result = MagicMock()
        mock_run_result.stdout = "new-container-id-789\n"
        mock_run_result.returncode = 0
        mock_run.return_value = mock_run_result

        container_id = start_qdrant_server(vault_path, ports=(6333, 6334))

        assert container_id == "new-container-id-789"
        # Should call docker run
        assert any("run" in str(call) for call in mock_run.call_args_list)

    @patch("obsistant.qdrant.server._check_docker_available")
    def test_start_server_docker_not_available(
        self, mock_docker_available: MagicMock, tmp_path: Path
    ) -> None:
        """Test that starting server raises error when Docker is not available."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = False

        with pytest.raises(RuntimeError, match="Docker is not available"):
            start_qdrant_server(vault_path)

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server._container_exists")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_start_server_port_already_allocated(
        self,
        mock_run: MagicMock,
        mock_container_exists: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that starting server raises error when port is already allocated."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = False
        mock_container_exists.return_value = False

        # Mock docker run to fail with port error
        from subprocess import CalledProcessError

        mock_error = CalledProcessError(1, "docker", stderr="port is already allocated")
        mock_run.side_effect = mock_error

        with pytest.raises(RuntimeError, match="Port.*is already in use"):
            start_qdrant_server(vault_path)


class TestStopQdrantServer:
    """Test stop_qdrant_server function."""

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_stop_server_success(
        self,
        mock_run: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test stopping server successfully."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = True

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = stop_qdrant_server(vault_path)

        assert result is True
        # Should call docker stop
        assert any("stop" in str(call) for call in mock_run.call_args_list)

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    def test_stop_server_not_running(
        self,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test stopping server when it's not running."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = False

        result = stop_qdrant_server(vault_path)

        assert result is False

    @patch("obsistant.qdrant.server._check_docker_available")
    def test_stop_server_docker_not_available(
        self, mock_docker_available: MagicMock, tmp_path: Path
    ) -> None:
        """Test that stopping server raises error when Docker is not available."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = False

        with pytest.raises(RuntimeError, match="Docker is not available"):
            stop_qdrant_server(vault_path)

    @patch("obsistant.qdrant.server._check_docker_available")
    @patch("obsistant.qdrant.server.is_qdrant_running")
    @patch("obsistant.qdrant.server.subprocess.run")
    def test_stop_server_error(
        self,
        mock_run: MagicMock,
        mock_is_running: MagicMock,
        mock_docker_available: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that stopping server raises error on failure."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        mock_docker_available.return_value = True
        mock_is_running.return_value = True

        from subprocess import CalledProcessError

        mock_error = CalledProcessError(1, "docker", stderr="Stop failed")
        mock_run.side_effect = mock_error

        with pytest.raises(RuntimeError, match="Failed to stop Qdrant server"):
            stop_qdrant_server(vault_path)
