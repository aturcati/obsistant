"""Utility functions for obsidian formatter."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()


def log_change(file: Path, added: set[str], removed: set[str], dry: bool) -> None:
    """Log changes made to a file using rich console formatting."""
    console.print(
        f"[bold cyan]{file}[/]: +{len(added)} tags, "
        f"-{len(removed)} tags {'[dry-run]' if dry else ''}"
    )
