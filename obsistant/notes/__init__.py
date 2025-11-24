"""Notes organization operations for obsistant.

This module handles organizing notes by tags and processing quick notes.
"""

from .processor import process_notes_folder, process_quick_notes_folder

__all__ = ["process_notes_folder", "process_quick_notes_folder"]
