"""Processing logic for obsidian formatter."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import mdformat
import yaml

from .utils import console, log_change

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

TAG_REGEX = r"(?<!\w)#([\w/-]+)(?=\s|$)"


def walk_markdown_files(root: Path) -> Iterator[Path]:
    """Walk through the directory to find .md files."""
    return root.rglob("*.md")


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split the front matter and return it with the content."""
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


def extract_tags(body: str) -> tuple[set[str], str]:
    """Use regex to extract tags from the content and remove them from the text.

    Only extracts tags that are not inside:
    - Code blocks (both inline and block)
    - HTML comments
    - Markdown links
    - Quoted strings
    - URLs or other contexts where # is part of a longer string
    """
    tags = set()
    clean_body = body

    # Find all potential tag matches with their positions
    tag_matches = list(re.finditer(TAG_REGEX, body))

    # Filter out tags that are in excluded contexts
    valid_tags = []
    for match in tag_matches:
        if _is_tag_in_valid_context(body, match.start(), match.end()):
            valid_tags.append(match)
            tags.add(match.group(1))

    # Remove valid tags from the body text (in reverse order to maintain positions)
    for match in reversed(valid_tags):
        clean_body = clean_body[: match.start()] + clean_body[match.end() :]

    # Clean up any extra whitespace that might be left, but preserve line structure
    # Remove standalone whitespace on lines where tags were removed
    clean_body = re.sub(r"^\s*$", "", clean_body, flags=re.MULTILINE)
    # Collapse multiple consecutive empty lines into at most two (preserving paragraph breaks)
    clean_body = re.sub(r"\n{3,}", "\n\n", clean_body)
    # Clean up any trailing/leading whitespace
    return tags, clean_body.strip()


def _is_tag_in_valid_context(body: str, start: int, end: int) -> bool:
    """Determine if a found tag is in a context where it should be ignored."""

    # Check for code blocks (fenced code blocks)
    if _is_in_code_block(body, start):
        return False

    # Check for inline code (backticks)
    if _is_in_inline_code(body, start, end):
        return False

    # Check for HTML comments
    if _is_in_html_comment(body, start):
        return False

    # Check for markdown links
    if _is_in_markdown_link(body, start):
        return False

    # Check for quoted strings
    if _is_in_quoted_string(body, start, end):
        return False

    return True


def _is_in_code_block(body: str, pos: int) -> bool:
    """Check if position is inside a fenced code block."""
    # Count how many ``` we've seen before this position
    code_block_markers = [
        m.start() for m in re.finditer(r"^```", body[:pos], re.MULTILINE)
    ]

    # If we have odd number of markers, we're in a code block
    return len(code_block_markers) % 2 == 1


def _is_in_inline_code(body: str, start: int, end: int) -> bool:
    """Check if position is inside inline code (backticks)."""
    # Look for backticks around the tag
    line_start = body.rfind("\n", 0, start) + 1
    line_end = body.find("\n", end)
    if line_end == -1:
        line_end = len(body)

    line = body[line_start:line_end]
    tag_pos_in_line = start - line_start

    # Count backticks before and after the tag position in the line
    backticks_before = line[:tag_pos_in_line].count("`")
    backticks_after = line[tag_pos_in_line:].count("`")

    # If we have odd number of backticks before and at least one after,
    # we're likely inside inline code
    return backticks_before % 2 == 1 and backticks_after > 0


def _is_in_html_comment(body: str, pos: int) -> bool:
    """Check if position is inside an HTML comment."""
    # Find the last comment start before this position
    last_comment_start = body.rfind("<!--", 0, pos)
    if last_comment_start == -1:
        return False

    # Find the corresponding comment end
    comment_end = body.find("-->", last_comment_start)

    # If there's no end, or the end is after our position, we're in a comment
    return comment_end == -1 or comment_end > pos


