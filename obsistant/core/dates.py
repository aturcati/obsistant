"""Date parsing and extraction functions for obsistant."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ..config import Config

# Default date formats
_DEFAULT_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%B %d, %Y",
    "%B %d %Y",
    "%b %d, %Y",
    "%b %d %Y",
    "%b. %d, %Y",
    "%b. %d %Y",
]

# Default date patterns
_DEFAULT_DATE_PATTERNS = [
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    r"(\d{1,2}[./]\d{1,2}[./]\d{4})",
    r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
    r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})",
]


def parse_date_string(date_str: str, config: Config | None = None) -> datetime | None:
    """Parse various date string formats into a datetime object.

    Args:
        date_str: Date string to parse.
        config: Optional configuration object.

    Returns:
        Datetime object or None if parsing fails.
    """
    date_formats = config.processing.date_formats if config else _DEFAULT_DATE_FORMATS

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def extract_date_from_body(body: str, config: Config | None = None) -> str | None:
    """Extract date from the first few lines of the note body.

    Looks for various date formats in the first 10 lines of the content.
    Returns the date in ISO format (YYYY-MM-DD) if found, None otherwise.

    Args:
        body: Body content to search for dates.
        config: Optional configuration object.

    Returns:
        Date string in ISO format or None.
    """
    if not body:
        return None

    date_patterns = (
        config.processing.date_patterns if config else _DEFAULT_DATE_PATTERNS
    )

    # Split body into lines and check only the first 10 lines
    lines = body.strip().split("\n")[:10]

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
                    parsed_date = parse_date_string(date_str, config)
                    if parsed_date:
                        return parsed_date.strftime("%Y-%m-%d")
                except Exception:
                    continue

    return None


def get_file_creation_date(path: Path) -> str:
    """Get the file creation date in ISO format.

    Args:
        path: Path to the file.

    Returns:
        Date string in ISO format (YYYY-MM-DD).
    """
    try:
        # On macOS, use st_birthtime for creation time
        stat = path.stat()
        # macOS/BSD creation time, fallback to modification time on other systems
        creation_time = getattr(stat, "st_birthtime", stat.st_mtime)

        # Convert to ISO format date string
        return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
    except OSError:
        # If we can't get the creation date, use current date
        return datetime.now().strftime("%Y-%m-%d")


def get_file_modification_date(path: Path) -> str:
    """Get the file modification date in ISO format.

    Args:
        path: Path to the file.

    Returns:
        Date string in ISO format (YYYY-MM-DD).
    """
    try:
        stat = path.stat()
        modification_time = stat.st_mtime
        # Convert to ISO format date string
        return datetime.fromtimestamp(modification_time).strftime("%Y-%m-%d")
    except OSError:
        # If we can't get the modification date, use current date
        return datetime.now().strftime("%Y-%m-%d")
