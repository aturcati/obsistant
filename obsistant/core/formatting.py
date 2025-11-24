"""Markdown formatting functions for obsistant."""

from __future__ import annotations

import importlib.util
import re
from typing import Any

import mdformat

from ..utils import console

MDFORMAT_GFM_AVAILABLE = importlib.util.find_spec("mdformat_gfm") is not None


def format_markdown(text: str) -> str:
    """Format markdown text using mdformat for consistent styling.

    Uses the GitHub Flavored Markdown (GFM) plugin to preserve tables and other
    GFM-specific syntax during formatting. This prevents table structure from
    being corrupted while still applying consistent markdown formatting.

    As a safeguard, detects pipe tables and skips formatting if mdformat-gfm
    is unavailable to prevent table corruption in end-user vaults.

    Args:
        text: Markdown text to format.

    Returns:
        Formatted markdown text.
    """
    # Table detection pattern: pipe table with header separator
    # Matches separator lines like |----------|----------|----------|
    table_pattern = r"\n\s*\|[-: |]+\|\s*\n"
    has_table = bool(re.search(table_pattern, text))

    extensions = {"gfm"} if MDFORMAT_GFM_AVAILABLE else None

    if has_table and not MDFORMAT_GFM_AVAILABLE:
        console.print(
            "[yellow]Warning: Detected pipe table but mdformat-gfm plugin is unavailable. "
            "Skipping formatting to prevent table corruption.[/]"
        )
        return text

    try:
        result = mdformat.text(
            text,
            options={
                "wrap": "no",
                "number": False,
            },
            extensions=extensions or (),
        )

        cleaned_result = _clean_list_blank_lines(result)

        return str(cleaned_result)
    except (ImportError, KeyError, ValueError):
        # mdformat-gfm plugin is not available
        if has_table:
            console.print(
                "[yellow]Warning: Detected pipe table but mdformat-gfm plugin is unavailable. "
                "Skipping formatting to prevent table corruption.[/]"
            )
            return text
        # If no tables, proceed with basic mdformat (fallback)
        try:
            result = mdformat.text(
                text,
                options={
                    "wrap": "no",
                    "number": False,
                },
            )
            cleaned_result = _clean_list_blank_lines(result)
            return str(cleaned_result)
        except Exception:
            return text
    except Exception:
        # If other formatting issues occur
        if has_table:
            console.print(
                "[yellow]Warning: Detected pipe table but formatting failed. "
                "Skipping formatting to prevent table corruption.[/]"
            )
            return text
        # If no tables, return original text as fallback
        return text


def _clean_list_blank_lines(text: str) -> str:
    """Remove blank lines between consecutive list items at the same indent level.

    This post-processes mdformat output to remove excessive blank lines while
    preserving intentional spacing for readability and structure.

    Removes blank lines between:
    - Sibling bullet/unordered list items (-, *, +) at same indent
    - Going from parent to child list items
    - Going from child back to parent/sibling list items

    Preserves blank lines around:
    - Code blocks and fenced content
    - Different markdown elements (headers, paragraphs)
    - Multi-paragraph list item content

    Args:
        text: Text to clean.

    Returns:
        Cleaned text.
    """
    lines = text.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        current_line = lines[i]

        # Check if this is a blank line that might need to be removed
        if current_line.strip() == "" and i > 0:
            # Look for context around this blank line
            prev_line_idx = i - 1
            next_non_blank_idx = _find_next_non_blank_line(lines, i)

            if next_non_blank_idx is not None:
                prev_line = lines[prev_line_idx]
                next_line = lines[next_non_blank_idx]

                prev_list_info = _parse_list_item(prev_line)
                next_list_info = _parse_list_item(next_line)

                # Special case: Don't remove blank lines directly adjacent to code blocks
                # Check if the previous or next line contains code block markers
                if "```" in prev_line or "```" in next_line:
                    result_lines.append(current_line)
                    i += 1
                    continue

                # Also check if we're between a list item and indented code block content
                if (
                    prev_list_info is not None
                    and next_line.strip().startswith("```")
                    and len(next_line) - len(next_line.lstrip())
                    > prev_list_info["indent"]
                ):
                    result_lines.append(current_line)
                    i += 1
                    continue

                # Both previous and next lines are list items
                if prev_list_info is not None and next_list_info is not None:
                    # Remove blank lines between list items based on the relationship
                    if _should_remove_blank_line_between_lists(
                        prev_list_info, next_list_info, prev_line, next_line
                    ):
                        # Skip this blank line (and any consecutive blank lines)
                        i = next_non_blank_idx
                        continue

                # Previous line is list item, next is indented content
                elif prev_list_info is not None and next_list_info is None:
                    # Check if next line is indented content of the list item
                    if _is_indented_paragraph_content(
                        next_line, prev_list_info["indent"]
                    ):
                        # This is a paragraph within a list item, keep the blank line
                        result_lines.append(current_line)
                        i += 1
                        continue
                    else:
                        # Next line starts a new block, keep blank line
                        result_lines.append(current_line)
                        i += 1
                        continue

        result_lines.append(current_line)
        i += 1

    return "\n".join(result_lines)


