"""Memory storage setup functions for CrewAI agents."""

from __future__ import annotations

import os
from pathlib import Path


def setup_crewai_storage(
    vault_path: Path | str | None, crew_name: str | None = None
) -> Path | None:
    """Setup CrewAI storage directory and environment variable.

    Creates a crew-specific storage directory in the vault and sets the
    `CREWAI_STORAGE_DIR` environment variable to point to it.

    Args:
        vault_path: Path to the Obsidian vault directory. If None, returns None
            without setting up storage.
        crew_name: Optional name identifier for the crew. If provided, creates
            a subdirectory `.obsistant/storage/{crew_name}`. If None, uses
            `.obsistant/storage` as before.

    Returns:
        Path to the storage directory if vault_path is provided, None otherwise.
    """
    if vault_path is None:
        return None

    vault_path_obj = Path(vault_path)
    if crew_name:
        storage_dir = vault_path_obj / ".obsistant" / "storage" / crew_name
    else:
        storage_dir = vault_path_obj / ".obsistant" / "storage"

    # Create storage directory if it doesn't exist
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Create default user_preference.md file for work crew if it doesn't exist
    # CrewAI expects knowledge sources in a 'knowledge' subdirectory
    if crew_name == "work":
        knowledge_dir = storage_dir / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        user_preference_file = knowledge_dir / "user_preference.md"
        if not user_preference_file.exists():
            user_preference_file.write_text(
                "# User Preferences\n\n"
                "This file contains user preferences and context for work-related tasks.\n\n"
                "Add your preferences here.\n",
                encoding="utf-8",
            )

    # Set environment variable to absolute path for CrewAI
    os.environ["CREWAI_STORAGE_DIR"] = str(storage_dir.resolve())

    return storage_dir
