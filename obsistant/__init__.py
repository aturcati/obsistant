"""Obsistant package.

A CLI tool to extract #tags from markdown content and add them to YAML frontmatter in Obsidian vaults.
"""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _get_version() -> str:
    """Get version from installed package metadata or pyproject.toml.

    Returns:
        Version string from package metadata (if installed) or pyproject.toml (if in development).
    """
    # Try to get version from installed package metadata first
    try:
        return version("obsistant")
    except PackageNotFoundError:
        # Fall back to reading from pyproject.toml for development
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")
            # Simple regex to extract version from pyproject.toml
            match = re.search(
                r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE
            )
            if match:
                return match.group(1)
        # Last resort fallback
        return "0.0.0"


__version__ = _get_version()
__author__ = "Andrea Turcati"
__license__ = "MIT"

# Public API
__all__ = [
    "__version__",
    "__author__",
    "__license__",
]