def _parse_list_item(line: str) -> dict[str, Any] | None:
    """Parse a line to determine if it's a list item and extract info.

    Returns dict with 'indent', 'marker', 'content' or None if not a list item.

    Args:
        line: Line to parse.

    Returns:
        Dictionary with list item info or None.
    """
    # Match unordered lists (-, *, +) and ordered lists (1., 2., etc.)
    unordered_pattern = r"^([ \t]*)([-*+])[ \t]+(.*)$"
    ordered_pattern = r"^([ \t]*)(\d+\.)[ \t]+(.*)$"
    # Also match lettered lists like a., b., i., ii., etc.
    lettered_pattern = r"^([ \t]*)([a-z]+\.|[ivx]+\.)[ \t]+(.*)$"

    # Try unordered list pattern first
    match = re.match(unordered_pattern, line)
    if match:
        return {
            "indent": len(match.group(1)),
            "marker": match.group(2),
            "content": match.group(3),
            "type": "unordered",
        }

    # Try ordered list pattern
    match = re.match(ordered_pattern, line)
    if match:
        return {
            "indent": len(match.group(1)),
            "marker": match.group(2),
            "content": match.group(3),
            "type": "ordered",
        }

    # Try lettered list pattern
    match = re.match(lettered_pattern, line)
    if match:
        return {
            "indent": len(match.group(1)),
            "marker": match.group(2),
            "content": match.group(3),
            "type": "lettered",
        }

    return None


def _should_remove_blank_line_between_lists(
    prev_list_info: dict[str, Any],
    next_list_info: dict[str, Any],
    prev_line: str,
    next_line: str,
) -> bool:
    """Determine if blank line between two list items should be removed.

    Remove blank lines when:
    - Both items are unordered at the same indent level (sibling unordered items)
    - Both items are the same type and nested appropriately
    - Going from child back to parent within unordered lists

    Preserve blank lines when:
    - Mixing ordered and unordered list types (for readability)
    - Large indent differences (different sections)

    Args:
        prev_list_info: Info about previous list item.
        next_list_info: Info about next list item.
        prev_line: Previous line text.
        next_line: Next line text.

    Returns:
        True if blank line should be removed.
    """
    prev_indent = prev_list_info["indent"]
    next_indent = next_list_info["indent"]
    prev_type = prev_list_info["type"]
    next_type = next_list_info["type"]

    # Same indent level - only remove blank line for same list types
    if prev_indent == next_indent:
        # Only remove blank lines between unordered list items
        # Keep blank lines between ordered items or mixed types for readability
        return bool(prev_type == "unordered" and next_type == "unordered")

    # Next item is indented more than the previous (child of parent)
    # Remove blank line only for unordered parent to unordered child
    if next_indent > prev_indent:
        return bool(prev_type == "unordered" and next_type == "unordered")

    # Next item is indented less than the previous (going back to parent level)
    # Remove blank line only for unordered lists within reasonable indent changes
    if next_indent < prev_indent:
        # Only remove for unordered lists
        if prev_type == "unordered" and next_type == "unordered":
            # If the difference is reasonable (typically 2-5 spaces per level)
            indent_diff = prev_indent - next_indent
            # Allow going back 1-3 levels without blank line
            if indent_diff <= 5:  # Reasonable parent level transition
                return True

    # Keep blank line for other cases (mixed types, new sections, etc.)
    return False


def _find_next_non_blank_line(lines: list[str], start_idx: int) -> int | None:
    """Find the index of the next non-blank line after start_idx.

    Args:
        lines: List of lines.
        start_idx: Starting index.

    Returns:
        Index of next non-blank line or None if not found.
    """
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip() != "":
            return i
    return None


def _is_indented_paragraph_content(line: str, list_indent: int) -> bool:
    """Check if a line is indented paragraph content belonging to a list item.

    Content is considered indented paragraph content if:
    1. It has more indentation than the list marker
    2. It's not itself a list item
    3. It's not a code block or other special markdown element

    Args:
        line: Line to check.
        list_indent: Indentation level of the list item.

    Returns:
        True if line is indented paragraph content.
    """
    if line.strip() == "":
        return False

    # Don't treat other list items as paragraph content
    if _parse_list_item(line) is not None:
        return False

    # Count leading whitespace
    leading_whitespace = len(line) - len(line.lstrip())

    # Content should be indented more than the list item marker
    # Standard markdown indentation is 2-4 spaces for list content
    return leading_whitespace > list_indent