def _is_in_markdown_link(body: str, pos: int) -> bool:
    """Check if position is inside a markdown link."""
    # Look for markdown link pattern around the position
    # Pattern: [text](url)

    # Find potential link start before our position
    line_start = body.rfind("\n", 0, pos) + 1
    line_end = body.find("\n", pos)
    if line_end == -1:
        line_end = len(body)

    line = body[line_start:line_end]
    pos_in_line = pos - line_start

    # Look for link patterns that contain our position
    for match in re.finditer(r"\[([^\]]+)\]\(([^\)]+)\)", line):
        if match.start() <= pos_in_line < match.end():
            return True

    return False


def _is_in_quoted_string(body: str, start: int, end: int) -> bool:
    """Check if position is inside a quoted string."""
    # Look at the line containing the tag
    line_start = body.rfind("\n", 0, start) + 1
    line_end = body.find("\n", end)
    if line_end == -1:
        line_end = len(body)

    line = body[line_start:line_end]
    tag_start_in_line = start - line_start
    tag_end_in_line = end - line_start

    # Check for double quotes
    quote_positions = [m.start() for m in re.finditer(r'"', line)]

    # Count how many quotes come before the tag
    quotes_before = sum(1 for pos in quote_positions if pos < tag_start_in_line)
    quotes_after = sum(1 for pos in quote_positions if pos > tag_end_in_line)

    # If we have odd number of quotes before and at least one after,
    # we're likely inside a quoted string
    return quotes_before % 2 == 1 and quotes_after > 0


def extract_granola_link(body: str) -> tuple[str | None, str]:
    """Extract meeting transcript URL from 'Chat with meeting transcript:' text and remove it."""
    # Pattern to match "Chat with meeting transcript:" followed by a markdown link
    # Example: "Chat with meeting transcript: [https://notes.granola.ai/d/...](https://notes.granola.ai/d/...)"
    pattern = r"Chat with meeting transcript:\s*\[([^\]]+)\]\([^\)]+\)"
    match = re.search(pattern, body, re.IGNORECASE)

    if match:
        url = match.group(1)  # Extract the URL from the markdown link
        # Remove the entire "Chat with meeting transcript: [URL](URL)" text
        clean_body = re.sub(pattern, "", body, flags=re.IGNORECASE)
        # Clean up any extra whitespace and empty lines
        clean_body = re.sub(r"\n\s*\n\s*\n", "\n\n", clean_body)
        clean_body = re.sub(r"^\s*$", "", clean_body, flags=re.MULTILINE)
        return url, clean_body.strip()

    return None, body


def extract_date_from_body(body: str) -> str | None:
    """Extract date from the first few lines of the note body.

    Looks for various date formats in the first 10 lines of the content.
    Returns the date in ISO format (YYYY-MM-DD) if found, None otherwise.
    """
    if not body:
        return None

    # Split body into lines and check only the first 10 lines
    lines = body.strip().split("\n")[:10]

    # Common date patterns to look for
    date_patterns = [
        # ISO format: 2024-01-15, 2024/01/15
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        # US format: 01/15/2024, 1/15/2024
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        # European format: 15/01/2024, 15.01.2024
        r"(\d{1,2}[./]\d{1,2}[./]\d{4})",
        # Long format: January 15, 2024
        r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
        # Short format: Jan 15, 2024
        r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})",
    ]

    for line in lines:
        # Skip empty lines and lines that are just headers
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        for pattern in date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse the date and convert to ISO format
                    parsed_date = parse_date_string(date_str)
                    if parsed_date:
                        return parsed_date.strftime("%Y-%m-%d")
                except Exception:
                    continue

    return None


