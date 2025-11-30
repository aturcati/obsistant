"""Vault initialization functions for obsistant."""

from __future__ import annotations

from pathlib import Path

from ..config import Config, save_config


def init_vault(
    vault_path: Path,
    overwrite_config: bool = False,
    skip_folders: bool = False,
) -> None:
    """Initialize a new vault with directory structure and config.yaml.

    Creates the recommended vault structure and a config.yaml file in .obsistant/ folder with default values.

    Args:
        vault_path: Path where the vault should be created.
        overwrite_config: If True, overwrite existing config.yaml.
        skip_folders: If True, don't create folder structure.

    Raises:
        OSError: If vault path cannot be created or written to.
    """
    # Create vault directory if it doesn't exist
    vault_path.mkdir(parents=True, exist_ok=True)

    # Create .obsistant folder (utility folder, always created)
    obsistant_dir = vault_path / ".obsistant"
    obsistant_dir.mkdir(parents=True, exist_ok=True)

    # Create storage directory for CrewAI memory
    storage_dir = obsistant_dir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Create qdrant_storage directory for Qdrant vector database
    qdrant_storage_dir = obsistant_dir / "qdrant_storage"
    qdrant_storage_dir.mkdir(parents=True, exist_ok=True)

    # Create folder structure
    if not skip_folders:
        folders = [
            "00-Quick Notes",
            "10-Meetings",
            "20-Notes",
            "30-Guides",
            "40-Vacations",
            "50-Files",
        ]

        for folder in folders:
            folder_path = vault_path / folder
            folder_path.mkdir(exist_ok=True)

        # Create subfolders in Notes
        notes_path = vault_path / "20-Notes"
        notes_subfolders = [
            "products",
            "projects",
            "devops",
            "challenges",
            "events",
            "various",
        ]
        for subfolder in notes_subfolders:
            (notes_path / subfolder).mkdir(exist_ok=True)

    # Create config.yaml in .obsistant folder
    config_path = obsistant_dir / "config.yaml"
    if config_path.exists() and not overwrite_config:
        raise FileExistsError(
            f"config.yaml already exists at {config_path}. Use --overwrite-config to overwrite."
        )

    config = Config()
    save_config(config, vault_path)
