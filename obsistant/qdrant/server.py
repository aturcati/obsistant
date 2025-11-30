"""Qdrant server management functions."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from loguru import logger


def get_qdrant_storage_path(vault_path: Path) -> Path:
    """Get the Qdrant storage directory path for a vault.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        Path to the Qdrant storage directory.
    """
    return vault_path / ".obsistant" / "qdrant_storage"


def ensure_qdrant_storage(vault_path: Path) -> Path:
    """Ensure the Qdrant storage directory exists.

    Creates the `.obsistant/qdrant_storage/` directory if it doesn't exist.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        Path to the Qdrant storage directory.
    """
    storage_path = get_qdrant_storage_path(vault_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def _get_container_name(vault_path: Path) -> str:
    """Generate a unique container name for a vault.

    Uses a hash of the absolute vault path to ensure uniqueness.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        Container name string.
    """
    vault_abs = str(vault_path.resolve())
    # Create a short hash of the vault path
    hash_obj = hashlib.md5(vault_abs.encode())
    hash_hex = hash_obj.hexdigest()[:8]
    return f"obsistant-qdrant-{hash_hex}"


def _check_docker_available() -> bool:
    """Check if Docker is available and running.

    Returns:
        True if Docker is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def _check_ports_available(ports: tuple[int, int]) -> bool:
    """Check if the required ports are available.

    Args:
        ports: Tuple of (http_port, grpc_port).

    Returns:
        True if ports appear available, False otherwise.
    """
    http_port, grpc_port = ports
    try:
        # Check if ports are in use by checking docker containers
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--format",
                "{{.Ports}}",
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        ports_output = result.stdout
        return (
            f":{http_port}->" not in ports_output
            and f":{grpc_port}->" not in ports_output
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        # If we can't check, assume available (will fail later if not)
        return True


def _container_exists(vault_path: Path) -> bool:
    """Check if Qdrant container exists (running or stopped).

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        True if container exists, False otherwise.
    """
    container_name = _get_container_name(vault_path)
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return container_name in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def is_qdrant_running(vault_path: Path) -> bool:
    """Check if Qdrant server is running for this vault.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        True if Qdrant container is running, False otherwise.
    """
    container_name = _get_container_name(vault_path)
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return container_name in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def start_qdrant_server(vault_path: Path, ports: tuple[int, int] = (6333, 6334)) -> str:
    """Start Qdrant server in Docker for the given vault.

    Args:
        vault_path: Path to the vault root directory.
        ports: Tuple of (http_port, grpc_port). Defaults to (6333, 6334).

    Returns:
        Container ID of the started container.

    Raises:
        RuntimeError: If Docker is not available or if starting fails.
        FileNotFoundError: If Docker command is not found.
    """
    if not _check_docker_available():
        raise RuntimeError(
            "Docker is not available. Please ensure Docker is installed and running."
        )

    container_name = _get_container_name(vault_path)
    http_port, grpc_port = ports

    # Check if container is already running
    if is_qdrant_running(vault_path):
        logger.info(f"Qdrant server is already running in container '{container_name}'")
        logger.info(f"Dashboard: http://localhost:{http_port}/dashboard")
        # Get container ID
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.ID}}",
                ],
                capture_output=True,
                check=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return container_name

    # Check if container exists but is stopped
    if _container_exists(vault_path):
        logger.info(
            f"Container '{container_name}' exists but is stopped. Starting it..."
        )
        try:
            subprocess.run(
                ["docker", "start", container_name],
                check=True,
                capture_output=True,
                timeout=30,
            )
            logger.info(f"Started existing container '{container_name}'")
            logger.info(f"Dashboard: http://localhost:{http_port}/dashboard")
            # Get container ID
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.ID}}",
                ],
                capture_output=True,
                check=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as start_error:
            error_msg = (
                start_error.stderr.strip() if start_error.stderr else "Unknown error"
            )
            raise RuntimeError(
                f"Failed to start existing container '{container_name}': {error_msg}"
            ) from start_error
        except subprocess.SubprocessError as start_error:
            raise RuntimeError(
                f"Failed to start existing container '{container_name}'. "
                "You may need to remove it first with: "
                f"docker rm {container_name}"
            ) from start_error

    # Ensure storage directory exists
    storage_path = ensure_qdrant_storage(vault_path)
    storage_abs = str(storage_path.resolve())

    # Check if ports are available (warning only)
    if not _check_ports_available(ports):
        logger.warning(
            f"Ports {http_port} or {grpc_port} may already be in use. "
            "Starting anyway - Docker will fail if ports are unavailable."
        )

    # Build docker run command
    cmd = [
        "docker",
        "run",
        "-d",  # Detached mode
        "--name",
        container_name,
        "-p",
        f"{http_port}:6333",
        "-p",
        f"{grpc_port}:6334",
        "-v",
        f"{storage_abs}:/qdrant/storage:z",
        "qdrant/qdrant",
    ]

    try:
        logger.info(f"Starting Qdrant server for vault at {vault_path}")
        logger.debug(f"Storage directory: {storage_abs}")
        logger.debug(f"Container name: {container_name}")
        logger.debug(f"Ports: HTTP {http_port}, gRPC {grpc_port}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            text=True,
            timeout=30,
        )
        container_id = result.stdout.strip()
        logger.info(f"Qdrant server started successfully. Container ID: {container_id}")
        logger.info(f"HTTP API: http://localhost:{http_port}")
        logger.info(f"gRPC API: localhost:{grpc_port}")
        logger.info(f"Dashboard: http://localhost:{http_port}/dashboard")
        return container_id
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown error"
        if "port is already allocated" in error_msg.lower():
            raise RuntimeError(
                f"Port {http_port} or {grpc_port} is already in use. "
                "Please stop the conflicting service or use different ports."
            ) from e
        if "name is already in use" in error_msg.lower():
            # Container exists but not running, try to start it
            logger.info(
                f"Container '{container_name}' exists but is not running. Starting it..."
            )
            try:
                subprocess.run(
                    ["docker", "start", container_name],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                logger.info(f"Started existing container '{container_name}'")
                # Get container ID
                result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        f"name={container_name}",
                        "--format",
                        "{{.ID}}",
                    ],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=5,
                )
                return result.stdout.strip()
            except subprocess.SubprocessError as start_error:
                raise RuntimeError(
                    f"Failed to start existing container '{container_name}'. "
                    "You may need to remove it first with: "
                    f"docker rm {container_name}"
                ) from start_error
        raise RuntimeError(f"Failed to start Qdrant server: {error_msg}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "Docker command timed out. Please check Docker status."
        ) from None
    except FileNotFoundError:
        raise FileNotFoundError(
            "Docker command not found. Please ensure Docker is installed."
        ) from None


def stop_qdrant_server(vault_path: Path) -> bool:
    """Stop Qdrant server for the given vault.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        True if container was stopped, False if it wasn't running.

    Raises:
        RuntimeError: If stopping fails.
        FileNotFoundError: If Docker command is not found.
    """
    if not _check_docker_available():
        raise RuntimeError(
            "Docker is not available. Please ensure Docker is installed and running."
        )

    container_name = _get_container_name(vault_path)

    if not is_qdrant_running(vault_path):
        logger.info(f"Qdrant server is not running for vault at {vault_path}")
        return False

    try:
        logger.info(f"Stopping Qdrant server container '{container_name}'")
        subprocess.run(
            ["docker", "stop", container_name],
            check=True,
            capture_output=True,
            timeout=30,
        )
        logger.info("Qdrant server stopped successfully")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown error"
        raise RuntimeError(f"Failed to stop Qdrant server: {error_msg}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "Docker command timed out. Please check Docker status."
        ) from None
    except FileNotFoundError:
        raise FileNotFoundError(
            "Docker command not found. Please ensure Docker is installed."
        ) from None
