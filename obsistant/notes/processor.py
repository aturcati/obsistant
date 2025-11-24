"""Notes organization functions for obsistant."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..backup.operations import create_backup_path
from ..config import Config
from ..core import process_file, split_frontmatter
from ..utils import console

if TYPE_CHECKING:
    from typing import Any


def _find_target_folder_for_tags(
    tags: list[str], config: Config | None = None
) -> str | None:
    """Find the appropriate target folder for a list of tags.

    Args:
        tags: List of tag strings from frontmatter.
        config: Optional configuration object.

    Returns:
        Target folder name or None if no match found.
    """
    target_tags = (
        config.tags.target_tags
        if config
        else ["products", "projects", "devops", "challenges", "events"]
    )
    ignored_tags = config.tags.ignored_tags if config else ["olt"]

    for tag in tags:
        tag_lower = tag.lower()

        # Skip ignored tags
        if tag_lower in [ignored.lower() for ignored in ignored_tags]:
            continue

        # Check if this tag matches any of our target tags or is a subtag
        for target_tag in target_tags:
            # Handle direct matches or subtags
            if tag_lower == target_tag or tag_lower.startswith(f"{target_tag}/"):
                # For subtags, create the full folder path
                if tag_lower.startswith(f"{target_tag}/"):
                    # Extract the subtag part and create folder structure
                    subtag_part = tag_lower[
                        len(target_tag) + 1 :
                    ]  # Remove "target_tag/" prefix
                    return f"{target_tag}/{subtag_part}"
                else:
                    return target_tag
            # Handle olt/ prefixed tags like "olt/challenges/reach"
            elif (
                tag_lower.startswith(f"olt/{target_tag}/")
                or tag_lower == f"olt/{target_tag}"
            ):
                if tag_lower.startswith(f"olt/{target_tag}/"):
                    # Extract the subtag part and create folder structure
                    subtag_part = tag_lower[
                        len(f"olt/{target_tag}") + 1 :
                    ]  # Remove "olt/target_tag/" prefix
                    return f"{target_tag}/{subtag_part}"
                else:
                    return target_tag
    return None


def _move_file_to_folder(
    file_path: Path,
    target_dir: Path,
    vault_root: Path,
    backup_ext: str,
    dry_run: bool,
    logger: Any,
    file_content: str,
    target_folder: str,
    destination_name: str = "",
) -> bool:
    """Move a file to a target directory with backup.

    Args:
        file_path: Source file path.
        target_dir: Target directory path.
        vault_root: Vault root path for relative path calculations.
        backup_ext: Backup file extension.
        dry_run: Whether this is a dry run.
        logger: Logger instance.
        file_content: Content of the file for backup.
        target_folder: Name of target folder for logging.
        destination_name: Optional custom destination name for logging.

    Returns:
        True if file was moved, False otherwise.
    """
    target_path = target_dir / file_path.name

    # Skip if file is already in the correct location
    if file_path.resolve() == target_path.resolve():
        return False

    # Create the directory if it doesn't exist
    if not target_dir.exists():
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {target_dir.relative_to(vault_root)}")
        else:
            logger.info(
                f"[DRY RUN] Would create folder: {target_dir.relative_to(vault_root)}"
            )

    # Check if target file already exists (different from source)
    if target_path.exists():
        logger.warning(
            f"Target file {target_path.relative_to(vault_root)} already exists, skipping move"
        )
        return False

    # Move the file
    if not dry_run:
        # Create backup before moving
        backup_path = create_backup_path(vault_root, file_path, backup_ext)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(file_content, encoding="utf-8")

        # Move the file
        file_path.rename(target_path)
        dest_display = destination_name or f"{target_folder}/{file_path.name}"
        logger.info(f"Moved {file_path.name} -> {dest_display}")
    else:
        dest_display = destination_name or f"{target_folder}/{file_path.name}"
        logger.info(f"[DRY RUN] Would move {file_path.name} -> {dest_display}")

    return True


def process_notes_folder(
    vault_root: Path,
    notes_folder: str,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
    config: Config | None = None,
) -> None:
    """Process all files in the Notes folder to organize them by tags into subfolders.

    Recursively traverses the entire notes directory tree and moves files to appropriate
    locations based on their tags. Creates subfolders for each relevant tag.
    Only handles specific tags configured in config (default: products, projects, devops, challenges, events).
    Ignores configured ignored tags (default: 'olt'). Files with multiple relevant tags are moved to the first matching tag folder.
    Files without matching tags are moved to a 'various' folder.
    Subtags create nested folder structures (e.g., 'olt/challenges/reach' creates 'challenges/reach/').

    Args:
        vault_root: Root directory of the vault.
        notes_folder: Name of the notes folder.
        dry_run: If True, don't write changes.
        backup_ext: Extension for backup files.
        logger: Logger instance.
        format_md: If True, format markdown.
        config: Optional configuration object.
    """
    notes_path = vault_root / notes_folder

    if not notes_path.exists() or not notes_path.is_dir():
        logger.error(f"Notes folder '{notes_folder}' not found in vault")
        return

    total_processed = 0
    total_moved = 0
    folders_created = set()

    # Recursively find all markdown files in the notes directory tree
    for markdown_file in notes_path.rglob("*.md"):
        try:
            # First process the file to extract tags, add metadata, and optionally format
            process_file(
                markdown_file,
                vault_root,
                dry_run,
                backup_ext,
                logger,
                format_md,
                config,
            )

            # Read the file content after processing
            with markdown_file.open("r", encoding="utf-8") as file:
                text = file.read()

            frontmatter, body = split_frontmatter(text)

            # Extract tags from frontmatter
            tags = frontmatter.get("tags", []) if frontmatter else []
            if not isinstance(tags, list):
                tags = []

            # Find the first matching target tag (including subtags)
            target_folder = _find_target_folder_for_tags(tags, config)

            # If we found a matching tag, move the file to that folder
            # Otherwise, move to "various" folder
            if not target_folder:
                target_folder = "various"

            # Create the target directory path
            target_dir = notes_path / target_folder

            # Move the file
            if _move_file_to_folder(
                markdown_file,
                target_dir,
                vault_root,
                backup_ext,
                dry_run,
                logger,
                text,
                target_folder,
            ):
                total_moved += 1
                folders_created.add(target_folder)

            total_processed += 1

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {markdown_file}: {e}")
            continue

    # Print summary
    console.print("[bold green]Notes Folder Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed}[/]")
    console.print(f"Files moved: [bold]{total_moved}[/]")
    console.print(f"Folders created: [bold]{len(folders_created)}[/]")
    if folders_created:
        console.print(f"Created folders: [bold]{', '.join(sorted(folders_created))}[/]")


def process_quick_notes_folder(
    vault_root: Path,
    notes_folder: str,
    quick_notes_folder: str,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    meetings_folder: str = "10-Meetings",
    format_md: bool = False,
    config: Config | None = None,
) -> None:
    """Process all files in the Quick Notes folder to organize them by tags.

    Processes the quick notes folder, sorts files into appropriate locations,
    applies meetings formatting to files moved to the meetings folder, and notes
    formatting to those moved to the notes folder.

    Moves files from the Quick Notes folder to the appropriate destinations:
    - Files with 'meeting' tag -> meetings folder
    - Other files -> appropriate subfolders in the Notes folder based on their tags

    Args:
        vault_root: Path to the vault root directory.
        notes_folder: Name of the notes folder (e.g., '20-Notes').
        quick_notes_folder: Name of the quick notes folder (e.g., '00-Quick Notes').
        dry_run: If True, only show what would be done without making changes.
        backup_ext: Extension to use for backup files.
        logger: Logger instance for output.
        meetings_folder: Name of the meetings folder (e.g., '10-Meetings').
        format_md: If True, format markdown.
        config: Optional configuration object.
    """
    quick_notes_path = vault_root / quick_notes_folder
    notes_path = vault_root / notes_folder

    if not quick_notes_path.exists() or not quick_notes_path.is_dir():
        logger.error(f"Quick notes folder '{quick_notes_folder}' not found in vault")
        return

    if not notes_path.exists() or not notes_path.is_dir():
        logger.error(f"Notes folder '{notes_folder}' not found in vault")
        return

    total_processed = 0
    total_moved = 0
    folders_created = set()

    # Get meeting tag from config
    meeting_tag = config.meetings.auto_tag if config else "meeting"

    # Recursively find all markdown files in the quick notes directory tree
    for markdown_file in quick_notes_path.rglob("*.md"):
        try:
            # First process the file to extract tags and add metadata
            process_file(
                markdown_file,
                vault_root,
                dry_run,
                backup_ext,
                logger,
                format_md,
                config,
            )

            # Read the file content after processing
            with markdown_file.open("r", encoding="utf-8") as file:
                text = file.read()

            frontmatter, body = split_frontmatter(text)

            # Extract tags from frontmatter
            tags = frontmatter.get("tags", []) if frontmatter else []
            if not isinstance(tags, list):
                tags = []

            # Check if file has meeting tag - if so, move to meetings folder
            has_meeting_tag = meeting_tag.lower() in [tag.lower() for tag in tags]

            if has_meeting_tag:
                # Move to meetings folder
                meetings_path = vault_root / meetings_folder

                # Move the file
                if _move_file_to_folder(
                    markdown_file,
                    meetings_path,
                    vault_root,
                    backup_ext,
                    dry_run,
                    logger,
                    text,
                    meetings_folder,
                    f"{meetings_folder}/{markdown_file.name}",
                ):
                    total_moved += 1
                    folders_created.add(meetings_folder)

                total_processed += 1
                continue

            # Find the first matching target tag (including subtags)
            target_folder = _find_target_folder_for_tags(tags, config)

            # If we found a matching tag, move the file to that folder in Notes
            # Otherwise, move to "various" folder in Notes
            if not target_folder:
                target_folder = "various"

            # Create the target directory path in the Notes folder
            target_dir = notes_path / target_folder

            # Move the file
            if _move_file_to_folder(
                markdown_file,
                target_dir,
                vault_root,
                backup_ext,
                dry_run,
                logger,
                text,
                target_folder,
                f"{notes_folder}/{target_folder}/{markdown_file.name}",
            ):
                total_moved += 1
                folders_created.add(target_folder)

            total_processed += 1

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {markdown_file}: {e}")
            continue

    # Print summary
    console.print("[bold green]Quick Notes Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed}[/]")
    console.print(f"Files moved: [bold]{total_moved}[/]")
    console.print(f"Folders created: [bold]{len(folders_created)}[/]")
    if folders_created:
        console.print(f"Created folders: [bold]{', '.join(sorted(folders_created))}[/]")
