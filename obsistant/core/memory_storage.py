"""Memory storage setup functions for CrewAI agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

# Import CrewAI knowledge sources at runtime
try:
    from crewai.knowledge.source.text_file_knowledge_source import (
        TextFileKnowledgeSource,
    )
except ImportError:
    TextFileKnowledgeSource = None  # type: ignore[assignment, misc]


def setup_crewai_storage(
    vault_path: Path | str | None, crew_name: str | None = None
) -> Path | None:
    """Setup CrewAI storage directory and environment variable.

    Creates a crew-specific storage directory in the vault and sets the
    `CREWAI_STORAGE_DIR` environment variable to point to it.

    For the "work" crew, also sets up the user_preference.md knowledge file:
    - Creates the knowledge directory if it doesn't exist
    - Creates a default placeholder file only if user_preference.md doesn't exist
    - The knowledge file should be edited directly at:
      `.obsistant/storage/{crew_name}/knowledge/user_preference.md`

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

    # Setup user_preference.md file for work crew
    # CrewAI expects knowledge sources in a 'knowledge' subdirectory
    # The file should be edited directly at: .obsistant/storage/{crew}/knowledge/user_preference.md
    if crew_name == "work":
        knowledge_dir = storage_dir / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        user_preference_file = knowledge_dir / "user_preference.md"

        # Only create default placeholder if file doesn't exist
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


def get_knowledge_sources(
    knowledge_file_name: str = "user_preference.md",
) -> list[BaseKnowledgeSource]:
    """Get knowledge sources for a crew from the storage directory.

    This function retrieves knowledge sources from the crew's storage directory,
    which is set via the CREWAI_STORAGE_DIR environment variable by setup_crewai_storage().

    The knowledge file should be located at:
    `{storage_dir}/knowledge/{knowledge_file_name}`

    Args:
        knowledge_file_name: Name of the knowledge file to load (default: "user_preference.md").
            The file should be in the `knowledge/` subdirectory of the storage directory.

    Returns:
        List of BaseKnowledgeSource objects. Returns empty list if:
        - CREWAI_STORAGE_DIR is not set
        - Knowledge file doesn't exist
        - Knowledge file is not a regular file
        - CrewAI imports are not available

    Example:
        ```python
        from obsistant.core.memory_storage import get_knowledge_sources

        # Use default user_preference.md
        knowledge_sources = get_knowledge_sources()

        # Use custom knowledge file
        knowledge_sources = get_knowledge_sources("custom_knowledge.md")
        ```
    """
    if TextFileKnowledgeSource is None:
        print(
            "Warning: CrewAI knowledge sources not available. Install CrewAI to use knowledge sources."
        )
        return []

    # Get storage directory from environment variable set by setup_crewai_storage
    storage_dir = os.getenv("CREWAI_STORAGE_DIR")
    if not storage_dir:
        print("Warning: CREWAI_STORAGE_DIR not set, cannot load knowledge sources")
        return []

    storage_path = Path(storage_dir)
    knowledge_file = storage_path / "knowledge" / knowledge_file_name

    # Verify file exists with absolute path
    if not knowledge_file.exists():
        print(
            f"Warning: Knowledge file not found at {knowledge_file}. "
            "Using default knowledge or no knowledge."
        )
        return []

    # Verify it's actually a file
    if not knowledge_file.is_file():
        print(f"Warning: Knowledge path exists but is not a file: {knowledge_file}")
        return []

    # Read file content to verify it's not the default placeholder
    try:
        content = knowledge_file.read_text(encoding="utf-8")
        if "Add your preferences here" in content and len(content) < 200:
            print(
                f"Warning: Knowledge file at {knowledge_file} appears to be "
                "the default placeholder. Please edit it with your preferences."
            )
    except Exception as e:
        print(f"Warning: Could not read knowledge file {knowledge_file}: {e}")
        return []

    # CrewAI prepends 'knowledge/' to paths, so we provide just the filename
    # The CWD is set to storage_dir in main.py, and CrewAI expects files in knowledge/
    print(f"Loading knowledge source from: {knowledge_file}")
    return [TextFileKnowledgeSource(file_paths=[knowledge_file_name])]
