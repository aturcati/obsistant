"""Meeting-specific operations for obsistant.

This module handles processing of meeting notes, including filename generation
and archiving.
"""

from .processor import process_meetings_folder

__all__ = ["process_meetings_folder"]
