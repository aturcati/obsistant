"""Vault-wide processing functions for obsistant."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..config import Config
from ..core import process_file, walk_markdown_files
from ..utils import console

if TYPE_CHECKING:
    from typing import Any


def process_vault(
    root: str,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
    specific_file: Path | None = None,
    config: Config | None = None,
) -> None:
    """Orchestrate processing of the entire vault or a specific file and provide summary statistics.

    Args:
        root: Root directory of the vault.
        dry_run: If True, don't write changes.
        backup_ext: Extension for backup files.
        logger: Logger instance.
        format_md: If True, format markdown.
        specific_file: Optional specific file to process. If None, processes all files.
        config: Optional configuration object.
    """
    vault_root = Path(root)

    total_added_tags = 0
    total_removed_tags = 0
    total_processed_files = 0

    if specific_file:
        # Process only the specific file
        stats = process_file(
            specific_file, vault_root, dry_run, backup_ext, logger, format_md, config
        )
        total_added_tags += stats["added_tags"]
        total_removed_tags += stats["removed_tags"]
        if stats["processed"]:
            total_processed_files += 1
    else:
        # Process all markdown files in the vault
        for markdown_file in walk_markdown_files(vault_root):
            stats = process_file(
                markdown_file,
                vault_root,
                dry_run,
                backup_ext,
                logger,
                format_md,
                config,
            )
            total_added_tags += stats["added_tags"]
            total_removed_tags += stats["removed_tags"]
            if stats["processed"]:
                total_processed_files += 1

    # Print summary statistics using rich
    if specific_file:
        console.print("[bold green]File Processing Summary[/]")
        console.print(f"File: [bold]{specific_file.relative_to(vault_root)}[/]")
    else:
        console.print("[bold green]Vault Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed_files}[/]")
    console.print(f"Total tags added: [bold]{total_added_tags}[/]")
    console.print(f"Total tags removed: [bold]{total_removed_tags}[/]")
