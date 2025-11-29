"""Configuration management for obsistant.

This module handles loading and validating configuration from .obsistant/config.yaml files.
"""

from .env_loader import load_vault_env
from .loader import load_config, save_config
from .schema import (
    Config,
    GranolaConfig,
    MeetingsConfig,
    ProcessingConfig,
    TagsConfig,
    VaultFoldersConfig,
)

__all__ = [
    "Config",
    "VaultFoldersConfig",
    "TagsConfig",
    "MeetingsConfig",
    "ProcessingConfig",
    "GranolaConfig",
    "load_config",
    "save_config",
    "load_vault_env",
]