def parse_date_string(date_str: str) -> datetime | None:
    """Parse various date string formats into a datetime object."""
    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",  # 2024-01-15
        "%Y/%m/%d",  # 2024/01/15
        "%m/%d/%Y",  # 01/15/2024
        "%m-%d-%Y",  # 01-15-2024
        "%d/%m/%Y",  # 15/01/2024
        "%d.%m.%Y",  # 15.01.2024
        "%B %d, %Y",  # January 15, 2024
        "%B %d %Y",  # January 15 2024
        "%b %d, %Y",  # Jan 15, 2024
        "%b %d %Y",  # Jan 15 2024
        "%b. %d, %Y",  # Jan. 15, 2024
        "%b. %d %Y",  # Jan. 15 2024
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def get_file_creation_date(path: Path) -> str:
    """Get the file creation date in ISO format."""
    try:
        # On macOS, use st_birthtime for creation time
        stat = path.stat()
        if hasattr(stat, "st_birthtime"):
            # macOS/BSD creation time
            creation_time = stat.st_birthtime
        else:
            # Fallback to modification time on other systems
            creation_time = stat.st_mtime

        # Convert to ISO format date string
        return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
    except OSError:
        # If we can't get the creation date, use current date
        return datetime.now().strftime("%Y-%m-%d")


def get_file_modification_date(path: Path) -> str:
    """Get the file modification date in ISO format."""
    try:
        stat = path.stat()
        modification_time = stat.st_mtime
        # Convert to ISO format date string
        return datetime.fromtimestamp(modification_time).strftime("%Y-%m-%d")
    except OSError:
        # If we can't get the modification date, use current date
        return datetime.now().strftime("%Y-%m-%d")


