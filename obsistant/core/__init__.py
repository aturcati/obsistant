"""Core processing functions for obsistant.

This module contains core functionality for processing markdown files,
including frontmatter handling, tag extraction, formatting, and date parsing.
"""

from .dates import (
    extract_date_from_body,
    get_file_creation_date,
    get_file_modification_date,
    parse_date_string,
)
from .file_processing import process_file, walk_markdown_files
from .formatting import format_markdown
from .frontmatter import merge_frontmatter, render_frontmatter, split_frontmatter
from .tags import extract_granola_link, extract_tags

__all__ = [
    "split_frontmatter",
    "merge_frontmatter",
    "render_frontmatter",
    "extract_tags",
    "extract_granola_link",
    "extract_date_from_body",
    "parse_date_string",
    "get_file_creation_date",
    "get_file_modification_date",
    "format_markdown",
    "process_file",
    "walk_markdown_files",
]
