"""Frontmatter processing functions for obsistant."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..config import Config


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split the front matter and return it with the content.

    Args:
        text: The markdown text with optional frontmatter.

    Returns:
        Tuple of (frontmatter dict or None, content string).
    """
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2]
                return frontmatter, content
            except yaml.YAMLError:
                # If YAML parsing fails, treat as no frontmatter
                return None, text
    return None, text


def merge_frontmatter(
    orig: dict[str, Any] | None,
    tags: set[str],
    meeting_transcript: str | None = None,
    file_path: Path | None = None,
    body: str | None = None,
    config: Config | None = None,
) -> dict[str, Any]:
    """Merge tags, meeting-transcript, creation date, and modification date into existing front matter.

    Properties are ordered as: created, modified, meeting-transcript, tags, then any other existing properties.

    Args:
        orig: Original frontmatter dictionary or None.
        tags: Set of tags to merge.
        meeting_transcript: Optional meeting transcript URL.
        file_path: Optional path to the file for date extraction.
        body: Optional body content for date extraction.
        config: Optional configuration object.

    Returns:
        Merged frontmatter dictionary.
    """
    from .dates import (
        extract_date_from_body,
        get_file_creation_date,
        get_file_modification_date,
    )

    if orig is None:
        orig = {}

    # Create a new ordered dictionary with the specific order we want
    result = {}

    # 1. Handle creation date - use earliest date found
    if "created" in orig:
        result["created"] = orig["created"]
    else:
        dates_to_compare = []

        # Get date from body content if available
        if body:
            body_date = extract_date_from_body(body, config)
            if body_date:
                dates_to_compare.append(body_date)

        # Get file creation date if file_path is provided
        if file_path:
            file_creation_date = get_file_creation_date(file_path)
            if file_creation_date:
                dates_to_compare.append(file_creation_date)

        # Use the earliest date found
        if dates_to_compare:
            # Sort dates and use the earliest one
            dates_to_compare.sort()
            result["created"] = dates_to_compare[0]

    # 2. Add modification date - always update to latest file modification date
    if file_path:
        result["modified"] = get_file_modification_date(file_path)

    # 3. Add meeting-transcript if provided
    if meeting_transcript:
        result["meeting-transcript"] = meeting_transcript
    elif "meeting-transcript" in orig:
        result["meeting-transcript"] = orig["meeting-transcript"]

    # 4. Handle tags
    orig_tags = set(orig.get("tags", []))
    merged_tags = orig_tags.union(tags)

    # Only set tags if we have any
    if merged_tags:
        result["tags"] = sorted(merged_tags)
    elif "tags" in orig:
        # Preserve existing empty tags field if it was there originally
        result["tags"] = orig["tags"]

    # 5. Add any other existing properties (preserving their order)
    for key, value in orig.items():
        if key not in result:
            result[key] = value

    return result


def render_frontmatter(data: dict[str, Any]) -> str:
    """Convert the data back to front matter format.

    Args:
        data: Dictionary to convert to YAML frontmatter.

    Returns:
        YAML frontmatter string with delimiters.
    """
    return "---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n"