def merge_frontmatter(
    orig: dict[str, Any] | None,
    tags: set[str],
    meeting_transcript: str | None = None,
    file_path: Path | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Merge tags, meeting-transcript, creation date, and modification date into existing front matter ensuring no duplication.

    Properties are ordered as: created, modified, meeting-transcript, tags, then any other existing properties.
    """
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
            body_date = extract_date_from_body(body)
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
    """Convert the data back to front matter format."""
    return "---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n"


def format_markdown(text: str) -> str:
    """Format markdown text using mdformat for consistent styling."""
    try:
        result = mdformat.text(
            text,
            options={
                "wrap": "no",  # Don't wrap lines
                "number": False,  # Don't number lists
            },
        )
        return str(result)
    except Exception:
        # If formatting fails, return original text
        return text


def create_backup_path(vault_root: Path, file_path: Path, backup_ext: str) -> Path:
    """Create backup path that mirrors the vault structure in a backup folder."""
    # Create backup folder in the same directory as the vault
    backup_root = vault_root.parent / f"{vault_root.name}_backups"

    # Get relative path from vault root
    relative_path = file_path.relative_to(vault_root)

    # Create backup path with same structure
    backup_path = backup_root / relative_path
    backup_path = backup_path.with_suffix(backup_path.suffix + backup_ext)

    return backup_path


def clear_backups(vault_root: Path) -> int:
    """Clear all backup files for a vault. Returns count of deleted files."""
    backup_root = vault_root.parent / f"{vault_root.name}_backups"

    if not backup_root.exists():
        return 0

    deleted_count = 0

    # Remove all files in backup directory
    for backup_file in backup_root.rglob("*"):
        if backup_file.is_file():
            backup_file.unlink()
            deleted_count += 1

    # Remove empty directories
    for backup_dir in sorted(
        backup_root.rglob("*"), key=lambda x: str(x), reverse=True
    ):
        if backup_dir.is_dir() and not any(backup_dir.iterdir()):
            backup_dir.rmdir()

    # Remove backup root if empty
    if backup_root.exists() and not any(backup_root.iterdir()):
        backup_root.rmdir()

    return deleted_count


def restore_files(vault_root: Path, specific_file: Path | None = None) -> int:
    """Restore corrupted files from backups. Returns count of restored files."""
    backup_root = vault_root.parent / f"{vault_root.name}_backups"

    if not backup_root.exists():
        return 0

    restored_count = 0

    if specific_file:
        # Restore a specific file
        backup_path = create_backup_path(vault_root, specific_file, ".bak")
        if backup_path.exists():
            try:
                backup_content = backup_path.read_text(encoding="utf-8")
                specific_file.write_text(backup_content, encoding="utf-8")
                restored_count = 1
            except (OSError, UnicodeDecodeError):
                pass
    else:
        # Restore all files
        for backup_file in backup_root.rglob("*.bak"):
            if backup_file.is_file():
                try:
                    # Calculate the original file path
                    relative_path = backup_file.relative_to(backup_root)
                    # Remove the .bak extension
                    original_relative_path = relative_path.with_suffix(
                        relative_path.suffix.replace(".bak", "")
                    )
                    original_path = vault_root / original_relative_path

                    # Read backup content and restore
                    backup_content = backup_file.read_text(encoding="utf-8")
                    # Ensure parent directory exists
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    original_path.write_text(backup_content, encoding="utf-8")
                    restored_count += 1
                except (OSError, UnicodeDecodeError):
                    # Skip files that can't be read or restored
                    continue

    return restored_count


def process_file(
    path: Path,
    vault_root: Path,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
) -> dict[str, Any]:
    """Process each file: read, modify, and write with a backup.

    Returns:
        dict: Statistics about the processing (added_tags, removed_tags, processed)
    """
    stats = {"added_tags": 0, "removed_tags": 0, "processed": False}

    try:
        with path.open("r", encoding="utf-8") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Error reading {path}: {e}")
        return stats

    frontmatter, body = split_frontmatter(text)
    original_body = body  # Keep original body for date extraction
    tags, body = extract_tags(body)
    meeting_transcript, body = extract_granola_link(body)

    # Always process files to potentially add creation date
    original_frontmatter = frontmatter.copy() if frontmatter else None
    new_frontmatter = merge_frontmatter(
        frontmatter, tags, meeting_transcript, path, original_body
    )

    # Calculate tag changes
    original_tags = (
        set(original_frontmatter.get("tags", [])) if original_frontmatter else set()
    )
    new_tags = set(new_frontmatter.get("tags", [])) if new_frontmatter else set()
    added_tags = new_tags - original_tags
    removed_tags = original_tags - new_tags

    # Check if we need to process this file
    needs_processing = (
        bool(tags)
        or bool(meeting_transcript)
        or frontmatter is not None
        or format_md
        or new_frontmatter != original_frontmatter  # Creation date was added
    )

    if not needs_processing:
        logger.info(f"No changes needed for {path}")
        return stats

    # Format markdown if requested
    if format_md:
        body = format_markdown(body)

    # Only add frontmatter if we have content for it
    if new_frontmatter:
        new_text = render_frontmatter(new_frontmatter) + body
    else:
        new_text = body

    # Only write if content has changed
    if new_text != text:
        stats["processed"] = True
        stats["added_tags"] = len(added_tags)
        stats["removed_tags"] = len(removed_tags)

        # Use rich logging for changes
        if added_tags or removed_tags:
            log_change(path, added_tags, removed_tags, dry_run)

        if not dry_run:
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
    else:
        logger.info(f"No changes needed for {path}")

    return stats


def process_vault(
    root: str,
    dry_run: bool,
    backup_ext: str,
    logger: Any,
    format_md: bool = False,
) -> None:
    """Orchestrate processing of the entire vault and provide summary statistics."""
    total_added_tags = 0
    total_removed_tags = 0
    total_processed_files = 0

    vault_root = Path(root)

    for markdown_file in walk_markdown_files(vault_root):
        stats = process_file(
            markdown_file, vault_root, dry_run, backup_ext, logger, format_md
        )
        total_added_tags += stats["added_tags"]
        total_removed_tags += stats["removed_tags"]
        if stats["processed"]:
            total_processed_files += 1

    # Print summary statistics using rich
    console.print("[bold green]Vault Processing Summary[/]")
    console.print(f"Total files processed: [bold]{total_processed_files}[/]")
    console.print(f"Total tags added: [bold]{total_added_tags}[/]")
    console.print(f"Total tags removed: [bold]{total_removed_tags}[/]")
