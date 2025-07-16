"""Command line interface for obsistant."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from .processor import (
    clear_backups as clear_backups_func,
)
from .processor import (
    create_vault_backup,
    process_meetings_folder,
    process_notes_folder,
    process_quick_notes_folder,
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
    - Create complete vault backups with timestamps
    - Restore corrupted files from backups
    """


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--file",
    "specific_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Process only this specific file instead of the entire vault",
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
    specific_file: Path | None,
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

    # Validate that specific_file is within vault_path if provided
    if specific_file:
        try:
            specific_file.resolve().relative_to(vault_path.resolve())
        except ValueError as e:
            raise click.ClickException(
                f"File {specific_file} is not within vault {vault_path}"
            ) from e

        # Validate that the file is a markdown file
        if not specific_file.suffix.lower() == ".md":
            raise click.ClickException(
                f"File {specific_file} is not a markdown file (.md)"
            )

    if specific_file:
        if dry_run:
            logger.info(
                f"DRY RUN: Processing file {specific_file} in vault {vault_path}"
            )
        else:
            logger.info(f"Processing file {specific_file} in vault {vault_path}")
    else:
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
            specific_file=specific_file,
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
@click.option(
    "--meetings-folder",
    "-m",
    default="10-Meetings",
    help="Name of the meetings folder within the vault (default: 10-Meetings)",
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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def meetings(
    vault_path: Path,
    meetings_folder: str,
    dry_run: bool,
    backup_ext: str,
    verbose: bool,
) -> None:
    """Process meetings folder to rename files and ensure 'meeting' tags.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Rename files using the template: YYMMDD_Title
    - Date comes from frontmatter 'created' field or file creation date
    - Ensure all files have the 'meeting' tag in frontmatter
    - Create backup files before making changes
    """
    logger = setup_logger(verbose)

    if dry_run:
        logger.info(
            f"DRY RUN: Processing meetings folder '{meetings_folder}' in vault {vault_path}"
        )
    else:
        logger.info(
            f"Processing meetings folder '{meetings_folder}' in vault {vault_path}"
        )

    try:
        process_meetings_folder(
            vault_root=vault_path,
            meetings_folder=meetings_folder,
            dry_run=dry_run,
            backup_ext=backup_ext,
            logger=logger,
        )
        logger.info("Meetings folder processing complete!")
    except Exception as e:
        logger.error(f"Error processing meetings folder: {e}")
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
    "--notes-folder",
    default="20-Notes",
    help="Name of the notes folder within the vault (default: 20-Notes)",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--backup-ext", "-b", default=".bak", help="Backup file extension (default: .bak)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def notes(
    vault_path: Path,
    notes_folder: str,
    dry_run: bool,
    backup_ext: str,
    verbose: bool,
) -> None:
    """Process notes folder to organize files by tags in separate folders.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Create folders for each tag: products, projects, devops, challenges, events
    - Move notes into corresponding tag folders
    - Ignores the 'olt' tag
    """
    logger = setup_logger(verbose)

    if dry_run:
        logger.info(
            f"DRY RUN: Processing notes folder '{notes_folder}' in vault {vault_path}"
        )
    else:
        logger.info(f"Processing notes folder '{notes_folder}' in vault {vault_path}")

    try:
        process_notes_folder(
            vault_root=vault_path,
            notes_folder=notes_folder,
            dry_run=dry_run,
            backup_ext=backup_ext,
            logger=logger,
        )
        logger.info("Notes folder processing complete!")
    except Exception as e:
        logger.error(f"Error processing notes folder: {e}")
        raise click.ClickException(str(e)) from e


@cli.command(name="quick-notes")
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--notes-folder",
    default="20-Notes",
    help="Name of the notes folder within the vault (default: 20-Notes)",
)
@click.option(
    "--quick-notes-folder",
    default="00-Quick Notes",
    help="Name of the quick notes folder within the vault (default: 00-Quick Notes)",
)
@click.option(
    "--meetings-folder",
    default="10-Meetings",
    help="Name of the meetings folder within the vault (default: 10-Meetings)",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--backup-ext", "-b", default=".bak", help="Backup file extension (default: .bak)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def quick_notes(
    vault_path: Path,
    notes_folder: str,
    quick_notes_folder: str,
    meetings_folder: str,
    dry_run: bool,
    backup_ext: str,
    verbose: bool,
) -> None:
    """Process quick notes folder to organize files by tags.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Move files with 'meeting' tag to the meetings folder
    - Move other files to appropriate tag folders in notes
    - Create folders for each tag: products, projects, devops, challenges, events
    - Ignores the 'olt' tag
    """
    logger = setup_logger(verbose)

    if dry_run:
        logger.info(
            f"DRY RUN: Processing quick notes folder '{quick_notes_folder}' to organize into '{notes_folder}' and '{meetings_folder}' in vault {vault_path}"
        )
    else:
        logger.info(
            f"Processing quick notes folder '{quick_notes_folder}' to organize into '{notes_folder}' and '{meetings_folder}' in vault {vault_path}"
        )

    try:
        process_quick_notes_folder(
            vault_root=vault_path,
            notes_folder=notes_folder,
            quick_notes_folder=quick_notes_folder,
            dry_run=dry_run,
            backup_ext=backup_ext,
            logger=logger,
            meetings_folder=meetings_folder,
        )
        logger.info("Quick notes processing complete!")
    except Exception as e:
        logger.error(f"Error processing quick notes folder: {e}")
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--backup-name",
    type=str,
    default=None,
    help="Optional name for the backup directory. Defaults to a timestamp.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def backup(
    vault_path: Path,
    backup_name: str | None,
    verbose: bool,
) -> None:
    """Create a complete backup of the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    This will create a full copy of the vault in a timestamped backup directory.
    """
    logger = setup_logger(verbose)

    logger.info(f"Creating backup for vault at {vault_path}")
    try:
        backup_path = create_vault_backup(
            vault_root=vault_path, backup_name=backup_name
        )
        logger.info(f"Backup created at: {backup_path}")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
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
