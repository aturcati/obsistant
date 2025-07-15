"""Command line interface for obsistant."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from .processor import (
    clear_backups as clear_backups_func,
)
from .processor import (
    process_vault,
)
from .processor import (
    restore_files as restore_files_func,
)


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Set up logger with appropriate level."""
    logger = logging.getLogger("obsistant")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Process Obsidian vault to extract tags and add metadata.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Extract #tags from markdown content and add them to frontmatter
    - Remove tags from the main text content
    - Add creation date using the earliest date between body content and file metadata
    - Add modification date from file metadata
    - Extract meeting transcript URLs from 'Chat with meeting transcript:' text
    - Optionally format markdown files for consistent styling
    - Create backup files in a separate backup folder structure
    - Restore corrupted files from backups
    """


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--backup-ext", "-b", default=".bak", help="Backup file extension (default: .bak)"
)
@click.option(
    "--format",
    "-f",
    "format_markdown",
    is_flag=True,
    help="Format markdown files for consistent styling",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def process(
    vault_path: Path,
    dry_run: bool,
    backup_ext: str,
    format_markdown: bool,
    verbose: bool,
) -> None:
    """Process Obsidian vault to extract tags and add metadata.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Extract #tags from markdown content and add them to frontmatter
    - Remove tags from the main text content
    - Add creation date using the earliest date between body content and file metadata
    - Add modification date from file metadata
    - Extract meeting transcript URLs from 'Chat with meeting transcript:' text
    - Optionally format markdown files for consistent styling
    - Create backup files in a separate backup folder structure
    """
    logger = setup_logger(verbose)

    if dry_run:
        logger.info(f"DRY RUN: Processing vault at {vault_path}")
    else:
        logger.info(f"Processing vault at {vault_path}")

    try:
        process_vault(
            root=str(vault_path),
            dry_run=dry_run,
            backup_ext=backup_ext,
            logger=logger,
            format_md=format_markdown,
        )
        logger.info("Processing complete!")
    except Exception as e:
        logger.error(f"Error processing vault: {e}")
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def clear_backups(
    vault_path: Path,
    verbose: bool,
) -> None:
    """Clear all backup files for the specified vault.

    VAULT_PATH: Path to the Obsidian vault directory

    This will remove all backup files in the corresponding backup folder.
    """
    logger = setup_logger(verbose)

    try:
        deleted_count = clear_backups_func(vault_path)
        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} backup files for vault {vault_path}")
        else:
            logger.info(f"No backup files found for vault {vault_path}")
    except Exception as e:
        logger.error(f"Error clearing backups: {e}")
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--file",
    "specific_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Restore a specific file instead of all files",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def restore(
    vault_path: Path,
    specific_file: Path | None,
    verbose: bool,
) -> None:
    """Restore corrupted files from backups.

    VAULT_PATH: Path to the Obsidian vault directory

    This will restore files from the corresponding backup folder.
    Use --file to restore only a specific file.
    """
    logger = setup_logger(verbose)

    try:
        # Validate that specific_file is within vault_path if provided
        if specific_file:
            try:
                specific_file.resolve().relative_to(vault_path.resolve())
            except ValueError as e:
                raise click.ClickException(
                    f"File {specific_file} is not within vault {vault_path}"
                ) from e

        restored_count = restore_files_func(vault_path, specific_file)
        if restored_count > 0:
            if specific_file:
                logger.info(f"Restored {specific_file} from backup")
            else:
                logger.info(
                    f"Restored {restored_count} files from backups for vault {vault_path}"
                )
        else:
            if specific_file:
                logger.info(f"No backup found for {specific_file}")
            else:
                logger.info(f"No backup files found for vault {vault_path}")
    except Exception as e:
        logger.error(f"Error restoring files: {e}")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
