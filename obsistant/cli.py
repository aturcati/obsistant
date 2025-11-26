"""Command line interface for obsistant."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
from loguru import logger

from . import __version__
from .agents import calendar_kickoff
from .backup import clear_backups as clear_backups_func
from .backup import create_vault_backup
from .backup import restore_files as restore_files_func
from .config import load_config, save_config
from .core.calendar_auth import authenticate_google_calendar
from .meetings import process_meetings_folder
from .notes import process_notes_folder, process_quick_notes_folder
from .vault import init_vault, process_vault


class DefaultCommandGroup(click.Group):
    """Group that falls back to a default command when none is provided."""

    def __init__(
        self,
        *args: Any,
        default_command: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.default_command = default_command

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, Any, list[str]]:
        if not args and self.default_command:
            cmd = self.get_command(ctx, self.default_command)
            if cmd is None:
                raise click.UsageError(
                    f"Default command '{self.default_command}' not found."
                )
            return self.default_command, cmd, args

        if args:
            cmd_name = args[0]
            cmd = self.get_command(ctx, cmd_name)
            if cmd is not None:
                return cmd_name, cmd, args[1:]

        if self.default_command:
            cmd = self.get_command(ctx, self.default_command)
            if cmd is None:
                raise click.UsageError(
                    f"Default command '{self.default_command}' not found."
                )
            return self.default_command, cmd, args
        result: tuple[str | None, Any, list[str]] = super().resolve_command(ctx, args)
        return result


def setup_logger(verbose: bool = False) -> Any:
    """Set up logger with appropriate level."""
    # Remove default handler
    logger.remove()

    # Add custom handler with format matching previous behavior
    # Loguru format: {level} gives uppercase level name (INFO, DEBUG, etc.)
    logger.add(
        sys.stderr,
        format="{level}: {message}",
        level="DEBUG" if verbose else "INFO",
    )

    return logger


def get_config_or_default(
    vault_path: Path, **kwargs: Any
) -> tuple[Any, dict[str, Any]]:
    """Load config from vault and merge with CLI arguments.

    CLI arguments override config values. If config doesn't exist, uses defaults.

    Args:
        vault_path: Path to the vault root.
        **kwargs: CLI argument values that override config.

    Returns:
        Tuple of (config object, dict of effective values).
    """
    config = load_config(vault_path)
    effective: dict[str, Any] = {}

    # Backup extension: CLI arg or config or default
    effective["backup_ext"] = kwargs.get("backup_ext") or (
        config.processing.backup_ext if config else ".bak"
    )

    # Folder names: CLI arg or config or defaults
    if config:
        effective["meetings_folder"] = (
            kwargs.get("meetings_folder") or config.vault.meetings
        )
        effective["notes_folder"] = kwargs.get("notes_folder") or config.vault.notes
        effective["quick_notes_folder"] = (
            kwargs.get("quick_notes_folder") or config.vault.quick_notes
        )
    else:
        effective["meetings_folder"] = kwargs.get("meetings_folder") or "10-Meetings"
        effective["notes_folder"] = kwargs.get("notes_folder") or "20-Notes"
        effective["quick_notes_folder"] = (
            kwargs.get("quick_notes_folder") or "00-Quick Notes"
        )

    return config, effective


@click.group(cls=DefaultCommandGroup, default_command="process")
@click.version_option(version=__version__, prog_name="obsistant")
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
    help="Format markdown files for consistent styling (preserves tables when mdformat-gfm is available)",
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
        config, effective = get_config_or_default(vault_path, backup_ext=backup_ext)
        process_vault(
            root=str(vault_path),
            dry_run=dry_run,
            backup_ext=effective["backup_ext"],
            logger=logger,
            format_md=format_markdown,
            specific_file=specific_file,
            config=config,
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
@click.option(
    "--format",
    "-f",
    "format_markdown",
    is_flag=True,
    help="Format markdown files for consistent styling (preserves tables when mdformat-gfm is available)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def meetings(
    vault_path: Path,
    meetings_folder: str,
    dry_run: bool,
    backup_ext: str,
    format_markdown: bool,
    verbose: bool,
) -> None:
    """Process meetings folder to rename files and ensure 'meeting' tags.

    VAULT_PATH: Path to the Obsidian vault directory

    This tool will:
    - Rename files using the template: YYMMDD_Title
    - Date comes from frontmatter 'created' field or file creation date
    - Ensure all files have the 'meeting' tag in frontmatter
    - Archive meetings older than 2 working weeks to Archive/YYYY/ folders
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
        config, effective = get_config_or_default(
            vault_path, meetings_folder=meetings_folder, backup_ext=backup_ext
        )
        process_meetings_folder(
            vault_root=vault_path,
            meetings_folder=effective["meetings_folder"],
            dry_run=dry_run,
            backup_ext=effective["backup_ext"],
            logger=logger,
            format_md=format_markdown,
            config=config,
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
    help="Format markdown files for consistent styling (preserves tables when mdformat-gfm is available)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def notes(
    vault_path: Path,
    notes_folder: str,
    dry_run: bool,
    backup_ext: str,
    format_markdown: bool,
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
        config, effective = get_config_or_default(
            vault_path, notes_folder=notes_folder, backup_ext=backup_ext
        )
        process_notes_folder(
            vault_root=vault_path,
            notes_folder=effective["notes_folder"],
            dry_run=dry_run,
            backup_ext=effective["backup_ext"],
            logger=logger,
            format_md=format_markdown,
            config=config,
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
    help="Format markdown files for consistent styling (preserves tables when mdformat-gfm is available)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def quick_notes(
    vault_path: Path,
    notes_folder: str,
    quick_notes_folder: str,
    meetings_folder: str,
    dry_run: bool,
    backup_ext: str,
    format_markdown: bool,
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
        config, effective = get_config_or_default(
            vault_path,
            notes_folder=notes_folder,
            quick_notes_folder=quick_notes_folder,
            meetings_folder=meetings_folder,
            backup_ext=backup_ext,
        )
        process_quick_notes_folder(
            vault_root=vault_path,
            notes_folder=effective["notes_folder"],
            quick_notes_folder=effective["quick_notes_folder"],
            dry_run=dry_run,
            backup_ext=effective["backup_ext"],
            logger=logger,
            meetings_folder=effective["meetings_folder"],
            format_md=format_markdown,
            config=config,
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
@click.option(
    "--backup-ext", "-b", default=".bak", help="Backup file extension (default: .bak)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def restore(
    vault_path: Path,
    specific_file: Path | None,
    backup_ext: str,
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

        config, effective = get_config_or_default(vault_path, backup_ext=backup_ext)
        restored_count = restore_files_func(
            vault_path, specific_file, effective["backup_ext"]
        )
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


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--overwrite-config",
    is_flag=True,
    help="Overwrite existing config.yaml if it exists",
)
@click.option(
    "--skip-folders",
    is_flag=True,
    help="Don't create folder structure, only create config.yaml",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def init(
    vault_path: Path,
    overwrite_config: bool,
    skip_folders: bool,
    verbose: bool,
) -> None:
    """Initialize a new vault with directory structure and config.yaml.

    VAULT_PATH: Path where the vault should be created

    This command will:
    - Create the recommended vault folder structure
    - Create .obsistant/ folder for utility files
    - Create .obsistant/config.yaml file with default configuration values
    """
    logger = setup_logger(verbose)

    try:
        init_vault(
            vault_path=vault_path,
            overwrite_config=overwrite_config,
            skip_folders=skip_folders,
        )
        logger.info(f"Vault initialized at {vault_path}")
        logger.info("Created .obsistant/config.yaml with default values")
        if not skip_folders:
            logger.info("Created recommended folder structure")
    except FileExistsError as e:
        logger.error(str(e))
        raise click.ClickException(str(e)) from e
    except Exception as e:
        logger.error(f"Error initializing vault: {e}")
        raise click.ClickException(str(e)) from e


@cli.command(name="calendar-login")
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def calendar_login(vault_path: Path, verbose: bool) -> None:
    """Authenticate with Google Calendar API.

    VAULT_PATH: Path to the Obsidian vault directory

    This command will:
    - Create .obsistant/ folder if it doesn't exist
    - Look for credentials.json in .obsistant/ (or path from .obsistant/config.yaml)
    - Run OAuth flow to authenticate with Google Calendar
    - Save token.json to .obsistant/ (or path from .obsistant/config.yaml)
    - Update .obsistant/config.yaml with credential paths if not already set
    """
    logger = setup_logger(verbose)

    try:
        # Load or create config
        config = load_config(vault_path)
        if config is None:
            from .config import Config

            config = Config()
            logger.info("No config.yaml found in .obsistant/, using defaults")

        # Get credential paths from config
        credentials_path = Path(config.calendar.credentials_path)
        token_path = Path(config.calendar.token_path)

        # Ensure .obsistant folder exists
        obsistant_dir = vault_path / ".obsistant"
        obsistant_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured .obsistant/ folder exists at {obsistant_dir}")

        # Resolve paths relative to vault_path if not absolute
        if not credentials_path.is_absolute():
            credentials_path = vault_path / credentials_path
        if not token_path.is_absolute():
            token_path = vault_path / token_path

        # Check if credentials.json exists
        if not credentials_path.exists():
            logger.error(
                f"credentials.json not found at {credentials_path}. "
                "Please place your Google OAuth credentials file there."
            )
            raise click.ClickException(
                f"credentials.json not found at {credentials_path}"
            )

        logger.info(f"Found credentials.json at {credentials_path}")
        logger.info("Starting OAuth flow...")

        # Authenticate (will run OAuth flow if needed)
        creds = authenticate_google_calendar(vault_path, credentials_path, token_path)

        if creds and creds.valid:
            logger.info(f"Successfully authenticated! Token saved to {token_path}")

            # Update config.yaml if paths are not already set to defaults
            # (in case user had custom paths, we don't overwrite)
            if (
                config.calendar.credentials_path != ".obsistant/credentials.json"
                or config.calendar.token_path != ".obsistant/token.json"
            ):
                logger.info("Updating config.yaml with credential paths...")
                save_config(config, vault_path)
            else:
                # Ensure config.yaml exists with defaults
                config_path = vault_path / ".obsistant" / "config.yaml"
                if not config_path.exists():
                    logger.info("Creating config.yaml with default credential paths...")
                    save_config(config, vault_path)

            logger.info("Calendar login completed successfully!")
        else:
            raise click.ClickException("Authentication failed")

    except FileNotFoundError as e:
        logger.error(str(e))
        raise click.ClickException(str(e)) from e
    except Exception as e:
        logger.error(f"Error during calendar login: {e}")
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def calendar(vault_path: Path, verbose: bool) -> None:
    """Run the CrewAI calendar flow to generate weekly events summary.

    VAULT_PATH: Path to the Obsidian vault directory

    This command will:
    - Fetch next week's calendar events
    - Generate a summary of upcoming events
    - Save the summary to Weekly Summaries folder in the meetings directory
    """
    logger = setup_logger(verbose)

    try:
        config, effective = get_config_or_default(vault_path)
        meetings_folder = effective["meetings_folder"]

        logger.info(f"Running calendar flow for vault at {vault_path}...")
        calendar_kickoff(vault_path=str(vault_path), meetings_folder=meetings_folder)
        logger.info("Calendar flow completed successfully!")
        logger.info(f"Summary saved to {meetings_folder}/Weekly Summaries/")
    except Exception as e:
        logger.error(f"Error running calendar flow: {e}")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
