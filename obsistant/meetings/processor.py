"""Meeting processing functions for obsistant."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import Config
from ..core import process_file, split_frontmatter
from ..core.dates import get_file_creation_date
from ..core.frontmatter import render_frontmatter
from ..utils import console

if TYPE_CHECKING:
    from typing import Any


def process_meetings_folder(
    vault_root: Path,
    meetings_folder: str,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
    config: Config | None = None,
) -> None:
    """Process all files in the Meetings folder to rename them and ensure they have the 'meeting' tag.

    Renames files using the template: YYMMDD_Title
    where YYMMDD comes from frontmatter 'created' field or file creation date.
    Also ensures all files have the 'meeting' tag.
    Archives meetings older than configured working weeks to Archive/YYYY/ folders.

    Args:
        vault_root: Root directory of the vault.
        meetings_folder: Name of the meetings folder.
        dry_run: If True, don't write changes.
        backup_ext: Extension for backup files.
        logger: Logger instance.
        format_md: If True, format markdown.
        config: Optional configuration object.
    """
    from ..backup.operations import create_backup_path

    meetings_path = vault_root / meetings_folder

    if not meetings_path.exists() or not meetings_path.is_dir():
        logger.error(f"Meetings folder '{meetings_folder}' not found in vault")
        return

    total_processed = 0
    total_renamed = 0
    total_meeting_tags_added = 0
    total_archived = 0

    # Calculate the cutoff date for archiving
    archive_weeks = config.meetings.archive_weeks if config else 2
    cutoff_date = _calculate_archive_cutoff_date(archive_weeks)
    auto_tag = config.meetings.auto_tag if config else "meeting"

    for markdown_file in meetings_path.rglob("*.md"):
        relative_parts = markdown_file.relative_to(meetings_path).parts
        if relative_parts and relative_parts[0] == "Archive":
            continue
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

            # Extract existing tags from frontmatter
            existing_tags = set(frontmatter.get("tags", [])) if frontmatter else set()

            # Check if we need to add the meeting tag
            needs_meeting_tag = auto_tag not in existing_tags
            if needs_meeting_tag:
                existing_tags.add(auto_tag)
                total_meeting_tags_added += 1

            # Update frontmatter with meeting tag if needed
            if needs_meeting_tag:
                if frontmatter is None:
                    frontmatter = {}
                frontmatter["tags"] = sorted(existing_tags)

                # Write the updated content back
                new_text = render_frontmatter(frontmatter) + body

                if not dry_run:
                    # Create backup
                    backup_path = create_backup_path(
                        vault_root, markdown_file, backup_ext
                    )
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    backup_path.write_text(text, encoding="utf-8")

                    # Write updated content
                    markdown_file.write_text(new_text, encoding="utf-8")
                    logger.info(f"Added '{auto_tag}' tag to {markdown_file.name}")
                else:
                    logger.info(
                        f"[DRY RUN] Would add '{auto_tag}' tag to {markdown_file.name}"
                    )

            # Generate new filename based on template
            new_filename = _generate_meeting_filename(
                markdown_file, frontmatter or {}, config
            )
            current_file = markdown_file

            if new_filename and new_filename != markdown_file.name:
                new_path = markdown_file.parent / new_filename

                # Check if target file already exists
                if new_path.exists():
                    logger.warning(
                        f"Target file {new_filename} already exists, skipping rename"
                    )
                else:
                    if not dry_run:
                        markdown_file.rename(new_path)
                        logger.info(f"Renamed {markdown_file.name} -> {new_filename}")
                        current_file = new_path
                    else:
                        logger.info(
                            f"[DRY RUN] Would rename {markdown_file.name} -> {new_filename}"
                        )
                    total_renamed += 1

            # Check if this meeting should be archived
            meeting_date = _extract_meeting_date(current_file, frontmatter or {})
            if meeting_date and meeting_date < cutoff_date:
                archive_result = _archive_meeting_file(
                    current_file, meetings_path, meeting_date, dry_run, logger
                )
                if archive_result:
                    total_archived += 1

            total_processed += 1

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {markdown_file}: {e}")
            continue

    # Print summary
    console.print("[bold green]Meetings Folder Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed}[/]")
    console.print(f"Files renamed: [bold]{total_renamed}[/]")
    console.print(f"'{auto_tag}' tags added: [bold]{total_meeting_tags_added}[/]")
    console.print(f"Files archived: [bold]{total_archived}[/]")


def _generate_meeting_filename(
    file_path: Path, frontmatter: dict[str, Any], config: Config | None = None
) -> str | None:
    """Generate a new filename for a meeting file based on the template YYMMDD_Title.

    Args:
        file_path: Path to the original file.
        frontmatter: Frontmatter dictionary containing tags and other metadata.
        config: Optional configuration object.

    Returns:
        New filename string or None if generation fails.
    """
    try:
        # Extract date - try from frontmatter first, then file creation date
        date_str = None
        if "created" in frontmatter:
            date_str = frontmatter["created"]
        else:
            # Fallback to file creation date
            date_str = get_file_creation_date(file_path)

        if not date_str:
            return None

        # Parse date and format as YYMMDD
        try:
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date_obj = date_str
            date_prefix = date_obj.strftime("%y%m%d")
        except (ValueError, AttributeError):
            return None

        # Extract title from filename (remove .md extension)
        title = file_path.stem

        # Remove any existing date prefix pattern from title
        # Pattern: YYMMDD_ at the beginning
        title = re.sub(r"^\d{6}_", "", title)

        # Clean up title - remove any leading/trailing underscores or hyphens
        title = title.strip("_-")

        # Build new filename with just date and title
        new_filename = f"{date_prefix}_{title}.md"

        # Clean up any double underscores or other artifacts
        new_filename = re.sub(r"_{2,}", "_", new_filename)

        return new_filename

    except Exception:
        return None


def _calculate_archive_cutoff_date(archive_weeks: int = 2) -> datetime:
    """Calculate the cutoff date for archiving meetings.

    Args:
        archive_weeks: Number of working weeks to keep meetings before archiving.

    Returns:
        The cutoff date, meetings older than this should be archived.
    """
    today = datetime.now()

    # Calculate working weeks (5 business days per week)
    working_days_back = archive_weeks * 5
    current_date = today

    while working_days_back > 0:
        current_date -= timedelta(days=1)
        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:  # Monday to Friday
            working_days_back -= 1

    return current_date


def _extract_meeting_date(
    file_path: Path, frontmatter: dict[str, Any]
) -> datetime | None:
    """Extract the meeting date from frontmatter or filename.

    Args:
        file_path: Path to the meeting file.
        frontmatter: Frontmatter dictionary.

    Returns:
        The meeting date or None if not found.
    """
    # Try frontmatter 'created' field first
    if "created" in frontmatter:
        date_str = frontmatter["created"]
        if isinstance(date_str, str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass

    # Try to extract date from filename (YYMMDD format)
    filename = file_path.stem
    date_match = re.match(r"^(\d{6})_", filename)
    if date_match:
        date_str = date_match.group(1)
        try:
            # Parse YYMMDD format
            return datetime.strptime(date_str, "%y%m%d")
        except ValueError:
            pass

    # Fallback to file creation date
    try:
        stat = file_path.stat()
        # macOS/BSD creation time, fallback to modification time on other systems
        creation_time = getattr(stat, "st_birthtime", stat.st_mtime)
        return datetime.fromtimestamp(creation_time)
    except OSError:
        return None


def _archive_meeting_file(
    file_path: Path,
    meetings_path: Path,
    meeting_date: datetime,
    dry_run: bool,
    logger: Any,
) -> bool:
    """Archive a meeting file to the Archive/YYYY/ folder.

    Args:
        file_path: Path to the meeting file.
        meetings_path: Path to the meetings folder.
        meeting_date: Date of the meeting.
        dry_run: Whether this is a dry run.
        logger: Logger instance.

    Returns:
        True if file was archived, False otherwise.
    """
    # Create archive folder structure: Archive/YYYY/
    year = meeting_date.year
    archive_dir = meetings_path / "Archive" / str(year)
    archive_path = archive_dir / file_path.name

    # Skip if file is already in archive
    if "Archive" in str(file_path.relative_to(meetings_path)):
        return False

    # Skip if target file already exists
    if archive_path.exists():
        logger.warning(
            f"Archive file {archive_path.relative_to(meetings_path)} already exists, skipping"
        )
        return False

    # Create archive directory if needed
    if not archive_dir.exists():
        if not dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"Created archive folder: {archive_dir.relative_to(meetings_path)}"
            )
        else:
            logger.info(
                f"[DRY RUN] Would create archive folder: {archive_dir.relative_to(meetings_path)}"
            )

    # Move file to archive
    if not dry_run:
        file_path.rename(archive_path)
        logger.info(f"Archived {file_path.name} -> Archive/{year}/{file_path.name}")
    else:
        logger.info(
            f"[DRY RUN] Would archive {file_path.name} -> Archive/{year}/{file_path.name}"
        )

    return True
