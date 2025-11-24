"""File processing functions for obsistant."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import Config

if TYPE_CHECKING:
    from typing import Any


def walk_markdown_files(root: Path) -> Iterator[Path]:
    """Walk through the directory to find .md files.

    Args:
        root: Root directory to search.

    Yields:
        Path objects for each markdown file found.
    """
    return root.rglob("*.md")


def process_file(
    path: Path,
    vault_root: Path,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
    config: Config | None = None,
) -> dict[str, Any]:
    """Process each file: read, modify, and write with a backup.

    Args:
        path: Path to the file to process.
        vault_root: Root directory of the vault.
        dry_run: If True, don't write changes.
        backup_ext: Extension for backup files.
        logger: Logger instance.
        format_md: If True, format markdown.
        config: Optional configuration object.

    Returns:
        Dictionary with statistics about the processing (added_tags, removed_tags, processed).
    """
    from ..backup.operations import create_backup_path
    from ..core.formatting import format_markdown
    from ..core.frontmatter import (
        merge_frontmatter,
        render_frontmatter,
        split_frontmatter,
    )
    from ..core.tags import extract_granola_link, extract_tags
    from ..utils import log_change

    stats = {"added_tags": 0, "removed_tags": 0, "processed": False}

    try:
        with path.open("r", encoding="utf-8") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Error reading {path}: {e}")
        return stats

    frontmatter, body = split_frontmatter(text)
    original_body = body  # Keep original body for date extraction
    tags, body = extract_tags(body, config)
    meeting_transcript, body = extract_granola_link(body, config)

    # Always process files to potentially add creation date
    original_frontmatter = frontmatter.copy() if frontmatter else None
    new_frontmatter = merge_frontmatter(
        frontmatter, tags, meeting_transcript, path, original_body, config
    )

    # Calculate tag changes
    original_tags = (
        set(original_frontmatter.get("tags", [])) if original_frontmatter else set()
    )
    new_tags = set(new_frontmatter.get("tags", [])) if new_frontmatter else set()
    added_tags = new_tags - original_tags
    removed_tags = original_tags - new_tags

    # Always process files for formatting and check for other changes
    needs_processing = format_md or (
        bool(tags) or bool(meeting_transcript) or frontmatter is not None
    )

    # Format markdown regardless, as requested
    if format_md:
        body = format_markdown(body)

    # Only add frontmatter if we have content for it
    if new_frontmatter:
        new_text = render_frontmatter(new_frontmatter) + body
    else:
        new_text = body

    # Check if frontmatter or body has changed after formatting
    if not needs_processing and new_text == text:
        return stats

    # Only write if content has changed
    if new_text != text:
        stats["added_tags"] = len(added_tags)
        stats["removed_tags"] = len(removed_tags)

        # Use rich logging for changes
        if added_tags or removed_tags:
            log_change(path, added_tags, removed_tags, dry_run)

        if not dry_run:
            stats["processed"] = True
            try:
                backup_path = create_backup_path(vault_root, path, backup_ext)
                # Create backup directory if it doesn't exist
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                # Create backup by copying, then overwrite original
                backup_path.write_text(text, encoding="utf-8")
                path.write_text(new_text, encoding="utf-8")
                actions = []
                if tags:
                    actions.append(f"added {len(tags)} tags")
                if meeting_transcript:
                    actions.append("added meeting-transcript")
                if format_md:
                    actions.append("formatted markdown")
                if (
                    original_frontmatter != new_frontmatter
                    and "created" in new_frontmatter
                ):
                    if (
                        original_frontmatter is None
                        or "created" not in original_frontmatter
                    ):
                        actions.append("added creation date")
                if (
                    original_frontmatter != new_frontmatter
                    and "modified" in new_frontmatter
                ):
                    if (
                        original_frontmatter is None
                        or "modified" not in original_frontmatter
                        or original_frontmatter.get("modified")
                        != new_frontmatter.get("modified")
                    ):
                        actions.append("updated modification date")
                logger.info(
                    f"Processed {path} - {' and '.join(actions)} (backup: {backup_path})"
                )
            except OSError as e:
                logger.error(f"Error writing {path}: {e}")
                stats["processed"] = False
                return stats
        else:
            actions = []
            if tags:
                actions.append(f"add {len(tags)} tags")
            if meeting_transcript:
                actions.append("add meeting-transcript")
            if format_md:
                actions.append("format markdown")
            if original_frontmatter != new_frontmatter and "created" in new_frontmatter:
                if (
                    original_frontmatter is None
                    or "created" not in original_frontmatter
                ):
                    actions.append("add creation date")
            if (
                original_frontmatter != new_frontmatter
                and "modified" in new_frontmatter
            ):
                if (
                    original_frontmatter is None
                    or "modified" not in original_frontmatter
                    or original_frontmatter.get("modified")
                    != new_frontmatter.get("modified")
                ):
                    actions.append("update modification date")
            logger.info(f"[DRY RUN] Would process {path} - {' and '.join(actions)}")

    return stats
