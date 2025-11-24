"""Vault-wide operations for obsistant.

This module handles vault-level processing and orchestration.
"""

from .init import init_vault
from .processor import process_vault

__all__ = ["process_vault", "init_vault"]
