"""Memory storage setup functions for CrewAI agents."""

from __future__ import annotations

import os
from pathlib import Path


def setup_crewai_storage(vault_path: Path | str | None) -> Path | None:
    """Setup CrewAI storage directory and environment variable.

    Creates the `.obsistant/storage` directory in the vault and sets the
    `CREWAI_STORAGE_DIR` environment variable to point to it.

    Args:
        vault_path: Path to the Obsidian vault directory. If None, returns None
            without setting up storage.

    Returns:
        Path to the storage directory if vault_path is provided, None otherwise.
    """
    if vault_path is None:
        return None

    vault_path_obj = Path(vault_path)
    storage_dir = vault_path_obj / ".obsistant" / "storage"

    # Create storage directory if it doesn't exist
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variable to absolute path for CrewAI
    os.environ["CREWAI_STORAGE_DIR"] = str(storage_dir.resolve())

    return storage_dir
