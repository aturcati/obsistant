"""Tag extraction functions for obsistant."""

from __future__ import annotations

import re

from ..config import Config


def extract_tags(body: str, config: Config | None = None) -> tuple[set[str], str]:
    """Extract tags from the content and remove them from the text.

    Only extracts tags that are not inside:
    - Code blocks (both inline and block)
    - HTML comments
    - Markdown links
    - Quoted strings
    - URLs or other contexts where # is part of a longer string

    Args:
        body: Body content to extract tags from.
        config: Optional configuration object.

    Returns:
        Tuple of (set of tags, cleaned body text).
    """
    tag_regex = config.tags.tag_regex if config else r"(?<!\w)#([\w/-]+)(?=\s|$)"

    tags = set()
    clean_body = body

    # Find all potential tag matches with their positions
    tag_matches = list(re.finditer(tag_regex, body))

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
    # Only strip leading whitespace, preserve trailing whitespace as it indicates where tags were removed
    clean_body = clean_body.lstrip()
    return tags, clean_body


def _is_tag_in_valid_context(body: str, start: int, end: int) -> bool:
    """Determine if a found tag is in a context where it should be ignored.

    Args:
        body: Body content.
        start: Start position of the tag.
        end: End position of the tag.

    Returns:
        True if tag should be extracted, False if it should be ignored.
    """
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
    """Check if position is inside a fenced code block.

    Args:
        body: Body content.
        pos: Position to check.

    Returns:
        True if position is inside a code block.
    """
    # Count how many ``` we've seen before this position
    code_block_markers = [
        m.start() for m in re.finditer(r"^```", body[:pos], re.MULTILINE)
    ]

    # If we have odd number of markers, we're in a code block
    return len(code_block_markers) % 2 == 1


def _is_in_inline_code(body: str, start: int, end: int) -> bool:
    """Check if position is inside inline code (backticks).

    Args:
        body: Body content.
        start: Start position.
        end: End position.

    Returns:
        True if position is inside inline code.
    """
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
    """Check if position is inside an HTML comment.

    Args:
        body: Body content.
        pos: Position to check.

    Returns:
        True if position is inside an HTML comment.
    """
    # Find the last comment start before this position
    last_comment_start = body.rfind("<!--", 0, pos)
    if last_comment_start == -1:
        return False

    # Find the corresponding comment end
    comment_end = body.find("-->", last_comment_start)

    # If there's no end, or the end is after our position, we're in a comment
    return comment_end == -1 or comment_end > pos


def _is_in_markdown_link(body: str, pos: int) -> bool:
    """Check if position is inside a markdown link.

    Args:
        body: Body content.
        pos: Position to check.

    Returns:
        True if position is inside a markdown link.
    """
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
    """Check if position is inside a quoted string.

    Args:
        body: Body content.
        start: Start position.
        end: End position.

    Returns:
        True if position is inside a quoted string.
    """
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


def extract_granola_link(
    body: str, config: Config | None = None
) -> tuple[str | None, str]:
    """Extract meeting transcript URL from 'Chat with meeting transcript:' text and remove it.

    Args:
        body: Body content to search.
        config: Optional configuration object.

    Returns:
        Tuple of (URL string or None, cleaned body text).
    """
    link_pattern = (
        config.granola.link_pattern
        if config
        else r"Chat with meeting transcript:\s*\[([^\]]+)\]\([^\)]+\)"
    )

    match = re.search(link_pattern, body, re.IGNORECASE)

    if match:
        url = match.group(1)  # Extract the URL from the markdown link
        # Remove the entire "Chat with meeting transcript: [URL](URL)" text
        clean_body = re.sub(link_pattern, "", body, flags=re.IGNORECASE)
        # Clean up any extra whitespace and empty lines
        clean_body = re.sub(r"\n\s*\n\s*\n", "\n\n", clean_body)
        clean_body = re.sub(r"^\s*$", "", clean_body, flags=re.MULTILINE)
        return url, clean_body.strip()

    return None, body
